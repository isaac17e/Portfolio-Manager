# Portfolio Manager

A set of standalone Python scripts for **managing an existing equity/ETF portfolio**: tactical rebalancing from options market microstructure, staged entry signals, risk scoring with dynamic leverage, a portfolio-level implied volatility index, a 3D gamma "force field" and fundamental screening.

Most scripts take a portfolio as a `ticker: weight` dictionary at the top of the file and use the **Polygon.io** options chain as their main input. If `PORTFOLIO_FILE` points at a portfolio JSON file (default `/workspace/pipeline/portfolio/portfolio_latest.json`), that file replaces the hardcoded dictionary; a missing or invalid file keeps the dictionary and prints a warning. Price history and fundamentals come from Polygon or **Yahoo Finance** (`yfinance`).

> Code comments, console output and the HTML reports are in Spanish.

| Script | What it does |
|---|---|
| [`active_management.py`](active_management.py) | Scores each holding from GEX, order flow, Vanna/Charm and expected move, then rebalances weights and cash with a portfolio risk layer |
| [`entry_signal_tool.py`](entry_signal_tool.py) | Daily conviction score to build positions gradually over a 5-day entry cycle |
| [`portfolio_risk_score_leverage.py`](portfolio_risk_score_leverage.py) | Ex-post and ex-ante risk metrics and a risk score that sets leverage per asset |
| [`portfolio_vix.py`](portfolio_vix.py) | A VIX-style model-free implied volatility index for the whole portfolio |
| [`portfolio_gex_field.py`](portfolio_gex_field.py) | Live 3D surface combining the portfolio's gamma exposure with a macro stress axis |
| [`fundamental_analysis.py`](fundamental_analysis.py) | Traffic-light fundamental scorecard per ticker, with an HTML report |

---

## `active_management.py` — Tactical active management engine

1. **Options data** (Polygon v3): spot price, the expiration closest to the investment horizon (30 trading days by default, about 42 calendar days) and the full chain snapshot.
2. **Microstructure metrics** per ticker:
   - **GEX**: total gamma exposure, regime and gamma flip level;
   - **order flow**: unusual options activity (volume/OI above a threshold), call vs. put sweep dominance, put/call ratio;
   - **Vanna and Charm** exposure (Black-Scholes-Merton);
   - **expected move** from the ATM straddle.
3. **Tactical score**: combines distance to the gamma flip, GEX regime and intensity, sweep bias, put/call ratio, Vanna and Charm, and dampens the score when GEX liquidity is low. The score maps to an action:

   | Score | Action |
   |---|---|
   | ≥ 50 | Increase (`AUMENTAR`) |
   | 0 to 50 | Hold (`MANTENER`) |
   | −50 to 0 | Trim 25–50% (`RECORTAR`) |
   | < −50 | Liquidate (`LIQUIDAR`) |

   A ticker without usable gamma or open interest gets no GEX points (missing data is not a signal), and the rest of its score is dampened like a low-liquidity name.

4. **Portfolio risk layer**:
   - volatility from ATM implied volatility (historical as fallback);
   - **implied correlation** solved from the dispersion equation against a benchmark ETF (SPY globally, DBC for the commodities block), keeping the shape of the historical correlation (sample, EWMA or random-matrix filtered);
   - **Euler risk attribution** (contribution to total risk per asset);
   - a **concentration guardrail** that shifts weight away from any asset whose risk contribution exceeds 1.5× the equal-share level.
5. **Rebalancing**: freed capital goes to cash up to a 30% cap, and the rest is distributed among "Increase" names in proportion to their score. Portfolio weights do not have to add up to 1: whatever is missing is existing cash and becomes the starting weight of the `CASH` row, so current and suggested cash are compared on the same basis. Weights above 1 are normalized with a warning.
6. **Risk regime history**: each run is appended to `portfolio_risk_history.csv`. After 20 runs, portfolio volatility and the diversification ratio are compared with their own percentiles to flag stress or diversification collapse.

**Output**: an executive summary with the rationale per asset, gamma profile charts, current vs. suggested allocation and a risk attribution chart.

## `entry_signal_tool.py` — Entry conviction score

For building new positions gradually. Each day it computes, per ticker, a **0–100 conviction score** from eight weighted signals:

| Signal | Weight |
|---|---|
| GEX regime | 18% |
| Distance to zero gamma | 15% |
| IV rank | 15% |
| Room between call and put walls | 12% |
| Skew | 10% |
| Expected move | 10% |
| Smart money (put/call) | 10% |
| Relative volume | 10% |

The score sets what fraction of the target weight to buy that day: high conviction (≥ 75) buys all of it, medium (40–75) scales between 40% and 80%, and low buys at most 30%.

The script runs a **5-business-day cycle** with no interactive prompts. The cycle day comes from `--cycle-day` or `ENTRY_CYCLE_DAY`, otherwise from the last executed day in `entry_state.json` (next day, or day 1 when the cycle is closed or the file is new). Percent already invested comes from `--invested-pct` or `ENTRY_INVESTED_PCT`, otherwise from that same file. Generating a signal does **not** mark the book as invested. `entry_state.json` advances only when a fills file confirms that signal (see [Pipeline signals](#pipeline-signals)). Indicator history still appends to `entry_signal_history.csv`. On day 5 the signal decides the unfilled fraction: buy the rest if the accumulated options flow is favorable (smart money and distance to zero gamma), or leave it in cash — that cash decision is stored as pending and applied only with the matching fills.

**Output**: a console summary and a Plotly chart.

## `portfolio_risk_score_leverage.py` — Risk score and dynamic leverage

1. **Ex-post risk** (Yahoo Finance prices since 2021): volatility over the investment horizon, historical and Cornish-Fisher VaR/ES at 95% and 99%, maximum drawdown, Sharpe, Sortino, correlation matrix and risk contribution per asset.
2. **Ex-ante risk** (Polygon options): ATM implied volatility, expected move, put/call ratio, GEX profile, zero gamma level and max pain. Missing IV and Greeks are filled with Black-Scholes.
3. **Risk score** (0–100): 30% historical volatility, 30% CVaR, 25% implied volatility and 15% GEX/put-call factor, each normalized across the portfolio.
4. **Dynamic leverage**: maps the score linearly to leverage between **2x (riskiest) and 5x (safest)** and reports the effective exposure per asset.

**Output**: an executive summary plus charts of risk contribution vs. weight, GEX profiles, the portfolio loss distribution and the leverage assignment.

## `portfolio_vix.py` — Portfolio VIX engine

Extends the **CBOE VIX methodology** from one index to a portfolio of N stocks/ETFs:

1. **Chain cleaning** with static no-arbitrage filters (quotes, spreads, bounds, monotonicity), and **de-Americanization** of American option prices (Bjerksund-Stensland 1993 or a CRR binomial tree). Dividends are handled as escrowed discrete payments or a continuous yield.
2. **Smile construction** per expiration with raw SVI (Gatheral's butterfly test and an R² guard), or a cubic spline as the alternative.
3. **CBOE model-free variance** per asset: implied forward from put-call parity, strike strip weighted by ΔK·Q(K)/K², interpolated to a constant 30-day horizon.
4. **Portfolio aggregation**: correlation matrix (EWMA, sample or random-matrix filtered) combined with the 30-day implied volatilities to get the portfolio VIX, plus **Euler risk attribution** per asset.

Data comes from Polygon, with Yahoo Finance as the fallback. Synthetic data is used only when asked for (`--synthetic` or `--source synthetic`), never as a silent fallback. `--weights` must give one non-negative value per ticker, in the same order. It has a CLI:

```bash
python portfolio_vix.py --tickers SPY QQQ GLD --weights 0.5 0.3 0.2 \
    --source polygon --vol-method svi --corr-method ewma --american-engine bs1993
```

**Output**: `portfolio_vix_report.html` with the smiles per asset, the variance strip weights and the risk attribution.

## `portfolio_gex_field.py` — 3D portfolio gamma field

A live visualization of where the portfolio sits in terms of dealer positioning and macro stress:

- **X axis**: price displacement in expected-move (σ) units. For each holding, net GEX is computed from options expiring within 2 months (implied volatility inverted with the Bjerksund-Stensland American model), smoothed and combined into a weighted **composite force** for the portfolio.
- **Y axis**: macro/liquidity/volatility stress, built from the 1-year percentile ranks of VIX (50%), the 10-year yield (25%) and the dollar index (25%).
- **Z**: a potential surface in which macro stress amplifies negative-gamma (risk) zones more than it deepens positive-gamma (stable) zones. The script marks the portfolio's current state, the gradient and reference lines for each holding.

**Pipeline mode is headless:** one calculation, then exit. It writes `portfolio_gex_field.html` and `portfolio_gex_field_data.json` and does not open a browser or start the local server.

```bash
python portfolio_gex_field.py --once
HEADLESS=1 python portfolio_gex_field.py
GEX_ONCE=1 python portfolio_gex_field.py
```

Without `--once` / `HEADLESS=1` / `GEX_ONCE=1` it still loops, refreshing every 60 seconds, and serves the page from a local HTTP server so the chart updates without a full reload.

## `fundamental_analysis.py` — Fundamental scorecard

Uses Yahoo Finance financial statements to grade each ticker as green / neutral / alert on 12 indicators across three horizons:

| Horizon | Indicators |
|---|---|
| Short term | Current ratio, EV/EBITDA, trailing → forward P/E, earnings surprise |
| Medium term | Net debt/EBITDA, interest coverage, FCF yield, PEG ratio |
| Long term | ROCE, ROIC, ROE (penalized when driven by high leverage), reinvestment rate |

The number of green signals gives a global rating: **Global Green Light** (≥ 9), **Medium Quality** (≥ 6) or **Global Alert**. All thresholds are editable in the `UMBRALES` dictionary.

**Output**: `reporte_fundamental.html`, with summary cards, a signal matrix and charts of the last 4 fiscal years and 5 quarters.

## Options horizon per script

Each options script reads a different part of the curve on purpose, so their numbers are not interchangeable:

| Script | Expirations used |
|---|---|
| `active_management` | the one closest to 30 trading days (about 42 calendar days) |
| `entry_signal_tool` | the one closest to 30 calendar days |
| `portfolio_risk_score_leverage` | the one closest to 1 month (21 trading days, about 29 calendar days) |
| `portfolio_vix` | the two that bracket 30 days (CBOE rule), interpolated to 30 days |
| `portfolio_gex_field` | every expiration within 2 months; GEX from those beyond 7 days |

The gamma flip (zero-gamma level) is computed once, in `gex_utils.py`, and shared by all four GEX scripts: strikes without exposure are ignored so they cannot create a false flip at the edge of the strike window.

---

## Setup

Python 3.10 or later.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project folder with your Polygon key (it is ignored by git):

```
POLYGON_API_KEY=your_key_here
```

`fundamental_analysis.py` only needs Yahoo Finance and no API key.

## Usage

Edit the portfolio dictionary and parameters in the configuration block at the top of each script, then run it:

```bash
python active_management.py
python entry_signal_tool.py --cycle-day 2 --invested-pct 'GLD=40,KO=10'
python portfolio_risk_score_leverage.py
python portfolio_vix.py
python portfolio_gex_field.py --once   # pipeline mode
python fundamental_analysis.py
```

`POLYGON_CALLS_PER_MINUTE` defaults to **100** (sliding window). Set it to `5` on the free Stocks tier. HTTP 429 and 5xx are retried with exponential backoff and jitter; a `Retry-After` header is honored.

## Pipeline signals

Each script also writes a JSON signal (contract section 4) through `pipeline_io.py`. The hardcoded portfolio dict stays in the script and is the fallback.

| Env | Default |
|---|---|
| `PORTFOLIO_FILE` | `/workspace/pipeline/portfolio/portfolio_latest.json` |
| `SIGNALS_OUT_DIR` | `/workspace/pipeline/signals` |
| `EXECUTIONS_DIR` | `/workspace/pipeline/executions` |
| `POLYGON_CALLS_PER_MINUTE` | `100` |
| `ENTRY_CYCLE_DAY` | next day from `entry_state.json` |
| `ENTRY_INVESTED_PCT` | percents already stored in `entry_state.json` |
| `HEADLESS` or `GEX_ONCE` | unset (set to `1` for the GEX pipeline run) |
| `ENTRY_STAGGER_PCT` | `0.20` (tier `none`: share of the target bought per cycle day) |
| `NO_OPTIONS_WEIGHT_CAP_FACTOR` | `0.5` (tier `none`: target weight x factor) |
| `NO_OPTIONS_WEIGHT_CAP` | unset (tier `none`: optional absolute weight cap) |

CLI equivalents: `entry_signal_tool.py --cycle-day` and `--invested-pct` (env is used when the flag is omitted). `portfolio_gex_field.py --once` is the same switch as `HEADLESS=1` or `GEX_ONCE=1`.

### Ticker symbols

`tickers.py` maps the canonical portfolio symbol:

| Canonical | Yahoo | Polygon | Capital.com epic (unverified) | US options |
|---|---|---|---|---|
| `BRK-B` or `BRK.B` | `BRK-B` | `BRK.B` | `BRK.B` | yes |
| `RY.TO` | `RY.TO` | `RY.TO` | `RY` (verified) | no (suffix `.TO`); analysed via ADR `RY` |

Polygon and Yahoo calls use those forms. Capital.com epics are a best-effort guess (class shares keep the Polygon dot; the exchange suffix is stripped) and **must be verified** against the broker catalogue before any order.

International tickers keep their local symbol as the portfolio key. `resolve_instrument` picks a tier:

- `adr`: a US twin listing in `_ADR_TABLE` (`RY.TO` -> `RY`, the only entry, verified on Capital.com 2026-10-06). Options and orders use the ADR. An unverified entry is used for analysis only, adds a warning, and gets `capital_epic: null`.
- `proxy`: no ADR. The country ETF of the exchange suffix stands in for IV / gamma / put-call. Only the six countries in the universe are mapped (verified on Polygon 2026-10-08: options with greeks, IV and OI): Canada `.TO`/`.V` -> `EWC`, Japan `.T` -> `EWJ`, Germany `.DE`/`.F`/`.BE`/`.DU`/`.HM`/`.MU`/`.SG` -> `EWG`, France `.PA` -> `EWQ`, Spain `.MC` -> `EWP`, UK `.L`/`.IL` -> `EWU`. `entry_signal_tool` adds daily-price indicators from Yahoo (trend vs SMA 50/200, RSI 14, realized vol vs its mean, drawdown). `portfolio_risk_score_leverage` adds the same indicators as `price_signals`.
- `none`: no ADR and no proxy ETF (any other exchange suffix, e.g. `.SA`, `.HK`, `.AX`), or no proxy data. `entry_signal_tool` buys a fixed `ENTRY_STAGGER_PCT` tranche of a capped target per signal, on top of what was filled, (`signal: "staggered"`). `portfolio_risk_score_leverage` reports `weight_cap` and `effective_exposure_capped`.

Entries, waiting rows and `by_ticker` items gain `tier`, `analysis_ticker` and `proxy_etf`. Non-native entries also carry `capital_epic`, which is null unless verified. `portfolio_gex_field`, `portfolio_vix` and `active_management` use the ADR. They exclude `proxy` and `none` tickers, naming the proxy ETF in the reason as a reference only.

Options scripts (`active_management`, `entry_signal_tool`, `portfolio_risk_score_leverage`, `portfolio_vix`, `portfolio_gex_field`) skip a ticker that has no US-listed options, or that returns no option chain, instead of aborting the run. Those scripts add:

- top-level `warnings`: an array of `"TICKER: reason"` strings (possibly empty);
- `data.excluded`: `[{ "ticker", "reason" }]`, with the portfolio ticker unchanged.

Typical reasons: `no US-listed options (exchange suffix .TO)`, `no option data returned` (sometimes with a detail in parentheses), and for the gamma field `no usable gamma field` or `no spot price returned`. A ticker that failed for another cause says so: `api error: ...` (Polygon still failing after the retries, e.g. HTTP 429 or 5xx) or `error: <Exception>: ...` (a code error), so it is not mistaken for a ticker without options. `portfolio_risk_score_leverage` also reports `no price history returned` (that ticker leaves the whole analysis) and `no polygon api key`. Other scripts omit `warnings` when they have nothing to flag. Existing envelope fields are unchanged.

`load_portfolio` drops weights below `1e-6`, renormalizes the rest so the 6-decimal-place weights sum to 1, and returns those weights plus `portfolio_source`, `portfolio_run_ts` and `portfolio_optimizer`. `export_signals` writes `<script>.json` and `<script>_YYYYMMDDTHHMMSS.json` (America/Bogota). The write is atomic (`*.tmp` then `os.replace`). If the directory cannot be created or written, the script warns and continues. `NaN` / `±Inf` become JSON `null`; numpy and pandas values are converted.

Envelope:

```json
{
  "schema_version": 1,
  "script": "entry_signal_tool",
  "run_ts": "2026-10-05T16:40:12-05:00",
  "portfolio_source": "/workspace/pipeline/portfolio/portfolio_latest.json",
  "portfolio_run_ts": "2026-10-05T16:40:12-05:00",
  "portfolio_optimizer": "black_litterman",
  "weights_used": {"GLD": 0.5, "SLV": 0.5},
  "data": {}
}
```

`portfolio_source` is `"hardcoded_fallback"` when the file was not used. `fundamental_analysis` has no weights of its own: the fallback is an equal weight on `PORTFOLIO_TICKERS` (that list's order). A real file replaces the list with the file's tickers, heaviest first.

`data` by script:

- **`entry_signal_tool`** — buys only, highest conviction first. `entries[]`: `order`, `ticker`, `action` (`"BUY"`), `target_weight`, `tranche_weight` (today's slice of the portfolio), `signal` (`high_conviction` ≥ 75, `medium_conviction` 40–75, `low_conviction`, or `cycle_close` on a day-5 buy), `score`, `reason`. Tickers with no buy today are `waiting[]` (`ticker`, `score`, `reason`). Also `cycle_day`, `cycle`, and `excluded`.
- **`active_management`** — `rebalances[]`: `ticker`, `action` (`BUY` / `SELL` / `HOLD` from the sign of `target_weight - current_weight`; `CASH` is included, and `BUY` there means a larger cash reserve), `current_weight`, `target_weight`, `delta_weight`, `reason`, `tactical_action` (`AUMENTAR`, `RECORTAR`, `LIQUIDAR`, `MANTENER`, `RESERVA_TACTICA`). `regime` is `normal`, `insufficient_history`, `stress`, `diversification_collapse`, or `stress+diversification_collapse`. Also `regime_state`, `regime_alerts`, `vol_portfolio`, `diversification_ratio`, and `excluded`. `portfolio_risk_history.csv` stays an observation log of volatility and diversification. It is not an execution ledger and is not gated on fills.
- **`portfolio_risk_score_leverage`** — `target_leverage` and `risk_score` are the weight-weighted means of the per-asset leverage (2x–5x) and risk score (0–100). `components`: `score_weights` (`hv`, `cvar`, `iv`, `gex_pcr`), `leverage_min`, `leverage_max`, `portfolio_iv`, and `by_ticker[]` (`ticker`, `weight`, `risk_score`, `leverage`, `effective_exposure`, `hv`, `cvar`, `iv`, `gex_total`, `pcr_oi`). Also `excluded`.
- **`portfolio_gex_field`** — one file per refresh, including the single `--once` run. Scalars: `macro_y`, `potential_z`, `grad_x`, `grad_y`, `grad_magnitude`, `n_holdings`. `holdings[]`: `ticker`, `weight`, `price`, `expected_move`, `total_gex`, `regime`, `gamma_flip`, `call_wall`, `put_wall`. Also `excluded`.
- **`portfolio_vix`** — `vix_portfolio`, `sigma_portfolio_30d`, `source`, `vol_method`, `corr_method`, `metrics` (the engine scalars: `VIX_portfolio`, `sigma_portfolio_30d`, `VIX_medio_ponderado`, `ratio_diversificacion`, `beneficio_diversificacion_pts`, `correlacion_implicita_media`) and `holdings[]` (`ticker`, `weight`, `vix`, `sigma_30d`, `mcr`, `ctr`, `ctr_vix_pts`, `ctr_pct`). Also `excluded`. `--tickers` / `--weights` and `EQUAL_WEIGHTS` replace `weights_used`. When nothing can be valued, `vix_portfolio` is null and `holdings` is empty; the process still writes the signal.

- **`fundamental_analysis`** — `n_tickers`, `n_indicators` (12), `score_green_min` (9), `score_medium_min` (6). `holdings[]`: `ticker`, `score_quality`, `n_green`, `n_indicators`, `rating` (`Luz Verde Global`, `Calidad Media`, `Señal de Alerta Global`), `incomplete`, `metrics` (the scorecard numbers) and `signals` (the traffic-light column for each indicator).

### Entry state and fills

`entry_state.json` keeps the last **executed** book (`pct_ya_invertido`, cycle day, cycle). A signal run only records a pending block: `pending_signal_run_ts`, `pending_cycle_day`, `pending_cycle`, `pending_targets` (portfolio `target_weight` per buy), `pending_cash` (fraction of the target left in cash on a day-5 cash decision), `pending_decisions`.

The executor writes fills under `EXECUTIONS_DIR`. The reader uses `entry_signal_tool_fills.json` when that file exists, otherwise the newest `fills_*.json`. Only a document whose `signal_run_ts` equals `pending_signal_run_ts` advances the state. `filled_weight` is a portfolio weight, same units as `tranche_weight`; the invested fraction increases by `filled_weight / target_weight` (capped at 1) for `action: "BUY"` and `status` of `filled`, `partial`, or `partially_filled`. The fills `ticker` is the canonical portfolio ticker.

```json
{
  "schema_version": 1,
  "signal_run_ts": "2026-10-05T16:40:12-05:00",
  "executed_ts": "2026-10-05T16:55:00-05:00",
  "fills": [
    {
      "ticker": "GLD",
      "action": "BUY",
      "filled_weight": 0.06,
      "filled_qty": 10,
      "price": 180.0,
      "deal_id": "abc",
      "status": "filled"
    }
  ]
}
```

`ENTRY_INVESTED_PCT` / `--invested-pct` overrides the in-memory baseline for that run only (it is not written as an execution). A bare number is a percent 0–100 for every ticker. `GLD=40,KO=0.25` or a JSON object is per ticker: values above 1, or written with `%`, are percents; values in `[0, 1]` are fractions of that ticker's target.

HTML reports and the risk-history CSV are unchanged aside from the headless GEX path, which writes the same HTML shell and JSON once and does not open a browser. `entry_state.json` gains the pending-signal fields above; older files still load.

```bash
python -m unittest discover -s tests -t .
```

## Disclaimer

This code is for research and educational purposes only and does not constitute investment advice. The portfolios in the scripts are examples, and the scores, leverage levels and thresholds are heuristics that should be reviewed before any real use.
