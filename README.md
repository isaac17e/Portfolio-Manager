# Portfolio Manager

A set of standalone Python scripts for **managing an existing equity/ETF portfolio**: tactical rebalancing from options market microstructure, staged entry signals, risk scoring with dynamic leverage, a portfolio-level implied volatility index, a 3D gamma "force field" and fundamental screening.

Most scripts take a portfolio as a `ticker: weight` dictionary at the top of the file and use the **Polygon.io** options chain as their main input. Price history and fundamentals come from Polygon or **Yahoo Finance** (`yfinance`).

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

1. **Options data** (Polygon v3): spot price, the expiration closest to the investment horizon (30 days by default) and the full chain snapshot.
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

4. **Portfolio risk layer**:
   - volatility from ATM implied volatility (historical as fallback);
   - **implied correlation** solved from the dispersion equation against a benchmark ETF (SPY globally, DBC for the commodities block), keeping the shape of the historical correlation (sample, EWMA or random-matrix filtered);
   - **Euler risk attribution** (contribution to total risk per asset);
   - a **concentration guardrail** that shifts weight away from any asset whose risk contribution exceeds 1.5× the equal-share level.
5. **Rebalancing**: freed capital goes to cash up to a 30% cap, and the rest is distributed among "Increase" names in proportion to their score.
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

The script runs as an interactive **5-business-day cycle**. It asks for the cycle day and current weights, and keeps state between runs in `entry_state.json` and `entry_signal_history.csv`. On day 5 it decides the unfilled fraction: it buys the remaining 100% if the accumulated options flow is favorable (smart money and distance to zero gamma), or leaves it in cash.

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

Data comes from Polygon, with Yahoo Finance or synthetic data as fallbacks. It has a CLI:

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

It runs in a loop, refreshing every 60 seconds. It serves the page from a local HTTP server (`portfolio_gex_field.html` + JSON data), updating the chart without a full reload and keeping the camera position.

## `fundamental_analysis.py` — Fundamental scorecard

Uses Yahoo Finance financial statements to grade each ticker as green / neutral / alert on 12 indicators across three horizons:

| Horizon | Indicators |
|---|---|
| Short term | Current ratio, EV/EBITDA, trailing → forward P/E, earnings surprise |
| Medium term | Net debt/EBITDA, interest coverage, FCF yield, PEG ratio |
| Long term | ROCE, ROIC, ROE (penalized when driven by high leverage), reinvestment rate |

The number of green signals gives a global rating: **Global Green Light** (≥ 9), **Medium Quality** (≥ 6) or **Global Alert**. All thresholds are editable in the `UMBRALES` dictionary.

**Output**: `reporte_fundamental.html`, with summary cards, a signal matrix and charts of the last 4 fiscal years and 5 quarters.

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
python entry_signal_tool.py
python portfolio_risk_score_leverage.py
python portfolio_vix.py
python portfolio_gex_field.py         # stop with Ctrl+C
python fundamental_analysis.py
```

Several scripts space out their Polygon calls (about 13 seconds apart) to respect the 5 requests/minute limit of the free Stocks tier, so a large portfolio can take a few minutes.

## Disclaimer

This code is for research and educational purposes only and does not constitute investment advice. The portfolios in the scripts are examples, and the scores, leverage levels and thresholds are heuristics that should be reviewed before any real use.
