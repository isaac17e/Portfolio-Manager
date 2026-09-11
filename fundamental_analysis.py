# Fundamental analysis module for stock tickers using yfinance.

from __future__ import annotations

import html
import json
import warnings
import webbrowser
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from string import Template
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

try:
    import yfinance as yf
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "Falta la librería 'yfinance'. Instálala con: pip install yfinance"
    ) from exc

warnings.filterwarnings("ignore", category=FutureWarning)

INF = float("inf")  # "sin límite" en los umbrales

# ==============================================================================
# BLOQUE 1: CONFIGURACIÓN  <<<  EDITA AQUÍ  >>>
# ==============================================================================

PORTFOLIO_TICKERS: List[str] = ["CRM", "DELL", "EBAY", "GOOGL", "META", "MSFT", "ORCL"]

# --- salida -------------------------------------------------------------------
OUTPUT_HTML: str = "reporte_fundamental.html"   # relativo a la carpeta del script
OPEN_BROWSER: bool = True                       # abre el reporte al terminar

# --- histórico (gráficos del reporte) -----------------------------------------
HIST_EJERCICIOS: int = 4       # ejercicios fiscales; Yahoo suele dar 4 completos
HIST_TRIMESTRES: int = 5       # trimestres de Current Ratio y Earnings Surprise

# --- score global -------------------------------------------------------------
SCORE_LUZ_VERDE_MIN: int = 9       # señales en verde para "Luz Verde Global"
SCORE_CALIDAD_MEDIA_MIN: int = 6   # para "Calidad Media"; debajo, "Alerta Global"

# --- supuestos de cálculo -----------------------------------------------------
TASA_IMPOSITIVA_FALLBACK: float = 0.21   # NOPAT si la tasa efectiva falta o es anómala

# --- umbrales de las señales --------------------------------------------------
# verde: rango (mín, máx) que da luz verde · alerta: lista de rangos que dan alerta.
UMBRALES: Dict[str, Dict[str, Any]] = {
    "Current_Ratio":       {"verde": (1.5, 2.5),   "alerta": [(-INF, 1.0), (3.0, INF)]},
    "EV_EBITDA":           {"verde": (0.0, 12.0),  "alerta": [(-INF, 0.0), (20.0, INF)]},
    "Earnings_Surprise_%": {"verde": (2.0, INF),   "alerta": [(-INF, 0.0)]},
    "Deuda_Neta_EBITDA":   {"verde": (-INF, 2.5),  "alerta": [(3.5, INF)]},  # + alerta si EBITDA ≤ 0
    "Interest_Coverage":   {"verde": (4.0, INF),   "alerta": [(-INF, 2.0)]},
    "FCF_Yield_%":         {"verde": (4.5, INF),   "alerta": [(-INF, 2.0)]},
    "PEG_Ratio":           {"verde": (0.0, 1.2),   "alerta": [(-INF, 0.0), (2.0, INF)]},
    "ROCE_%":              {"verde": (15.0, INF),  "alerta": [(-INF, 8.0)]},
    "ROIC_%":              {"verde": (12.0, INF),  "alerta": [(-INF, 6.0)]},
    "ROE_%":               {"verde": (15.0, INF),  "alerta": [(-INF, 8.0)]},
    "Reinvestment_Rate_%": {"verde": (20.0, 60.0), "alerta": [(-INF, 5.0), (90.0, INF)]},
}

# ROE: el verde exige además apalancamiento bajo; un ROE en rango verde con
# apalancamiento alto se marca como alerta (ROE "inflado" por deuda).
ROE_APALANCAMIENTO_VERDE_MAX: float = 2.5
ROE_APALANCAMIENTO_ALERTA_MIN: float = 4.0


# ==============================================================================
# BLOQUE 2: CONSTANTES Y UTILIDADES DE DATOS
# Etiquetas de señal, extracción resiliente de datos de yfinance y nombres de
# línea contable candidatos.
# ==============================================================================
VERDE = "🟢 Luz Verde"
ALERTA = "🔴 Alerta"
NEUTRAL = "🟡 Neutral"
NA = "⚪ N/D"


def get_row(
    df: Optional[pd.DataFrame], candidates: Sequence[str], col_index: int = 0
) -> float:
    """
    Busca la primera fila cuyo índice coincida con alguno de los nombres
    candidatos (yfinance no es consistente con los nombres de línea contable
    entre tickers/versiones) y devuelve el valor en la columna col_index
    (0 = periodo más reciente). Devuelve np.nan si no encuentra nada.
    """
    if df is None or df.empty:
        return np.nan
    for name in candidates:
        if name in df.index:
            try:
                serie = df.loc[name]
                if isinstance(serie, pd.DataFrame):  # índices duplicados
                    serie = serie.iloc[0]
                val = serie.iloc[col_index]
                if val is None or pd.isna(val):
                    continue
                return float(val)
            except (IndexError, ValueError, TypeError):
                continue
    return np.nan


def get_info_field(info: Dict[str, Any], *keys: str) -> float:
    """Devuelve el primer valor no nulo entre varias posibles claves de .info"""
    for k in keys:
        val = info.get(k)
        if val is not None and not (isinstance(val, float) and np.isnan(val)):
            return float(val)
    return np.nan


def safe_get_df(tk: "yf.Ticker", attr_name: str) -> Optional[pd.DataFrame]:
    """Obtiene un DataFrame contable de un Ticker de forma resiliente."""
    try:
        df = getattr(tk, attr_name)
        if df is None or df.empty:
            return None
        return df
    except Exception:
        return None


def safe_div(numerador: float, denominador: float) -> float:
    """División segura: devuelve NaN si el denominador es 0, NaN o None."""
    try:
        if denominador in (0, None) or pd.isna(denominador) or pd.isna(numerador):
            return np.nan
        return numerador / denominador
    except (TypeError, ZeroDivisionError):
        return np.nan


def safe_calc(func: Callable[[], float], *_args: Any) -> float:
    """Envuelve cualquier cálculo en try/except -> NaN si falla."""
    try:
        val = func()
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return np.nan
        return float(val)
    except Exception:
        return np.nan


def clasificar(
    valor: float,
    es_verde: Callable[[float], bool],
    es_alerta: Callable[[float], bool],
) -> str:
    """Aplica la matriz de reglas: Verde > Alerta > Neutral > N/D."""
    if pd.isna(valor):
        return NA
    try:
        if es_verde(valor):
            return VERDE
        if es_alerta(valor):
            return ALERTA
        return NEUTRAL
    except Exception:
        return NA


# Nombres de línea contable candidatos (yfinance varía entre versiones)
ROWS = {
    "current_assets": ["Total Current Assets", "Current Assets"],
    "current_liab": ["Total Current Liabilities", "Current Liabilities"],
    "total_debt": ["Total Debt"],
    "long_term_debt": ["Long Term Debt"],
    "short_term_debt": ["Current Debt", "Short Long Term Debt", "Short Term Debt"],
    "cash": ["Cash And Cash Equivalents", "Cash Financial", "Cash And Short Term Investments", "Cash"],
    "ebitda": ["EBITDA", "Normalized EBITDA"],
    "ebit": ["EBIT", "Operating Income"],
    "interest_expense": ["Interest Expense", "Interest Expense Non Operating"],
    "operating_cf": ["Operating Cash Flow", "Total Cash From Operating Activities"],
    "capex": ["Capital Expenditure", "Capital Expenditures"],
    "depreciation": ["Depreciation And Amortization", "Depreciation Amortization Depletion", "Depreciation"],
    "net_income": ["Net Income", "Net Income Common Stockholders"],
    "revenue": ["Total Revenue"],
    "total_assets": ["Total Assets"],
    "total_equity": ["Total Stockholder Equity", "Stockholders Equity", "Common Stock Equity"],
    "tax_provision": ["Tax Provision", "Income Tax Expense"],
    "pretax_income": ["Pretax Income"],
    "shares": ["Ordinary Shares Number", "Share Issued"],
    "eps": ["Diluted EPS", "Basic EPS"],
}


# ==============================================================================
# BLOQUE 3: CATÁLOGO DE INDICADORES
# ==============================================================================
@dataclass(frozen=True)
class Indicador:
    horizonte: str
    nombre: str
    columnas: Tuple[str, ...]  # métricas que se muestran en la celda
    formato: str               # str.format aplicado a las columnas
    senal: str                 # columna de señal
    regla: str                 # umbrales en texto para el reporte
    unidad: str = ""           # sufijo en los gráficos: "x", "%" o ""
    # Zonas (lo, hi) con límites exclusivos, tomadas de UMBRALES
    verde: Optional[Tuple[float, float]] = None
    alerta: Tuple[Tuple[float, float], ...] = ()


def _rango(zona: Tuple[float, float], sufijo: str) -> str:
    lo, hi = zona
    if lo == -INF:
        return f"<{hi:g}{sufijo}"
    if hi == INF:
        return f">{lo:g}{sufijo}"
    return f"{lo:g}–{hi:g}{sufijo}"


def _indicador(
    horizonte: str,
    nombre: str,
    columnas: Tuple[str, ...],
    formato: str,
    senal: str,
    unidad: str = "",
    regla: Optional[str] = None,
    alerta_extra: str = "",
) -> Indicador:
    """Crea un indicador con las zonas de UMBRALES[columnas[0]] y su texto de regla."""
    umbral = UMBRALES.get(columnas[0], {})
    verde = tuple(umbral["verde"]) if umbral.get("verde") else None
    alerta = tuple(tuple(z) for z in umbral.get("alerta", ()))
    if regla is None:
        sufijo = "%" if unidad == "%" else ""
        partes = []
        if verde:
            partes.append("Verde " + _rango(verde, sufijo))
        condiciones = [_rango(z, sufijo) for z in alerta] + ([alerta_extra] if alerta_extra else [])
        if condiciones:
            partes.append("Alerta " + " o ".join(condiciones))
        regla = " · ".join(partes)
    return Indicador(horizonte, nombre, columnas, formato, senal, regla, unidad, verde, alerta)


def _regla_roe() -> str:
    roe = UMBRALES["ROE_%"]
    verde = _rango(roe["verde"], "%")
    alerta = " o ".join(_rango(z, "%") for z in roe["alerta"])
    return (f"Verde {verde} con apal. <{ROE_APALANCAMIENTO_VERDE_MAX:g}x · "
            f"Alerta {alerta}, o {verde} con apal. >{ROE_APALANCAMIENTO_ALERTA_MIN:g}x")


INDICADORES: List[Indicador] = [
    _indicador("Corto plazo", "Current Ratio", ("Current_Ratio",), "{:.2f}x",
               "Current_Ratio_Señal", "x"),
    _indicador("Corto plazo", "EV / EBITDA", ("EV_EBITDA",), "{:.1f}x",
               "EV_EBITDA_Señal", "x"),
    _indicador("Corto plazo", "P/E Trailing → Forward", ("PE_Trailing", "PE_Forward"), "{:.1f} → {:.1f}",
               "PE_Señal", regla="Verde si baja · Alerta si sube o Forward ≤0"),
    _indicador("Corto plazo", "Earnings Surprise", ("Earnings_Surprise_%",), "{:+.1f}%",
               "Earnings_Surprise_Señal", "%"),
    _indicador("Mediano plazo", "Deuda Neta / EBITDA", ("Deuda_Neta_EBITDA",), "{:.2f}x",
               "Deuda_Neta_EBITDA_Señal", "x", alerta_extra="EBITDA ≤0"),
    _indicador("Mediano plazo", "Interest Coverage", ("Interest_Coverage",), "{:.1f}x",
               "Interest_Coverage_Señal", "x"),
    _indicador("Mediano plazo", "FCF Yield", ("FCF_Yield_%",), "{:.2f}%",
               "FCF_Yield_Señal", "%"),
    _indicador("Mediano plazo", "PEG Ratio", ("PEG_Ratio",), "{:.2f}",
               "PEG_Señal"),
    _indicador("Largo plazo", "ROCE", ("ROCE_%",), "{:.1f}%",
               "ROCE_Señal", "%"),
    _indicador("Largo plazo", "ROIC", ("ROIC_%",), "{:.1f}%",
               "ROIC_Señal", "%"),
    _indicador("Largo plazo", "ROE (DuPont)", ("ROE_%", "Apalancamiento_x"), "{:.1f}% · apal. {:.1f}x",
               "ROE_Señal", "%", regla=_regla_roe()),
    _indicador("Largo plazo", "Reinvestment Rate", ("Reinvestment_Rate_%",), "{:.1f}%",
               "Reinvestment_Señal", "%"),
]
IND: Dict[str, Indicador] = {ind.senal: ind for ind in INDICADORES}


def clasificar_zonas(valor: float, ind: Indicador) -> str:
    """Clasifica un valor según las zonas verde/alerta del indicador."""
    return clasificar(
        valor,
        lambda v: ind.verde is not None and ind.verde[0] < v < ind.verde[1],
        lambda v: any(lo < v < hi for lo, hi in ind.alerta),
    )


def etiqueta_score(n_verde: int) -> Tuple[str, str]:
    """Devuelve (etiqueta global, clave de estado) según las señales en verde."""
    if n_verde >= SCORE_LUZ_VERDE_MIN:
        return "Luz Verde Global", "good"
    if n_verde >= SCORE_CALIDAD_MEDIA_MIN:
        return "Calidad Media", "warn"
    return "Señal de Alerta Global", "crit"


@dataclass
class ResultadoTicker:
    ticker: str
    metricas: Dict[str, float] = field(default_factory=dict)
    senales: Dict[str, str] = field(default_factory=dict)
    errores: List[str] = field(default_factory=list)
    # señal -> {"f": frecuencia, "n": nota, "p": [(etiqueta, valor, es_hoy), ...]}
    historico: Dict[str, Dict[str, Any]] = field(default_factory=dict)


# ==============================================================================
# BLOQUE 4: CÁLCULO DE MÉTRICAS
# ==============================================================================
def deuda_total(bs: Optional[pd.DataFrame], j: int = 0) -> float:
    total_debt = get_row(bs, ROWS["total_debt"], j)
    if pd.isna(total_debt):
        total_debt = get_row(bs, ROWS["long_term_debt"], j) + get_row(bs, ROWS["short_term_debt"], j)
    return total_debt


def metricas_anuales(
    bs: Optional[pd.DataFrame],
    fin: Optional[pd.DataFrame],
    cf: Optional[pd.DataFrame],
    j: int = 0,
) -> Dict[str, float]:
    """Métricas del ejercicio en la columna j (0 = más reciente). NaN si faltan datos."""
    def g(df: Optional[pd.DataFrame], clave: str) -> float:
        return get_row(df, ROWS[clave], j)

    ebit = g(fin, "ebit")
    ebitda = g(fin, "ebitda")
    total_assets = g(bs, "total_assets")
    total_equity = g(bs, "total_equity")
    revenue = g(fin, "revenue")
    deuda = deuda_total(bs, j)
    caja = g(bs, "cash")

    # Tasa impositiva efectiva para NOPAT
    tax_rate = safe_div(g(fin, "tax_provision"), g(fin, "pretax_income"))
    if pd.isna(tax_rate) or tax_rate < 0 or tax_rate > 0.6:
        tax_rate = TASA_IMPOSITIVA_FALLBACK
    nopat = ebit * (1 - tax_rate)

    capex = abs(g(cf, "capex"))  # yfinance lo reporta normalmente negativo
    apalancamiento = safe_div(total_assets, total_equity)
    margen_neto = safe_div(g(fin, "net_income"), revenue)
    rotacion_activos = safe_div(revenue, total_assets)

    return {
        "EBITDA": ebitda,
        "Deuda": deuda,
        "Caja": caja,
        "FCF": g(cf, "operating_cf") - capex,
        "Deuda_Neta_EBITDA": safe_div(deuda - caja, ebitda),
        "Interest_Coverage": safe_div(ebit, abs(g(fin, "interest_expense"))),
        "ROCE_%": safe_div(ebit, total_assets - g(bs, "current_liab")) * 100,
        "ROIC_%": safe_div(nopat, deuda + total_equity - caja) * 100,
        # ROE por descomposición DuPont 3-Way
        "ROE_%": margen_neto * rotacion_activos * apalancamiento * 100,
        "Apalancamiento_x": apalancamiento,
        "Reinvestment_Rate_%": safe_div(capex - g(cf, "depreciation"), nopat) * 100,
    }


def _estados_anuales(tk: "yf.Ticker") -> Tuple[Optional[pd.DataFrame], ...]:
    return tuple(safe_get_df(tk, a) for a in ("balance_sheet", "financials", "cashflow"))


def calcular_corto_plazo(tk: "yf.Ticker", info: Dict[str, Any], res: ResultadoTicker) -> None:
    q_bs = safe_get_df(tk, "quarterly_balance_sheet")

    # 1. Current Ratio
    def _current_ratio():
        ca = get_row(q_bs, ROWS["current_assets"])
        cl = get_row(q_bs, ROWS["current_liab"])
        return safe_div(ca, cl)

    cr = safe_calc(_current_ratio)
    res.metricas["Current_Ratio"] = cr
    res.senales["Current_Ratio_Señal"] = clasificar_zonas(cr, IND["Current_Ratio_Señal"])

    # 2. EV / EBITDA (yfinance ya lo expone como TTM en .info)
    ev_ebitda = safe_calc(lambda: get_info_field(info, "enterpriseToEbitda"))
    res.metricas["EV_EBITDA"] = ev_ebitda
    res.senales["EV_EBITDA_Señal"] = clasificar_zonas(ev_ebitda, IND["EV_EBITDA_Señal"])

    # 3. P/E Trailing vs Forward
    pe_trailing = safe_calc(lambda: get_info_field(info, "trailingPE"))
    pe_forward = safe_calc(lambda: get_info_field(info, "forwardPE"))
    res.metricas["PE_Trailing"] = pe_trailing
    res.metricas["PE_Forward"] = pe_forward

    def _pe_signal():
        if pd.isna(pe_trailing) or pd.isna(pe_forward):
            return NA
        if pe_forward <= 0:  # se esperan pérdidas
            return ALERTA
        if pe_forward < pe_trailing:
            return VERDE
        if pe_forward > pe_trailing:
            return ALERTA
        return NEUTRAL

    res.senales["PE_Señal"] = _pe_signal()

    # 4. Earnings Surprise %
    def _earnings_surprise():
        ed = tk.get_earnings_dates(limit=8)
        if ed is None or ed.empty or "Surprise(%)" not in ed.columns:
            return np.nan
        pasados = ed.dropna(subset=["Surprise(%)"]).sort_index(ascending=False)
        if pasados.empty:
            return np.nan
        # yfinance ya entrega la sorpresa en % (ej. 3.46 = 3.46%)
        return float(pasados["Surprise(%)"].iloc[0])

    surprise = safe_calc(_earnings_surprise)
    res.metricas["Earnings_Surprise_%"] = surprise
    res.senales["Earnings_Surprise_Señal"] = clasificar_zonas(surprise, IND["Earnings_Surprise_Señal"])


def calcular_mediano_plazo(tk: "yf.Ticker", info: Dict[str, Any], res: ResultadoTicker) -> None:
    m = metricas_anuales(*_estados_anuales(tk))

    # EBITDA TTM de .info; si falta, el del último ejercicio
    ebitda = safe_calc(lambda: get_info_field(info, "ebitda"))
    if pd.isna(ebitda):
        ebitda = m["EBITDA"]

    # 5. Deuda Neta / EBITDA
    dn_ebitda = safe_div(m["Deuda"] - m["Caja"], ebitda)
    res.metricas["Deuda_Neta_EBITDA"] = dn_ebitda
    if not pd.isna(ebitda) and ebitda <= 0:
        # Con EBITDA negativo el ratio sale negativo y parecería "sano"
        res.senales["Deuda_Neta_EBITDA_Señal"] = ALERTA
    else:
        res.senales["Deuda_Neta_EBITDA_Señal"] = clasificar_zonas(dn_ebitda, IND["Deuda_Neta_EBITDA_Señal"])

    # 6. Interest Coverage Ratio (EBIT / Intereses)
    res.metricas["Interest_Coverage"] = m["Interest_Coverage"]
    res.senales["Interest_Coverage_Señal"] = clasificar_zonas(m["Interest_Coverage"], IND["Interest_Coverage_Señal"])

    # 7. Free Cash Flow Yield (FCF del último ejercicio / capitalización actual)
    market_cap = safe_calc(lambda: get_info_field(info, "marketCap"))
    fcf_yield = safe_div(m["FCF"], market_cap) * 100
    res.metricas["FCF_Yield_%"] = fcf_yield
    res.senales["FCF_Yield_Señal"] = clasificar_zonas(fcf_yield, IND["FCF_Yield_Señal"])

    # 8. PEG Ratio
    def _peg():
        peg = get_info_field(info, "pegRatio", "trailingPegRatio")
        if not pd.isna(peg):
            return peg
        pe_trailing = get_info_field(info, "trailingPE")
        crecimiento = get_info_field(info, "earningsGrowth")  # fracción, ej 0.15
        if pd.isna(crecimiento) or crecimiento == 0:
            return np.nan
        return safe_div(pe_trailing, crecimiento * 100)

    peg = safe_calc(_peg)
    res.metricas["PEG_Ratio"] = peg
    res.senales["PEG_Señal"] = clasificar_zonas(peg, IND["PEG_Señal"])


def calcular_largo_plazo(tk: "yf.Ticker", info: Dict[str, Any], res: ResultadoTicker) -> None:
    m = metricas_anuales(*_estados_anuales(tk))

    # 9. ROCE  10. ROIC  12. Reinvestment Rate
    for col, senal in (
        ("ROCE_%", "ROCE_Señal"),
        ("ROIC_%", "ROIC_Señal"),
        ("Reinvestment_Rate_%", "Reinvestment_Señal"),
    ):
        res.metricas[col] = m[col]
        res.senales[senal] = clasificar_zonas(m[col], IND[senal])

    # 11. ROE — Descomposición DuPont 3-Way
    roe, apalancamiento = m["ROE_%"], m["Apalancamiento_x"]
    res.metricas["ROE_%"] = roe
    res.metricas["Apalancamiento_x"] = apalancamiento

    def _roe_signal():
        if pd.isna(roe) or pd.isna(apalancamiento):
            return NA
        zona = clasificar_zonas(roe, IND["ROE_Señal"])
        if zona == VERDE and apalancamiento < ROE_APALANCAMIENTO_VERDE_MAX:
            return VERDE
        if zona == VERDE and apalancamiento > ROE_APALANCAMIENTO_ALERTA_MIN:
            return ALERTA  # ROE alto "inflado" por apalancamiento excesivo
        if zona == ALERTA:
            return ALERTA
        return NEUTRAL

    res.senales["ROE_Señal"] = _roe_signal()


# ==============================================================================
# BLOQUE 5: HISTÓRICO
# Series de los últimos ejercicios/trimestres para los gráficos del reporte.
# ==============================================================================
_MESES = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")


def _etiqueta_mes(fecha: Any) -> str:
    f = pd.Timestamp(fecha)
    return f"{_MESES[f.month - 1]} {f.year}"


def _serie(
    puntos: Sequence[Tuple[str, float]],
    n: int,
    frecuencia: str,
    nota: str = "",
    hoy: Sequence[Tuple[str, float]] = (),
) -> Dict[str, Any]:
    """
    puntos: (etiqueta, valor) del más reciente al más antiguo. Devuelve los n
    últimos válidos en orden cronológico, seguidos de los puntos "hoy" (valores
    con precio actual/TTM, que el gráfico dibuja con línea discontinua).
    """
    def ok(v: float) -> bool:
        return not pd.isna(v) and np.isfinite(v)

    pts = [(e, float(v), False) for e, v in puntos if ok(v)][:n][::-1]
    pts += [(e, float(v), True) for e, v in hoy if ok(v)]
    return {"f": frecuencia, "n": nota, "p": pts}


def calcular_historico(
    tk: "yf.Ticker",
    res: ResultadoTicker,
    n_anual: int = HIST_EJERCICIOS,
    n_trim: int = HIST_TRIMESTRES,
) -> None:
    h, met = res.historico, res.metricas

    # Current Ratio: balances trimestrales
    q_bs = safe_get_df(tk, "quarterly_balance_sheet")
    if q_bs is not None:
        h["Current_Ratio_Señal"] = _serie(
            [(_etiqueta_mes(c), safe_div(get_row(q_bs, ROWS["current_assets"], j),
                                         get_row(q_bs, ROWS["current_liab"], j)))
             for j, c in enumerate(q_bs.columns)],
            n_trim, "Trimestral",
        )

    # Earnings Surprise: últimas publicaciones de resultados
    try:
        ed = tk.get_earnings_dates(limit=8)
        pasados = ed.dropna(subset=["Surprise(%)"]).sort_index(ascending=False)
        h["Earnings_Surprise_Señal"] = _serie(
            [(_etiqueta_mes(f), v) for f, v in pasados["Surprise(%)"].items()],
            n_trim, "Trimestral · por publicación",
        )
    except Exception:
        pass

    bs, fin, cf = _estados_anuales(tk)
    if fin is None:
        return
    fechas = list(fin.columns)
    etiquetas = [f"FY{pd.Timestamp(f).year}" for f in fechas]
    ms = [metricas_anuales(bs, fin, cf, j) for j in range(len(fechas))]

    # Precio de cierre ajustado por splits (Yahoo también ajusta acciones y BPA)
    try:
        close = tk.history(period=f"{n_anual + 2}y", auto_adjust=False)["Close"]
        close.index = close.index.tz_localize(None)
    except Exception:
        close = pd.Series(dtype=float)

    # Valoración al cierre de cada ejercicio
    for j, fecha in enumerate(fechas):
        precio = float(close.asof(pd.Timestamp(fecha))) if not close.empty else np.nan
        mcap = precio * get_row(bs, ROWS["shares"], j)
        eps = get_row(fin, ROWS["eps"], j)
        eps_prev = get_row(fin, ROWS["eps"], j + 1)
        pe = safe_div(precio, eps) if eps > 0 else np.nan
        crecimiento = safe_div(eps, eps_prev) - 1 if eps_prev > 0 else np.nan
        ms[j]["EV_EBITDA"] = safe_div(mcap + ms[j]["Deuda"] - ms[j]["Caja"], ms[j]["EBITDA"])
        ms[j]["PE"] = pe
        ms[j]["FCF_Yield_%"] = safe_div(ms[j]["FCF"], mcap) * 100
        ms[j]["PEG"] = safe_div(pe, crecimiento * 100)

    anual = "Anual · cierre fiscal"
    series = [
        ("EV_EBITDA_Señal", "EV_EBITDA", "Hoy = EV actual / EBITDA TTM (Yahoo)",
         [("Hoy", met.get("EV_EBITDA", np.nan))]),
        ("PE_Señal", "PE", "P/E trailing por ejercicio · Hoy = TTM · Fwd = estimado",
         [("Hoy", met.get("PE_Trailing", np.nan)), ("Fwd", met.get("PE_Forward", np.nan))]),
        ("Deuda_Neta_EBITDA_Señal", "Deuda_Neta_EBITDA", "Hoy = deuda neta del último balance / EBITDA TTM",
         [("Hoy", met.get("Deuda_Neta_EBITDA", np.nan))]),
        ("Interest_Coverage_Señal", "Interest_Coverage", "", []),
        ("FCF_Yield_Señal", "FCF_Yield_%", "Hoy = FCF del último ejercicio / capitalización actual",
         [("Hoy", met.get("FCF_Yield_%", np.nan))]),
        ("PEG_Señal", "PEG", "Histórico con crecimiento real del BPA · Hoy = estimación de Yahoo",
         [("Hoy", met.get("PEG_Ratio", np.nan))]),
        ("ROCE_Señal", "ROCE_%", "", []),
        ("ROIC_Señal", "ROIC_%", "", []),
        ("ROE_Señal", "ROE_%", "La señal también depende del apalancamiento", []),
        ("Reinvestment_Señal", "Reinvestment_Rate_%", "", []),
    ]
    for senal, clave, nota, hoy in series:
        h[senal] = _serie([(e, m.get(clave, np.nan)) for e, m in zip(etiquetas, ms)],
                          n_anual, anual, nota, hoy)


# ==============================================================================
# BLOQUE 6: ANÁLISIS DE LA CARTERA
# Orquesta el cálculo por ticker y consolida los resultados.
# ==============================================================================
def analizar_cartera(tickers_list: Sequence[str]) -> pd.DataFrame:
    """
    Analiza una lista de tickers y devuelve un DataFrame consolidado con los
    12 indicadores fundamentales, sus señales y un Score_Calidad global.

    Parameters
    ----------
    tickers_list : lista de símbolos bursátiles, ej. ["AAPL", "MSFT"]

    Returns
    -------
    pd.DataFrame con una fila por ticker. El histórico de cada indicador
    queda en df.attrs["historico"] (lo usa exportar_html).
    """
    filas: List[Dict[str, Any]] = []
    historicos: Dict[str, Dict[str, Any]] = {}

    for ticker_str in tickers_list:
        print(f"Procesando {ticker_str}...")
        res = ResultadoTicker(ticker=ticker_str)
        try:
            tk = yf.Ticker(ticker_str)
            try:
                info = tk.info or {}
            except Exception:
                info = {}
                res.errores.append("No se pudo obtener .info")

            calcular_corto_plazo(tk, info, res)
            calcular_mediano_plazo(tk, info, res)
            calcular_largo_plazo(tk, info, res)
            try:
                calcular_historico(tk, res)
            except Exception as exc:
                res.errores.append(f"Histórico: {exc}")

        except Exception as exc:  # nunca debe tumbar el batch completo
            res.errores.append(str(exc))
        historicos[ticker_str] = res.historico

        if res.errores:
            print(f"  Avisos en {ticker_str}: {'; '.join(res.errores)}")

        # --- Score de calidad ---
        n_verde = sum(1 for v in res.senales.values() if v == VERDE)
        etiqueta, _ = etiqueta_score(n_verde)
        score = f"{n_verde}/{len(INDICADORES)} Criterios Cumplidos - {etiqueta}"

        fila = {"Ticker": ticker_str}
        fila.update(res.metricas)
        fila.update(res.senales)
        fila["Score_Calidad"] = score
        filas.append(fila)

    columnas_orden = ["Ticker"]
    for ind in INDICADORES:
        columnas_orden += [*ind.columnas, ind.senal]
    columnas_orden.append("Score_Calidad")

    df = pd.DataFrame(filas)
    columnas_presentes = [c for c in columnas_orden if c in df.columns]
    df = df[columnas_presentes]

    # Redondeo de columnas numéricas para presentación
    for col in df.columns:
        if col not in ("Ticker", "Score_Calidad") and "Señal" not in col:
            df[col] = df[col].apply(lambda x: round(x, 2) if pd.notna(x) else np.nan)

    df.attrs["historico"] = historicos
    return df


# ==============================================================================
# BLOQUE 7: REPORTE HTML
# Tarjetas resumen, matriz de señales y gráficos de histórico.
# ==============================================================================
# Señal -> (clase CSS, glifo, texto). El glifo distingue el estado sin
# depender del color (daltonismo / impresión en B/N).
_SENAL_HTML = {
    VERDE: ("good", "✓", "Verde"),
    NEUTRAL: ("warn", "–", "Neutral"),
    ALERTA: ("crit", "!", "Alerta"),
    NA: ("na", "?", "N/D"),
}

_HTML_TEMPLATE = Template("""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Análisis Fundamental</title>
<style>
  :root {
    color-scheme: light;
    --page: #f9f9f7; --surface: #fcfcfb; --ink: #0b0b0b; --ink-2: #52514e;
    --muted: #898781; --grid: #e1e0d9; --border: rgba(11,11,11,0.10);
    --good: #0ca30c; --warn: #fab219; --crit: #d03b3b; --na: #c3c2b7;
    --series: #2a78d6; --axis: #c3c2b7; --tint: 13%; --band: 0.12;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      color-scheme: dark;
      --page: #0d0d0d; --surface: #1a1a19; --ink: #ffffff; --ink-2: #c3c2b7;
      --grid: #2c2c2a; --border: rgba(255,255,255,0.10); --na: #5a5955;
      --series: #3987e5; --axis: #383835; --tint: 20%; --band: 0.2;
    }
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--page); color: var(--ink);
         font: 14px/1.45 system-ui, -apple-system, "Segoe UI", sans-serif; }
  .wrap { max-width: 1200px; margin: 0 auto; padding: 32px 20px 48px; }
  header h1 { font-size: 24px; margin: 0 0 4px; letter-spacing: -0.01em; }
  .meta { color: var(--ink-2); margin: 0; }
  h2.section { font-size: 15px; margin: 32px 0 12px; }

  /* Estados: cada clase fija --s (color) y --s-ink (tinta del glifo) */
  .good { --s: var(--good); --s-ink: #0b0b0b; }
  .warn { --s: var(--warn); --s-ink: #0b0b0b; }
  .crit { --s: var(--crit); --s-ink: #ffffff; }
  .na   { --s: var(--na);   --s-ink: var(--ink-2); }
  .ico { display: inline-grid; place-items: center; width: 16px; height: 16px;
         border-radius: 50%; background: var(--s); color: var(--s-ink);
         font: 700 10px/1 system-ui, sans-serif; font-style: normal; flex: none; }

  .legend { display: flex; flex-wrap: wrap; gap: 8px 18px; margin-top: 16px;
            color: var(--ink-2); font-size: 13px; }
  .legend span { display: inline-flex; align-items: center; gap: 6px; }

  /* Tarjetas resumen */
  .cards { display: grid; gap: 12px;
           grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); }
  .card { background: var(--surface); border: 1px solid var(--border);
          border-radius: 10px; padding: 16px; }
  .card-head { display: flex; flex-wrap: wrap; justify-content: space-between;
               align-items: baseline; gap: 4px 8px; }
  .card h3 { margin: 0; font-size: 18px; }
  .badge { display: inline-flex; align-items: center; gap: 6px; font-size: 12px;
           color: var(--ink-2); white-space: nowrap; }
  .score { margin: 10px 0 12px; }
  .score b { font-size: 36px; line-height: 1; font-weight: 650; }
  .score span { color: var(--ink-2); margin-left: 4px; }
  .strip { display: flex; gap: 8px; }
  .strip-group { flex: 1; min-width: 0; }
  .strip-cells { display: flex; gap: 2px; }
  .strip-cells .ico { flex: 1; width: auto; height: 22px; border-radius: 4px;
                      cursor: default; outline-offset: 2px; }
  .strip-label { color: var(--muted); font-size: 11px; margin-top: 4px; }
  .counts { color: var(--ink-2); font-size: 12px; margin-top: 12px;
            font-variant-numeric: tabular-nums; }

  /* Matriz */
  .table-wrap { overflow-x: auto; background: var(--surface);
                border: 1px solid var(--border); border-radius: 10px; }
  table { border-collapse: separate; border-spacing: 0; width: 100%; }
  th, td { padding: 10px 12px; text-align: left; vertical-align: middle;
           border-bottom: 1px solid var(--grid); }
  thead th { font-size: 13px; position: sticky; top: 0; background: var(--surface); }
  thead th.tk { text-align: center; font-size: 15px; }
  th.ind { position: sticky; left: 0; background: var(--surface); min-width: 220px;
           font-weight: 600; z-index: 1; }
  .rule { display: block; font-weight: 400; color: var(--muted); font-size: 12px;
          margin-top: 2px; }
  tr.group th { background: var(--page); color: var(--ink-2); font-size: 12px;
                text-transform: uppercase; letter-spacing: 0.06em; padding: 8px 12px; }
  td.cell { text-align: center; min-width: 150px; cursor: pointer;
            background: color-mix(in srgb, var(--s) var(--tint), var(--surface)); }
  td.cell:hover, td.cell:focus-visible, td.cell.open {
    outline: 2px solid var(--series); outline-offset: -2px; }
  .val { display: block; font-variant-numeric: tabular-nums; font-weight: 600;
         white-space: nowrap; }
  .sub { display: flex; align-items: center; justify-content: center; gap: 8px;
         margin-top: 3px; }
  .pill { display: inline-flex; align-items: center; gap: 5px;
          font-size: 12px; color: var(--ink-2); }
  .spark { display: block; }
  .spark .l { stroke: var(--ink-2); stroke-width: 1.5; stroke-linecap: round; }
  .spark .l.d { stroke-dasharray: 2 2.5; }
  .spark .dot { fill: var(--ink); }

  /* Ventana con el histórico */
  .pop { position: fixed; z-index: 20; width: 380px; max-width: calc(100vw - 16px);
         background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
         box-shadow: 0 10px 28px rgba(0,0,0,0.22); padding: 12px 14px 10px;
         pointer-events: none; }
  .pop[hidden] { display: none; }
  .pop-h { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; }
  .pop-h b { font-size: 14px; }
  .pop-h span { color: var(--muted); font-size: 11px; text-align: right; }
  .pop-e { color: var(--ink-2); font-size: 13px; padding: 18px 0 8px; }
  .pop-n { color: var(--muted); font-size: 11px; margin-top: 2px; }
  .pop-k { display: flex; flex-wrap: wrap; gap: 4px 12px; color: var(--ink-2);
           font-size: 11px; margin-top: 6px; }
  .pop-k span { display: inline-flex; align-items: center; gap: 5px; }
  .sw { display: inline-block; width: 12px; height: 8px; border-radius: 2px;
        background: color-mix(in srgb, var(--s) 45%, var(--surface)); }
  .sw-d { display: inline-block; width: 14px; border-top: 2px dashed var(--series); }
  .spk:empty { display: none; }
  .chart { display: block; width: 100%; height: auto; margin-top: 6px; }
  .chart .band { fill: var(--s); fill-opacity: var(--band); }
  .chart .grid { stroke: var(--grid); }
  .chart .zero { stroke: var(--axis); }
  .chart .tick { fill: var(--muted); font-size: 10px; font-variant-numeric: tabular-nums; }
  .chart .ln { stroke: var(--series); stroke-width: 2; stroke-linecap: round; }
  .chart .ln.d { stroke-dasharray: 4 4; }
  .chart .mk { fill: var(--series); stroke: var(--surface); stroke-width: 2; }
  .chart .mk.d { fill: var(--surface); stroke: var(--series); }
  .chart .xv { fill: var(--ink-2); font-size: 11px; font-variant-numeric: tabular-nums; }
  .chart .xv.last { fill: var(--ink); font-weight: 650; }
  .chart .xl { fill: var(--muted); font-size: 10px; }
  tbody tr:not(.group):hover th.ind { color: var(--ink); background: var(--page); }
  tr.total th, tr.total td { border-bottom: 0; font-weight: 650; }
  tr.total td { text-align: center; font-variant-numeric: tabular-nums; }

  .note { color: var(--muted); font-size: 12px; margin-top: 16px; }

  .tip { position: fixed; z-index: 10; pointer-events: none; max-width: 260px;
         background: var(--ink); color: var(--page); padding: 6px 9px;
         border-radius: 6px; font-size: 12px; transform: translate(-50%, -100%); }
  .tip[hidden] { display: none; }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Análisis Fundamental</h1>
    <p class="meta">$n_tickers tickers · $n_ind indicadores · generado $fecha · datos de Yahoo Finance</p>
    <div class="legend">
      <span><i class="ico good">✓</i>Verde: cumple el criterio</span>
      <span><i class="ico warn">–</i>Neutral</span>
      <span><i class="ico crit">!</i>Alerta</span>
      <span><i class="ico na">?</i>Sin datos</span>
    </div>
  </header>

  <h2 class="section">Resumen por ticker</h2>
  <div class="cards">$cards</div>

  <h2 class="section">Detalle de indicadores</h2>
  <div class="table-wrap">
    <table>
      <thead><tr><th class="ind">Indicador</th>$thead</tr></thead>
      <tbody>$tbody</tbody>
    </table>
  </div>
  <p class="note">Pasa el cursor sobre un valor (o tócalo en el móvil) para ver su histórico.
  La mini-línea de cada celda resume la misma serie.<br>
  Score = señales en verde sobre $n_ind. Una señal sin datos cuenta como no cumplida.
  Tickers ordenados por score. Luz Verde Global ≥ $score_verde · Calidad Media ≥ $score_media ·
  Alerta Global &lt; $score_media.</p>
</div>
<div class="tip" id="tip" role="tooltip" hidden></div>
<div class="pop" id="pop" role="dialog" hidden></div>
<script type="application/json" id="d-ind">$ind_json</script>
<script type="application/json" id="d-hist">$hist_json</script>
<script type="application/json" id="d-tk">$tk_json</script>
<script>
(function () {
  var IND = JSON.parse(document.getElementById('d-ind').textContent);
  var HIST = JSON.parse(document.getElementById('d-hist').textContent);
  var TK = JSON.parse(document.getElementById('d-tk').textContent);
  var NS = 'http://www.w3.org/2000/svg';

  function svgEl(tag, attrs, parent) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function fmt(v, u) {
    var a = Math.abs(v);
    return v.toFixed(a >= 100 ? 0 : a >= 10 ? 1 : 2) + u;
  }
  function extent(vals) {
    var lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals);
    if (lo === hi) { var d = Math.abs(lo) * 0.1 || 1; lo -= d; hi += d; }
    var pad = (hi - lo) * 0.12;
    return [lo - pad, hi + pad];
  }
  function niceStep(span) {
    var raw = span / 3, p = Math.pow(10, Math.floor(Math.log10(raw))), m = raw / p;
    return (m < 1.5 ? 1 : m < 3 ? 2 : m < 7 ? 5 : 10) * p;
  }
  function values(h) { return h.p.map(function (p) { return p[1]; }); }

  // Mini-línea dentro de la celda
  function sparkline(h) {
    var W = 56, H = 18, n = h.p.length, vals = values(h), dom = extent(vals);
    var svg = svgEl('svg', {width: W, height: H, viewBox: '0 0 ' + W + ' ' + H,
                            'class': 'spark', 'aria-hidden': 'true'});
    function x(i) { return 3 + i * (W - 6) / (n - 1); }
    function y(v) { return H - 3 - (v - dom[0]) / (dom[1] - dom[0]) * (H - 6); }
    for (var i = 1; i < n; i++) {
      svgEl('line', {x1: x(i - 1), y1: y(vals[i - 1]), x2: x(i), y2: y(vals[i]),
                     'class': h.p[i][2] ? 'l d' : 'l'}, svg);
    }
    svgEl('circle', {cx: x(n - 1), cy: y(vals[n - 1]), r: 2.5, 'class': 'dot'}, svg);
    return svg;
  }

  // Gráfico de líneas con zonas verde / alerta del indicador
  function chart(h, ind) {
    var W = 360, H = 190, L = 44, R = 10, T = 8, B = 42;
    var pw = W - L - R, ph = H - T - B, n = h.p.length, vals = values(h);
    // Extiende el eje hasta el umbral más cercano por debajo/encima si está
    // cerca, para que se vea a qué distancia está el indicador de cada zona
    var lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals);
    var reach = Math.max(hi - lo, Math.abs(hi) * 0.5), below = null, above = null;
    [].concat(ind.v || [], [].concat.apply([], ind.a)).forEach(function (b) {
      if (b === null) return;
      if (b < lo && lo - b <= reach && (below === null || b > below)) below = b;
      if (b > hi && b - hi <= reach && (above === null || b < above)) above = b;
    });
    var dom = extent(vals.concat(below === null ? [] : [below], above === null ? [] : [above]));
    var step = niceStep(dom[1] - dom[0]);
    var y0 = Math.floor(dom[0] / step) * step, y1 = Math.ceil(dom[1] / step) * step;
    function x(i) { return L + 22 + i * (pw - 44) / Math.max(n - 1, 1); }
    function y(v) { return T + ph - (v - y0) / (y1 - y0) * ph; }
    var svg = svgEl('svg', {viewBox: '0 0 ' + W + ' ' + H, 'class': 'chart', role: 'img'});
    svg.bands = {};  // zonas que quedaron visibles (para la leyenda)

    function band(z, cls) {
      var zlo = z[0] === null ? y0 : Math.max(z[0], y0);
      var zhi = z[1] === null ? y1 : Math.min(z[1], y1);
      if (zhi <= zlo) return;
      svgEl('rect', {x: L, y: y(zhi), width: pw, height: y(zlo) - y(zhi), 'class': 'band ' + cls}, svg);
      svg.bands[cls] = true;
    }
    if (ind.v) band(ind.v, 'good');
    ind.a.forEach(function (z) { band(z, 'crit'); });

    var dec = step >= 1 ? 0 : step >= 0.1 ? 1 : 2;
    for (var k = 0; y0 + k * step <= y1 + step / 2; k++) {
      var t = y0 + k * step, zero = Math.abs(t) < step / 1e6;
      svgEl('line', {x1: L, x2: W - R, y1: y(t), y2: y(t), 'class': zero ? 'zero' : 'grid'}, svg);
      svgEl('text', {x: L - 6, y: y(t) + 3.5, 'text-anchor': 'end', 'class': 'tick'}, svg)
        .textContent = (zero ? 0 : t).toFixed(dec) + ind.u;
    }
    for (var i = 1; i < n; i++) {
      svgEl('line', {x1: x(i - 1), y1: y(vals[i - 1]), x2: x(i), y2: y(vals[i]),
                     'class': h.p[i][2] ? 'ln d' : 'ln'}, svg);
    }
    var desc = [];
    h.p.forEach(function (p, i) {
      var last = i === n - 1;
      svgEl('circle', {cx: x(i), cy: y(p[1]), r: last ? 5 : 4, 'class': p[2] ? 'mk d' : 'mk'}, svg);
      svgEl('text', {x: x(i), y: H - B + 18, 'text-anchor': 'middle',
                     'class': last ? 'xv last' : 'xv'}, svg).textContent = fmt(p[1], ind.u);
      svgEl('text', {x: x(i), y: H - B + 32, 'text-anchor': 'middle', 'class': 'xl'}, svg)
        .textContent = p[0];
      desc.push(p[0] + ': ' + fmt(p[1], ind.u));
    });
    svg.setAttribute('aria-label', ind.n + '. ' + desc.join(', '));
    return svg;
  }

  function div(cls, text) {
    var d = document.createElement('div');
    d.className = cls;
    if (text) d.textContent = text;
    return d;
  }

  // Ventana emergente: hover la muestra, clic/toque la fija, Esc la cierra
  var pop = document.getElementById('pop'), anchor = null, pinned = false;

  function place() {
    var r = anchor.getBoundingClientRect(), w = pop.offsetWidth, hh = pop.offsetHeight;
    var left = Math.min(Math.max(r.left + r.width / 2 - w / 2, 8), window.innerWidth - w - 8);
    var top = r.bottom + 8;
    if (top + hh > window.innerHeight - 8) top = Math.max(8, r.top - hh - 8);
    pop.style.left = left + 'px';
    pop.style.top = top + 'px';
  }
  function open(cell) {
    if (anchor) anchor.classList.remove('open');
    var t = +cell.getAttribute('data-t'), i = +cell.getAttribute('data-i');
    var ind = IND[i], h = HIST[t][i];
    pop.textContent = '';
    var head = div('pop-h');
    var b = document.createElement('b');
    b.textContent = ind.n + ' · ' + TK[t];
    var f = document.createElement('span');
    f.textContent = h ? h.f : '';
    head.appendChild(b);
    head.appendChild(f);
    pop.appendChild(head);
    if (h && h.p.length >= 2) {
      var svg = chart(h, ind);
      pop.appendChild(svg);
      var key = div('pop-k'), parts = [];
      if (svg.bands.good) parts.push(['sw good', 'Zona verde']);
      if (svg.bands.crit) parts.push(['sw crit', 'Zona alerta']);
      if (h.p.some(function (p) { return p[2]; })) parts.push(['sw-d', 'Precio de hoy / estimado']);
      parts.forEach(function (p) {
        var s = document.createElement('span'), sw = document.createElement('i');
        sw.className = p[0];
        s.appendChild(sw);
        s.appendChild(document.createTextNode(p[1]));
        key.appendChild(s);
      });
      pop.appendChild(key);
      if (h.n) pop.appendChild(div('pop-n', h.n));
    } else {
      pop.appendChild(div('pop-e', 'Sin histórico suficiente para graficar.'));
    }
    pop.hidden = false;
    anchor = cell;
    cell.classList.add('open');
    place();
  }
  function close() {
    pop.hidden = true;
    if (anchor) anchor.classList.remove('open');
    anchor = null;
    pinned = false;
  }

  document.querySelectorAll('td.cell').forEach(function (c) {
    var h = HIST[+c.getAttribute('data-t')][+c.getAttribute('data-i')];
    var slot = c.querySelector('.spk');
    if (h && h.p.length >= 2 && slot) slot.appendChild(sparkline(h));
  });

  document.addEventListener('mouseover', function (e) {
    var c = e.target.closest('td.cell');
    if (c && !pinned && c !== anchor) open(c);
  });
  document.addEventListener('mouseout', function (e) {
    if (pinned || !anchor || !anchor.contains(e.target)) return;
    if (!e.relatedTarget || !anchor.contains(e.relatedTarget)) close();
  });
  document.addEventListener('click', function (e) {
    var c = e.target.closest('td.cell');
    if (c) {
      if (pinned && c === anchor) { close(); return; }
      open(c);
      pinned = true;
    } else if (pinned) {
      close();
    }
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { close(); return; }
    var c = e.target.closest && e.target.closest('td.cell');
    if (c && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); c.click(); }
  });
  document.addEventListener('focusin', function (e) {
    var c = e.target.closest('td.cell');
    if (c && !pinned) open(c);
  });
  document.addEventListener('focusout', function (e) {
    if (!pinned && anchor && e.target === anchor) close();
  });
  window.addEventListener('scroll', function () { if (anchor) place(); }, true);
  window.addEventListener('resize', function () { if (anchor) place(); });
})();
</script>
<script>
(function () {
  var tip = document.getElementById('tip');
  function show(e) {
    var el = e.target.closest('[data-tip]');
    if (!el) return;
    tip.textContent = el.getAttribute('data-tip');
    tip.hidden = false;
    var r = el.getBoundingClientRect();
    var half = tip.offsetWidth / 2;
    var x = Math.min(Math.max(r.left + r.width / 2, half + 8), window.innerWidth - half - 8);
    tip.style.left = x + 'px';
    tip.style.top = (r.top - 8) + 'px';
  }
  function hide(e) {
    if (e.target.closest('[data-tip]')) tip.hidden = true;
  }
  document.addEventListener('mouseover', show);
  document.addEventListener('focusin', show);
  document.addEventListener('mouseout', hide);
  document.addEventListener('focusout', hide);
  window.addEventListener('scroll', function () { tip.hidden = true; }, true);
})();
</script>
</body>
</html>
""")


def _formatear_valor(row: pd.Series, ind: Indicador) -> str:
    valores = [row.get(c, np.nan) for c in ind.columnas]
    if any(pd.isna(v) for v in valores):
        return "N/D"
    return ind.formato.format(*valores)


def exportar_html(
    df: pd.DataFrame, path: str = OUTPUT_HTML, abrir: bool = OPEN_BROWSER
) -> str:
    """
    Genera un reporte HTML autocontenido (tarjetas + matriz de señales).
    Una ruta relativa se resuelve contra la carpeta del script.
    """
    esc = html.escape
    n_ind = len(INDICADORES)

    # Tickers ordenados por número de señales en verde (orden estable)
    tickers = []
    for _, row in df.iterrows():
        senales = [row.get(ind.senal, NA) for ind in INDICADORES]
        senales = [s if s in _SENAL_HTML else NA for s in senales]
        tickers.append((row, senales, sum(s == VERDE for s in senales)))
    tickers.sort(key=lambda t: -t[2])

    horizontes = list(dict.fromkeys(ind.horizonte for ind in INDICADORES))

    # --- Tarjetas resumen ---
    cards = []
    for row, senales, n_verde in tickers:
        conteo = {k: sum(s == k for s in senales) for k in (VERDE, NEUTRAL, ALERTA, NA)}
        if conteo[NA] == n_ind:  # ticker inválido o sin datos en Yahoo
            etiqueta, clave = "Sin datos", "na"
        else:
            etiqueta, clave = etiqueta_score(n_verde)
        glifo_badge = {"good": "✓", "warn": "–", "crit": "!", "na": "?"}[clave]
        grupos = []
        for hz in horizontes:
            celdas = []
            for ind, s in zip(INDICADORES, senales):
                if ind.horizonte != hz:
                    continue
                cls, glifo, texto = _SENAL_HTML[s]
                tip = f"{ind.nombre}: {_formatear_valor(row, ind)} · {texto}"
                celdas.append(
                    f'<i class="ico {cls}" tabindex="0" data-tip="{esc(tip)}" '
                    f'aria-label="{esc(tip)}">{glifo}</i>'
                )
            grupos.append(
                f'<div class="strip-group"><div class="strip-cells">{"".join(celdas)}</div>'
                f'<div class="strip-label">{esc(hz)}</div></div>'
            )
        cards.append(
            f'<article class="card">'
            f'<div class="card-head"><h3>{esc(str(row["Ticker"]))}</h3>'
            f'<span class="badge"><i class="ico {clave}">{glifo_badge}</i>{esc(etiqueta)}</span></div>'
            f'<div class="score"><b>{n_verde}</b><span>/ {n_ind} en verde</span></div>'
            f'<div class="strip">{"".join(grupos)}</div>'
            f'<div class="counts">{conteo[VERDE]} verde · {conteo[NEUTRAL]} neutral · '
            f'{conteo[ALERTA]} alerta · {conteo[NA]} sin datos</div>'
            f'</article>'
        )

    # --- Matriz: filas = indicadores, columnas = tickers ---
    thead = "".join(f'<th class="tk">{esc(str(row["Ticker"]))}</th>' for row, _, _ in tickers)
    tbody = []
    for hz in horizontes:
        tbody.append(f'<tr class="group"><th colspan="{len(tickers) + 1}">{esc(hz)}</th></tr>')
        for i, ind in enumerate(INDICADORES):
            if ind.horizonte != hz:
                continue
            celdas = []
            for t, (row, senales, _) in enumerate(tickers):
                cls, glifo, texto = _SENAL_HTML[senales[i]]
                celdas.append(
                    f'<td class="cell {cls}" data-t="{t}" data-i="{i}" tabindex="0">'
                    f'<span class="val">{esc(_formatear_valor(row, ind))}</span>'
                    f'<span class="sub"><span class="pill"><i class="ico">{glifo}</i>{texto}</span>'
                    f'<span class="spk"></span></span></td>'
                )
            tbody.append(
                f'<tr><th class="ind">{esc(ind.nombre)}<span class="rule">{esc(ind.regla)}</span></th>'
                f'{"".join(celdas)}</tr>'
            )
    tbody.append(
        '<tr class="total"><th class="ind">Score</th>'
        + "".join(f"<td>{n}/{n_ind}</td>" for _, _, n in tickers)
        + "</tr>"
    )

    # --- Datos para los gráficos (JSON embebido) ---
    def _limites(zona: Tuple[float, float]) -> List[Optional[float]]:
        return [None if np.isinf(x) else x for x in zona]

    def _json(obj: Any) -> str:
        return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")

    historico = df.attrs.get("historico", {})
    ind_json = [
        {"n": ind.nombre, "u": ind.unidad,
         "v": _limites(ind.verde) if ind.verde else None,
         "a": [_limites(z) for z in ind.alerta]}
        for ind in INDICADORES
    ]
    hist_json = [
        [historico.get(str(row["Ticker"]), {}).get(ind.senal) for ind in INDICADORES]
        for row, _, _ in tickers
    ]

    contenido = _HTML_TEMPLATE.substitute(
        n_tickers=len(tickers),
        n_ind=n_ind,
        score_verde=SCORE_LUZ_VERDE_MIN,
        score_media=SCORE_CALIDAD_MEDIA_MIN,
        fecha=datetime.now().strftime("%Y-%m-%d %H:%M"),
        cards="".join(cards),
        thead=thead,
        tbody="".join(tbody),
        ind_json=_json(ind_json),
        hist_json=_json(hist_json),
        tk_json=_json([str(row["Ticker"]) for row, _, _ in tickers]),
    )

    ruta = Path(path)
    if not ruta.is_absolute():
        ruta = Path(__file__).resolve().parent / ruta
    ruta.write_text(contenido, encoding="utf-8")
    print(f"Reporte HTML: {ruta}")
    if abrir:
        webbrowser.open(ruta.as_uri())
    return str(ruta)


# ==============================================================================
# BLOQUE 8: EJECUCIÓN
# ==============================================================================
if __name__ == "__main__":
    df_resultado = analizar_cartera(PORTFOLIO_TICKERS)

    pd.set_option("display.width", 200)
    print("\n=== TABLERO DE INDICADORES FUNDAMENTALES ===\n")
    print(df_resultado[["Ticker", "Score_Calidad"]].to_string(index=False))

    exportar_html(df_resultado, OUTPUT_HTML, abrir=OPEN_BROWSER)
