# ==============================================================================
# DRAWDOWN ROTATION - Rotacion por caida anormal de un activo
# ==============================================================================
# Corre en el ciclo diario (run_cycle, antes de entry_signal_tool):
#
#   1. DETECTOR: un activo del portafolio dispara si su retorno acumulado de las
#      ultimas 5 sesiones es <= -5%. Un archivo de estado evita que la misma
#      caida dispare todos los dias (enfriamiento de 5 sesiones, salvo que caiga
#      otro 5% desde el precio del disparo anterior).
#   2. DIAGNOSTICO por puntaje de deterioro (0-100): lectura de opciones hacia
#      adelante (score tactico de active_management: GEX, flujo, Vanna/Charm),
#      "cansancio" del activo (vol realizada vs su media, expansion del ATR,
#      distancia a su media de 20 dias en sigmas) y severidad de la caida en
#      sigmas semanales -> MANTENER / RECORTAR x% / LIQUIDAR.
#   3. UNIVERSO: top 30 del S&P 500 + top 30 del NASDAQ por market cap (sin
#      duplicados, relleno en orden de market cap; universe.py), o la lista
#      propia, o ambos. Sin los activos que ya estan en el portafolio.
#   4. SCREENER sobre todo el universo: momentum de precio (12-1, ajustado por
#      volatilidad, 3 meses), opciones hacia adelante y frescura (100 - cansancio)
#      -> top 10.
#   5. SELECCION de 1 a 3 activos del top 10: la combinacion que maximiza el
#      Sharpe esperado del portafolio despues del cambio. Covarianza = IV ATM
#      (hacia adelante) x correlacion historica; retorno esperado desde el
#      puntaje. El capital liberado se reparte en partes iguales.
#   6. SALIDA: terminal + figuras HTML (viz_utils). La senal JSON y el estado
#      de rotacion son internos: entry_signal_tool lee el estado y escalona la
#      entrada de los activos nuevos en su ciclo de 5 dias.
# ==============================================================================

from __future__ import annotations

import argparse
import itertools
import math
import os
import warnings
from datetime import date, timedelta

import numpy as np
import pandas as pd

from dotenv import load_dotenv

load_dotenv()

from pipeline_io import (  # noqa: E402
    announce_signals_dir,
    apply_rotation_overrides,
    cycle_today,
    export_signals,
    load_portfolio,
    load_rotation_state,
    resolve_horizon,
    resolve_risk_free_rate,
    save_rotation_state,
)
from polygon_client import PolygonClient, failure_reason  # noqa: E402
from price_signals import price_indicators  # noqa: E402
from tickers import exchange_suffix, options_underlying, to_polygon, to_yahoo  # noqa: E402
from universe import UNIVERSE_MODES, build_universe  # noqa: E402
from viz_utils import show_or_save  # noqa: E402

SCRIPT = "drawdown_rotation"

# ==============================================================================
# BLOQUE 1: CONFIGURACION  <<<  EDITA AQUI  >>>
# ==============================================================================
PORTFOLIO_HOLDINGS = {
    "XLU": 0.12, "GLD": 0.12, "T": 0.1031, "GILD": 0.0925, "FXI": 0.0779,
    "MRK": 0.0734, "ADP": 0.0595, "KO": 0.0578, "ABT": 0.0562, "VRTX": 0.0541,
    "AMGN": 0.0509, "UNP": 0.0485, "NEE": 0.0484, "ABBV": 0.0235, "TMO": 0.0142,
}

# --- universo -----------------------------------------------------------------
UNIVERSE_MODE = os.environ.get("ROTATION_UNIVERSE", "indices")   # indices | custom | both
CUSTOM_TICKERS: list[str] = []          # tu lista propia (o ROTATION_CUSTOM_TICKERS="A,B,C")
N_TOP_SP500 = 30
N_TOP_NASDAQ = 30

# --- detector -----------------------------------------------------------------
DROP_WINDOW_SESSIONS = 5                 # caida acumulada en las ultimas 5 sesiones
DROP_THRESHOLD = -0.05                   # <= -5% dispara
RETRIGGER_EXTRA_DROP = 0.05              # dentro del enfriamiento, otro -5% vuelve a disparar

# --- diagnostico (puntaje de deterioro, 0-100; mas alto = peor) ----------------
DIAG_WEIGHTS = {"opciones": 0.40, "cansancio": 0.30, "severidad": 0.30}
DIAG_HOLD_BELOW = 40.0                   # < 40: MANTENER
DIAG_LIQUIDATE_FROM = 70.0               # >= 70: LIQUIDAR; entre ambos: RECORTAR
DIAG_CUT_RANGE = (0.25, 0.75)            # recorte lineal entre 40 (25%) y 70 (75%)

# --- screener (puntaje de candidato, 0-100; mas alto = mejor) ------------------
SCREEN_WEIGHTS = {"momentum": 0.50, "opciones": 0.35, "frescura": 0.15}
TOP_N = 10
MAX_NEW_ASSETS = 3
# Retorno esperado en exceso = SHARPE_SCALE * (puntaje - 50) / 50 * sigma.
# Un puntaje de 100 equivale a un Sharpe individual de SHARPE_SCALE.
SHARPE_SCALE = 0.5

# --- datos --------------------------------------------------------------------
HISTORY_CALENDAR_DAYS = 420              # ~290 sesiones: alcanza para el momentum 12-1
CORR_SESSIONS = 252                      # ventana de la correlacion historica
RISK_FREE_RATE = resolve_risk_free_rate(0.046)
HORIZON_DEFAULT_DAYS = 42                # vencimiento de opciones, como active_management

# ==============================================================================
# BLOQUE 2: PORTAFOLIO Y ESTADO
# ==============================================================================
_PORTFOLIO_META = load_portfolio(PORTFOLIO_HOLDINGS)
HORIZON = resolve_horizon(_PORTFOLIO_META, HORIZON_DEFAULT_DAYS, mode="remaining")


def _custom_tickers():
    raw = os.environ.get("ROTATION_CUSTOM_TICKERS", "")
    extra = [t.strip() for t in raw.split(",") if t.strip()]
    return list(CUSTOM_TICKERS) + extra


# ==============================================================================
# BLOQUE 3: DATOS DE PRECIO
# ==============================================================================
_cliente = None


def polygon():
    global _cliente
    if _cliente is None:
        _cliente = PolygonClient(api_key=os.environ.get("POLYGON_API_KEY"))
    return _cliente


def _ohlc_polygon(ticker, days):
    end = date.today()
    start = end - timedelta(days=days)
    payload = polygon().get(
        f"/v2/aggs/ticker/{to_polygon(ticker)}/range/1/day/{start.isoformat()}/{end.isoformat()}",
        {"adjusted": "true", "sort": "asc", "limit": 50000},
    )
    rows = payload.get("results") or []
    if not rows:
        raise RuntimeError(f"Polygon no devolvio historico para {ticker}")
    idx = pd.to_datetime([r["t"] for r in rows], unit="ms").normalize()
    return pd.DataFrame({"high": [r["h"] for r in rows], "low": [r["l"] for r in rows],
                         "close": [r["c"] for r in rows]}, index=idx, dtype=float)


def _ohlc_yahoo(ticker, days):
    import yfinance as yf

    hist = yf.Ticker(to_yahoo(ticker)).history(period=f"{max(days // 365 + 1, 2)}y", auto_adjust=True)
    if hist is None or hist.empty:
        raise RuntimeError(f"Yahoo no devolvio historico para {ticker}")
    out = hist[["High", "Low", "Close"]].rename(columns=str.lower).dropna()
    out.index = pd.to_datetime(out.index).tz_localize(None).normalize()
    return out[out.index >= pd.Timestamp(date.today() - timedelta(days=days))]


def fetch_ohlc(ticker, days=HISTORY_CALENDAR_DAYS):
    """Diario high/low/close ajustado. Polygon para tickers de EE. UU., Yahoo para
    listados con sufijo de bolsa (RY.TO) o si Polygon falla."""
    if not exchange_suffix(ticker) and os.environ.get("POLYGON_API_KEY"):
        try:
            return _ohlc_polygon(ticker, days)
        except Exception as exc:  # noqa: BLE001
            print(f"  [precios] {ticker}: Polygon fallo ({failure_reason(exc)}); se usa Yahoo.")
    return _ohlc_yahoo(ticker, days)


# ==============================================================================
# BLOQUE 4: METRICAS DE PRECIO Y "CANSANCIO"
# ==============================================================================
def _wilder_atr(ohlc, period=14):
    prev_close = ohlc["close"].shift(1)
    tr = pd.concat([ohlc["high"] - ohlc["low"], (ohlc["high"] - prev_close).abs(),
                    (ohlc["low"] - prev_close).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def _ret(close, sessions):
    if len(close) <= sessions:
        return np.nan
    base = close.iloc[-1 - sessions]
    return float(close.iloc[-1] / base - 1) if base > 0 else np.nan


def price_metrics(ohlc) -> dict:
    """Metricas de precio de un activo sobre su OHLC diario (orden ascendente)."""
    close = ohlc["close"].astype(float).dropna()
    base = price_indicators(close)
    out = {
        "precio": base["precio"], "rsi14": base["rsi14"], "vol_ratio": base["vol_ratio"],
        "vol_realizada": base["vol_realizada"], "n_sesiones": int(len(close)),
        "ret_5d": _ret(close, DROP_WINDOW_SESSIONS), "ret_3m": _ret(close, 63),
        "ret_6m": _ret(close, 126), "mom_12_1": np.nan, "mom_ajustado": np.nan,
        "atr_ratio": np.nan, "z20": np.nan, "caida_sigmas": np.nan, "vol_1y": np.nan,
    }
    if len(close) > 252:
        base_12m, base_1m = close.iloc[-253], close.iloc[-22]
        if base_12m > 0:
            out["mom_12_1"] = float(base_1m / base_12m - 1)
    rets = np.log(close / close.shift(1)).dropna()
    if len(rets) >= 126:
        vol_6m = float(rets.tail(126).std() * math.sqrt(252))
        if vol_6m > 0 and np.isfinite(out["ret_6m"]):
            out["mom_ajustado"] = out["ret_6m"] / vol_6m
    if len(rets) >= 60:
        out["vol_1y"] = float(rets.tail(252).std() * math.sqrt(252))

    if {"high", "low"}.issubset(ohlc.columns) and len(close) >= 40:
        atr_pct = (_wilder_atr(ohlc.loc[close.index]) / close).dropna()
        media = atr_pct.tail(120).mean()
        if media > 0:
            out["atr_ratio"] = float(atr_pct.iloc[-1] / media)
    if len(close) >= 20:
        ventana = close.tail(20)
        sd = ventana.std()
        if sd > 0:
            out["z20"] = float((close.iloc[-1] - ventana.mean()) / sd)
    rv = out["vol_realizada"]
    if np.isfinite(rv) and rv > 0 and np.isfinite(out["ret_5d"]):
        out["caida_sigmas"] = out["ret_5d"] / (rv * math.sqrt(DROP_WINDOW_SESSIONS / 252))
    return out


def _ratio_score(ratio):
    """0.5x su media -> 0, 1x -> 50, 1.5x o mas -> 100. Sin dato -> 50."""
    if ratio is None or not np.isfinite(ratio):
        return 50.0
    return float(np.clip(ratio - 0.5, 0.0, 1.0) * 100)


def cansancio_score(metrics: dict) -> dict:
    """Cansancio / riesgo del activo, 0-100 (mas alto = mas cansado o riesgoso).

    Reemplaza a la SMA200. Promedio de tres partes:
    - vol realizada de 20 dias contra su media de 120 dias (vol_ratio);
    - ATR% de 14 dias contra su media de 120 dias (expansion del rango);
    - distancia del precio a su media de 20 dias en sigmas (|z20|: 3 sigmas -> 100).
    """
    z = metrics.get("z20")
    partes = {
        "vol": _ratio_score(metrics.get("vol_ratio")),
        "atr": _ratio_score(metrics.get("atr_ratio")),
        "estiramiento": 50.0 if z is None or not np.isfinite(z) else float(np.clip(abs(z) / 3, 0, 1) * 100),
    }
    partes["total"] = float(np.mean([partes["vol"], partes["atr"], partes["estiramiento"]]))
    return partes


def options_risk_score(tactical_score) -> float:
    """Score tactico de active_management (-100..100, alto = favorable) -> riesgo 0-100."""
    if tactical_score is None or not np.isfinite(tactical_score):
        return 50.0
    return float(np.clip((100.0 - tactical_score) / 2.0, 0.0, 100.0))


def options_favor_score(tactical_score) -> float:
    """Score tactico -> favorabilidad 0-100 para un candidato. Sin dato -> 50."""
    if tactical_score is None or not np.isfinite(tactical_score):
        return 50.0
    return float(np.clip((tactical_score + 100.0) / 2.0, 0.0, 100.0))


# ==============================================================================
# BLOQUE 5: DETECTOR Y DIAGNOSTICO
# ==============================================================================
def should_trigger(ticker, metrics, close_index, state_triggers):
    """(dispara, motivo). Enfriamiento: un disparo previo de este activo bloquea
    los siguientes DROP_WINDOW_SESSIONS sesiones, salvo otra caida de
    RETRIGGER_EXTRA_DROP desde el cierre de aquel disparo."""
    ret5 = metrics.get("ret_5d")
    if ret5 is None or not np.isfinite(ret5):
        return False, "sin historico suficiente"
    if ret5 > DROP_THRESHOLD:
        return False, f"{ret5:+.2%} en {DROP_WINDOW_SESSIONS} sesiones"
    previo = (state_triggers or {}).get(ticker)
    if not previo:
        return True, f"{ret5:+.2%} en {DROP_WINDOW_SESSIONS} sesiones"
    try:
        fecha_previa = pd.Timestamp(previo.get("date")).normalize()
    except (TypeError, ValueError):
        return True, f"{ret5:+.2%} (disparo previo ilegible)"
    sesiones = int((pd.DatetimeIndex(close_index) > fecha_previa).sum())
    if sesiones >= DROP_WINDOW_SESSIONS:
        return True, f"{ret5:+.2%} en {DROP_WINDOW_SESSIONS} sesiones (nueva ventana)"
    cierre_previo = previo.get("close")
    precio = metrics.get("precio")
    if cierre_previo and precio and precio <= float(cierre_previo) * (1 - RETRIGGER_EXTRA_DROP):
        return True, (f"{ret5:+.2%}; otro {RETRIGGER_EXTRA_DROP:.0%} bajo el disparo del "
                      f"{previo.get('date')}")
    return False, (f"enfriamiento: disparo el {previo.get('date')} "
                   f"({sesiones}/{DROP_WINDOW_SESSIONS} sesiones)")


def diagnosis_score(metrics: dict, tactical_score) -> dict:
    cans = cansancio_score(metrics)
    sig = metrics.get("caida_sigmas")
    severidad = 50.0 if sig is None or not np.isfinite(sig) else float(np.clip(abs(sig) / 3, 0, 1) * 100)
    partes = {"opciones": options_risk_score(tactical_score), "cansancio": cans["total"],
              "severidad": severidad}
    total = sum(DIAG_WEIGHTS[k] * partes[k] for k in DIAG_WEIGHTS)
    return {"total": float(total), **partes, "cansancio_detalle": cans}


def decide_action(deterioro: float) -> tuple[str, float]:
    """Puntaje de deterioro -> (accion, fraccion del peso actual que se vende)."""
    if deterioro < DIAG_HOLD_BELOW:
        return "MANTENER", 0.0
    if deterioro >= DIAG_LIQUIDATE_FROM:
        return "LIQUIDAR", 1.0
    lo, hi = DIAG_CUT_RANGE
    frac = (deterioro - DIAG_HOLD_BELOW) / (DIAG_LIQUIDATE_FROM - DIAG_HOLD_BELOW)
    return "RECORTAR", float(lo + frac * (hi - lo))


# ==============================================================================
# BLOQUE 6: OPCIONES (lectura hacia adelante, reutiliza active_management)
# ==============================================================================
def options_view(ticker, horizon_days):
    """Score tactico, IV ATM y movimiento esperado del ticker (o de su ADR)."""
    import active_management as am

    simbolo = options_underlying(ticker)
    vacio = {"tactical_score": np.nan, "iv_atm": np.nan, "expected_move_pct": np.nan,
             "rationale": "", "status": "sin opciones"}
    if simbolo is None:
        vacio["status"] = "sin opciones de EE. UU."
        return vacio
    analisis = am.analyze_ticker_options(simbolo, horizon_days)
    if analisis.get("status") != "OK":
        vacio["status"] = analisis.get("exclusion_reason") or "sin datos de opciones"
        return vacio
    tactico = am.calculate_tactical_score(analisis)
    return {
        "tactical_score": float(tactico.get("score")) if tactico.get("score") is not None else np.nan,
        "iv_atm": am.implied_sigma_annual(analisis),
        "expected_move_pct": tactico.get("expected_move_pct", np.nan),
        "rationale": tactico.get("rationale", ""),
        "status": "OK",
    }


# ==============================================================================
# BLOQUE 7: SCREENER Y SELECCION
# ==============================================================================
def _pct_rank(values):
    serie = pd.Series(values, dtype=float)
    return serie.rank(pct=True).fillna(0.5).to_numpy()


def screen_candidates(rows: list[dict]) -> pd.DataFrame:
    """Puntaje 0-100 de cada candidato. ``rows``: ticker + price_metrics + options_view.

    momentum = promedio de los percentiles (dentro del universo) del momentum 12-1,
    el retorno de 6 meses ajustado por volatilidad y el retorno de 3 meses.
    Un candidato que el mismo detector marcaria (cae >= 5% en 5 sesiones) se descarta.
    """
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["momentum"] = 100.0 * np.mean(
        [_pct_rank(df["mom_12_1"]), _pct_rank(df["mom_ajustado"]), _pct_rank(df["ret_3m"])], axis=0)
    df["opciones"] = [options_favor_score(s) for s in df["tactical_score"]]
    df["cansancio"] = [cansancio_score(r)["total"] for r in df.to_dict("records")]
    df["frescura"] = 100.0 - df["cansancio"]
    df["puntaje"] = sum(SCREEN_WEIGHTS[k] * df[k] for k in SCREEN_WEIGHTS)
    df["descartado"] = df["ret_5d"].apply(lambda r: bool(np.isfinite(r) and r <= DROP_THRESHOLD))
    return df.sort_values(["descartado", "puntaje"], ascending=[True, False]).reset_index(drop=True)


def expected_excess(score, sigma):
    if not (np.isfinite(score) and np.isfinite(sigma)):
        return 0.0
    return SHARPE_SCALE * (score - 50.0) / 50.0 * sigma


def portfolio_sharpe(weights, mu, cov):
    w = np.asarray(weights, dtype=float)
    var = float(w @ cov @ w)
    if var <= 0:
        return np.nan, np.nan, 0.0
    sigma = math.sqrt(var)
    excess = float(w @ mu)
    return excess / sigma, excess, sigma


def choose_combination(names, base_weights, mu, cov, freed, candidates, max_new=MAX_NEW_ASSETS):
    """Mejor combinacion de 1..max_new candidatos para el peso ``freed``.

    ``names``: tickers en el orden de ``mu`` / ``cov`` (activos + candidatos).
    ``base_weights``: pesos de ``names`` despues del recorte (candidatos en 0).
    El peso liberado se reparte en partes iguales. Devuelve el mejor resultado
    y la lista de todas las combinaciones evaluadas.
    """
    idx = {name: i for i, name in enumerate(names)}
    evaluadas = []
    for k in range(1, min(max_new, len(candidates)) + 1):
        for combo in itertools.combinations(candidates, k):
            w = np.array(base_weights, dtype=float)
            for name in combo:
                w[idx[name]] += freed / k
            sharpe, excess, sigma = portfolio_sharpe(w, mu, cov)
            evaluadas.append({"tickers": list(combo), "sharpe": sharpe, "exceso": excess, "sigma": sigma})
    validas = [e for e in evaluadas if np.isfinite(e["sharpe"])]
    if not validas:
        return None, evaluadas
    # Empate: menos activos (no ampliar el portafolio sin necesidad).
    mejor = max(validas, key=lambda e: (round(e["sharpe"], 10), -len(e["tickers"])))
    return mejor, evaluadas


def covariance(names, closes: dict, sigmas: dict):
    """IV ATM (o vol historica) x correlacion historica de los ultimos CORR_SESSIONS."""
    import active_management as am

    frame = pd.DataFrame({n: closes[n] for n in names}).dropna().tail(CORR_SESSIONS + 1)
    corr = am.estimate_correlation(frame)
    sig = np.array([sigmas[n] for n in names], dtype=float)
    return np.outer(sig, sig) * corr, corr


# ==============================================================================
# BLOQUE 8: SALIDA EN TERMINAL Y FIGURAS
# ==============================================================================
def _pct(x, digits=2):
    return "-" if x is None or not np.isfinite(x) else f"{x * 100:+.{digits}f}%"


def _w(x):
    return "-" if x is None or not np.isfinite(x) else f"{x * 100:.2f}%"


def print_detector(rows):
    print("\n=== DETECTOR: caida acumulada en las ultimas "
          f"{DROP_WINDOW_SESSIONS} sesiones (umbral {DROP_THRESHOLD:.0%}) ===")
    tabla = pd.DataFrame([{"Ticker": r["ticker"], "Peso": _w(r["weight"]), "Ret 5d": _pct(r["ret_5d"]),
                           "Dispara": "SI" if r["triggered"] else "no", "Motivo": r["motivo"]}
                          for r in rows])
    print(tabla.to_string(index=False) if not tabla.empty else "  (sin activos)")


def print_diagnosis(triggers):
    print("\n=== DIAGNOSTICO DE LOS ACTIVOS QUE DISPARARON (deterioro 0-100) ===")
    for t in triggers:
        d = t["diagnostico"]
        c = d["cansancio_detalle"]
        print(f"\n[{t['ticker']}] {t['accion']}  deterioro {d['total']:.1f}  "
              f"-> vende {t['recorte_pct']:.0%} del peso ({_w(t['peso_actual'])} -> {_w(t['peso_nuevo'])}, "
              f"libera {_w(t['peso_liberado'])})")
        print(f"   opciones {d['opciones']:.1f} | cansancio {d['cansancio']:.1f} "
              f"(vol {c['vol']:.0f}, ATR {c['atr']:.0f}, estiramiento {c['estiramiento']:.0f}) | "
              f"severidad {d['severidad']:.1f} ({t['caida_sigmas']:+.2f} sigmas semanales)"
              if np.isfinite(t["caida_sigmas"]) else
              f"   opciones {d['opciones']:.1f} | cansancio {d['cansancio']:.1f} | severidad {d['severidad']:.1f}")
        if t.get("opciones_status") != "OK":
            print(f"   opciones: {t.get('opciones_status')} (componente neutral = 50)")
        elif t.get("rationale"):
            print(f"   lectura de opciones: {t['rationale']}")


def print_top(top: pd.DataFrame, universe_info: dict):
    fuentes = ", ".join(f"{k}: {v}" for k, v in universe_info.get("sources", {}).items())
    print(f"\n=== UNIVERSO: {len(universe_info.get('tickers', []))} candidatos ({fuentes}) ===")
    if universe_info.get("shortfall"):
        print(f"   faltaron nombres para completar: {universe_info['shortfall']}")
    print(f"\n=== TOP {TOP_N} POR MOMENTUM DE INVERSION (0-100) ===")
    if top.empty:
        print("  (sin candidatos con datos)")
        return
    tabla = pd.DataFrame({
        "#": range(1, len(top) + 1), "Ticker": top["ticker"], "Puntaje": top["puntaje"].round(1),
        "Momentum": top["momentum"].round(1), "Opciones": top["opciones"].round(1),
        "Frescura": top["frescura"].round(1), "Mom 12-1": top["mom_12_1"].map(_pct),
        "Ret 3m": top["ret_3m"].map(_pct), "IV ATM": top["iv_atm"].map(_w),
        "Origen": top["origin"],
    })
    print(tabla.to_string(index=False))


def print_selection(sel: dict):
    print(f"\n=== SELECCION (max {MAX_NEW_ASSETS} activos, mejor Sharpe esperado) ===")
    if not sel:
        print("  No hay capital liberado: no se reasigna.")
        return
    mejor = sel["mejor"]
    print(f"  Peso liberado: {_w(sel['liberado'])} -> {', '.join(mejor['tickers'])} "
          f"({_w(sel['liberado'] / len(mejor['tickers']))} cada uno)")
    print(f"  Sharpe esperado: antes del recorte {sel['sharpe_antes']:.3f} | "
          f"liberado en caja {sel['sharpe_caja']:.3f} | con la rotacion {mejor['sharpe']:.3f}")
    print(f"  Combinaciones evaluadas: {sel['n_combinaciones']}")
    mejores = sorted([e for e in sel["evaluadas"] if np.isfinite(e["sharpe"])],
                     key=lambda e: -e["sharpe"])[:5]
    for e in mejores:
        print(f"     {'+'.join(e['tickers']):<24s} Sharpe {e['sharpe']:.3f}  "
              f"exceso {e['exceso'] * 100:.2f}%  vol {e['sigma'] * 100:.2f}%")


def print_rebalances(rebalances):
    print("\n=== PROPUESTA (los nuevos entran por entry_signal_tool en 5 dias) ===")
    if not rebalances:
        print("  Sin cambios.")
        return
    for r in rebalances:
        print(f"  {r['action']:<4s} {r['ticker']:<6s} {_w(r['current_weight'])} -> {_w(r['target_weight'])}  "
              f"({r['tactical_action']}) {r['reason']}")


def figure_detector(rows):
    import plotly.graph_objects as go

    if not rows:
        return None
    df = pd.DataFrame(rows).sort_values("ret_5d")
    colores = ["#d03b3b" if t else "#2a78d6" for t in df["triggered"]]
    fig = go.Figure(go.Bar(x=df["ticker"], y=df["ret_5d"] * 100, marker_color=colores,
                           hovertemplate="%{x}: %{y:.2f}%<extra></extra>"))
    fig.add_hline(y=DROP_THRESHOLD * 100, line_dash="dash", line_color="#d03b3b",
                  annotation_text=f"umbral {DROP_THRESHOLD:.0%}")
    fig.update_layout(title=f"Retorno acumulado de {DROP_WINDOW_SESSIONS} sesiones por activo",
                      yaxis_title="%", template="plotly_white")
    return fig


def figure_top(top: pd.DataFrame, elegidos):
    import plotly.graph_objects as go

    if top.empty:
        return None
    df = top.iloc[::-1]
    fig = go.Figure()
    for col, color in (("momentum", "#2a78d6"), ("opciones", "#1baf7a"), ("frescura", "#e6893c")):
        fig.add_trace(go.Bar(y=df["ticker"], x=SCREEN_WEIGHTS[col] * df[col], name=col.capitalize(),
                             orientation="h", marker_color=color,
                             hovertemplate=f"%{{y}} {col}: %{{x:.1f}} pts<extra></extra>"))
    nombres = [f"<b>{t}</b> ✓" if t in (elegidos or []) else t for t in df["ticker"]]
    fig.update_yaxes(ticktext=nombres, tickvals=list(df["ticker"]))
    fig.update_layout(barmode="stack", title=f"Top {len(top)} candidatos (✓ = elegidos para la rotacion)",
                      xaxis_title="Puntaje (0-100)", template="plotly_white",
                      legend=dict(orientation="h", y=-0.15))
    return fig


# ==============================================================================
# BLOQUE 9: ORQUESTACION
# ==============================================================================
def build_rebalances(triggers, elegidos, peso_cada):
    out = []
    for t in triggers:
        if t["recorte_pct"] <= 0:
            continue
        out.append({
            "ticker": t["ticker"], "action": "SELL",
            "current_weight": round(t["peso_actual"], 6), "target_weight": round(t["peso_nuevo"], 6),
            "delta_weight": round(t["peso_nuevo"] - t["peso_actual"], 6),
            "reason": f"{t['motivo']}; deterioro {t['diagnostico']['total']:.1f}",
            "tactical_action": t["accion"],
        })
    for ticker in elegidos or []:
        out.append({
            "ticker": ticker, "action": "BUY", "current_weight": 0.0,
            "target_weight": round(peso_cada, 6), "delta_weight": round(peso_cada, 6),
            "reason": "rotacion: entra escalonado por entry_signal_tool",
            "tactical_action": "ROTACION_ENTRADA",
        })
    return out


def update_state(state, triggers, elegidos, peso_cada, today):
    state = dict(state)
    overrides = dict(state.get("target_overrides") or {})
    disparos = dict(state.get("triggers") or {})
    for t in triggers:
        disparos[t["ticker"]] = {"date": today, "close": t["precio"], "ret_5d": t["ret_5d"],
                                 "action": t["accion"], "deterioro": t["diagnostico"]["total"]}
        if t["recorte_pct"] > 0:
            overrides[t["ticker"]] = t["peso_nuevo"]
    for ticker in elegidos or []:
        overrides[ticker] = float(overrides.get(ticker) or 0.0) + peso_cada
    state["target_overrides"] = overrides
    state["triggers"] = disparos
    state["history"] = list(state.get("history") or []) + [{
        "date": today,
        "triggers": [{"ticker": t["ticker"], "action": t["accion"], "cut": t["recorte_pct"],
                      "freed": t["peso_liberado"]} for t in triggers],
        "bought": list(elegidos or []), "weight_each": peso_cada,
    }]
    return state


def run(force=(), dry_run=False):
    announce_signals_dir(SCRIPT, _PORTFOLIO_META)
    today = cycle_today().isoformat()
    state = load_rotation_state(_PORTFOLIO_META)
    pesos, notas = apply_rotation_overrides(_PORTFOLIO_META["weights"], state)
    for nota in notas:
        print(f"  [estado] {nota}")
    warnings_out, excluded = [], []

    # --- 1. detector -----------------------------------------------------------
    closes, metricas, filas_det = {}, {}, []
    for ticker, peso in pesos.items():
        try:
            ohlc = fetch_ohlc(ticker)
        except Exception as exc:  # noqa: BLE001
            excluded.append({"ticker": ticker, "reason": failure_reason(exc)})
            filas_det.append({"ticker": ticker, "weight": peso, "ret_5d": np.nan,
                              "triggered": False, "motivo": "sin precios"})
            continue
        closes[ticker] = ohlc["close"]
        metricas[ticker] = price_metrics(ohlc)
        dispara, motivo = should_trigger(ticker, metricas[ticker], ohlc.index, state.get("triggers"))
        if ticker in force and not dispara:
            dispara, motivo = True, f"forzado por --force ({motivo})"
        filas_det.append({"ticker": ticker, "weight": peso, "ret_5d": metricas[ticker]["ret_5d"],
                          "triggered": dispara, "motivo": motivo})
    print_detector(filas_det)
    show_or_save(figure_detector([f for f in filas_det if np.isfinite(f["ret_5d"])]),
                 SCRIPT, "detector", portfolio=_PORTFOLIO_META)

    disparados = [f for f in filas_det if f["triggered"]]
    data = {"triggered": bool(disparados), "cycle_date": today, "horizon": HORIZON,
            "drop_window_sessions": DROP_WINDOW_SESSIONS, "drop_threshold": DROP_THRESHOLD,
            "detector": [{"ticker": f["ticker"], "weight": f["weight"], "ret_5d": f["ret_5d"],
                          "triggered": f["triggered"], "reason": f["motivo"]} for f in filas_det],
            "triggers": [], "universe": None, "top": [], "selection": None, "rebalances": [],
            "target_overrides": state.get("target_overrides") or {}, "excluded": excluded}
    sin_precio = [f["ticker"] for f in filas_det if f["motivo"] == "sin precios"]
    if not disparados:
        warnings_out += [f"{item['ticker']}: {item['reason']}" for item in excluded]
        evaluados = len(filas_det) - len(sin_precio)
        if sin_precio:
            print(f"\nATENCION: sin precios para {len(sin_precio)} de {len(filas_det)} activos "
                  f"({', '.join(sin_precio)}); esos no se pudieron evaluar.")
        if evaluados:
            print(f"\nNinguno de los {evaluados} activos evaluados cayo 5% o mas en las ultimas "
                  f"{DROP_WINDOW_SESSIONS} sesiones: no hay rotacion hoy.")
        else:
            print("\nNo se pudo evaluar ningun activo: revisa la conexion a Polygon / Yahoo.")
        return data, warnings_out

    # --- 2. diagnostico ----------------------------------------------------------
    triggers, vistas = [], {}
    for f in disparados:
        ticker = f["ticker"]
        vista = vistas[ticker] = options_view(ticker, HORIZON["days"])
        diag = diagnosis_score(metricas[ticker], vista["tactical_score"])
        accion, recorte = decide_action(diag["total"])
        peso = pesos[ticker]
        triggers.append({
            "ticker": ticker, "precio": metricas[ticker]["precio"], "ret_5d": f["ret_5d"],
            "caida_sigmas": metricas[ticker]["caida_sigmas"], "motivo": f["motivo"],
            "diagnostico": diag, "accion": accion, "recorte_pct": recorte,
            "peso_actual": peso, "peso_nuevo": peso * (1 - recorte), "peso_liberado": peso * recorte,
            "opciones_status": vista["status"], "rationale": vista["rationale"],
        })
        if vista["status"] != "OK":
            warnings_out.append(f"{ticker}: options view unavailable ({vista['status']}); neutral 50 used")
    print_diagnosis(triggers)
    liberado = float(sum(t["peso_liberado"] for t in triggers))

    # --- 3-4. universo y screener ------------------------------------------------
    info = build_universe(N_TOP_SP500, N_TOP_NASDAQ, UNIVERSE_MODE, _custom_tickers(), exclude=list(pesos))
    origen = {row["ticker"]: row["origin"] for row in info["rows"]}
    filas = []
    for ticker in info["tickers"]:
        try:
            ohlc = fetch_ohlc(ticker)
        except Exception as exc:  # noqa: BLE001
            excluded.append({"ticker": ticker, "reason": failure_reason(exc)})
            continue
        closes[ticker] = ohlc["close"]
        vista = options_view(ticker, HORIZON["days"])
        filas.append({"ticker": ticker, "origin": origen.get(ticker), **price_metrics(ohlc),
                      "tactical_score": vista["tactical_score"], "iv_atm": vista["iv_atm"],
                      "expected_move_pct": vista["expected_move_pct"], "opciones_status": vista["status"]})
    # Los activos actuales entran al MISMO ranking (percentiles comparables) para
    # que su retorno esperado y el de los candidatos salgan de la misma escala.
    for ticker in pesos:
        if ticker not in metricas:
            continue
        vista = vistas.get(ticker) or options_view(ticker, HORIZON["days"])
        filas.append({"ticker": ticker, "origin": "portafolio", "es_activo": True, **metricas[ticker],
                      "tactical_score": vista["tactical_score"], "iv_atm": vista["iv_atm"],
                      "expected_move_pct": vista["expected_move_pct"], "opciones_status": vista["status"]})
    ranking = screen_candidates(filas)
    if not ranking.empty:
        ranking["es_activo"] = ranking.get("es_activo", False)
        ranking["es_activo"] = ranking["es_activo"].fillna(False).astype(bool)
        top = ranking[~ranking["descartado"] & ~ranking["es_activo"]].head(TOP_N).reset_index(drop=True)
    else:
        top = ranking
    print_top(top, info)

    # --- 5. seleccion ---------------------------------------------------------------
    seleccion, elegidos, peso_cada = None, [], 0.0
    if liberado > 1e-9 and not top.empty:
        seleccion = select_rotation(pesos, triggers, top, ranking, closes, liberado)
        if seleccion:
            elegidos = seleccion["mejor"]["tickers"]
            peso_cada = liberado / len(elegidos)
    print_selection(seleccion)
    show_or_save(figure_top(top, elegidos), SCRIPT, "top", portfolio=_PORTFOLIO_META)

    rebalances = build_rebalances(triggers, elegidos, peso_cada)
    print_rebalances(rebalances)

    if dry_run:
        print("\n[dry-run] El estado de rotacion NO se actualiza.")
    else:
        state = update_state(state, triggers, elegidos, peso_cada, today)
        ruta = save_rotation_state(state, _PORTFOLIO_META)
        if ruta:
            print(f"\nEstado de rotacion: {ruta}")

    data.update({
        "triggers": [{
            "ticker": t["ticker"], "ret_5d": t["ret_5d"], "drop_sigmas": t["caida_sigmas"],
            "deterioration": t["diagnostico"]["total"],
            "components": {k: t["diagnostico"][k] for k in DIAG_WEIGHTS},
            "action": t["accion"], "cut_pct": t["recorte_pct"], "current_weight": t["peso_actual"],
            "target_weight": t["peso_nuevo"], "freed_weight": t["peso_liberado"],
            "options_status": t["opciones_status"],
        } for t in triggers],
        "universe": {"mode": UNIVERSE_MODE, "n": len(info["tickers"]), "sources": info["sources"],
                     "shortfall": info["shortfall"], "tickers": info["tickers"]},
        "top": [{"rank": i + 1, "ticker": r["ticker"], "score": r["puntaje"], "momentum": r["momentum"],
                 "options": r["opciones"], "freshness": r["frescura"], "mom_12_1": r["mom_12_1"],
                 "ret_3m": r["ret_3m"], "iv_atm": r["iv_atm"], "origin": r["origin"],
                 "options_status": r["opciones_status"]}
                for i, r in enumerate(top.to_dict("records"))],
        "selection": None if not seleccion else {
            "tickers": elegidos, "weight_each": peso_cada, "freed_weight": liberado,
            "sharpe_before": seleccion["sharpe_antes"], "sharpe_cash": seleccion["sharpe_caja"],
            "sharpe_after": seleccion["mejor"]["sharpe"], "n_combinations": seleccion["n_combinaciones"],
        },
        "rebalances": rebalances,
        "target_overrides": state.get("target_overrides") or {},
        "dry_run": bool(dry_run),
    })
    warnings_out += [f"{item['ticker']}: {item['reason']}" for item in excluded]
    return data, warnings_out


def select_rotation(pesos, triggers, top, ranking, closes, liberado):
    """Arma mu y la covarianza (activos actuales + top) y evalua las combinaciones.

    sigma de cada nombre: IV ATM (hacia adelante) si la hay, si no la vol
    historica de 1 ano. Retorno esperado en exceso desde el puntaje del ranking
    conjunto (expected_excess). Correlacion historica (active_management).
    """
    recortes = {t["ticker"]: t["peso_nuevo"] for t in triggers}
    candidatos = [t for t in top["ticker"] if t in closes]
    if not candidatos:
        return None
    activos = [t for t in pesos if t in closes]
    nombres = activos + [c for c in candidatos if c not in activos]
    info = ranking.set_index("ticker")

    sigmas, mu = {}, []
    for name in nombres:
        fila = info.loc[name] if name in info.index else None
        s = np.nan if fila is None else fila.get("iv_atm", np.nan)
        if not (s is not None and np.isfinite(s) and s > 0):
            s = np.nan if fila is None else fila.get("vol_1y", np.nan)
        if not (s is not None and np.isfinite(s) and s > 0):
            rets = np.log(closes[name] / closes[name].shift(1)).dropna()
            s = float(rets.tail(252).std() * math.sqrt(252)) if len(rets) > 20 else 0.25
        sigmas[name] = float(s)
        puntaje = 50.0 if fila is None else float(fila.get("puntaje", 50.0))
        mu.append(expected_excess(puntaje, sigmas[name]))
    mu = np.array(mu)
    cov, _ = covariance(nombres, closes, sigmas)

    w_antes = np.array([pesos.get(n, 0.0) for n in nombres])
    w_base = np.array([recortes.get(n, pesos.get(n, 0.0)) for n in nombres])
    mejor, evaluadas = choose_combination(nombres, w_base, mu, cov, liberado, candidatos)
    if mejor is None:
        return None
    return {
        "mejor": mejor, "evaluadas": evaluadas, "n_combinaciones": len(evaluadas), "liberado": liberado,
        "sharpe_antes": portfolio_sharpe(w_antes, mu, cov)[0],
        "sharpe_caja": portfolio_sharpe(w_base, mu, cov)[0],
    }


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Rotacion por caida anormal (5 sesiones)")
    p.add_argument("--force", action="append", default=[], metavar="TICKER",
                   help="diagnostica TICKER aunque no haya caido 5%% (pruebas)")
    p.add_argument("--dry-run", action="store_true", help="no actualiza el estado de rotacion")
    p.add_argument("--universe", choices=UNIVERSE_MODES, default=None,
                   help="indices | custom | both (por defecto ROTATION_UNIVERSE o indices)")
    return p.parse_args(argv)


def main(argv=None):
    global UNIVERSE_MODE
    args = parse_args(argv)
    if args.universe:
        UNIVERSE_MODE = args.universe
    warnings.filterwarnings("ignore", category=FutureWarning)
    data, warns = run(force=set(t.upper() for t in args.force), dry_run=args.dry_run)
    export_signals(SCRIPT, data, _PORTFOLIO_META, warnings=warns)


if __name__ == "__main__":
    main()
