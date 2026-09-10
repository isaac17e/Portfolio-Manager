# Fundamental analysis module for stock tickers using yfinance.

from __future__ import annotations

import html
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

# --------------------------------------------------------------------------- #
# Constantes de estilo para señales
# --------------------------------------------------------------------------- #
VERDE = "🟢 Luz Verde"
ALERTA = "🔴 Alerta"
NEUTRAL = "🟡 Neutral"
NA = "⚪ N/D"


# --------------------------------------------------------------------------- #
# Utilidades de extracción segura de datos
# --------------------------------------------------------------------------- #
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


# --------------------------------------------------------------------------- #
# Nombres de línea contable candidatos (yfinance varía entre versiones)
# --------------------------------------------------------------------------- #
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
}


# --------------------------------------------------------------------------- #
# Catálogo de indicadores (orden de columnas y presentación en el reporte)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Indicador:
    horizonte: str
    nombre: str
    columnas: Tuple[str, ...]  # métricas que se muestran en la celda
    formato: str               # str.format aplicado a las columnas
    senal: str                 # columna de señal
    regla: str                 # umbrales; deben reflejar los de calcular_*


INDICADORES: List[Indicador] = [
    Indicador("Corto plazo", "Current Ratio", ("Current_Ratio",), "{:.2f}x",
              "Current_Ratio_Señal", "Verde 1.5–2.5 · Alerta <1.0 o >3.0"),
    Indicador("Corto plazo", "EV / EBITDA", ("EV_EBITDA",), "{:.1f}x",
              "EV_EBITDA_Señal", "Verde 0–12 · Alerta ≤0 o >20"),
    Indicador("Corto plazo", "P/E Trailing → Forward", ("PE_Trailing", "PE_Forward"), "{:.1f} → {:.1f}",
              "PE_Señal", "Verde si baja · Alerta si sube o Forward ≤0"),
    Indicador("Corto plazo", "Earnings Surprise", ("Earnings_Surprise_%",), "{:+.1f}%",
              "Earnings_Surprise_Señal", "Verde >2% · Alerta <0%"),
    Indicador("Mediano plazo", "Deuda Neta / EBITDA", ("Deuda_Neta_EBITDA",), "{:.2f}x",
              "Deuda_Neta_EBITDA_Señal", "Verde <2.5 · Alerta >3.5 o EBITDA ≤0"),
    Indicador("Mediano plazo", "Interest Coverage", ("Interest_Coverage",), "{:.1f}x",
              "Interest_Coverage_Señal", "Verde >4 · Alerta <2"),
    Indicador("Mediano plazo", "FCF Yield", ("FCF_Yield_%",), "{:.2f}%",
              "FCF_Yield_Señal", "Verde >4.5% · Alerta <2%"),
    Indicador("Mediano plazo", "PEG Ratio", ("PEG_Ratio",), "{:.2f}",
              "PEG_Señal", "Verde 0–1.2 · Alerta ≤0 o >2"),
    Indicador("Largo plazo", "ROCE", ("ROCE_%",), "{:.1f}%",
              "ROCE_Señal", "Verde >15% · Alerta <8%"),
    Indicador("Largo plazo", "ROIC", ("ROIC_%",), "{:.1f}%",
              "ROIC_Señal", "Verde >12% · Alerta <6%"),
    Indicador("Largo plazo", "ROE (DuPont)", ("ROE_%", "Apalancamiento_x"), "{:.1f}% · apal. {:.1f}x",
              "ROE_Señal", "Verde >15% con apal. <2.5x · Alerta <8%, o >15% con apal. >4x"),
    Indicador("Largo plazo", "Reinvestment Rate", ("Reinvestment_Rate_%",), "{:.1f}%",
              "Reinvestment_Señal", "Verde 20–60% · Alerta <5% o >90%"),
]


def etiqueta_score(n_verde: int) -> Tuple[str, str]:
    """Devuelve (etiqueta global, clave de estado) según las señales en verde."""
    if n_verde >= 9:
        return "Luz Verde Global", "good"
    if n_verde >= 6:
        return "Calidad Media", "warn"
    return "Señal de Alerta Global", "crit"


# --------------------------------------------------------------------------- #
# Contenedor de resultados por ticker
# --------------------------------------------------------------------------- #
@dataclass
class ResultadoTicker:
    ticker: str
    metricas: Dict[str, float] = field(default_factory=dict)
    senales: Dict[str, str] = field(default_factory=dict)
    errores: List[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Cálculo de métricas por bloque de temporalidad
# --------------------------------------------------------------------------- #
def calcular_corto_plazo(tk: "yf.Ticker", info: Dict[str, Any], res: ResultadoTicker) -> None:
    q_bs = safe_get_df(tk, "quarterly_balance_sheet")

    # 1. Current Ratio
    def _current_ratio():
        ca = get_row(q_bs, ROWS["current_assets"])
        cl = get_row(q_bs, ROWS["current_liab"])
        return safe_div(ca, cl)

    cr = safe_calc(_current_ratio)
    res.metricas["Current_Ratio"] = cr
    res.senales["Current_Ratio_Señal"] = clasificar(
        cr, lambda v: 1.5 <= v <= 2.5, lambda v: v < 1.0 or v > 3.0
    )

    # 2. EV / EBITDA (yfinance ya lo expone como TTM en .info)
    ev_ebitda = safe_calc(lambda: get_info_field(info, "enterpriseToEbitda"))
    res.metricas["EV_EBITDA"] = ev_ebitda
    # EV/EBITDA <= 0 implica EBITDA negativo: no es "barato", es alerta
    res.senales["EV_EBITDA_Señal"] = clasificar(
        ev_ebitda, lambda v: 0 < v < 12.0, lambda v: v <= 0 or v > 20.0
    )

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
    res.senales["Earnings_Surprise_Señal"] = clasificar(
        surprise, lambda v: v > 2.0, lambda v: v < 0.0
    )


def calcular_mediano_plazo(tk: "yf.Ticker", info: Dict[str, Any], res: ResultadoTicker) -> None:
    bs = safe_get_df(tk, "balance_sheet")
    fin = safe_get_df(tk, "financials")
    cf = safe_get_df(tk, "cashflow")

    ebitda = safe_calc(lambda: get_info_field(info, "ebitda"))
    if pd.isna(ebitda):
        ebitda = safe_calc(lambda: get_row(fin, ROWS["ebitda"]))
    total_debt = safe_calc(lambda: get_row(bs, ROWS["total_debt"]))
    if pd.isna(total_debt):
        total_debt = safe_calc(
            lambda: get_row(bs, ROWS["long_term_debt"]) + get_row(bs, ROWS["short_term_debt"])
        )
    cash = safe_calc(lambda: get_row(bs, ROWS["cash"]))

    # 5. Deuda Neta / EBITDA
    def _deuda_neta_ebitda():
        deuda_neta = total_debt - cash
        return safe_div(deuda_neta, ebitda)

    dn_ebitda = safe_calc(_deuda_neta_ebitda)
    res.metricas["Deuda_Neta_EBITDA"] = dn_ebitda
    if not pd.isna(ebitda) and ebitda <= 0:
        # Con EBITDA negativo el ratio sale negativo y parecería "sano"
        res.senales["Deuda_Neta_EBITDA_Señal"] = ALERTA
    else:
        res.senales["Deuda_Neta_EBITDA_Señal"] = clasificar(
            dn_ebitda, lambda v: v < 2.5, lambda v: v > 3.5
        )

    # 6. Interest Coverage Ratio (EBIT / Intereses)
    ebit = safe_calc(lambda: get_row(fin, ROWS["ebit"]))

    def _interest_coverage():
        interes = abs(get_row(fin, ROWS["interest_expense"]))
        return safe_div(ebit, interes)

    icr = safe_calc(_interest_coverage)
    res.metricas["Interest_Coverage"] = icr
    res.senales["Interest_Coverage_Señal"] = clasificar(
        icr, lambda v: v > 4.0, lambda v: v < 2.0
    )

    # 7. Free Cash Flow Yield
    market_cap = safe_calc(lambda: get_info_field(info, "marketCap"))

    def _fcf_yield():
        ocf = get_row(cf, ROWS["operating_cf"])
        capex = get_row(cf, ROWS["capex"])  # normalmente negativo en yfinance
        fcf = ocf + capex if capex < 0 else ocf - capex
        return safe_div(fcf, market_cap) * 100

    fcf_yield = safe_calc(_fcf_yield)
    res.metricas["FCF_Yield_%"] = fcf_yield
    res.senales["FCF_Yield_Señal"] = clasificar(
        fcf_yield, lambda v: v > 4.5, lambda v: v < 2.0
    )

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
    res.senales["PEG_Señal"] = clasificar(
        peg, lambda v: 0 < v < 1.2, lambda v: v <= 0 or v > 2.0
    )


def calcular_largo_plazo(tk: "yf.Ticker", info: Dict[str, Any], res: ResultadoTicker) -> None:
    bs = safe_get_df(tk, "balance_sheet")
    fin = safe_get_df(tk, "financials")
    cf = safe_get_df(tk, "cashflow")

    ebit = safe_calc(lambda: get_row(fin, ROWS["ebit"]))
    total_assets = safe_calc(lambda: get_row(bs, ROWS["total_assets"]))
    current_liab = safe_calc(lambda: get_row(bs, ROWS["current_liab"]))
    total_equity = safe_calc(lambda: get_row(bs, ROWS["total_equity"]))
    net_income = safe_calc(lambda: get_row(fin, ROWS["net_income"]))
    revenue = safe_calc(lambda: get_row(fin, ROWS["revenue"]))

    # Tasa impositiva efectiva para NOPAT
    def _tax_rate():
        tax = get_row(fin, ROWS["tax_provision"])
        pretax = get_row(fin, ROWS["pretax_income"])
        rate = safe_div(tax, pretax)
        if pd.isna(rate) or rate < 0 or rate > 0.6:
            return 0.21  # tasa corporativa EE.UU. como fallback razonable
        return rate

    tax_rate = safe_calc(_tax_rate)
    if pd.isna(tax_rate):
        tax_rate = 0.21

    nopat = safe_calc(lambda: ebit * (1 - tax_rate))

    # 9. ROCE
    def _roce():
        capital_empleado = total_assets - current_liab
        return safe_div(ebit, capital_empleado) * 100

    roce = safe_calc(_roce)
    res.metricas["ROCE_%"] = roce
    res.senales["ROCE_Señal"] = clasificar(
        roce, lambda v: v > 15.0, lambda v: v < 8.0
    )

    # 10. ROIC
    def _roic():
        total_debt = get_row(bs, ROWS["total_debt"])
        cash = get_row(bs, ROWS["cash"])
        if pd.isna(total_debt):
            total_debt = get_row(bs, ROWS["long_term_debt"]) + get_row(bs, ROWS["short_term_debt"])
        capital_invertido = total_debt + total_equity - cash
        return safe_div(nopat, capital_invertido) * 100

    roic = safe_calc(_roic)
    res.metricas["ROIC_%"] = roic
    res.senales["ROIC_Señal"] = clasificar(
        roic, lambda v: v > 12.0, lambda v: v < 6.0
    )

    # 11. ROE — Descomposición DuPont 3-Way
    margen_neto = safe_calc(lambda: safe_div(net_income, revenue))
    rotacion_activos = safe_calc(lambda: safe_div(revenue, total_assets))
    apalancamiento = safe_calc(lambda: safe_div(total_assets, total_equity))

    def _roe_dupont():
        return margen_neto * rotacion_activos * apalancamiento * 100

    roe = safe_calc(_roe_dupont)
    res.metricas["ROE_%"] = roe
    res.metricas["Apalancamiento_x"] = apalancamiento

    def _roe_signal():
        if pd.isna(roe) or pd.isna(apalancamiento):
            return NA
        if roe > 15.0 and apalancamiento < 2.5:
            return VERDE
        if apalancamiento > 4.0 and roe > 15.0:
            return ALERTA  # ROE alto "inflado" por apalancamiento excesivo
        if roe < 8.0:
            return ALERTA
        return NEUTRAL

    res.senales["ROE_Señal"] = _roe_signal()

    # 12. Reinvestment Rate
    def _reinvestment():
        capex = get_row(cf, ROWS["capex"])
        capex = abs(capex) if not pd.isna(capex) else np.nan
        depreciacion = get_row(cf, ROWS["depreciation"])
        return safe_div(capex - depreciacion, nopat) * 100

    reinvestment = safe_calc(_reinvestment)
    res.metricas["Reinvestment_Rate_%"] = reinvestment
    res.senales["Reinvestment_Señal"] = clasificar(
        reinvestment,
        lambda v: 20.0 <= v <= 60.0,
        lambda v: v < 5.0 or v > 90.0,
    )


# --------------------------------------------------------------------------- #
# Helpers de acceso a datos de yfinance con resiliencia
# --------------------------------------------------------------------------- #
def safe_get_df(tk: "yf.Ticker", attr_name: str) -> Optional[pd.DataFrame]:
    """Obtiene un DataFrame contable de un Ticker de forma resiliente."""
    try:
        df = getattr(tk, attr_name)
        if df is None or df.empty:
            return None
        return df
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# Función principal
# --------------------------------------------------------------------------- #
def analizar_cartera(tickers_list: Sequence[str]) -> pd.DataFrame:
    """
    Analiza una lista de tickers y devuelve un DataFrame consolidado con los
    12 indicadores fundamentales, sus señales y un Score_Calidad global.

    Parameters
    ----------
    tickers_list : lista de símbolos bursátiles, ej. ["AAPL", "MSFT"]

    Returns
    -------
    pd.DataFrame con una fila por ticker.
    """
    filas: List[Dict[str, Any]] = []

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

        except Exception as exc:  # nunca debe tumbar el batch completo
            res.errores.append(str(exc))

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

    return df


# --------------------------------------------------------------------------- #
# Exportación
# --------------------------------------------------------------------------- #
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
    --tint: 13%;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      color-scheme: dark;
      --page: #0d0d0d; --surface: #1a1a19; --ink: #ffffff; --ink-2: #c3c2b7;
      --grid: #2c2c2a; --border: rgba(255,255,255,0.10); --na: #5a5955;
      --tint: 20%;
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
  td.cell { text-align: center; min-width: 140px;
            background: color-mix(in srgb, var(--s) var(--tint), var(--surface)); }
  .val { display: block; font-variant-numeric: tabular-nums; font-weight: 600;
         white-space: nowrap; }
  .pill { display: inline-flex; align-items: center; gap: 5px; margin-top: 3px;
          font-size: 12px; color: var(--ink-2); }
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
  <p class="note">Score = señales en verde sobre $n_ind. Una señal sin datos cuenta como no cumplida.
  Tickers ordenados por score. Luz Verde Global ≥ 9 · Calidad Media ≥ 6 · Alerta Global &lt; 6.</p>
</div>
<div class="tip" id="tip" role="tooltip" hidden></div>
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
    df: pd.DataFrame, path: str = "reporte_fundamental.html", abrir: bool = True
) -> str:
    """Genera un reporte HTML autocontenido (tarjetas + matriz de señales)."""
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
            for row, senales, _ in tickers:
                cls, glifo, texto = _SENAL_HTML[senales[i]]
                celdas.append(
                    f'<td class="cell {cls}"><span class="val">{esc(_formatear_valor(row, ind))}</span>'
                    f'<span class="pill"><i class="ico">{glifo}</i>{texto}</span></td>'
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

    contenido = _HTML_TEMPLATE.substitute(
        n_tickers=len(tickers),
        n_ind=n_ind,
        fecha=datetime.now().strftime("%Y-%m-%d %H:%M"),
        cards="".join(cards),
        thead=thead,
        tbody="".join(tbody),
    )

    ruta = Path(path).resolve()
    ruta.write_text(contenido, encoding="utf-8")
    print(f"Reporte HTML: {ruta}")
    if abrir:
        webbrowser.open(ruta.as_uri())
    return str(ruta)


# --------------------------------------------------------------------------- #
# Caso de prueba ejecutable
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    TICKERS_PRUEBA = ["AAPL", "MSFT", "GOOGL", "NVDA"]

    df_resultado = analizar_cartera(TICKERS_PRUEBA)

    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 200)
    print("\n=== TABLERO DE INDICADORES FUNDAMENTALES ===\n")
    print(df_resultado[["Ticker", "Score_Calidad"]])

    exportar_html(df_resultado)
