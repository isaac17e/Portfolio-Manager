"""Daily-price indicators for tickers without their own options (tier ``proxy``).

Trend (price vs 50/200-day SMA), RSI(14), 20-day realized vol against its own
rolling mean, and drawdown from the 252-day high. ``price_scores`` turns them
into 0-100 entry scores (higher = better entry), the same scale the options
indicators use in entry_signal_tool.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from tickers import to_yahoo

SMA_CORTA = 50
SMA_LARGA = 200
RSI_PERIODO = 14
VOL_VENTANA = 20
VOL_MEDIA_VENTANA = 120
MAXIMO_VENTANA = 252


def _num(value):
    if value is None:
        return np.nan
    try:
        number = float(value)
    except (TypeError, ValueError):
        return np.nan
    return number if math.isfinite(number) else np.nan


def rsi(closes: pd.Series, period: int = RSI_PERIODO) -> float:
    """RSI de Wilder (medias exponenciales con alpha = 1/period) del ultimo dia."""
    delta = closes.diff().dropna()
    if len(delta) < period:
        return np.nan
    gains = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    losses = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    gain, loss = gains.iloc[-1], losses.iloc[-1]
    if loss == 0:
        return 100.0 if gain > 0 else 50.0
    return float(100 - 100 / (1 + gain / loss))


def price_indicators(closes) -> dict:
    """Indicadores crudos sobre una serie de cierres diarios (orden ascendente)."""
    serie = pd.Series(closes, dtype=float).dropna()
    out = {
        "precio": np.nan, "sma50": np.nan, "sma200": np.nan, "rsi14": np.nan,
        "vol_realizada": np.nan, "vol_realizada_media": np.nan, "vol_ratio": np.nan,
        "drawdown": np.nan, "n_dias": int(len(serie)),
    }
    if serie.empty:
        return out
    precio = float(serie.iloc[-1])
    out["precio"] = precio
    if len(serie) >= SMA_CORTA:
        out["sma50"] = float(serie.tail(SMA_CORTA).mean())
    if len(serie) >= SMA_LARGA:
        out["sma200"] = float(serie.tail(SMA_LARGA).mean())
    out["rsi14"] = rsi(serie)

    rets = np.log(serie / serie.shift(1)).dropna()
    if len(rets) >= VOL_VENTANA:
        rv = rets.rolling(VOL_VENTANA).std().dropna() * np.sqrt(252)
        out["vol_realizada"] = float(rv.iloc[-1])
        media = rv.tail(VOL_MEDIA_VENTANA).mean()
        out["vol_realizada_media"] = float(media)
        if media > 0:
            out["vol_ratio"] = float(rv.iloc[-1] / media)

    maximo = serie.tail(MAXIMO_VENTANA).max()
    if maximo > 0:
        out["drawdown"] = float(precio / maximo - 1)
    return out


def price_scores(ind: dict) -> dict:
    """Puntajes 0-100 por indicador. Un indicador sin dato vale 50 (neutral)."""
    precio = _num(ind.get("precio"))
    sma50 = _num(ind.get("sma50"))
    sma200 = _num(ind.get("sma200"))
    rsi14 = _num(ind.get("rsi14"))
    vol_ratio = _num(ind.get("vol_ratio"))
    dd = _num(ind.get("drawdown"))

    # Tendencia: mitad por estar sobre la SMA50 y mitad sobre la SMA200.
    partes = [float(precio > sma) for sma in (sma50, sma200) if not np.isnan(sma) and not np.isnan(precio)]
    tendencia = 100.0 * sum(partes) / len(partes) if partes else 50.0

    # RSI: sobreventa (<= 30) favorece la entrada, sobrecompra (>= 70) la frena.
    rsi_score = 50.0 if np.isnan(rsi14) else float(np.clip((70 - rsi14) / 40, 0, 1) * 100)

    # Vol realizada contra su propia media: 0.5x -> 100, 1x -> 50, 1.5x -> 0.
    vol_score = 50.0 if np.isnan(vol_ratio) else float(np.clip(1.5 - vol_ratio, 0, 1) * 100)

    # Drawdown: un retroceso de hasta 10% mejora el precio de entrada (50 -> 100);
    # mas alla castiga hasta 0 en -30%.
    if np.isnan(dd):
        dd_score = 50.0
    elif dd >= -0.10:
        dd_score = 50.0 + min(-dd, 0.10) / 0.10 * 50.0
    else:
        dd_score = float(np.clip(100.0 * (0.30 + dd) / 0.20, 0, 100))

    return {
        "tendencia": tendencia,
        "rsi": rsi_score,
        "vol_realizada": vol_score,
        "drawdown": dd_score,
    }


def yahoo_closes(ticker, period: str = "2y") -> pd.Series:
    """Cierres diarios ajustados de Yahoo para la cotizacion local (``RY.TO``)."""
    import yfinance as yf

    hist = yf.Ticker(to_yahoo(ticker)).history(period=period, auto_adjust=True)
    if hist is None or hist.empty or "Close" not in hist.columns:
        raise RuntimeError(f"no price history returned for {ticker}")
    closes = hist["Close"].dropna()
    if closes.empty:
        raise RuntimeError(f"no price history returned for {ticker}")
    closes.index = pd.to_datetime(closes.index).tz_localize(None)
    return closes
