# Graph Report - Portfolio-Manager  (2026-10-07)

## Corpus Check
- 17 files · ~46,222 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 3)

## Summary
- 598 nodes · 1547 edges · 31 communities (22 shown, 9 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 31 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `26abb0f3`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- active_management.py
- fundamental_analysis.py
- test_cycle1_fixes.py
- portfolio_gex_field.py
- pipeline_io.py
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
- entry_signal_tool.py
- test_review_fixes.py
- correr_entry_signal
- test_signal_shapes.py
- json
- NoOptionData
- PolygonClient
- PolygonBackoffTests
- ActiveManagementTests
- LoadPortfolioTests
- VixWeightsArgsTests
- resolve_cycle_day

## God Nodes (most connected - your core abstractions)
1. `to_polygon()` - 30 edges
2. `to_yahoo()` - 22 edges
3. `no_us_options_reason()` - 22 edges
4. `NoOptionData` - 21 edges
5. `PolygonClient` - 20 edges
6. `run_active_management_engine()` - 19 edges
7. `correr_entry_signal()` - 19 edges
8. `PolygonError` - 19 edges
9. `failure_reason()` - 18 edges
10. `calcular_indicadores_ticker()` - 17 edges

## Surprising Connections (you probably didn't know these)
- `PolygonBackoffTests` --uses--> `PolygonError`  [INFERRED]
  tests/test_cycle1_fixes.py → polygon_client.py
- `PolygonBackoffTests` --uses--> `PolygonClient`  [INFERRED]
  tests/test_cycle1_fixes.py → polygon_client.py
- `FailureReasonTests` --uses--> `PolygonError`  [INFERRED]
  tests/test_review_fixes.py → polygon_client.py
- `FailureReasonTests` --uses--> `PolygonNotFound`  [INFERRED]
  tests/test_review_fixes.py → polygon_client.py
- `FailureReasonTests` --uses--> `NoOptionData`  [INFERRED]
  tests/test_review_fixes.py → polygon_client.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Signal to fills to entry state loop** — readme_entry_signal_tool, readme_pipeline_signals, readme_entry_state_and_fills, readme_portfolio_file [EXTRACTED 1.00]
- **Polygon options-chain driven scripts** — readme_active_management, readme_entry_signal_tool, readme_risk_score_dynamic_leverage, readme_portfolio_vix, readme_portfolio_gex_field, readme_polygon_io [EXTRACTED 1.00]
- **Portfolio risk aggregation via correlation and Euler attribution** — readme_correlation_estimators, readme_euler_risk_attribution, readme_implied_correlation, readme_portfolio_vix, readme_active_management [INFERRED 0.75]

## Communities (31 total, 9 thin omitted)

### Community 0 - "active_management.py"
Cohesion: 0.08
Nodes (52): analyze_ticker_options(), apply_diversification_guardrail(), _assemble_regions(), benchmark_implied_sigma(), benchmark_implied_sigmas(), _bsm_d1_d2(), build_implied_correlation(), build_risk_inputs() (+44 more)

### Community 1 - "fundamental_analysis.py"
Cohesion: 0.08
Nodes (31): analizar_cartera(), calcular_corto_plazo(), _current_ratio(), calcular_historico(), calcular_info_adicional(), calcular_largo_plazo(), _roe_signal(), calcular_mediano_plazo() (+23 more)

### Community 2 - "test_cycle1_fixes.py"
Cohesion: 0.12
Nodes (3): _now_bogota(), GexHeadlessTests, ExportSignalsTests

### Community 3 - "portfolio_gex_field.py"
Cohesion: 0.07
Nodes (40): failure_reason(), american_delta_gamma(), american_iv_bisection(), american_price(), _bs93_american_call(), _bs93_phi(), bs_price(), build_composite_portfolio_force() (+32 more)

### Community 4 - "pipeline_io.py"
Cohesion: 0.14
Nodes (13): apply_entry_fills(), _as_float(), _atomic_write(), _blank_activo(), executions_dir(), export_signals(), _fallback_result(), _is_nan() (+5 more)

### Community 5 - "portfolio_risk_score_leverage.py"
Cohesion: 0.10
Nodes (42): bs_gamma(), bs_price(), compute_atm_iv(), compute_corr_cov(), compute_expected_move(), compute_gex_pcr_factor(), compute_gex_profile(), compute_max_drawdown() (+34 more)

### Community 6 - "Tactical active management engine"
Cohesion: 0.08
Nodes (39): Portfolio Manager README, Tactical active management engine, CBOE VIX methodology (model-free variance), Concentration guardrail (1.5x equal-share risk), Cornish-Fisher VaR/ES and CVaR, Correlation estimators (sample, EWMA, random-matrix filtered), De-Americanization (Bjerksund-Stensland 1993 / CRR binomial), Research and educational disclaimer (+31 more)

### Community 7 - "polygon_client.py"
Cohesion: 0.16
Nodes (5): calls_per_minute_configurado(), _limiter_for(), _RateLimiter, retry_after_seconds(), retry_backoff_seconds()

### Community 8 - "to_polygon"
Cohesion: 0.15
Nodes (16): get_current_price(), TickerMappingTests, capital_epic_verified(), _class_parts(), _clean(), exchange_suffix(), _format_class(), has_us_options() (+8 more)

### Community 9 - "portfolio_vix.py"
Cohesion: 0.12
Nodes (13): guardar_estado(), bjerksund_stensland_call(), bjerksund_stensland_price(), bs_price(), clamp_iv(), crr_american(), _euro_call_carry(), implied_vol() (+5 more)

### Community 11 - "PolygonMarketLoader"
Cohesion: 0.27
Nodes (4): escrowed_inputs(), PolygonMarketLoader, select_cboe_expiries(), year_fraction()

### Community 12 - ".__init__"
Cohesion: 0.21
Nodes (4): DeAmericanizer, OptionChainCleaner, PortfolioVIX, VIXConfig

### Community 13 - "DataFrame"
Cohesion: 0.32
Nodes (3): PortfolioVIXCalculator, ReportPlotter, SmileFit

### Community 14 - ".load"
Cohesion: 0.21
Nodes (5): AssetMarketData, ExpirySlice, SingleAssetVIX, SyntheticMarketGenerator, YahooMarketLoader

### Community 15 - "FillsGatingTests"
Cohesion: 0.33
Nodes (3): _estado(), _fills(), FillsGatingTests

### Community 19 - "entry_signal_tool.py"
Cohesion: 0.16
Nodes (22): calcular_espacio_walls(), calcular_expected_move(), calcular_gex_y_zero_gamma(), calcular_indicadores_ticker(), calcular_iv_atm(), calcular_skew(), calcular_smart_money(), calcular_vanna_charm_factor() (+14 more)

### Community 20 - "test_review_fixes.py"
Cohesion: 0.18
Nodes (4): EntryPercentileTests, GexLiveShellTests, _load_functions(), RiskPriceHistoryTests

### Community 21 - "correr_entry_signal"
Cohesion: 0.24
Nodes (9): _activo_vacio(), cargar_estado(), cargar_historial(), _contexto(), correr_entry_signal(), _estado_vacio(), evaluar_flujo_opciones(), normalizar_estado() (+1 more)

### Community 23 - "json"
Cohesion: 0.22
Nodes (5): _flexible_fraction(), load_portfolio(), parse_invested_overrides(), _percent_number(), _renormalize_weights()

### Community 24 - "NoOptionData"
Cohesion: 0.36
Nodes (4): NoOptionData, PolygonError, PolygonNotFound, FailureReasonTests

### Community 25 - "PolygonClient"
Cohesion: 0.31
Nodes (3): PolygonClient, PolygonTruncated, polygon()

### Community 26 - "PolygonBackoffTests"
Cohesion: 0.28
Nodes (3): PolygonBackoffTests, fake_get(), _Resp

## Knowledge Gaps
- **14 isolated node(s):** `graphify`, `CBOE VIX methodology (model-free variance)`, `Cornish-Fisher VaR/ES and CVaR`, `Research and educational disclaimer`, `Excluded tickers and warnings (no US-listed options)` (+9 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 134 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `to_polygon()` connect `to_polygon` to `active_management.py`, `test_cycle1_fixes.py`, `portfolio_gex_field.py`, `portfolio_risk_score_leverage.py`, `portfolio_vix.py`, `PolygonMarketLoader`, `entry_signal_tool.py`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **What connects `graphify`, `CBOE VIX methodology (model-free variance)`, `Cornish-Fisher VaR/ES and CVaR` to the rest of the system?**
  _14 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `active_management.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07502131287297528 - nodes in this community are weakly interconnected._
- **Why does `PolygonClient` connect `PolygonClient` to `active_management.py`, `test_cycle1_fixes.py`, `portfolio_gex_field.py`, `portfolio_risk_score_leverage.py`, `polygon_client.py`, `portfolio_vix.py`, `PolygonMarketLoader`, `entry_signal_tool.py`, `PolygonBackoffTests`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Should `fundamental_analysis.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07924984875983061 - nodes in this community are weakly interconnected._
- **Why does `to_yahoo()` connect `to_polygon` to `fundamental_analysis.py`, `test_cycle1_fixes.py`, `portfolio_gex_field.py`, `portfolio_risk_score_leverage.py`, `portfolio_vix.py`, `PolygonMarketLoader`, `.load`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Should `test_cycle1_fixes.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11578947368421053 - nodes in this community are weakly interconnected._