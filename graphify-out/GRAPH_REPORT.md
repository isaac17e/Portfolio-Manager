# Graph Report - Portfolio-Manager  (2026-10-06)

## Corpus Check
- Corpus is ~44,135 words - fits in a single context window. You may not need a graph.

## Summary
- 550 nodes · 1412 edges · 18 communities (15 shown, 3 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 21 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Covariance & Risk Estimators
- Fundamental Scorecard
- Pipeline IO Tests
- GEX & Macro Series
- Walls & Expected Move
- Polygon Options Analytics
- README: Scripts & Concepts
- Polygon Client
- Ticker Mapping & Headless Tests
- VIX & American Engine
- SVI & Correlation Fit
- Market Data Chain Loader
- Convexity Masks
- Reports & Plotting
- Community 14
- Community 15
- Community 16

## God Nodes (most connected - your core abstractions)
1. `to_polygon()` - 30 edges
2. `to_yahoo()` - 22 edges
3. `no_us_options_reason()` - 22 edges
4. `PolygonClient` - 20 edges
5. `run_active_management_engine()` - 18 edges
6. `calcular_indicadores_ticker()` - 17 edges
7. `correr_entry_signal()` - 17 edges
8. `export_signals()` - 17 edges
9. `run_options_module_for_ticker()` - 16 edges
10. `PolygonError` - 15 edges

## Surprising Connections (you probably didn't know these)
- `PolygonBackoffTests` --uses--> `PolygonError`  [INFERRED]
  tests/test_cycle1_fixes.py → polygon_client.py
- `PolygonBackoffTests` --uses--> `PolygonClient`  [INFERRED]
  tests/test_cycle1_fixes.py → polygon_client.py
- `polygon_get()` --uses--> `PolygonError`  [INFERRED]
  active_management.py → polygon_client.py
- `cargar_estado()` --indirect_call--> `f()`  [INFERRED]
  entry_signal_tool.py → portfolio_vix.py
- `guardar_estado()` --indirect_call--> `f()`  [INFERRED]
  entry_signal_tool.py → portfolio_vix.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Polygon options-chain driven scripts** — readme_active_management, readme_entry_signal_tool, readme_risk_score_dynamic_leverage, readme_portfolio_vix, readme_portfolio_gex_field, readme_polygon_io [EXTRACTED 1.00]
- **Portfolio risk aggregation via correlation and Euler attribution** — readme_correlation_estimators, readme_euler_risk_attribution, readme_implied_correlation, readme_portfolio_vix, readme_active_management [INFERRED 0.75]
- **Signal to fills to entry state loop** — readme_entry_signal_tool, readme_pipeline_signals, readme_entry_state_and_fills, readme_portfolio_file [EXTRACTED 1.00]

## Communities (18 total, 3 thin omitted)

### Community 0 - "Covariance & Risk Estimators"
Cohesion: 0.09
Nodes (59): analyze_ticker_options(), apply_diversification_guardrail(), _assemble_regions(), benchmark_implied_sigma(), benchmark_implied_sigmas(), _bsm_d1_d2(), build_implied_correlation(), build_risk_inputs() (+51 more)

### Community 1 - "Fundamental Scorecard"
Cohesion: 0.08
Nodes (31): analizar_cartera(), calcular_corto_plazo(), _current_ratio(), calcular_historico(), calcular_info_adicional(), calcular_largo_plazo(), _roe_signal(), calcular_mediano_plazo() (+23 more)

### Community 2 - "Pipeline IO Tests"
Cohesion: 0.05
Nodes (21): apply_entry_fills(), _as_float(), _blank_activo(), executions_dir(), _fallback_result(), _flexible_fraction(), _is_nan(), load_fills() (+13 more)

### Community 3 - "GEX & Macro Series"
Cohesion: 0.08
Nodes (40): _atomic_write(), export_signals(), american_delta_gamma(), american_iv_bisection(), american_price(), _bs93_american_call(), _bs93_phi(), bs_price() (+32 more)

### Community 4 - "Walls & Expected Move"
Cohesion: 0.08
Nodes (36): _activo_vacio(), calcular_espacio_walls(), calcular_expected_move(), calcular_gex_y_zero_gamma(), calcular_indicadores_ticker(), calcular_iv_atm(), calcular_skew(), calcular_smart_money() (+28 more)

### Community 5 - "Polygon Options Analytics"
Cohesion: 0.09
Nodes (34): PolygonNotFound, bs_gamma(), bs_price(), compute_atm_iv(), compute_corr_cov(), compute_expected_move(), compute_gex_pcr_factor(), compute_gex_profile() (+26 more)

### Community 6 - "README: Scripts & Concepts"
Cohesion: 0.08
Nodes (39): Portfolio Manager README, Tactical active management engine, CBOE VIX methodology (model-free variance), Concentration guardrail (1.5x equal-share risk), Cornish-Fisher VaR/ES and CVaR, Correlation estimators (sample, EWMA, random-matrix filtered), De-Americanization (Bjerksund-Stensland 1993 / CRR binomial), Research and educational disclaimer (+31 more)

### Community 7 - "Polygon Client"
Cohesion: 0.09
Nodes (11): calls_per_minute_configurado(), _limiter_for(), PolygonClient, PolygonError, PolygonTruncated, _RateLimiter, retry_after_seconds(), retry_backoff_seconds() (+3 more)

### Community 8 - "Ticker Mapping & Headless Tests"
Cohesion: 0.13
Nodes (17): get_current_price(), GexHeadlessTests, TickerMappingTests, capital_epic_verified(), _class_parts(), _clean(), exchange_suffix(), _format_class() (+9 more)

### Community 9 - "VIX & American Engine"
Cohesion: 0.13
Nodes (12): bjerksund_stensland_call(), bjerksund_stensland_price(), bs_price(), crr_american(), _euro_call_carry(), implied_vol(), f(), _parse_args() (+4 more)

### Community 11 - "Market Data Chain Loader"
Cohesion: 0.26
Nodes (4): clamp_iv(), PolygonMarketLoader, select_cboe_expiries(), year_fraction()

### Community 12 - "Convexity Masks"
Cohesion: 0.21
Nodes (4): DeAmericanizer, OptionChainCleaner, PortfolioVIX, SingleAssetVIX

### Community 13 - "Reports & Plotting"
Cohesion: 0.32
Nodes (3): PortfolioVIXCalculator, ReportPlotter, SmileFit

### Community 14 - "Community 14"
Cohesion: 0.21
Nodes (5): AssetMarketData, escrowed_inputs(), ExpirySlice, SyntheticMarketGenerator, YahooMarketLoader

### Community 15 - "Community 15"
Cohesion: 0.33
Nodes (3): _estado(), _fills(), FillsGatingTests

## Knowledge Gaps
- **13 isolated node(s):** `Vanna and Charm exposure`, `Options order flow (unusual activity, sweeps, put/call ratio)`, `Risk regime history (portfolio_risk_history.csv)`, `CBOE VIX methodology (model-free variance)`, `SVI volatility smile (Gatheral)` (+8 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 122 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `to_polygon()` connect `Ticker Mapping & Headless Tests` to `Covariance & Risk Estimators`, `GEX & Macro Series`, `Walls & Expected Move`, `Polygon Options Analytics`, `VIX & American Engine`, `Market Data Chain Loader`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **What connects `Vanna and Charm exposure`, `Options order flow (unusual activity, sweeps, put/call ratio)`, `Risk regime history (portfolio_risk_history.csv)` to the rest of the system?**
  _13 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Covariance & Risk Estimators` be split into smaller, more focused modules?**
  _Cohesion score 0.08779631255487269 - nodes in this community are weakly interconnected._
- **Why does `PolygonClient` connect `Polygon Client` to `Covariance & Risk Estimators`, `GEX & Macro Series`, `Walls & Expected Move`, `Polygon Options Analytics`, `Ticker Mapping & Headless Tests`, `VIX & American Engine`, `Market Data Chain Loader`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Should `Fundamental Scorecard` be split into smaller, more focused modules?**
  _Cohesion score 0.07924984875983061 - nodes in this community are weakly interconnected._
- **Why does `no_us_options_reason()` connect `Ticker Mapping & Headless Tests` to `Covariance & Risk Estimators`, `GEX & Macro Series`, `Walls & Expected Move`, `Polygon Options Analytics`, `VIX & American Engine`, `Market Data Chain Loader`, `Reports & Plotting`, `Community 14`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Should `Pipeline IO Tests` be split into smaller, more focused modules?**
  _Cohesion score 0.053246753246753244 - nodes in this community are weakly interconnected._