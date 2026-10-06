# Graph Report - Portfolio-Manager  (2026-10-06)

## Corpus Check
- 16 files · ~44,283 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 3)

## Summary
- 552 nodes · 1413 edges · 19 communities (14 shown, 5 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 21 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e6272227`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- active_management.py
- fundamental_analysis.py
- test_pipeline_io.py
- portfolio_gex_field.py
- entry_signal_tool.py
- portfolio_risk_score_leverage.py
- Tactical active management engine
- polygon_client.py
- to_polygon
- portfolio_vix.py
- ndarray
- PolygonMarketLoader
- .__init__
- DataFrame
- .load
- FillsGatingTests
- CBOEVarianceEngine
- CLAUDE.md

## God Nodes (most connected - your core abstractions)
1. `to_polygon()` - 30 edges
2. `no_us_options_reason()` - 22 edges
3. `to_yahoo()` - 22 edges
4. `PolygonClient` - 20 edges
5. `run_active_management_engine()` - 18 edges
6. `export_signals()` - 17 edges
7. `calcular_indicadores_ticker()` - 17 edges
8. `correr_entry_signal()` - 17 edges
9. `run_options_module_for_ticker()` - 16 edges
10. `PolygonError` - 15 edges

## Surprising Connections (you probably didn't know these)
- `PolygonBackoffTests` --uses--> `PolygonClient`  [INFERRED]
  tests/test_cycle1_fixes.py → polygon_client.py
- `PolygonBackoffTests` --uses--> `PolygonError`  [INFERRED]
  tests/test_cycle1_fixes.py → polygon_client.py
- `PolygonMarketLoader` --uses--> `PolygonClient`  [INFERRED]
  portfolio_vix.py → polygon_client.py
- `polygon_get()` --uses--> `PolygonError`  [INFERRED]
  active_management.py → polygon_client.py
- `get_polygon_options_data()` --uses--> `PolygonError`  [INFERRED]
  portfolio_gex_field.py → polygon_client.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Signal to fills to entry state loop** — readme_entry_signal_tool, readme_pipeline_signals, readme_entry_state_and_fills, readme_portfolio_file [EXTRACTED 1.00]
- **Polygon options-chain driven scripts** — readme_active_management, readme_entry_signal_tool, readme_risk_score_dynamic_leverage, readme_portfolio_vix, readme_portfolio_gex_field, readme_polygon_io [EXTRACTED 1.00]
- **Portfolio risk aggregation via correlation and Euler attribution** — readme_correlation_estimators, readme_euler_risk_attribution, readme_implied_correlation, readme_portfolio_vix, readme_active_management [INFERRED 0.75]

## Communities (19 total, 5 thin omitted)

### Community 0 - "active_management.py"
Cohesion: 0.10
Nodes (50): analyze_ticker_options(), apply_diversification_guardrail(), _assemble_regions(), benchmark_implied_sigma(), benchmark_implied_sigmas(), _bsm_d1_d2(), build_implied_correlation(), build_risk_inputs() (+42 more)

### Community 1 - "fundamental_analysis.py"
Cohesion: 0.08
Nodes (31): analizar_cartera(), calcular_corto_plazo(), _current_ratio(), calcular_historico(), calcular_info_adicional(), calcular_largo_plazo(), _roe_signal(), calcular_mediano_plazo() (+23 more)

### Community 2 - "test_pipeline_io.py"
Cohesion: 0.08
Nodes (5): ExportSignalsTests, LoadPortfolioTests, _portfolio(), _load_function(), SignalShapeTests

### Community 3 - "portfolio_gex_field.py"
Cohesion: 0.09
Nodes (38): american_delta_gamma(), american_iv_bisection(), american_price(), _bs93_american_call(), _bs93_phi(), bs_price(), build_composite_portfolio_force(), _build_gex_force_function_sigma() (+30 more)

### Community 4 - "entry_signal_tool.py"
Cohesion: 0.05
Nodes (54): _activo_vacio(), calcular_espacio_walls(), calcular_expected_move(), calcular_gex_y_zero_gamma(), calcular_indicadores_ticker(), calcular_iv_atm(), calcular_skew(), calcular_smart_money() (+46 more)

### Community 5 - "portfolio_risk_score_leverage.py"
Cohesion: 0.08
Nodes (43): PolygonNotFound, bs_gamma(), bs_price(), compute_atm_iv(), compute_corr_cov(), compute_expected_move(), compute_gex_pcr_factor(), compute_gex_profile() (+35 more)

### Community 6 - "Tactical active management engine"
Cohesion: 0.08
Nodes (39): Portfolio Manager README, Tactical active management engine, CBOE VIX methodology (model-free variance), Concentration guardrail (1.5x equal-share risk), Cornish-Fisher VaR/ES and CVaR, Correlation estimators (sample, EWMA, random-matrix filtered), De-Americanization (Bjerksund-Stensland 1993 / CRR binomial), Research and educational disclaimer (+31 more)

### Community 7 - "polygon_client.py"
Cohesion: 0.09
Nodes (11): calls_per_minute_configurado(), _limiter_for(), PolygonClient, PolygonError, PolygonTruncated, _RateLimiter, retry_after_seconds(), retry_backoff_seconds() (+3 more)

### Community 8 - "to_polygon"
Cohesion: 0.13
Nodes (17): get_current_price(), GexHeadlessTests, TickerMappingTests, capital_epic_verified(), _class_parts(), _clean(), exchange_suffix(), _format_class() (+9 more)

### Community 9 - "portfolio_vix.py"
Cohesion: 0.12
Nodes (11): bjerksund_stensland_call(), bjerksund_stensland_price(), bs_price(), crr_american(), _euro_call_carry(), implied_vol(), f(), _parse_args() (+3 more)

### Community 12 - ".__init__"
Cohesion: 0.17
Nodes (6): DeAmericanizer, escrowed_inputs(), OptionChainCleaner, PortfolioVIX, SingleAssetVIX, VIXConfig

### Community 13 - "DataFrame"
Cohesion: 0.32
Nodes (3): PortfolioVIXCalculator, ReportPlotter, SmileFit

### Community 14 - ".load"
Cohesion: 0.21
Nodes (6): AssetMarketData, ExpirySlice, select_cboe_expiries(), SyntheticMarketGenerator, YahooMarketLoader, year_fraction()

### Community 15 - "FillsGatingTests"
Cohesion: 0.33
Nodes (3): _estado(), _fills(), FillsGatingTests

## Knowledge Gaps
- **14 isolated node(s):** `graphify`, `CBOE VIX methodology (model-free variance)`, `Cornish-Fisher VaR/ES and CVaR`, `Research and educational disclaimer`, `Excluded tickers and warnings (no US-listed options)` (+9 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 124 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `to_polygon()` connect `to_polygon` to `active_management.py`, `portfolio_gex_field.py`, `entry_signal_tool.py`, `portfolio_risk_score_leverage.py`, `portfolio_vix.py`, `PolygonMarketLoader`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **What connects `graphify`, `CBOE VIX methodology (model-free variance)`, `Cornish-Fisher VaR/ES and CVaR` to the rest of the system?**
  _14 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `active_management.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10461718293395675 - nodes in this community are weakly interconnected._
- **Why does `PolygonClient` connect `polygon_client.py` to `active_management.py`, `portfolio_gex_field.py`, `entry_signal_tool.py`, `portfolio_risk_score_leverage.py`, `to_polygon`, `portfolio_vix.py`, `PolygonMarketLoader`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Should `fundamental_analysis.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07514124293785311 - nodes in this community are weakly interconnected._
- **Why does `no_us_options_reason()` connect `to_polygon` to `active_management.py`, `portfolio_gex_field.py`, `entry_signal_tool.py`, `portfolio_risk_score_leverage.py`, `portfolio_vix.py`, `PolygonMarketLoader`, `DataFrame`, `.load`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Should `test_pipeline_io.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08465608465608465 - nodes in this community are weakly interconnected._