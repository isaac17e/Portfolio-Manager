# Graph Report - Portfolio-Manager  (2026-10-08)

## Corpus Check
- 18 files · ~46,646 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 3)

## Summary
- 607 nodes · 1556 edges · 29 communities (23 shown, 6 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 31 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8ec6588e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- active_management.py
- fundamental_analysis.py
- test_pipeline_io.py
- portfolio_gex_field.py
- export_signals
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
- gamma_flip_level
- CBOEVarianceEngine
- Working with the graphify knowledge graph
- Working with the graphify knowledge graph
- entry_signal_tool.py
- test_review_fixes.py
- correr_entry_signal
- test_signal_shapes.py
- pipeline_io.py
- NoOptionData
- PolygonClient
- ActiveManagementTests
- VixWeightsArgsTests
- resolve_cycle_day

## God Nodes (most connected - your core abstractions)
1. `to_polygon()` - 30 edges
2. `no_us_options_reason()` - 22 edges
3. `to_yahoo()` - 22 edges
4. `NoOptionData` - 21 edges
5. `PolygonClient` - 20 edges
6. `PolygonError` - 19 edges
7. `run_active_management_engine()` - 19 edges
8. `correr_entry_signal()` - 19 edges
9. `failure_reason()` - 18 edges
10. `gamma_flip_level()` - 17 edges

## Surprising Connections (you probably didn't know these)
- `PolygonError` --uses--> `PolygonBackoffTests`  [INFERRED]
  polygon_client.py → tests/test_cycle1_fixes.py
- `NoOptionData` --uses--> `FailureReasonTests`  [INFERRED]
  polygon_client.py → tests/test_review_fixes.py
- `PolygonError` --uses--> `FailureReasonTests`  [INFERRED]
  polygon_client.py → tests/test_review_fixes.py
- `PolygonNotFound` --uses--> `FailureReasonTests`  [INFERRED]
  polygon_client.py → tests/test_review_fixes.py
- `PolygonClient` --uses--> `PolygonBackoffTests`  [INFERRED]
  polygon_client.py → tests/test_cycle1_fixes.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Signal to fills to entry state loop** — readme_entry_signal_tool, readme_pipeline_signals, readme_entry_state_and_fills, readme_portfolio_file [EXTRACTED 1.00]
- **Polygon options-chain driven scripts** — readme_active_management, readme_entry_signal_tool, readme_risk_score_dynamic_leverage, readme_portfolio_vix, readme_portfolio_gex_field, readme_polygon_io [EXTRACTED 1.00]
- **Portfolio risk aggregation via correlation and Euler attribution** — readme_correlation_estimators, readme_euler_risk_attribution, readme_implied_correlation, readme_portfolio_vix, readme_active_management [INFERRED 0.75]

## Communities (29 total, 6 thin omitted)

### Community 0 - "active_management.py"
Cohesion: 0.10
Nodes (51): analyze_ticker_options(), apply_diversification_guardrail(), _assemble_regions(), benchmark_implied_sigma(), benchmark_implied_sigmas(), _bsm_d1_d2(), build_implied_correlation(), build_risk_inputs() (+43 more)

### Community 1 - "fundamental_analysis.py"
Cohesion: 0.08
Nodes (31): analizar_cartera(), calcular_corto_plazo(), _current_ratio(), calcular_historico(), calcular_info_adicional(), calcular_largo_plazo(), _roe_signal(), calcular_mediano_plazo() (+23 more)

### Community 2 - "test_pipeline_io.py"
Cohesion: 0.12
Nodes (3): ExportSignalsTests, LoadPortfolioTests, _portfolio()

### Community 3 - "portfolio_gex_field.py"
Cohesion: 0.08
Nodes (41): failure_reason(), american_delta_gamma(), american_iv_bisection(), american_price(), _bs93_american_call(), _bs93_phi(), bs_price(), build_composite_portfolio_force() (+33 more)

### Community 4 - "export_signals"
Cohesion: 0.14
Nodes (11): _atomic_write(), executions_dir(), export_signals(), _fallback_result(), _is_nan(), load_fills(), load_portfolio(), locate_fills_file() (+3 more)

### Community 5 - "portfolio_risk_score_leverage.py"
Cohesion: 0.09
Nodes (40): bs_gamma(), bs_price(), compute_atm_iv(), compute_corr_cov(), compute_expected_move(), compute_gex_pcr_factor(), compute_gex_profile(), compute_max_drawdown() (+32 more)

### Community 6 - "Tactical active management engine"
Cohesion: 0.08
Nodes (39): Portfolio Manager README, Tactical active management engine, CBOE VIX methodology (model-free variance), Concentration guardrail (1.5x equal-share risk), Cornish-Fisher VaR/ES and CVaR, Correlation estimators (sample, EWMA, random-matrix filtered), De-Americanization (Bjerksund-Stensland 1993 / CRR binomial), Research and educational disclaimer (+31 more)

### Community 7 - "polygon_client.py"
Cohesion: 0.14
Nodes (6): calls_per_minute_configurado(), _limiter_for(), PolygonTruncated, _RateLimiter, retry_after_seconds(), retry_backoff_seconds()

### Community 8 - "to_polygon"
Cohesion: 0.11
Nodes (18): _estado(), _fills(), FillsGatingTests, TickerMappingTests, capital_epic_verified(), _class_parts(), _clean(), exchange_suffix() (+10 more)

### Community 9 - "portfolio_vix.py"
Cohesion: 0.14
Nodes (12): bjerksund_stensland_call(), bjerksund_stensland_price(), bs_price(), crr_american(), _euro_call_carry(), implied_vol(), f(), _parse_args() (+4 more)

### Community 11 - "PolygonMarketLoader"
Cohesion: 0.27
Nodes (3): clamp_iv(), escrowed_inputs(), PolygonMarketLoader

### Community 12 - ".__init__"
Cohesion: 0.17
Nodes (4): DeAmericanizer, OptionChainCleaner, PortfolioVIX, SingleAssetVIX

### Community 13 - "DataFrame"
Cohesion: 0.32
Nodes (3): PortfolioVIXCalculator, ReportPlotter, SmileFit

### Community 14 - ".load"
Cohesion: 0.21
Nodes (6): AssetMarketData, ExpirySlice, select_cboe_expiries(), SyntheticMarketGenerator, YahooMarketLoader, year_fraction()

### Community 15 - "gamma_flip_level"
Cohesion: 0.23
Nodes (3): gamma_flip_level(), compute_zero_gamma_level(), GammaFlipTests

### Community 17 - "Working with the graphify knowledge graph"
Cohesion: 0.33
Nodes (5): Freshness check, Git hygiene, Navigating, Verify before asserting, Working with the graphify knowledge graph

### Community 18 - "Working with the graphify knowledge graph"
Cohesion: 0.33
Nodes (5): Freshness check, Git hygiene, Navigating, Verify before asserting, Working with the graphify knowledge graph

### Community 19 - "entry_signal_tool.py"
Cohesion: 0.16
Nodes (23): calcular_espacio_walls(), calcular_expected_move(), calcular_gex_y_zero_gamma(), calcular_indicadores_ticker(), calcular_iv_atm(), calcular_skew(), calcular_smart_money(), calcular_vanna_charm_factor() (+15 more)

### Community 20 - "test_review_fixes.py"
Cohesion: 0.13
Nodes (6): DividendYieldTests, EntryPercentileTests, GexLiveShellTests, _load_functions(), RiskPriceHistoryTests, dividend_yield_from_info()

### Community 21 - "correr_entry_signal"
Cohesion: 0.24
Nodes (9): _activo_vacio(), cargar_estado(), cargar_historial(), _contexto(), correr_entry_signal(), _estado_vacio(), evaluar_flujo_opciones(), normalizar_estado() (+1 more)

### Community 23 - "pipeline_io.py"
Cohesion: 0.18
Nodes (8): apply_entry_fills(), _as_float(), _blank_activo(), _flexible_fraction(), _now_bogota(), parse_invested_overrides(), _percent_number(), stage_pending_entry()

### Community 24 - "NoOptionData"
Cohesion: 0.36
Nodes (4): NoOptionData, PolygonError, PolygonNotFound, FailureReasonTests

### Community 26 - "PolygonClient"
Cohesion: 0.20
Nodes (4): PolygonClient, PolygonBackoffTests, fake_get(), _Resp

## Knowledge Gaps
- **21 isolated node(s):** `Navigating`, `Verify before asserting`, `Freshness check`, `Git hygiene`, `Navigating` (+16 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 141 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `to_polygon()` connect `to_polygon` to `active_management.py`, `portfolio_gex_field.py`, `portfolio_risk_score_leverage.py`, `portfolio_vix.py`, `PolygonMarketLoader`, `entry_signal_tool.py`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **What connects `Navigating`, `Verify before asserting`, `Freshness check` to the rest of the system?**
  _21 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `active_management.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10225988700564972 - nodes in this community are weakly interconnected._
- **Why does `PolygonClient` connect `PolygonClient` to `active_management.py`, `portfolio_gex_field.py`, `portfolio_risk_score_leverage.py`, `polygon_client.py`, `to_polygon`, `portfolio_vix.py`, `PolygonMarketLoader`, `.__init__`, `entry_signal_tool.py`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Should `fundamental_analysis.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0771478667445938 - nodes in this community are weakly interconnected._
- **Why does `to_yahoo()` connect `to_polygon` to `fundamental_analysis.py`, `portfolio_gex_field.py`, `portfolio_risk_score_leverage.py`, `portfolio_vix.py`, `PolygonMarketLoader`, `.load`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Should `test_pipeline_io.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12418300653594772 - nodes in this community are weakly interconnected._