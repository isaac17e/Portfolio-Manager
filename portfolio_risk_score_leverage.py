# =============================================================================
# BLOQUE 1: CONFIGURACION
# =============================================================================
import numpy as np
import pandas as pd
from datetime import date

portfolio = {
    "XLU": 0.12,
    "GLD": 0.12,
    "T": 0.1031,
    "GILD": 0.0925,
    "FXI": 0.0779,
    "MRK": 0.0734,
    "ADP": 0.0595,
    "KO": 0.0578,
    "ABT": 0.0562,
    "VRTX": 0.0541,
    "AMGN": 0.0509,
    "UNP": 0.0485,
    "NEE": 0.0484,
    "ABBV": 0.0235,
    "TMO": 0.0142
}

total_weight = sum(portfolio.values())
if abs(total_weight - 1) > 1e-6:
    print(f"[WARN]  Los pesos de 'portfolio' no suman 1 (suma actual: {total_weight:.4f}). Se usarán tal cual, sin normalizar.")

investment_horizon_months = 1
trading_days_per_month = 21
trading_days_per_year = 252
horizon_days = round(investment_horizon_months * trading_days_per_month)

start_date = date(2021, 1, 1)
end_date = date.today()

# --- API KEY DE POLYGON ---
import os
from dotenv import load_dotenv
load_dotenv()
polygon_api_key = os.environ.get("POLYGON_API_KEY")

risk_free_rate_annual = 0.046
confidence_levels = [0.95, 0.99]
mar_annual = 0

leverage_min = 2.0
leverage_max = 5.0

risk_score_weights = {"hv": 0.30, "cvar": 0.30, "iv": 0.25, "gex_pcr": 0.15}

polygon_base_url = "https://api.polygon.io"
polygon_max_retries = 5
polygon_retry_wait_secs = 15
polygon_max_pages_snapshot = 20

print(
    f"[CONFIG] Portafolio: {', '.join(portfolio.keys())} | "
    f"Horizonte: {investment_horizon_months} mes(es) (~{horizon_days} dias habiles) | "
    f"Ventana: {start_date} a {end_date}"
)

# =============================================================================
# BLOQUE 2: UTILIDADES Y CONEXION A LA API
# =============================================================================
from polygon_client import PolygonClient, PolygonError, PolygonNotFound

def log_info(msg):
    print(f"[INFO]  {msg}")

def log_warn(msg):
    print(f"[WARN]  {msg}")

def log_error(msg):
    print(f"[ERROR] {msg}")

_clientes_polygon = {}

def polygon_client(api_key=None):
    # Transporte compartido (polygon_client.py): ritmo por ventana de 60s
    # (POLYGON_CALLS_PER_MINUTE en el .env), timeout, reintentos ante
    # 429/5xx/red y paginacion que falla en vez de truncar.
    api_key = api_key or polygon_api_key
    if api_key not in _clientes_polygon:
        _clientes_polygon[api_key] = PolygonClient(
            api_key=api_key, max_retries=polygon_max_retries,
            retry_wait=polygon_retry_wait_secs, base_url=polygon_base_url)
    return _clientes_polygon[api_key]

def polygon_get(path, params=None, api_key=None):
    # Lanza PolygonError si la API no responde algo utilizable; nunca devuelve None.
    return polygon_client(api_key).get(path, params)

def pct(x, digits=2):
    return f"{x * 100:.{digits}f}%"

# =============================================================================
# BLOQUE 3: DATOS DE MERCADO Y RETORNOS
# =============================================================================
import yfinance as yf

def get_price_data(tickers, start, end):
    log_info(f"Descargando precios historicos para: {', '.join(tickers)}")

    data = yf.download(tickers, start=start, end=end, auto_adjust=False, progress=False)
    if data.empty:
        raise ValueError("No se pudo descargar ningun precio. Revisa los tickers/conexion.")

    if isinstance(data.columns, pd.MultiIndex):
        prices = data["Adj Close"][tickers]
    else:
        prices = data[["Adj Close"]]
        prices.columns = tickers

    prices = prices.ffill().dropna()
    return prices

def get_log_returns(prices):
    rets = np.log(prices / prices.shift(1)).dropna()
    return rets

def get_portfolio_returns(asset_returns, weights):
    w = pd.Series(weights)[asset_returns.columns]
    port_ret = asset_returns.dot(w)
    port_ret.name = "Portfolio"
    return port_ret

# =============================================================================
# BLOQUE 4: RIESGO EX-POST (HISTORICO)
# =============================================================================
from scipy import stats

def compute_volatility(returns_df, horizon_days, trading_days_per_year=252):
    daily_sd = returns_df.std()
    return pd.DataFrame({
        "Activo": daily_sd.index,
        "Vol_Diaria": daily_sd.values,
        "Vol_Anualizada": (daily_sd * np.sqrt(trading_days_per_year)).values,
        "Vol_Horizonte": (daily_sd * np.sqrt(horizon_days)).values
    })

def historical_var(r, p):
    return -np.percentile(r, (1 - p) * 100)

def historical_es(r, p):
    var = historical_var(r, p)
    tail = r[r <= -var]
    if len(tail) == 0:
        return var
    return -tail.mean()

def cornish_fisher_var(r, p):
    # Aproximacion Cornish-Fisher (equivalente al metodo "modified" de PerformanceAnalytics)
    mu = r.mean()
    sigma = r.std()
    S = stats.skew(r)
    K = stats.kurtosis(r, fisher=True)  # curtosis en exceso
    z = stats.norm.ppf(1 - p)
    z_cf = (z
            + (z**2 - 1) * S / 6
            + (z**3 - 3 * z) * K / 24
            - (2 * z**3 - 5 * z) * (S**2) / 36)
    return -(mu + z_cf * sigma)

def cornish_fisher_es(r, p):
    var_cf = cornish_fisher_var(r, p)
    tail = r[r <= -var_cf]
    if len(tail) == 0:
        return var_cf
    return -tail.mean()

def compute_var_es(returns_df, confidence_levels, horizon_days, trading_days_per_year=252):
    rows = []
    for asset in returns_df.columns:
        r = returns_df[asset].dropna().values
        row = {"Activo": asset}
        for cl in confidence_levels:
            p_tag = int(cl * 100)

            var_hist = historical_var(r, cl)
            var_cf = cornish_fisher_var(r, cl)
            es_hist = historical_es(r, cl)
            es_cf = cornish_fisher_es(r, cl)

            horizon_scale = np.sqrt(horizon_days)
            annual_scale = np.sqrt(trading_days_per_year)

            row[f"VaR_Hist_{p_tag}_Diario"] = var_hist
            row[f"VaR_CF_{p_tag}_Diario"] = var_cf
            row[f"CVaR_Hist_{p_tag}_Diario"] = es_hist
            row[f"CVaR_CF_{p_tag}_Diario"] = es_cf
            row[f"VaR_Hist_{p_tag}_Anualizado"] = var_hist * annual_scale
            row[f"VaR_CF_{p_tag}_Anualizado"] = var_cf * annual_scale
            row[f"CVaR_Hist_{p_tag}_Anualizado"] = es_hist * annual_scale
            row[f"CVaR_CF_{p_tag}_Anualizado"] = es_cf * annual_scale
            row[f"VaR_Hist_{p_tag}_Horizonte"] = var_hist * horizon_scale
            row[f"VaR_CF_{p_tag}_Horizonte"] = var_cf * horizon_scale
            row[f"CVaR_Hist_{p_tag}_Horizonte"] = es_hist * horizon_scale
            row[f"CVaR_CF_{p_tag}_Horizonte"] = es_cf * horizon_scale
        rows.append(row)
    return pd.DataFrame(rows)

def compute_max_drawdown(returns_df):
    rows = []
    for asset in returns_df.columns:
        r = returns_df[asset]
        # Los retornos son logaritmicos: el valor acumulado es exp(suma), no prod(1 + r)
        cum = np.exp(r.cumsum())
        running_max = cum.cummax()
        drawdown = (cum - running_max) / running_max
        mdd = -drawdown.min()
        rows.append({"Activo": asset, "Max_Drawdown": mdd})
    return pd.DataFrame(rows)

def compute_sharpe_sortino(returns_df, rf_annual, mar_annual, trading_days_per_year, horizon_days):
    rf_daily = rf_annual / trading_days_per_year
    mar_daily = mar_annual / trading_days_per_year

    rows = []
    for asset in returns_df.columns:
        r = returns_df[asset]
        excess = r - rf_daily
        sharpe_ann = (excess.mean() / r.std()) * np.sqrt(trading_days_per_year)

        downside = (r[r < mar_daily] - mar_daily)
        downside_dev = np.sqrt((downside ** 2).mean()) if len(downside) > 0 else np.nan
        if downside_dev and downside_dev > 0:
            sortino_ann = ((r.mean() - mar_daily) / downside_dev) * np.sqrt(trading_days_per_year)
        else:
            sortino_ann = np.nan

        scale_factor = np.sqrt(horizon_days / trading_days_per_year)

        rows.append({
            "Activo": asset,
            "Sharpe_Anualizado": sharpe_ann,
            "Sortino_Anualizado": sortino_ann,
            "Sharpe_Horizonte": sharpe_ann * scale_factor,
            "Sortino_Horizonte": sortino_ann * scale_factor
        })
    return pd.DataFrame(rows)

def compute_corr_cov(returns_df, trading_days_per_year=252):
    cov_daily = returns_df.cov()
    cov_annual = cov_daily * trading_days_per_year
    corr_mat = returns_df.corr()
    return {"correlation": corr_mat, "covariance_daily": cov_daily, "covariance_annual": cov_annual}

def compute_risk_contribution(cov_daily, weights):
    assets = cov_daily.index
    w = pd.Series(weights)[assets].values
    cov_matrix = cov_daily.values
    sigma_p = np.sqrt(w @ cov_matrix @ w)
    mcr = (cov_matrix @ w) / sigma_p
    cr = w * mcr
    pcr = cr / sigma_p
    return pd.DataFrame({
        "Activo": assets,
        "Peso": w,
        "MCR_Diario": mcr,
        "CR_Diario": cr,
        "PCR": pcr
    })

def run_expost_risk_module(asset_returns, portfolio_returns, weights, horizon_days,
                            confidence_levels, rf_annual, mar_annual, trading_days_per_year):
    log_info("MODULO 1: calculando metricas Ex-Post (historicas)...")

    all_returns = asset_returns.copy()
    all_returns["Portfolio"] = portfolio_returns

    vol_tbl = compute_volatility(all_returns, horizon_days, trading_days_per_year)
    var_es_tbl = compute_var_es(all_returns, confidence_levels, horizon_days, trading_days_per_year)
    mdd_tbl = compute_max_drawdown(all_returns)
    sharpe_tbl = compute_sharpe_sortino(all_returns, rf_annual, mar_annual, trading_days_per_year, horizon_days)
    corr_cov = compute_corr_cov(asset_returns, trading_days_per_year)
    risk_contrib = compute_risk_contribution(corr_cov["covariance_daily"], weights)

    annualized_summary = vol_tbl[["Activo", "Vol_Anualizada"]].merge(mdd_tbl, on="Activo", how="left")
    annualized_summary = annualized_summary.merge(
        sharpe_tbl[["Activo", "Sharpe_Anualizado", "Sortino_Anualizado"]], on="Activo", how="left"
    )
    anualizado_cols = [c for c in var_es_tbl.columns if c.endswith("_Anualizado")]
    annualized_summary = annualized_summary.merge(
        var_es_tbl[["Activo"] + anualizado_cols], on="Activo", how="left"
    )

    horizon_summary = vol_tbl[["Activo", "Vol_Horizonte"]].merge(
        sharpe_tbl[["Activo", "Sharpe_Horizonte", "Sortino_Horizonte"]], on="Activo", how="left"
    )
    horizonte_cols = [c for c in var_es_tbl.columns if c.endswith("_Horizonte")]
    horizon_summary = horizon_summary.merge(
        var_es_tbl[["Activo"] + horizonte_cols], on="Activo", how="left"
    )

    return {
        "volatility": vol_tbl,
        "var_es": var_es_tbl,
        "max_drawdown": mdd_tbl,
        "sharpe_sortino": sharpe_tbl,
        "correlation": corr_cov["correlation"],
        "covariance_daily": corr_cov["covariance_daily"],
        "covariance_annual": corr_cov["covariance_annual"],
        "risk_contribution": risk_contrib,
        "annualized_summary": annualized_summary,
        "horizon_summary": horizon_summary
    }

# =============================================================================
# BLOQUE 5: RIESGO EX-ANTE (OPCIONES, POLYGON)
# =============================================================================
import datetime as dt
from scipy.stats import norm

# Black-Scholes vectorizado: S, K, sigma e is_call son arreglos (uno por contrato);
# Tt y r son escalares. Devuelve NaN donde las entradas no son validas.
def bs_price(S, K, Tt, r, sigma, is_call):
    S, K, sigma = (np.asarray(x, dtype=float) for x in (S, K, sigma))
    with np.errstate(all="ignore"):
        valido = (np.isfinite(S) & np.isfinite(K) & np.isfinite(sigma)
                  & (S > 0) & (K > 0) & (sigma > 0) & (Tt > 0) & np.isfinite(r))
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * Tt) / (sigma * np.sqrt(Tt))
        d2 = d1 - sigma * np.sqrt(Tt)
        call = S * norm.cdf(d1) - K * np.exp(-r * Tt) * norm.cdf(d2)
        put = K * np.exp(-r * Tt) * norm.cdf(-d2) - S * norm.cdf(-d1)
    return np.where(valido, np.where(is_call, call, put), np.nan)

def bs_gamma(S, K, Tt, r, sigma):
    S, K, sigma = (np.asarray(x, dtype=float) for x in (S, K, sigma))
    with np.errstate(all="ignore"):
        valido = (np.isfinite(S) & np.isfinite(K) & np.isfinite(sigma)
                  & (S > 0) & (K > 0) & (sigma > 0) & (Tt > 0) & np.isfinite(r))
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * Tt) / (sigma * np.sqrt(Tt))
        gamma = norm.pdf(d1) / (S * sigma * np.sqrt(Tt))
    return np.where(valido, gamma, np.nan)

def implied_vol_bisection(market_price, S, K, Tt, r, is_call,
                           tol=1e-4, max_iter=100, lower=1e-4, upper=5):
    # Biseccion sobre todos los contratos a la vez. Cada contrato sigue la misma
    # regla que la version escalar: se detiene cuando |f(mid)| < tol, devuelve
    # NaN si el precio no queda acotado entre lower y upper, y si agota las
    # iteraciones devuelve el ultimo punto medio.
    mp, S, K = (np.asarray(x, dtype=float) for x in (market_price, S, K))
    is_call = np.asarray(is_call, dtype=bool)
    iv = np.full(mp.shape, np.nan)
    if Tt <= 0:
        return iv

    lo = np.full(mp.shape, float(lower))
    hi = np.full(mp.shape, float(upper))
    with np.errstate(invalid="ignore"):
        f_lo = bs_price(S, K, Tt, r, lo, is_call) - mp
        f_hi = bs_price(S, K, Tt, r, hi, is_call) - mp
        activo = (np.isfinite(mp) & np.isfinite(S) & np.isfinite(K) & (mp > 0)
                  & np.isfinite(f_lo) & np.isfinite(f_hi) & ~(f_lo * f_hi > 0))

    mid = (lo + hi) / 2
    for _ in range(max_iter):
        if not activo.any():
            break
        mid = np.where(activo, (lo + hi) / 2, mid)
        f_mid = bs_price(S, K, Tt, r, mid, is_call) - mp
        activo &= np.isfinite(f_mid)             # f(mid) invalido -> queda NaN
        listo = activo & (np.abs(f_mid) < tol)
        iv[listo] = mid[listo]
        activo &= ~listo
        izquierda = f_lo * f_mid < 0
        hi = np.where(activo & izquierda, mid, hi)
        derecha = activo & ~izquierda
        lo = np.where(derecha, mid, lo)
        f_lo = np.where(derecha, f_mid, f_lo)
    iv[activo] = mid[activo]
    return iv

def fill_missing_iv_greeks(chain, days_to_expiry, rf_annual, spot_fallback):
    chain = chain.copy()
    if chain["spot"].isna().all() and not pd.isna(spot_fallback):
        chain["spot"] = spot_fallback

    Tt = days_to_expiry / 365
    market_price = chain["last_quote_mid"].combine_first(chain["day_close"])

    needs_iv = (chain["iv"].isna() | (chain["iv"] <= 0)).to_numpy()
    if needs_iv.any():
        sub = chain.loc[needs_iv]
        chain.loc[needs_iv, "iv"] = implied_vol_bisection(
            market_price[needs_iv].to_numpy(), sub["spot"].to_numpy(), sub["strike"].to_numpy(),
            Tt, rf_annual, (sub["contract_type"] == "call").to_numpy())

    needs_gamma = chain["gamma"].isna().to_numpy()
    if needs_gamma.any():
        sub = chain.loc[needs_gamma]
        chain.loc[needs_gamma, "gamma"] = bs_gamma(
            sub["spot"].to_numpy(), sub["strike"].to_numpy(), Tt, rf_annual, sub["iv"].to_numpy())

    return chain

def get_target_expiration(ticker, horizon_days, api_key):
    today = dt.date.today()
    target_date = today + dt.timedelta(days=round(horizon_days * 7 / 5))

    # Se piden solo los dos vencimientos que rodean al objetivo (el primero en o
    # despues y el ultimo en o antes), con limit=1 cada uno. Antes se pedia una
    # sola pagina de 1000 contratos sin filtro de fecha: en activos con
    # vencimientos semanales esa pagina cubria apenas los proximos dias y el
    # vencimiento "mas cercano al objetivo" salia de ahi.
    base = {"underlying_ticker": ticker, "contract_type": "call",
            "sort": "expiration_date", "limit": 1}
    respuestas = [
        polygon_get("/v3/reference/options/contracts",
                    params={**base, "order": "asc", "expiration_date.gte": target_date.isoformat()},
                    api_key=api_key),
        polygon_get("/v3/reference/options/contracts",
                    params={**base, "order": "desc",
                            "expiration_date.gte": today.isoformat(),
                            "expiration_date.lte": target_date.isoformat()},
                    api_key=api_key),
    ]

    expirations = sorted({
        dt.date.fromisoformat(r["expiration_date"])
        for resp in respuestas
        for r in ((resp or {}).get("results") or [])
        if r.get("expiration_date")
    })
    if not expirations:
        log_warn(f"Sin contratos de opciones disponibles para {ticker} (posible activo sin mercado de opciones).")
        return {"expiration": None, "days_to_expiry": None}

    best_exp = min(expirations, key=lambda e: abs((e - target_date).days))
    return {"expiration": best_exp, "days_to_expiry": (best_exp - today).days}

def get_option_chain_snapshot(ticker, expiration_date, api_key):
    if expiration_date is None:
        return None

    # Una pagina fallida o el tope de paginas lanzan PolygonError: antes se
    # cortaba en silencio y el GEX / max pain se calculaban sobre media cadena.
    all_results = polygon_client(api_key).paginate(
        f"/v3/snapshot/options/{ticker}",
        params={"expiration_date": expiration_date.strftime("%Y-%m-%d"), "limit": 250},
        max_pages=polygon_max_pages_snapshot,
    )
    if not all_results:
        log_warn(f"Snapshot de opciones vacio para {ticker} @ {expiration_date}.")
        return None

    def g(d, path, default=None):
        cur = d
        for key in path.split("."):
            if not isinstance(cur, dict) or key not in cur:
                return default
            cur = cur[key]
        return cur

    rows = []
    for item in all_results:
        rows.append({
            "contract_ticker": g(item, "details.ticker"),
            "contract_type": g(item, "details.contract_type"),
            "strike": g(item, "details.strike_price"),
            "expiration": g(item, "details.expiration_date"),
            "iv": g(item, "implied_volatility"),
            "delta": g(item, "greeks.delta"),
            "gamma": g(item, "greeks.gamma"),
            "theta": g(item, "greeks.theta"),
            "vega": g(item, "greeks.vega"),
            "volume": g(item, "day.volume"),
            "open_interest": g(item, "open_interest"),
            "spot": g(item, "underlying_asset.price"),
            "day_close": g(item, "day.close"),
            "last_quote_mid": g(item, "last_quote.midpoint"),
        })

    chain = pd.DataFrame(rows)
    if chain.empty:
        return None

    numeric_cols = ["strike", "iv", "delta", "gamma", "theta", "vega",
                     "volume", "open_interest", "spot", "day_close", "last_quote_mid"]
    for c in numeric_cols:
        chain[c] = pd.to_numeric(chain[c], errors="coerce")

    chain = chain.dropna(subset=["strike", "contract_type"])
    if chain.empty:
        return None
    return chain.reset_index(drop=True)

def compute_atm_iv(chain):
    spot = chain["spot"].median(skipna=True)
    if pd.isna(spot) or chain.empty:
        return np.nan
    atm_strike = chain.loc[(chain["strike"] - spot).abs().idxmin(), "strike"]
    atm_rows = chain[(chain["strike"] == atm_strike) & chain["iv"].notna() & (chain["iv"] > 0)]
    if atm_rows.empty:
        return np.nan
    return atm_rows["iv"].mean()

def compute_expected_move(chain, days_to_expiry):
    spot = chain["spot"].median(skipna=True)
    atm_iv = compute_atm_iv(chain)
    if pd.isna(spot) or pd.isna(atm_iv):
        return {"spot": spot, "atm_iv": np.nan, "move_usd": np.nan, "move_pct": np.nan}
    move_pct = atm_iv * np.sqrt(days_to_expiry / 365)
    move_usd = spot * move_pct
    return {"spot": spot, "atm_iv": atm_iv, "move_usd": move_usd, "move_pct": move_pct}

def compute_put_call_ratio(chain):
    vol_call = chain.loc[chain["contract_type"] == "call", "volume"].sum(skipna=True)
    vol_put = chain.loc[chain["contract_type"] == "put", "volume"].sum(skipna=True)
    oi_call = chain.loc[chain["contract_type"] == "call", "open_interest"].sum(skipna=True)
    oi_put = chain.loc[chain["contract_type"] == "put", "open_interest"].sum(skipna=True)

    return {
        "PCR_Volumen": np.nan if vol_call == 0 else vol_put / vol_call,
        "PCR_OI": np.nan if oi_call == 0 else oi_put / oi_call
    }

def compute_gex_profile(chain):
    spot = chain["spot"].median(skipna=True)
    if pd.isna(spot):
        return pd.DataFrame()

    df = chain.dropna(subset=["gamma", "open_interest"]).copy()
    df["gamma_oi"] = df["gamma"] * df["open_interest"]
    grouped = df.groupby(["strike", "contract_type"])["gamma_oi"].sum().reset_index()
    pivot = grouped.pivot(index="strike", columns="contract_type", values="gamma_oi").fillna(0).reset_index()
    if "call" not in pivot.columns:
        pivot["call"] = 0
    if "put" not in pivot.columns:
        pivot["put"] = 0

    pivot["GEX_call"] = pivot["call"] * 100 * spot ** 2 * 0.01
    pivot["GEX_put"] = -pivot["put"] * 100 * spot ** 2 * 0.01
    pivot["GEX_neto"] = pivot["GEX_call"] + pivot["GEX_put"]
    return pivot.sort_values("strike").reset_index(drop=True)

def compute_zero_gamma_level(gex_profile):
    if len(gex_profile) < 2:
        return np.nan
    gp = gex_profile.sort_values("strike").reset_index(drop=True)
    gp["cum_gex"] = gp["GEX_neto"].cumsum()

    # Se excluyen strikes sin exposicion real (GEX_neto == 0, tipicamente sin
    # OI en ese vencimiento) de la busqueda del cruce de signo. Sin este filtro,
    # el cumsum se queda en signo 0 durante esos strikes y np.sign() detecta un
    # "cambio" espurio en el borde de la ventana de datos en vez de un nivel
    # de zero-gamma genuino. Los valores de cum_gex usados si son los reales.
    gp_sig = gp[gp["GEX_neto"] != 0].reset_index(drop=True)
    if len(gp_sig) < 2:
        return np.nan

    signs = np.sign(gp_sig["cum_gex"].values)
    diffs = np.diff(signs)
    sign_change_idx = np.where(diffs != 0)[0]
    if len(sign_change_idx) == 0:
        return np.nan
    i = sign_change_idx[0]
    x1, x2 = gp_sig["strike"].iloc[i], gp_sig["strike"].iloc[i + 1]
    y1, y2 = gp_sig["cum_gex"].iloc[i], gp_sig["cum_gex"].iloc[i + 1]
    return x1 + (0 - y1) * (x2 - x1) / (y2 - y1)

def compute_max_pain(chain):
    strikes = sorted(chain["strike"].unique())
    if len(strikes) == 0:
        return {"max_pain_strike": np.nan, "payout_curve": pd.DataFrame(), "notional_concentration": pd.DataFrame()}

    calls = chain[chain["contract_type"] == "call"]
    puts = chain[chain["contract_type"] == "put"]

    payouts = []
    for K in strikes:
        call_payout = (np.maximum(K - calls["strike"], 0) * calls["open_interest"]).sum(skipna=True)
        put_payout = (np.maximum(puts["strike"] - K, 0) * puts["open_interest"]).sum(skipna=True)
        payouts.append(call_payout + put_payout)

    notional_tbl = pd.DataFrame({"strike": strikes, "payout": payouts})
    max_pain_strike = strikes[int(np.argmin(payouts))]

    notional_conc = (
        chain.assign(notional=chain["open_interest"] * chain["strike"] * 100)
        .groupby("strike")["notional"].sum()
        .reset_index()
        .sort_values("notional", ascending=False)
    )

    return {"max_pain_strike": max_pain_strike, "payout_curve": notional_tbl, "notional_concentration": notional_conc}

def run_options_module_for_ticker(ticker, hv_annual, horizon_days, api_key,
                                   spot_fallback=np.nan, rf_annual=0):
    log_info(f"MODULO 2: procesando cadena de opciones de {ticker}...")

    try:
        exp_info = get_target_expiration(ticker, horizon_days, api_key)
        if exp_info["expiration"] is None:
            log_warn(f"{ticker}: sin expiracion valida encontrada. Se omite del modulo de opciones.")
            return None
        chain = get_option_chain_snapshot(ticker, exp_info["expiration"], api_key)
    except PolygonNotFound:
        log_warn(f"{ticker}: recurso no encontrado (404), posible activo sin mercado de opciones. "
                 "Se omite del modulo de opciones.")
        return None
    except PolygonError as e:
        log_error(f"{ticker}: {e}. Se omite del modulo de opciones.")
        return None

    if chain is None:
        log_warn(f"{ticker}: cadena de opciones no disponible. Se omite del modulo de opciones.")
        return None

    chain = fill_missing_iv_greeks(chain, exp_info["days_to_expiry"], rf_annual, spot_fallback)

    exp_move = compute_expected_move(chain, exp_info["days_to_expiry"])
    pcr = compute_put_call_ratio(chain)
    gex = compute_gex_profile(chain)
    zero_gamma = compute_zero_gamma_level(gex)
    max_pain = compute_max_pain(chain)

    iv_hv_ratio = (
        np.nan if (pd.isna(exp_move["atm_iv"]) or pd.isna(hv_annual) or hv_annual == 0)
        else exp_move["atm_iv"] / hv_annual
    )

    return {
        "ticker": ticker,
        "expiration": exp_info["expiration"],
        "days_to_expiry": exp_info["days_to_expiry"],
        "spot": exp_move["spot"],
        "atm_iv": exp_move["atm_iv"],
        "hv_annual": hv_annual,
        "iv_hv_ratio": iv_hv_ratio,
        "expected_move_usd": exp_move["move_usd"],
        "expected_move_pct": exp_move["move_pct"],
        "pcr_volume": pcr["PCR_Volumen"],
        "pcr_oi": pcr["PCR_OI"],
        "gex_profile": gex,
        "zero_gamma_level": zero_gamma,
        "max_pain_strike": max_pain["max_pain_strike"],
        "notional_concentration": max_pain["notional_concentration"]
    }

def run_options_module(tickers, hv_by_asset, weights, horizon_days, api_key,
                        spot_by_asset=None, rf_annual=0):
    results = {}
    for tk in tickers:
        spot_fb = spot_by_asset.get(tk, np.nan) if spot_by_asset else np.nan
        r = run_options_module_for_ticker(
            tk, hv_by_asset.get(tk), horizon_days, api_key,
            spot_fallback=spot_fb, rf_annual=rf_annual
        )
        if r is not None:
            results[tk] = r

    if len(results) == 0:
        log_warn("MODULO 2: ningun activo tuvo datos de opciones disponibles.")
        return {"by_asset": {}, "summary": pd.DataFrame(), "portfolio_iv": np.nan}

    summary_rows = []
    for r in results.values():
        summary_rows.append({
            "Activo": r["ticker"],
            "Vencimiento": r["expiration"],
            "Dias_a_Vencimiento": r["days_to_expiry"],
            "Spot": r["spot"],
            "IV_ATM": r["atm_iv"],
            "HV_Anual": r["hv_annual"],
            "Ratio_IV_HV": r["iv_hv_ratio"],
            "Movimiento_Esperado_USD": r["expected_move_usd"],
            "Movimiento_Esperado_Pct": r["expected_move_pct"],
            "PCR_Volumen": r["pcr_volume"],
            "PCR_OI": r["pcr_oi"],
            "Zero_Gamma_Level": r["zero_gamma_level"],
            "Max_Pain_Strike": r["max_pain_strike"]
        })
    summary_tbl = pd.DataFrame(summary_rows)

    available_w = pd.Series(weights)[summary_tbl["Activo"]]
    available_w = available_w / available_w.sum()
    if summary_tbl["IV_ATM"].isna().all():
        portfolio_iv = np.nan
    else:
        portfolio_iv = float((summary_tbl["IV_ATM"].values * available_w.values).sum())

    return {"by_asset": results, "summary": summary_tbl, "portfolio_iv": portfolio_iv}

# =============================================================================
# BLOQUE 6: APALANCAMIENTO DINAMICO POR ACTIVO
# =============================================================================

def min_max_normalize(x):
    x = np.array(x, dtype=float)
    if np.all(np.isnan(x)):
        return np.full(len(x), 0.5)
    rng = (np.nanmin(x), np.nanmax(x))
    if rng[1] - rng[0] == 0:
        return np.full(len(x), 0.5)
    out = (x - rng[0]) / (rng[1] - rng[0])
    mean_val = np.nanmean(out)
    out = np.where(np.isnan(out), mean_val, out)
    return out

def compute_gex_pcr_factor(options_by_asset, tickers):
    rows = []
    for tk in tickers:
        r = options_by_asset.get(tk)
        if r is None:
            rows.append({"Activo": tk, "gex_total": np.nan, "pcr_oi": np.nan})
            continue
        gex_total = r["gex_profile"]["GEX_neto"].sum() if len(r["gex_profile"]) > 0 else np.nan
        rows.append({"Activo": tk, "gex_total": gex_total, "pcr_oi": r["pcr_oi"]})
    return pd.DataFrame(rows)

def run_leverage_module(expost_results, options_module, weights,
                         leverage_min, leverage_max, risk_score_weights):
    log_info("MODULO 3: calculando Risk Score y apalancamiento dinamico...")

    tickers = list(weights.keys())

    hv_tbl = (
        expost_results["volatility"][expost_results["volatility"]["Activo"].isin(tickers)]
        [["Activo", "Vol_Anualizada"]].rename(columns={"Vol_Anualizada": "HV"})
    )
    cvar_tbl = (
        expost_results["var_es"][expost_results["var_es"]["Activo"].isin(tickers)]
        [["Activo", "CVaR_Hist_95_Diario"]].rename(columns={"CVaR_Hist_95_Diario": "CVaR"})
    )

    if len(options_module["summary"]) > 0:
        iv_tbl = options_module["summary"][["Activo", "IV_ATM"]].rename(columns={"IV_ATM": "IV"})
    else:
        iv_tbl = pd.DataFrame({"Activo": tickers, "IV": np.nan})

    gex_pcr_tbl = compute_gex_pcr_factor(options_module["by_asset"], tickers)

    scoring = pd.DataFrame({"Activo": tickers})
    scoring = scoring.merge(hv_tbl, on="Activo", how="left")
    scoring = scoring.merge(cvar_tbl, on="Activo", how="left")
    scoring = scoring.merge(iv_tbl, on="Activo", how="left")
    scoring = scoring.merge(gex_pcr_tbl, on="Activo", how="left")

    scoring["hv_norm"] = min_max_normalize(scoring["HV"])
    scoring["cvar_norm"] = min_max_normalize(scoring["CVaR"])
    scoring["iv_norm"] = min_max_normalize(scoring["IV"])
    scoring["gex_norm"] = min_max_normalize(-scoring["gex_total"])
    scoring["pcr_norm"] = min_max_normalize(scoring["pcr_oi"])
    scoring["gex_pcr_norm"] = scoring[["gex_norm", "pcr_norm"]].mean(axis=1, skipna=True)

    w = risk_score_weights
    scoring["Risk_Score"] = 100 * (
        w["hv"] * scoring["hv_norm"] +
        w["cvar"] * scoring["cvar_norm"] +
        w["iv"] * scoring["iv_norm"] +
        w["gex_pcr"] * scoring["gex_pcr_norm"]
    )

    score_min, score_max = scoring["Risk_Score"].min(), scoring["Risk_Score"].max()
    if score_max - score_min == 0:
        scoring["Risk_Score_Norm"] = 0.5
    else:
        scoring["Risk_Score_Norm"] = (scoring["Risk_Score"] - score_min) / (score_max - score_min)

    scoring["Apalancamiento"] = leverage_max - scoring["Risk_Score_Norm"] * (leverage_max - leverage_min)
    scoring["Peso_Inicial"] = scoring["Activo"].map(weights)
    scoring["Exposicion_Efectiva"] = scoring["Peso_Inicial"] * scoring["Apalancamiento"]

    final_tbl = (
        scoring[["Activo", "Peso_Inicial", "Risk_Score", "Apalancamiento", "Exposicion_Efectiva"]]
        .sort_values("Risk_Score", ascending=False)
        .reset_index(drop=True)
    )

    return {"detail": scoring, "summary": final_tbl}

# =============================================================================
# BLOQUE 7: REPORTE Y GRAFICOS
# =============================================================================
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def print_executive_summary(expost_results, options_module, leverage_results):
    print("\n\n================ RESUMEN EJECUTIVO ================\n")

    print("\n--- MODULO 1: Metricas Anualizadas por Activo ---")
    print(expost_results["annualized_summary"].round(4).to_string(index=False))

    print("\n--- MODULO 1: Metricas al Horizonte de Inversion ---")
    print(expost_results["horizon_summary"].round(4).to_string(index=False))

    print("\n--- MODULO 1: Contribucion al Riesgo (MCR / PCR) ---")
    print(expost_results["risk_contribution"].round(4).to_string(index=False))

    print("\n--- MODULO 1: Matriz de Correlacion ---")
    print(expost_results["correlation"].round(3).to_string())

    if len(options_module["summary"]) > 0:
        print("\n--- MODULO 2: Metricas Forward-Looking (Opciones) ---")
        print(options_module["summary"].round(4).to_string(index=False))
        print(f"\nIV Ponderada del Portafolio: {options_module['portfolio_iv'] * 100:.2f}%")
    else:
        print("\n--- MODULO 2: sin datos de opciones disponibles ---")

    print("\n--- MODULO 3: Apalancamiento Dinamico Asignado ---")
    print(leverage_results["summary"].round(3).to_string(index=False))

    print("\n=====================================================\n")

def plot_pcr_vs_weight(risk_contribution):
    df = risk_contribution[["Activo", "Peso", "PCR"]].melt(
        id_vars="Activo", var_name="Metrica", value_name="Valor"
    )
    fig = px.bar(
        df, x="Activo", y="Valor", color="Metrica", barmode="group",
        color_discrete_map={"Peso": "#4C72B0", "PCR": "#DD8452"},
        labels={"Valor": "", "Activo": ""},
    )
    fig.update_traces(hovertemplate="%{x}: %{y:.2%}<extra></extra>")
    fig.update_layout(
        title="Contribucion Porcentual al Riesgo (PCR) vs. Peso Invertido",
        yaxis_tickformat=".0%",
        template="plotly_white",
        legend_title_text="",
    )
    return fig

def plot_gex_profile(options_by_asset):
    frames = []
    for tk, r in options_by_asset.items():
        if r is None or len(r["gex_profile"]) == 0:
            continue
        df = r["gex_profile"].copy()
        df["Activo"] = tk
        frames.append(df)

    if not frames:
        log_warn("Sin datos de GEX disponibles para graficar.")
        return None

    gex_all = pd.concat(frames, ignore_index=True)
    tickers_ = gex_all["Activo"].unique()
    fig = make_subplots(rows=1, cols=len(tickers_), subplot_titles=list(tickers_))
    for i, tk in enumerate(tickers_):
        sub = gex_all[gex_all["Activo"] == tk]
        colors = ["#55A868" if v > 0 else "#C44E52" for v in sub["GEX_neto"]]
        fig.add_trace(go.Bar(x=sub["strike"], y=sub["GEX_neto"], marker_color=colors, showlegend=False,
                              hovertemplate="Strike %{x}: $%{y:,.0f}<extra></extra>"), row=1, col=i + 1)
        fig.add_hline(y=0, line_color="black", line_width=0.5, row=1, col=i + 1)
        fig.update_xaxes(title_text="Strike", row=1, col=i + 1)
        fig.update_yaxes(title_text="GEX Neto ($)", row=1, col=i + 1)
    fig.update_layout(
        title="Perfil de Gamma Exposure (GEX) por Strike",
        template="plotly_white",
        width=max(600, 500 * len(tickers_)),
    )
    return fig

def plot_loss_distribution(portfolio_returns, var_es_row):
    var95 = var_es_row["VaR_Hist_95_Diario"].values[0]
    cvar95 = var_es_row["CVaR_Hist_95_Diario"].values[0]
    var99 = var_es_row["VaR_Hist_99_Diario"].values[0]

    port_vals = np.asarray(portfolio_returns, dtype=float)
    df_ret = pd.DataFrame({"retorno": port_vals})

    fig = px.histogram(
        df_ret, x="retorno", nbins=60, histnorm="probability density",
        color_discrete_sequence=["#4C72B0"], opacity=0.7,
        labels={"retorno": "Retorno diario"},
    )
    fig.update_traces(hovertemplate="Retorno: %{x:.4f}<br>Densidad: %{y:.2f}<extra></extra>")

    kde = stats.gaussian_kde(port_vals)
    x_kde = np.linspace(port_vals.min(), port_vals.max(), 300)
    fig.add_trace(go.Scatter(x=x_kde, y=kde(x_kde), mode="lines", line=dict(color="black", width=1.2),
                              name="Densidad (KDE)", hoverinfo="skip"))

    fig.add_vline(x=-var95, line_dash="dash", line_color="#DD8452",
                  annotation_text="VaR 95%", annotation_textangle=-90)
    fig.add_vline(x=-cvar95, line_dash="dash", line_color="#C44E52",
                  annotation_text="CVaR 95%", annotation_textangle=-90)
    fig.add_vline(x=-var99, line_dash="dot", line_color="#8172B2",
                  annotation_text="VaR 99%", annotation_textangle=-90)

    fig.update_layout(
        title="Distribucion de Retornos Diarios del Portafolio",
        xaxis_title="Retorno diario", yaxis_title="Densidad",
        template="plotly_white", showlegend=False,
    )
    return fig

def plot_leverage_assignment(leverage_summary, leverage_min, leverage_max):
    df = leverage_summary.sort_values("Apalancamiento")
    fig = px.bar(
        df, x="Activo", y="Apalancamiento", color="Risk_Score",
        color_continuous_scale="RdYlGn_r",
        text=df["Apalancamiento"].map(lambda x: f"x{x:.2f}"),
        labels={"Risk_Score": "Risk Score"},
    )
    fig.update_traces(textposition="outside",
                       hovertemplate="%{x}: x%{y:.2f} (Risk Score: %{marker.color:.2f})<extra></extra>")
    fig.update_layout(
        title=f"Apalancamiento Asignado por Activo (x{leverage_min:.1f} - x{leverage_max:.1f})",
        yaxis_title="Apalancamiento", yaxis_range=[0, leverage_max * 1.15],
        template="plotly_white",
    )
    return fig

def run_reporting_module(expost_results, options_module, leverage_results,
                          portfolio_returns, leverage_min, leverage_max):
    print_executive_summary(expost_results, options_module, leverage_results)

    var_es_portfolio = expost_results["var_es"][expost_results["var_es"]["Activo"] == "Portfolio"]

    plots = {
        "pcr_vs_weight": plot_pcr_vs_weight(expost_results["risk_contribution"]),
        "gex_profile": plot_gex_profile(options_module["by_asset"]),
        "loss_distribution": (
            plot_loss_distribution(portfolio_returns, var_es_portfolio)
            if len(var_es_portfolio) == 1 else None
        ),
        "leverage_assignment": plot_leverage_assignment(
            leverage_results["summary"], leverage_min, leverage_max
        )
    }

    for p in plots.values():
        if p is not None:
            p.show()

    return plots

# =============================================================================
# BLOQUE 8: EJECUCION DEL PIPELINE
# =============================================================================
tickers = list(portfolio.keys())

prices = get_price_data(tickers, start_date, end_date)
asset_returns = get_log_returns(prices)
portfolio_returns = get_portfolio_returns(asset_returns, portfolio)

expost_results = run_expost_risk_module(
    asset_returns=asset_returns,
    portfolio_returns=portfolio_returns,
    weights=portfolio,
    horizon_days=horizon_days,
    confidence_levels=confidence_levels,
    rf_annual=risk_free_rate_annual,
    mar_annual=mar_annual,
    trading_days_per_year=trading_days_per_year
)

hv_by_asset = dict(zip(expost_results["volatility"]["Activo"], expost_results["volatility"]["Vol_Anualizada"]))
spot_by_asset = dict(zip(tickers, prices.iloc[-1][tickers].values))

if not polygon_api_key:
    log_warn("polygon_api_key no configurada. Se omite el MODULO 2 (Ex-Ante).")
    options_module = {"by_asset": {}, "summary": pd.DataFrame(), "portfolio_iv": np.nan}
else:
    options_module = run_options_module(
        tickers=tickers,
        hv_by_asset=hv_by_asset,
        weights=portfolio,
        horizon_days=horizon_days,
        api_key=polygon_api_key,
        spot_by_asset=spot_by_asset,
        rf_annual=risk_free_rate_annual
    )

leverage_results = run_leverage_module(
    expost_results=expost_results,
    options_module=options_module,
    weights=portfolio,
    leverage_min=leverage_min,
    leverage_max=leverage_max,
    risk_score_weights=risk_score_weights
)

plots = run_reporting_module(
    expost_results=expost_results,
    options_module=options_module,
    leverage_results=leverage_results,
    portfolio_returns=portfolio_returns,
    leverage_min=leverage_min,
    leverage_max=leverage_max
)

log_info("Pipeline completo. Objetos disponibles: expost_results, options_module, leverage_results, plots.")
