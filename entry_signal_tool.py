# ============================================================
# ENTRY SIGNAL TOOL - Score de Conviccion para Entrada en Portafolio
# ============================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
import argparse
import copy
import os
import json
import plotly.graph_objects as go

from gex_utils import gamma_flip_level
from polygon_client import NO_OPTION_DATA, NoOptionData, PolygonClient, failure_reason
from pipeline_io import (
    apply_entry_fills,
    cycle_today,
    entry_state_path,
    export_signals,
    load_fills,
    load_portfolio,
    load_portfolio_fills,
    parse_invested_overrides,
    portfolio_key,
    resolve_cycle_day,
    signal_cycle_number,
    stage_pending_entry,
    tranche_lock,
)
from price_signals import price_indicators, price_scores, yahoo_closes
from tickers import exclusion_warnings, no_options_weight_cap, resolve_instrument, to_polygon

# ---------------- CONFIGURACION ----------------
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.environ.get("POLYGON_API_KEY")

BASE_URL = "https://api.polygon.io"

# Peso objetivo de cada activo dentro del portafolio total 
PESOS_OBJETIVO = {
    "XLU": 0.12, "GLD": 0.12, "T": 0.1031, "GILD": 0.0925, "FXI": 0.0779,
    "MRK": 0.0734, "ADP": 0.0595, "KO": 0.0578, "ABT": 0.0562, "VRTX": 0.0541,
    "AMGN": 0.0509, "UNP": 0.0485, "NEE": 0.0484, "ABBV": 0.0235, "TMO": 0.0142,
}

_PORTFOLIO_META = load_portfolio(PESOS_OBJETIVO)
PESOS_OBJETIVO = _PORTFOLIO_META["weights"]
TICKERS = list(PESOS_OBJETIVO.keys())

PESOS = {
    "gex_regime": 0.18,
    "zero_gamma_dist": 0.15,
    "wall_space": 0.12,
    "iv_rank": 0.15,
    "skew": 0.1,
    "expected_move": 0.1,
    "smart_money": 0.1,
    "volumen_relativo": 0.1,
}

# Tier "proxy" (tickers.resolve_instrument): sin opciones propias ni ADR. La
# mitad del score sale del precio diario de la cotizacion local y la otra mitad
# de las opciones del ETF pais (proxy de IV / gamma / put-call).
PESOS_PROXY = {
    "tendencia": 0.15,
    "rsi": 0.10,
    "vol_realizada": 0.15,
    "drawdown": 0.10,
    "gex_regime": 0.10,
    "iv_rank": 0.15,
    "skew": 0.10,
    "smart_money": 0.15,
}

# Tier "none" (sin opciones, ADR ni proxy): entrada fija escalonada, por defecto
# 20% del peso objetivo por dia del ciclo, con el peso objetivo recortado por
# tickers.no_options_weight_cap (NO_OPTIONS_WEIGHT_CAP_FACTOR / _CAP).
def _pct_escalonado():
    try:
        valor = float(os.environ.get("ENTRY_STAGGER_PCT", "0.20"))
    except ValueError:
        return 0.20
    return valor if 0 < valor <= 1 else 0.20

ENTRADA_ESCALONADA_PCT = _pct_escalonado()

UMBRAL_ALTO = 75
UMBRAL_MEDIO = 40

# Duracion del ciclo de entrada en dias habiles. En el ultimo dia se decide en
# firme la fraccion no invertida: comprar el 100% restante o consolidarla en cash.
DIAS_CICLO = 5

HORIZON_DIAS_OBJETIVO = 30
VENTANA_BUSQUEDA_VENCIMIENTO_DIAS = 20

MAX_PAGINAS_CADENA = 40

HIST_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry_signal_history.csv")
# Estado y fills van por portafolio (optimizer + run_ts del JSON del portafolio):
# dos portafolios corriendo a la vez (p. ej. MV y QU) ya no comparten archivo.
# El entry_state.json junto al script es el formato heredado; nunca se borra.
LEGACY_STATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry_state.json")

def ruta_estado():
    return entry_state_path(_PORTFOLIO_META)

def _portafolio_del_estado():
    return {
        "optimizer": _PORTFOLIO_META.get("portfolio_optimizer"),
        "run_ts": _PORTFOLIO_META.get("portfolio_run_ts"),
    }

# Si ya corriste el script hoy con el mismo portafolio, se reemplaza esa fila en vez de duplicarla
def cargar_historial():
    if os.path.exists(HIST_PATH):
        return pd.read_csv(HIST_PATH, parse_dates=["fecha"])
    return pd.DataFrame()

# ---------------- ESTADO DEL CICLO Y DE LAS ENTRADAS ----------------

def _activo_vacio():
    return {"pct_ya_invertido": 0.0, "pct_cash_consolidado": 0.0, "decision_final": None}

def _estado_vacio():
    return {
        "ciclo": 1,
        "dia_ciclo": 1,
        "ciclo_cerrado": False,
        "ultima_actualizacion": None,
        "pending_signal_run_ts": None,
        "pending_cycle_day": None,
        "pending_cycle": None,
        "pending_targets": {},
        "pending_cash": {},
        "pending_decisions": {},
        "last_tranche_date": None,
        "last_tranche": None,
        "activos": {ticker: _activo_vacio() for ticker in TICKERS},
    }

# El dia del ciclo vive una sola vez a nivel global (antes cada activo llevaba su
# propio contador dias_score_bajo). Los estados en formato antiguo se migran aqui.
def normalizar_estado(estado):
    if not estado:
        return _estado_vacio()
    if "activos" not in estado:
        antiguo = estado
        estado = _estado_vacio()
        for ticker, info in antiguo.items():
            if isinstance(info, dict) and "pct_ya_invertido" in info:
                estado["activos"].setdefault(ticker, _activo_vacio())
                estado["activos"][ticker]["pct_ya_invertido"] = float(info["pct_ya_invertido"])
    for ticker in TICKERS:
        estado["activos"].setdefault(ticker, _activo_vacio())
    return estado

def cargar_estado():
    ruta = ruta_estado()
    if os.path.exists(ruta):
        with open(ruta, "r") as f:
            return normalizar_estado(json.load(f))
    # Migracion: el entry_state.json heredado se lee una sola vez y solo si
    # registra este mismo portafolio; si no, se empieza de cero.
    if os.path.exists(LEGACY_STATE_PATH) and portfolio_key(_PORTFOLIO_META) is not None:
        try:
            with open(LEGACY_STATE_PATH, "r") as f:
                heredado = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"  entry_state.json heredado ilegible ({exc}); se empieza de cero.")
            return _estado_vacio()
        if isinstance(heredado, dict) and heredado.get("portfolio") == _portafolio_del_estado():
            print(f"  Estado migrado desde {LEGACY_STATE_PATH} (mismo portafolio).")
            return normalizar_estado(heredado)
        print(f"  {LEGACY_STATE_PATH} no registra este portafolio; se empieza de cero (no se borra).")
    return _estado_vacio()

def guardar_estado(estado):
    ruta = ruta_estado()
    estado = dict(estado, portfolio=_portafolio_del_estado())
    os.makedirs(os.path.dirname(os.path.abspath(ruta)), exist_ok=True)
    temporal = ruta + ".tmp"
    with open(temporal, "w") as f:
        json.dump(estado, f, indent=2)
    os.replace(temporal, ruta)

def cargar_fills():
    """Fills del portafolio actual (fills_<optimizer>_<run_ts>.json en EXECUTIONS_DIR).

    Sin optimizer / run_ts (portafolio de respaldo del script) se usa la
    busqueda heredada de pipeline_io.load_fills.
    """
    if portfolio_key(_PORTFOLIO_META) is None:
        return load_fills("entry_signal_tool")
    return load_portfolio_fills(_PORTFOLIO_META)

def parse_entry_args(argv=None):
    parser = argparse.ArgumentParser(description="Score de conviccion para entrada en portafolio")
    parser.add_argument("--cycle-day", type=int, default=None,
                        help=f"dia del ciclo 1..{DIAS_CICLO} (si no, ENTRY_CYCLE_DAY o el estado del portafolio). "
                             "Un dia explicito valido salta el bloqueo del mismo dia.")
    parser.add_argument("--force-new-tranche", action="store_true",
                        help="prepara un tramo nuevo aunque ya exista uno de hoy (America/Bogota); "
                             "env ENTRY_FORCE_NEW_TRANCHE=1")
    parser.add_argument("--invested-pct", default=None,
                        help="%% ya invertido: '40', 'GLD=40,KO=0.25' o JSON. "
                             "Por defecto, el estado del portafolio. No marca la posicion como ejecutada.")
    return parser.parse_known_args(argv)[0]

# ---------------- DECISION DE CIERRE (DIA 5) ----------------

def evaluar_flujo_opciones(ticker, hist_df):
    hist_ticker = hist_df[hist_df["ticker"] == ticker].sort_values("fecha").tail(DIAS_CICLO)
    if len(hist_ticker) < 3:
        return "CASH", "historial insuficiente para forzar la compra del restante"

    señales_favorables = 0
    señales_totales = 0
    detalles = []

    smart_money = hist_ticker["smart_money"].dropna()
    if len(smart_money) >= 2:
        señales_totales += 1
        if smart_money.tail(3).mean() > 0:
            señales_favorables += 1
            detalles.append("smart money favorable (put/call < 1)")
        else:
            detalles.append("smart money desfavorable (put/call >= 1)")

    dist_zg = hist_ticker["dist_zero_gamma"].dropna().abs()
    if len(dist_zg) >= 2:
        señales_totales += 1
        if dist_zg.iloc[-1] < dist_zg.iloc[0]:
            señales_favorables += 1
            detalles.append("acortamiento a zero-gamma (mayor estabilidad esperada)")
        else:
            detalles.append("precio alejandose del zero-gamma")

    if señales_totales == 0:
        return "CASH", "sin señales de flujo de opciones suficientes"

    decision = "ENTRAR" if señales_favorables / señales_totales >= 0.5 else "CASH"
    return decision, "; ".join(detalles)

# ---------------- FUNCIONES DE EXTRACCION ----------------

_cliente_polygon = None

# Transporte compartido (polygon_client.py): ritmo por ventana de 60s, timeout,
# reintentos ante 429/5xx/red y paginacion que falla en vez de truncar.
def polygon():
    global _cliente_polygon
    if _cliente_polygon is None:
        _cliente_polygon = PolygonClient(api_key=API_KEY)
    return _cliente_polygon

def get_daily_history(ticker, dias=40):
    fecha_fin = datetime.now(timezone.utc).date()
    fecha_inicio = fecha_fin - timedelta(days=dias * 2)  # buffer por fines de semana
    url = f"{BASE_URL}/v2/aggs/ticker/{to_polygon(ticker)}/range/1/day/{fecha_inicio}/{fecha_fin}"
    params = {"adjusted": "true", "sort": "asc", "limit": 5000}
    r = polygon().get(url, params)
    if r.get("status") not in ("OK", "DELAYED") or "results" not in r:
        raise RuntimeError(f"Fallo consultando historico diario de {ticker}: {r}")
    df = pd.DataFrame(r["results"])
    if df.empty:
        return df
    df["fecha"] = pd.to_datetime(df["t"], unit="ms")
    return df[["fecha", "v", "vw", "c"]].rename(columns={"v": "volumen", "vw": "vwap", "c": "cierre"})

def get_spot_y_volumen_relativo(ticker):
    df = get_daily_history(ticker, dias=30)
    if df.empty or len(df) < 5:
        return np.nan, np.nan
    spot = df["cierre"].iloc[-1]
    adv_20 = df["volumen"].tail(20).mean()
    volumen_hoy = df["volumen"].iloc[-1]
    volumen_relativo = volumen_hoy / adv_20
    return spot, volumen_relativo

# Se piden solo los dos vencimientos que rodean al objetivo (el primero en o despues
# y el ultimo en o antes) con limit=1 cada uno. Una sola pagina de 1000 contratos
# ordenada por fecha cubre apenas 2-5 dias en subyacentes con vencimientos
# semanales (GLD, XLU, KO...) y el "mas cercano" terminaba siendo uno de esos.
def seleccionar_vencimiento_objetivo(ticker, horizon_days):
    hoy = datetime.now(timezone.utc).date()
    fecha_objetivo = hoy + timedelta(days=horizon_days)
    url = f"{BASE_URL}/v3/reference/options/contracts"
    base = {"underlying_ticker": to_polygon(ticker), "contract_type": "call",
            "sort": "expiration_date", "limit": 1}
    consultas = [
        {**base, "order": "asc",
         "expiration_date.gte": str(fecha_objetivo),
         "expiration_date.lte": str(fecha_objetivo + timedelta(days=VENTANA_BUSQUEDA_VENCIMIENTO_DIAS))},
        {**base, "order": "desc",
         "expiration_date.gte": str(hoy),
         "expiration_date.lte": str(fecha_objetivo)},
    ]
    vencimientos = set()
    for params in consultas:
        # Si una de las dos consultas falla se lanza el error: con un solo lado
        # se elegiria un vencimiento lejano al objetivo sin saberlo.
        r = polygon().get(url, params)
        for c in r.get("results", []):
            if c.get("expiration_date"):
                vencimientos.add(datetime.strptime(c["expiration_date"], "%Y-%m-%d").date())
    if not vencimientos:
        return None
    return min(sorted(vencimientos), key=lambda d: abs((d - fecha_objetivo).days))

def get_options_chain(ticker, spot, vencimiento):
    url = f"{BASE_URL}/v3/snapshot/options/{to_polygon(ticker)}"
    params = {
        "strike_price.gte": round(spot * 0.85, 2),
        "strike_price.lte": round(spot * 1.15, 2),
        "expiration_date": vencimiento.strftime("%Y-%m-%d"),
        "limit": 250,
    }
    # Una pagina fallida o el tope de paginas lanzan PolygonError en vez de
    # devolver la cadena a medias: el ticker se reporta como error y se omite hoy.
    return polygon().paginate(url, params, max_pages=MAX_PAGINAS_CADENA)

def parse_chain(chain):
    filas = []
    for c in chain:
        details = c.get("details", {})
        greeks = c.get("greeks", {})
        day = c.get("day", {})
        filas.append({
            "strike": details.get("strike_price"),
            "tipo": details.get("contract_type"),
            "vencimiento": details.get("expiration_date"),
            "oi": c.get("open_interest", 0),
            "volumen": day.get("volume", 0),
            "iv": c.get("implied_volatility", None),
            "delta": greeks.get("delta"),
            "gamma": greeks.get("gamma"),
            "bid": c.get("last_quote", {}).get("bid"),
            "ask": c.get("last_quote", {}).get("ask"),
        })
    return pd.DataFrame(filas)

# ---------------- CALCULO DE INDICADORES ----------------

def calcular_gex_y_zero_gamma(df_chain, spot):
    df = df_chain.dropna(subset=["gamma", "oi"]).copy()
    if df.empty:
        return np.nan, np.nan
    signo = np.where(df["tipo"] == "call", 1, -1)
    df["gex_strike"] = signo * df["gamma"] * df["oi"] * 100 * spot**2 * 0.01
    gex_por_strike = df.groupby("strike")["gex_strike"].sum().sort_index()
    gex_total = gex_por_strike.sum()

    # Cruce de signo del GEX acumulado (gex_utils.py: ignora strikes sin
    # exposicion y detecta el cruce en cualquier direccion).
    zero_gamma = gamma_flip_level(gex_por_strike.index, gex_por_strike.values)

    if pd.isna(zero_gamma):
        # Sin cruce de signo real dentro de la ventana: no hay nivel de
        # zero-gamma confiable que reportar (antes esto devolvia por error
        # la strike de mayor concentracion de gamma, un "wall", como si
        # fuera el flip).
        return gex_total, np.nan

    distancia_zero_gamma = (spot - zero_gamma) / spot
    return gex_total, distancia_zero_gamma

def calcular_walls(df_chain):
    df = df_chain.dropna(subset=["oi"])
    calls = df[df["tipo"] == "call"]
    puts = df[df["tipo"] == "put"]
    call_wall = calls.loc[calls["oi"].idxmax(), "strike"] if not calls.empty else np.nan
    put_wall = puts.loc[puts["oi"].idxmax(), "strike"] if not puts.empty else np.nan
    return call_wall, put_wall

def calcular_espacio_walls(spot, call_wall, put_wall):
    if pd.isna(call_wall) or pd.isna(put_wall) or call_wall == put_wall:
        return np.nan
    rango = call_wall - put_wall
    posicion = (spot - put_wall) / rango
    return 1 - abs(posicion - 0.5) * 2

def calcular_iv_atm(df_chain, spot):
    df = df_chain.dropna(subset=["iv", "strike"]).copy()
    if df.empty:
        return np.nan
    df["dist_spot"] = (df["strike"] - spot).abs()
    atm = df.sort_values("dist_spot").head(6)
    return atm["iv"].mean()

def calcular_skew(df_chain):
    df = df_chain.dropna(subset=["delta", "iv"]).copy()
    if df.empty:
        return np.nan
    calls = df[df["tipo"] == "call"].copy()
    puts = df[df["tipo"] == "put"].copy()
    if calls.empty or puts.empty:
        return np.nan
    calls["dist_delta"] = (calls["delta"] - 0.25).abs()
    puts["dist_delta"] = (puts["delta"] - (-0.25)).abs()
    iv_call_25 = calls.sort_values("dist_delta").iloc[0]["iv"]
    iv_put_25 = puts.sort_values("dist_delta").iloc[0]["iv"]
    return iv_put_25 - iv_call_25

def calcular_expected_move(df_chain, spot):
    df = df_chain.dropna(subset=["delta", "bid", "ask"]).copy()
    if df.empty:
        return np.nan
    df["dist_delta_call"] = (df["delta"] - 0.5).abs()
    df["dist_delta_put"] = (df["delta"] - (-0.5)).abs()
    call_atm = df[df["tipo"] == "call"].sort_values("dist_delta_call").head(1)
    put_atm = df[df["tipo"] == "put"].sort_values("dist_delta_put").head(1)
    if call_atm.empty or put_atm.empty:
        return np.nan
    precio_call = (call_atm["bid"].values[0] + call_atm["ask"].values[0]) / 2
    precio_put = (put_atm["bid"].values[0] + put_atm["ask"].values[0]) / 2
    return (precio_call + precio_put) / spot

def calcular_smart_money(df_chain):
    df = df_chain.dropna(subset=["volumen", "oi"])
    if df.empty:
        return np.nan
    calls_vol = df[df["tipo"] == "call"]["volumen"].sum()
    puts_vol = df[df["tipo"] == "put"]["volumen"].sum()
    if (calls_vol + puts_vol) == 0:
        return np.nan
    put_call_ratio = puts_vol / (calls_vol + 1e-9)
    vol_oi_ratio = df["volumen"].sum() / (df["oi"].sum() + 1e-9)
    return vol_oi_ratio * (1 if put_call_ratio < 1 else -1)

def dias_a_opex(hoy=None):
    hoy = hoy or datetime.now(timezone.utc).date()
    primer_dia = hoy.replace(day=1)
    primer_viernes = primer_dia + timedelta(days=(4 - primer_dia.weekday()) % 7)
    tercer_viernes = primer_viernes + timedelta(days=14)
    if tercer_viernes < hoy:
        if hoy.month == 12:
            primer_dia = hoy.replace(year=hoy.year + 1, month=1, day=1)
        else:
            primer_dia = hoy.replace(month=hoy.month + 1, day=1)
        primer_viernes = primer_dia + timedelta(days=(4 - primer_dia.weekday()) % 7)
        tercer_viernes = primer_viernes + timedelta(days=14)
    return (tercer_viernes - hoy).days

def calcular_vanna_charm_factor():
    dias = dias_a_opex()
    if dias <= 5:
        return (5 - dias) / 5
    return 0.0

# ---------------- NORMALIZACION Y SCORE ----------------

def percentile_historico(hist_df, ticker, columna, valor_actual, absoluto=False):
    # absoluto=True compara magnitudes: |valor_actual| contra |historial|. El
    # historial guarda el valor con signo (evaluar_flujo_opciones lo usa asi),
    # y comparar un valor absoluto contra una serie con signo sesga el percentil.
    if hist_df.empty or valor_actual is None or pd.isna(valor_actual):
        return 50.0
    serie = hist_df[hist_df["ticker"] == ticker][columna].dropna()
    if len(serie) < 5:
        return 50.0
    if absoluto:
        serie = serie.abs()
        valor_actual = abs(valor_actual)
    return (serie < valor_actual).mean() * 100

def _pct_entrada(score):
    if score >= UMBRAL_ALTO:
        return 1.0
    if score >= UMBRAL_MEDIO:
        return 0.4 + (score - UMBRAL_MEDIO) / (UMBRAL_ALTO - UMBRAL_MEDIO) * 0.4
    return max(score / UMBRAL_MEDIO * 0.3, 0.0)

def _metricas_opciones(simbolo):
    """Metricas crudas de la cadena de opciones de ``simbolo`` en Polygon.

    ``simbolo`` es el ticker propio, su ADR o el ETF proxy; lanza NoOptionData
    si no hay cadena.
    """
    spot, vol_relativo = get_spot_y_volumen_relativo(simbolo)
    vencimiento = seleccionar_vencimiento_objetivo(simbolo, HORIZON_DIAS_OBJETIVO)
    if vencimiento is None:
        raise NoOptionData(NO_OPTION_DATA)
    chain = parse_chain(get_options_chain(simbolo, spot, vencimiento))
    if chain.empty:
        raise NoOptionData(NO_OPTION_DATA)

    gex_total, dist_zero_gamma = calcular_gex_y_zero_gamma(chain, spot)
    call_wall, put_wall = calcular_walls(chain)
    espacio_walls = calcular_espacio_walls(spot, call_wall, put_wall)
    iv_atm = calcular_iv_atm(chain, spot)
    skew = calcular_skew(chain)
    expected_move = calcular_expected_move(chain, spot)
    smart_money = calcular_smart_money(chain)
    vanna_charm = calcular_vanna_charm_factor()

    return {
        "spot": spot,
        "vencimiento": vencimiento,
        "gex_total": gex_total,
        "dist_zero_gamma": dist_zero_gamma,
        "call_wall": call_wall,
        "put_wall": put_wall,
        "espacio_walls": espacio_walls,
        "iv_atm": iv_atm,
        "skew": skew,
        "expected_move": expected_move,
        "smart_money": smart_money,
        "volumen_relativo": vol_relativo,
        "vanna_charm": vanna_charm,
    }

def calcular_indicadores_ticker(ticker, hist_df):
    # Tier "native" usa la cadena propia; tier "adr" la del ADR (RY.TO -> RY).
    # La fila conserva el ticker local como llave del portafolio.
    instrumento = resolve_instrument(ticker)
    if instrumento["tier"] not in ("native", "adr"):
        raise NoOptionData(instrumento["reason"] or NO_OPTION_DATA)
    crudos = _metricas_opciones(instrumento["analysis_ticker"])
    gex_total = crudos["gex_total"]
    dist_zero_gamma = crudos["dist_zero_gamma"]
    espacio_walls = crudos["espacio_walls"]
    iv_atm = crudos["iv_atm"]
    skew = crudos["skew"]
    expected_move = crudos["expected_move"]
    smart_money = crudos["smart_money"]
    vol_relativo = crudos["volumen_relativo"]

    normalizados = {
        "gex_regime": 100 - abs(percentile_historico(hist_df, ticker, "gex_total", gex_total) - 50) * 2,
        "zero_gamma_dist": percentile_historico(
            hist_df, ticker, "dist_zero_gamma", dist_zero_gamma, absoluto=True
        ),
        "wall_space": (espacio_walls * 100) if not pd.isna(espacio_walls) else 50.0,
        "iv_rank": percentile_historico(hist_df, ticker, "iv_atm", iv_atm),
        "skew": 100 - percentile_historico(hist_df, ticker, "skew", skew, absoluto=True),
        "expected_move": 100 - percentile_historico(hist_df, ticker, "expected_move", expected_move),
        "smart_money": percentile_historico(hist_df, ticker, "smart_money", smart_money),
        "volumen_relativo": (min(vol_relativo, 2.0) / 2.0 * 100) if not pd.isna(vol_relativo) else 50.0,
    }

    score = sum(normalizados[k] * PESOS[k] for k in PESOS)
    pct_entrada = _pct_entrada(score)

    fila = {
        "fecha": pd.Timestamp.now(timezone.utc).normalize(),
        "ticker": ticker,
        **crudos,
        **{f"norm_{k}": v for k, v in normalizados.items()},
        "score_conviccion": score,
        "pct_entrada_sugerido": round(pct_entrada, 3),
        "tier": instrumento["tier"],
        "analysis_ticker": instrumento["analysis_ticker"],
        "proxy_etf": None,
        "modo_entrada": "opciones",
    }
    return fila

def calcular_indicadores_proxy(ticker, instrumento, hist_df, closes=None, metricas_proxy=None):
    """Tier "proxy": precio diario local (Yahoo) + opciones del ETF pais.

    ``closes`` y ``metricas_proxy`` se pueden inyectar (pruebas); si faltan se
    descargan. Las metricas del ETF se guardan con los mismos nombres de columna
    que las de opciones propias, bajo el ticker local, para que los percentiles
    y la decision del dia 5 comparen siempre contra la misma serie proxy.
    """
    etf = instrumento["proxy_etf"]
    if closes is None:
        closes = yahoo_closes(ticker)
    indicadores = price_indicators(closes)
    if pd.isna(indicadores["precio"]):
        raise RuntimeError(f"no price history returned for {ticker}")
    if metricas_proxy is None:
        metricas_proxy = _metricas_opciones(etf)

    normalizados = {
        **price_scores(indicadores),
        "gex_regime": 100 - abs(
            percentile_historico(hist_df, ticker, "gex_total", metricas_proxy.get("gex_total")) - 50
        ) * 2,
        "iv_rank": percentile_historico(hist_df, ticker, "iv_atm", metricas_proxy.get("iv_atm")),
        "skew": 100 - percentile_historico(
            hist_df, ticker, "skew", metricas_proxy.get("skew"), absoluto=True
        ),
        "smart_money": percentile_historico(
            hist_df, ticker, "smart_money", metricas_proxy.get("smart_money")
        ),
    }
    score = sum(normalizados[k] * PESOS_PROXY[k] for k in PESOS_PROXY)
    pct_entrada = _pct_entrada(score)

    crudos_proxy = {k: v for k, v in metricas_proxy.items() if k != "spot"}
    return {
        "fecha": pd.Timestamp.now(timezone.utc).normalize(),
        "ticker": ticker,
        "spot": indicadores["precio"],
        **crudos_proxy,
        "spot_proxy": metricas_proxy.get("spot"),
        **{f"px_{k}": v for k, v in indicadores.items()},
        **{f"norm_{k}": v for k, v in normalizados.items()},
        "score_conviccion": score,
        "pct_entrada_sugerido": round(pct_entrada, 3),
        "tier": "proxy",
        "analysis_ticker": instrumento["analysis_ticker"],
        "proxy_etf": etf,
        "capital_epic": instrumento.get("capital_epic"),
        "modo_entrada": "proxy",
    }

def fila_escalonada(ticker, instrumento):
    """Tier "none": sin score; la entrada es fija por dia (ENTRADA_ESCALONADA_PCT)."""
    return {
        "fecha": pd.Timestamp.now(timezone.utc).normalize(),
        "ticker": ticker,
        "spot": np.nan,
        "score_conviccion": np.nan,
        "pct_entrada_sugerido": np.nan,
        "tier": "none",
        "analysis_ticker": instrumento["analysis_ticker"],
        "proxy_etf": instrumento.get("proxy_etf"),
        "capital_epic": instrumento.get("capital_epic"),
        "modo_entrada": "escalonado",
    }

def calcular_fila_instrumento(ticker, hist_df, warnings, excluded):
    """Fila del dia segun el tier del ticker, o None si se excluye.

    native / adr -> opciones propias o del ADR; proxy -> precio + ETF pais;
    none (o proxy sin datos) -> entrada escalonada con tope de peso.
    """
    instrumento = resolve_instrument(ticker)
    warnings.extend(instrumento["warnings"])
    tier = instrumento["tier"]
    if tier in ("native", "adr"):
        try:
            fila = calcular_indicadores_ticker(ticker, hist_df)
            if tier == "adr":
                # Orden por el ADR solo con epic verificado (None si no lo esta).
                fila["capital_epic"] = instrumento["capital_epic"]
            return fila
        except NoOptionData as exc:
            excluded.append({"ticker": ticker, "reason": str(exc) or NO_OPTION_DATA, "tier": tier})
            print(f"{ticker}: {exc}; se omite.")
        except Exception as exc:
            excluded.append({"ticker": ticker, "reason": failure_reason(exc), "tier": tier})
            print(f"Error con {ticker}: {exc}; se omite.")
        return None

    if tier == "proxy":
        try:
            fila = calcular_indicadores_proxy(ticker, instrumento, hist_df)
            warnings.append(
                f"{ticker}: no US options or ADR; scored with daily prices and "
                f"{instrumento['proxy_etf']} options as proxy (tier proxy)"
            )
            return fila
        except Exception as exc:
            motivo = str(exc) if isinstance(exc, NoOptionData) else failure_reason(exc)
            warnings.append(
                f"{ticker}: proxy {instrumento['proxy_etf']} unavailable ({motivo}); "
                "falling back to staggered entry"
            )
            print(f"{ticker}: proxy {instrumento['proxy_etf']} sin datos ({exc}); entrada escalonada.")
            fila = fila_escalonada(ticker, instrumento)
            fila["tier"] = "none"
            return fila

    warnings.append(
        f"{ticker}: {instrumento['reason'] or 'no US options'}; no ADR or proxy ETF; "
        f"staggered entry {ENTRADA_ESCALONADA_PCT*100:.0f}%/day with capped weight (tier none)"
    )
    return fila_escalonada(ticker, instrumento)

# ---------------- VISUALIZACION ----------------

COLORES_ACCION = {
    "CIERRE: ENTRAR": "#0ca30c",
    "CIERRE: CASH": "#d03b3b",
    "COMPLETO": "#2a78d6",
    "ESCALONADO": "#8a6d00",
}
COLOR_TEXTO_NORMAL = "#52514e"

def graficar_resumen(resumen):
    if resumen.empty:
        return None

    df = resumen.sort_values("score_conviccion", ascending=True).reset_index(drop=True)
    dia = int(df["dia_ciclo"].iloc[0])
    ciclo = int(df["ciclo"].iloc[0])
    es_ultimo_dia = dia >= DIAS_CICLO

    cash = df["cash_definitivo_pct"]
    pendiente = (100 - df["pct_invertido_final_pct"] - cash).clip(lower=0)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df["ticker"], x=df["pct_ya_invertido_previo"], name="Ya invertido", orientation="h",
        marker_color="#2a78d6",
        hovertemplate="<b>%{y}</b><br>Ya invertido: %{x:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=df["ticker"], x=df["delta_sugerido_hoy_pct"], name="Sugerido hoy", orientation="h",
        marker_color="#1baf7a",
        customdata=df["recomendacion"],
        hovertemplate="<b>%{y}</b><br>Sugerido hoy: %{x:.1f}%<br>%{customdata}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=df["ticker"], x=pendiente, name="Pendiente (goteo)", orientation="h",
        marker_color="#e1e0d9",
        customdata=df["recomendacion"],
        hovertemplate="<b>%{y}</b><br>Pendiente: %{x:.1f}%<br>%{customdata}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=df["ticker"], x=cash, name=f"Cash definitivo (cierre dia {DIAS_CICLO})", orientation="h",
        marker_color="#f0b7b7",
        marker_line=dict(color="#d03b3b", width=1),
        customdata=df["recomendacion"],
        hovertemplate="<b>%{y}</b><br>Cash definitivo: %{x:.1f}%<br>%{customdata}<extra></extra>",
    ))

    anotaciones = []
    for _, fila in df.iterrows():
        accion = fila["accion"]
        color_txt = COLORES_ACCION.get(accion, COLOR_TEXTO_NORMAL)
        peso_obj = fila["peso_objetivo_pct"]
        peso_obj_txt = f"{peso_obj:.1f}%" if not pd.isna(peso_obj) else "?"
        if accion == "CIERRE: CASH":
            detalle = f"{fila['cash_definitivo_pct']:.0f}% a cash"
        elif fila["delta_sugerido_hoy_pct"] > 0:
            detalle = f"+{fila['delta_sugerido_hoy_pct']:.0f}%"
        else:
            detalle = "sin cambios"
        linea1 = f"<b>{accion} · {detalle}</b>"
        linea2 = (
            f"<span style='font-size:10px;color:{COLOR_TEXTO_NORMAL}'>"
            f"peso obj. {peso_obj_txt} · hoy +{fila['delta_puntos_portafolio']:.2f} pts portafolio</span>"
        )
        anotaciones.append(dict(
            x=1.02, y=fila["ticker"], xref="paper", yref="y",
            text=f"{linea1}<br>{linea2}",
            showarrow=False, xanchor="left", align="left",
            font=dict(size=12, color=color_txt),
        ))

    subtitulo = (
        "cierre del ciclo: la fraccion no invertida se compra al 100% o queda en cash"
        if es_ultimo_dia else "entrada por goteo segun el score de conviccion"
    )
    fig.update_layout(
        barmode="stack",
        title=(
            f"CICLO {ciclo} · DIA {dia} DE {DIAS_CICLO} — {subtitulo}"
            "<br><span style='font-size:12px'>% del PESO OBJETIVO propio de cada activo (no del capital total)</span>"
        ),
        xaxis=dict(title="% del peso objetivo del activo", range=[0, 100], ticksuffix="%"),
        yaxis=dict(title=None, categoryorder="array", categoryarray=df["ticker"].tolist()),
        template="plotly_white",
        legend=dict(orientation="h", yanchor="top", y=-0.12, x=0),
        margin=dict(r=340, l=80, t=90, b=90),
        annotations=anotaciones,
        height=max(420, 58 * len(df) + 170),
        width=1200,
    )
    return fig

# ---------------- EJECUCION PRINCIPAL ----------------

def _contexto(estado, warnings, excluded, dia_ciclo, ciclo, pending_cash=None, pending_decisions=None,
              locked=None):
    return {
        "locked": locked,
        "estado": estado,
        "warnings": warnings,
        "excluded": excluded,
        "cycle_day": dia_ciclo,
        "cycle": ciclo,
        "pending_cash": pending_cash or {},
        "pending_decisions": pending_decisions or {},
    }


def _texto(fila, columna):
    valor = fila.get(columna) if hasattr(fila, "get") else None
    if valor is None or (not isinstance(valor, str) and pd.isna(valor)):
        return None
    return str(valor)


def construir_fila_estado(fila, pct_previo, peso_original, dia_ciclo, ciclo, hist_actualizado):
    """Decision del dia para un activo: cuanto sumar hoy, en % de su peso objetivo.

    ``pct_previo`` es la fraccion del peso objetivo ya ejecutada (fills). En
    entrada escalonada (tier "none") el objetivo es el peso recortado
    (tickers.no_options_weight_cap) y cada senal compra un tramo fijo de
    ENTRADA_ESCALONADA_PCT (o lo que falte) sobre lo ejecutado: nunca el 100%
    de una vez, aunque se hayan perdido fills o sea el dia 5.
    """
    ticker = fila["ticker"]
    escalonado = _texto(fila, "modo_entrada") == "escalonado"
    peso_objetivo = no_options_weight_cap(peso_original) if escalonado else peso_original
    es_ultimo_dia = dia_ciclo >= DIAS_CICLO
    pct_cash = 0.0

    if escalonado:
        pct_objetivo_hoy = min(1.0, pct_previo + ENTRADA_ESCALONADA_PCT)
    else:
        pct_objetivo_hoy = fila["pct_entrada_sugerido"]

    if pct_previo >= 0.999:
        delta = 0.0
        accion = "COMPLETO"
        recomendacion = "COMPLETO (100% del peso objetivo)"
    elif escalonado:
        delta = pct_objetivo_hoy - pct_previo
        tope = f"{peso_objetivo*100:.2f}%" if not pd.isna(peso_objetivo) else "?"
        accion = "ESCALONADO"
        recomendacion = (
            f"ENTRADA ESCALONADA (sin opciones, ADR ni proxy): +{delta*100:.1f}% hoy, "
            f"{pct_objetivo_hoy*100:.0f}% acumulado del peso recortado {tope}"
        )
    elif es_ultimo_dia:
        # Dia 5: no hay goteo adicional, se cierra el ciclo en firme.
        decision, motivo = evaluar_flujo_opciones(ticker, hist_actualizado)
        if decision == "ENTRAR":
            delta = 1.0 - pct_previo
            accion = "CIERRE: ENTRAR"
            recomendacion = f"CIERRE DIA {DIAS_CICLO} -> COMPRAR EL {delta*100:.1f}% RESTANTE ({motivo})"
        else:
            delta = 0.0
            pct_cash = 1.0 - pct_previo
            accion = "CIERRE: CASH"
            recomendacion = f"CIERRE DIA {DIAS_CICLO} -> DEJAR {pct_cash*100:.1f}% EN CASH ({motivo})"
    else:
        delta = max(0.0, pct_objetivo_hoy - pct_previo)
        if delta > 0:
            accion = "SUMAR"
            recomendacion = "COMPLETAR A 100%" if pct_objetivo_hoy >= 1.0 else f"SUMAR +{delta*100:.1f}%"
        else:
            accion = "MANTENER"
            recomendacion = "MANTENER (ya en el nivel objetivo de hoy)"

    pct_final = min(1.0, pct_previo + delta)

    return {
        "ciclo": ciclo,
        "dia_ciclo": dia_ciclo,
        "ticker": ticker,
        "peso_objetivo_pct": round(peso_objetivo * 100, 2) if not pd.isna(peso_objetivo) else np.nan,
        "peso_objetivo_original_pct": (
            round(peso_original * 100, 2) if not pd.isna(peso_original) else np.nan
        ),
        "pct_ya_invertido_previo": round(pct_previo * 100, 1),
        "pct_objetivo_hoy": round(pct_objetivo_hoy * 100, 1),
        "delta_sugerido_hoy_pct": round(delta * 100, 1),
        "pct_invertido_final_pct": round(pct_final * 100, 1),
        "cash_definitivo_pct": round(pct_cash * 100, 1),
        "delta_puntos_portafolio": (
            round(delta * peso_objetivo * 100, 2) if not pd.isna(peso_objetivo) else np.nan
        ),
        "accion": accion,
        "recomendacion": recomendacion,
        "tier": _texto(fila, "tier") or "native",
        "analysis_ticker": _texto(fila, "analysis_ticker") or ticker,
        "proxy_etf": _texto(fila, "proxy_etf"),
        "capital_epic": _texto(fila, "capital_epic"),
        "tope_peso_aplicado": escalonado,
    }


def correr_entry_signal(cycle_day=None, invested_pct=None, force_new_tranche=False):
    """Calcula la senal del dia. No marca el estado del portafolio como invertido.

    Bloqueo del mismo dia: si el estado ya registra un tramo preparado hoy
    (America/Bogota, pendiente o ejecutado) no se prepara otro y ctx["locked"]
    describe ese tramo. force_new_tranche o un dia de ciclo explicito valido
    lo saltan.

    Los porcentajes ya invertidos solo cambian si hay un fills file cuyo
    signal_run_ts coincide con la senal pendiente. El dia y el % invertido de
    esta corrida salen de los argumentos (CLI / env) o, si faltan, del estado.
    """
    hist_df = cargar_historial()
    warnings = []
    excluded = []

    estado = cargar_estado()
    fills_payload = cargar_fills()
    hoy = cycle_today()
    estado, fills_applied = apply_entry_fills(
        estado, fills_payload, cycle_length=DIAS_CICLO, today=hoy.isoformat(),
    )
    if fills_applied:
        guardar_estado(estado)
        print(f"Fills confirmados: {ruta_estado()} avanza con la ejecucion.")
    elif fills_payload and estado.get("pending_signal_run_ts"):
        warnings.append(
            "fills ignored: signal_run_ts "
            f"{fills_payload.get('signal_run_ts')!r} does not match pending "
            f"{estado.get('pending_signal_run_ts')!r}"
        )

    dia_ciclo, day_warn = resolve_cycle_day(cycle_day, estado, DIAS_CICLO)
    dia_explicito = cycle_day is not None and str(cycle_day).strip() != "" and not day_warn
    bloqueo = None if (force_new_tranche or dia_explicito) else tranche_lock(estado, hoy)
    if bloqueo:
        aviso = (
            f"already_prepared_today: el tramo del {bloqueo['prepared_date']} "
            f"({bloqueo['status']}) ya existe; no se prepara otro. "
            "Use --force-new-tranche o un dia de ciclo explicito para saltar el bloqueo."
        )
        if day_warn:
            warnings.append(day_warn)
        warnings.append(aviso)
        print(f"\n{aviso}")
        return pd.DataFrame(), hist_df, _contexto(
            estado, warnings, excluded, dia_ciclo, estado.get("ciclo"), locked=bloqueo,
        )
    if day_warn:
        warnings.append(day_warn)
        print(f"  {day_warn}")
    ciclo = signal_cycle_number(estado, dia_ciclo, DIAS_CICLO)
    if estado.get("ciclo_cerrado"):
        print(f"\nEl ciclo {estado.get('ciclo')} esta cerrado. Esta senal abre el ciclo {ciclo}.")
    elif estado.get("ultima_actualizacion") and dia_ciclo < int(estado.get("dia_ciclo") or 1):
        print(f"\nDia {dia_ciclo} anterior al guardado: la senal usa el ciclo {ciclo}.")

    overrides, override_warns = parse_invested_overrides(invested_pct, TICKERS)
    warnings.extend(override_warns)
    for message in override_warns:
        print(f"  {message}")

    # Copia solo para el calculo. El archivo no recibe estos porcentajes.
    scoring = copy.deepcopy(estado)
    if overrides:
        for ticker, frac in overrides.items():
            scoring["activos"].setdefault(ticker, _activo_vacio())
            scoring["activos"][ticker]["pct_ya_invertido"] = frac

    es_ultimo_dia = dia_ciclo >= DIAS_CICLO
    if es_ultimo_dia:
        print(
            f"\nDIA {DIAS_CICLO} (ultimo del ciclo): la senal decide la fraccion no invertida."
            "\nEl estado no cambia hasta que el ejecutor confirme los fills.\n"
        )
    else:
        print(f"\nDia {dia_ciclo} de {DIAS_CICLO}: entrada por goteo segun el score de hoy.\n")

    filas_nuevas = []
    for ticker in TICKERS:
        fila = calcular_fila_instrumento(ticker, hist_df, warnings, excluded)
        if fila is not None:
            filas_nuevas.append(fila)

    warnings.extend(exclusion_warnings(excluded))
    df_nuevo = pd.DataFrame(filas_nuevas)
    if df_nuevo.empty:
        return pd.DataFrame(), hist_df, _contexto(estado, warnings, excluded, dia_ciclo, ciclo)

    hist_actualizado = pd.concat([hist_df, df_nuevo], ignore_index=True)
    # Si el mismo ticker ya tiene una fila con la fecha de hoy, se queda solo la mas reciente
    hist_actualizado["fecha_dia"] = pd.to_datetime(hist_actualizado["fecha"]).dt.date
    hist_actualizado = hist_actualizado.drop_duplicates(subset=["ticker", "fecha_dia"], keep="last")
    hist_actualizado = hist_actualizado.drop(columns=["fecha_dia"]).sort_values(["ticker", "fecha"])
    hist_actualizado.to_csv(HIST_PATH, index=False)

    # ---- Combina el score de hoy con el estado de entradas ya tomadas ----
    filas_estado = []
    for _, fila in df_nuevo.iterrows():
        ticker = fila["ticker"]
        activo = scoring["activos"].setdefault(ticker, _activo_vacio())
        filas_estado.append(construir_fila_estado(
            fila, activo["pct_ya_invertido"], PESOS_OBJETIVO.get(ticker, np.nan),
            dia_ciclo, ciclo, hist_actualizado,
        ))

    pending_cash = {}
    pending_decisions = {}
    for fila in filas_estado:
        if fila["accion"] == "CIERRE: CASH":
            pending_cash[fila["ticker"]] = fila["cash_definitivo_pct"] / 100.0
            pending_decisions[fila["ticker"]] = "CASH"
        elif fila["accion"] == "CIERRE: ENTRAR":
            pending_decisions[fila["ticker"]] = "ENTRAR"

    df_estado = pd.DataFrame(filas_estado)
    resumen = df_nuevo[["ticker", "spot", "score_conviccion", "pct_entrada_sugerido"]].merge(
        df_estado, on="ticker"
    ).sort_values("score_conviccion", ascending=False)

    return resumen, hist_actualizado, _contexto(
        estado, warnings, excluded, dia_ciclo, ciclo, pending_cash, pending_decisions
    )

def imprimir_resumen(resumen):
    if resumen.empty:
        print("\nSin datos: ningun ticker devolvio indicadores.")
        return

    dia = int(resumen["dia_ciclo"].iloc[0])
    ciclo = int(resumen["ciclo"].iloc[0])
    print(f"\n=== CICLO {ciclo} · DIA {dia} DE {DIAS_CICLO} ===")

    columnas = [
        "dia_ciclo", "ticker", "spot", "score_conviccion", "peso_objetivo_pct",
        "pct_ya_invertido_previo", "delta_sugerido_hoy_pct", "pct_invertido_final_pct",
        "cash_definitivo_pct", "delta_puntos_portafolio", "accion", "recomendacion",
    ]
    print(resumen[columnas].to_string(index=False))

    pts_invertidos = (resumen["pct_invertido_final_pct"] / 100 * resumen["peso_objetivo_pct"]).sum()
    pts_cash = (resumen["cash_definitivo_pct"] / 100 * resumen["peso_objetivo_pct"]).sum()
    if dia >= DIAS_CICLO:
        entrar = resumen[resumen["accion"] == "CIERRE: ENTRAR"]["ticker"].tolist()
        a_cash = resumen[resumen["accion"] == "CIERRE: CASH"]["ticker"].tolist()
        print(f"\nCIERRE DE CICLO (dia {DIAS_CICLO}) — decision definitiva, sin goteo adicional:")
        print(f"  Compra del restante al 100%: {', '.join(entrar) if entrar else '(ninguno)'}")
        print(f"  Consolidado en cash / no entrar: {', '.join(a_cash) if a_cash else '(ninguno)'}")
        print(f"  Asignacion final invertida: {pts_invertidos:.2f} pts de portafolio")
        print(f"  Reserva final en cash: {pts_cash:.2f} pts de portafolio")
    else:
        pendiente = resumen["peso_objetivo_pct"].sum() - pts_invertidos
        print(f"\nDia {dia} de {DIAS_CICLO} — quedan {DIAS_CICLO - dia} dia(s) de goteo antes del cierre forzado.")
        print(f"  Invertido tras hoy: {pts_invertidos:.2f} pts de portafolio")
        print(f"  Pendiente por asignar: {pendiente:.2f} pts de portafolio")

def construir_senal_entrada(resumen):
    """entries en orden de ejecucion (mayor conviccion primero); el resto en waiting."""
    if resumen is None or len(resumen) == 0:
        return {"entries": [], "waiting": [], "cycle_day": None, "cycle": None}

    dia = resumen["dia_ciclo"].iloc[0]
    ciclo = resumen["ciclo"].iloc[0]
    entries = []
    waiting = []
    ordered = resumen.sort_values("score_conviccion", ascending=False, na_position="last")
    for _, fila in ordered.iterrows():
        score = None if pd.isna(fila["score_conviccion"]) else float(fila["score_conviccion"])
        target = None if pd.isna(fila["peso_objetivo_pct"]) else float(fila["peso_objetivo_pct"]) / 100.0
        reason = "" if pd.isna(fila["recomendacion"]) else str(fila["recomendacion"])
        accion = "" if pd.isna(fila["accion"]) else str(fila["accion"])
        delta_pct = 0.0 if pd.isna(fila["delta_sugerido_hoy_pct"]) else float(fila["delta_sugerido_hoy_pct"])
        # Campos de tier (tickers.resolve_instrument): solo si la fila los trae.
        extra = {}
        if "tier" in fila.index and not pd.isna(fila["tier"]):
            extra["tier"] = str(fila["tier"])
            claves = ["analysis_ticker", "proxy_etf"]
            if extra["tier"] != "native":
                # Epic de Capital.com solo si esta verificado; None = no operar.
                claves.append("capital_epic")
            for key in claves:
                value = fila.get(key)
                extra[key] = None if value is None or pd.isna(value) else str(value)
        if delta_pct > 0 and target is not None:
            if accion == "CIERRE: ENTRAR":
                signal = "cycle_close"
            elif accion == "ESCALONADO":
                signal = "staggered"
            elif score is not None and score >= UMBRAL_ALTO:
                signal = "high_conviction"
            elif score is not None and score >= UMBRAL_MEDIO:
                signal = "medium_conviction"
            else:
                signal = "low_conviction"
            entry = {
                "order": len(entries) + 1,
                "ticker": str(fila["ticker"]),
                "action": "BUY",
                "target_weight": round(target, 6),
                "tranche_weight": round(delta_pct / 100.0 * target, 6),
                "signal": signal,
                "score": score,
                "reason": reason,
                **extra,
            }
            original = fila.get("peso_objetivo_original_pct")
            tope = fila.get("tope_peso_aplicado")
            if tope is not None and not pd.isna(tope) and bool(tope) \
                    and original is not None and not pd.isna(original):
                entry["uncapped_target_weight"] = round(float(original) / 100.0, 6)
            entries.append(entry)
        else:
            waiting.append({"ticker": str(fila["ticker"]), "score": score, "reason": reason, **extra})

    return {
        "entries": entries,
        "waiting": waiting,
        "cycle_day": None if pd.isna(dia) else int(dia),
        "cycle": None if pd.isna(ciclo) else int(ciclo),
    }


def construir_senal_bloqueada(bloqueo):
    """Senal de un dia con tramo ya preparado: sin entries nuevas.

    ``entries`` queda vacio para que ningun ejecutor repita el tramo; el tramo
    existente va en ``existing_tranche`` con su signal_run_ts original, que es
    el que debe llevar su fills file.
    """
    tramo = bloqueo.get("tranche") or {}
    return {
        "signal": "already_prepared_today",
        "tranche_status": bloqueo["status"],
        "prepared_date": bloqueo["prepared_date"],
        "existing_signal_run_ts": bloqueo.get("signal_run_ts"),
        "entries": [],
        "waiting": [],
        "existing_tranche": {
            "entries": tramo.get("entries") or [],
            "waiting": tramo.get("waiting") or [],
        },
        "cycle_day": tramo.get("cycle_day"),
        "cycle": tramo.get("cycle"),
        "excluded": [],
    }


def _truthy(valor):
    return str(valor or "").strip().lower() in ("1", "true", "yes", "on")


def main(argv=None):
    args = parse_entry_args(argv)
    cycle_day = args.cycle_day if args.cycle_day is not None else os.environ.get("ENTRY_CYCLE_DAY")
    invested = args.invested_pct if args.invested_pct is not None else os.environ.get("ENTRY_INVESTED_PCT")
    force_new = args.force_new_tranche or _truthy(os.environ.get("ENTRY_FORCE_NEW_TRANCHE"))
    resumen, _historial, ctx = correr_entry_signal(cycle_day, invested, force_new_tranche=force_new)
    if ctx.get("locked"):
        # Nada que preparar: se escribe la senal con el estado y no se toca el
        # estado del portafolio (el tramo pendiente conserva su signal_run_ts).
        export_signals(
            "entry_signal_tool", construir_senal_bloqueada(ctx["locked"]), _PORTFOLIO_META,
            warnings=ctx["warnings"],
        )
        return
    imprimir_resumen(resumen)
    data = construir_senal_entrada(resumen)
    data["signal"] = "new_tranche"
    if data.get("cycle_day") is None:
        data["cycle_day"] = ctx["cycle_day"]
        data["cycle"] = ctx["cycle"]
    data["excluded"] = ctx["excluded"]
    path = export_signals(
        "entry_signal_tool", data, _PORTFOLIO_META, warnings=ctx["warnings"],
    )
    if path:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                run_ts = json.load(handle).get("run_ts")
        except (OSError, json.JSONDecodeError):
            run_ts = None
        if run_ts:
            targets = {
                entry["ticker"]: entry["target_weight"]
                for entry in data["entries"]
                if entry.get("target_weight")
            }
            # Sin datos de ningun ticker no hubo tramo real: no se bloquea el dia.
            produjo_tramo = len(resumen) > 0
            guardar_estado(stage_pending_entry(
                ctx["estado"], run_ts, data.get("cycle_day"), data.get("cycle"),
                targets, ctx["pending_cash"], ctx["pending_decisions"],
                prepared_date=cycle_today().isoformat() if produjo_tramo else None,
                tranche={key: data[key] for key in ("entries", "waiting", "cycle_day", "cycle")},
            ))
    fig_resumen = graficar_resumen(resumen)
    if fig_resumen is not None:
        fig_resumen.show()


if __name__ == "__main__":
    main()
