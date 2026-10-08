# Graph Report - Portfolio-Manager  (2026-10-08)

## Corpus Check
- 20 files · ~51,449 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 3)

## Summary
- 691 nodes · 1756 edges · 32 communities (23 shown, 9 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 27 edges (avg confidence: 0.84)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e3742910`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- portfolio_risk_score_leverage.py
- fundamental_analysis.py
- test_pipeline_io.py
- portfolio_gex_field.py
- json
- apply_entry_fills
- Tactical active management engine
- test_review_fixes.py
- tickers.py
- portfolio_vix.py
- ndarray
- .load
- .__init__
- DataFrame
- .load
- gamma_flip_level
- CBOEVarianceEngine
- Working with the graphify knowledge graph
- Working with the graphify knowledge graph
- entry_signal_tool.py
- ExportSignalsTests
- test_signal_shapes.py
- pipeline_io.py
- PolygonClient
- test_international_fallback.py
- polygon_client.py
- FillsGatingTests
- .__init__
- VixWeightsArgsTests
- resolve_cycle_day
- StaggeredEntryTests

## God Nodes (most connected - your core abstractions)
1. `to_polygon()` - 31 edges
2. `resolve_instrument()` - 26 edges
3. `to_yahoo()` - 25 edges
4. `NoOptionData` - 20 edges
5. `run_active_management_engine()` - 20 edges
6. `failure_reason()` - 20 edges
7. `PolygonClient` - 19 edges
8. `gamma_flip_level()` - 17 edges
9. `_metricas_opciones()` - 17 edges
10. `export_signals()` - 17 edges

## Surprising Connections (you probably didn't know these)
- `PolygonError` --uses--> `PolygonBackoffTests`  [INFERRED]
  polygon_client.py → tests/test_cycle1_fixes.py
- `fake_chain()` --calls--> `NoOptionData`  [EXTRACTED]
  tests/test_international_fallback.py → polygon_client.py
- `NoOptionData` --uses--> `FailureReasonTests`  [INFERRED]
  polygon_client.py → tests/test_review_fixes.py
- `PolygonClient` --uses--> `PolygonBackoffTests`  [INFERRED]
  polygon_client.py → tests/test_cycle1_fixes.py
- `PolygonError` --uses--> `FailureReasonTests`  [INFERRED]
  polygon_client.py → tests/test_review_fixes.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Signal to fills to entry state loop** — readme_entry_signal_tool, readme_pipeline_signals, readme_entry_state_and_fills, readme_portfolio_file [EXTRACTED 1.00]
- **Polygon options-chain driven scripts** — readme_active_management, readme_entry_signal_tool, readme_risk_score_dynamic_leverage, readme_portfolio_vix, readme_portfolio_gex_field, readme_polygon_io [EXTRACTED 1.00]
- **Portfolio risk aggregation via correlation and Euler attribution** — readme_correlation_estimators, readme_euler_risk_attribution, readme_implied_correlation, readme_portfolio_vix, readme_active_management [INFERRED 0.75]

## Communities (32 total, 9 thin omitted)

### Community 0 - "portfolio_risk_score_leverage.py"
Cohesion: 0.05
Nodes (94): analyze_ticker_options(), apply_diversification_guardrail(), _assemble_regions(), benchmark_implied_sigma(), benchmark_implied_sigmas(), _bsm_d1_d2(), build_implied_correlation(), build_risk_inputs() (+86 more)

### Community 1 - "fundamental_analysis.py"
Cohesion: 0.08
Nodes (31): analizar_cartera(), calcular_corto_plazo(), _current_ratio(), calcular_historico(), calcular_info_adicional(), calcular_largo_plazo(), _roe_signal(), calcular_mediano_plazo() (+23 more)

### Community 3 - "portfolio_gex_field.py"
Cohesion: 0.06
Nodes (41): american_delta_gamma(), american_iv_bisection(), american_price(), _bs93_american_call(), _bs93_phi(), bs_price(), build_composite_portfolio_force(), _build_gex_force_function_sigma() (+33 more)

### Community 4 - "json"
Cohesion: 0.20
Nodes (7): executions_dir(), _fallback_result(), load_fills(), load_portfolio(), locate_fills_file(), _renormalize_weights(), _warn()

### Community 5 - "apply_entry_fills"
Cohesion: 0.29
Nodes (4): apply_entry_fills(), _as_float(), _blank_activo(), stage_pending_entry()

### Community 6 - "Tactical active management engine"
Cohesion: 0.08
Nodes (39): Portfolio Manager README, Tactical active management engine, CBOE VIX methodology (model-free variance), Concentration guardrail (1.5x equal-share risk), Cornish-Fisher VaR/ES and CVaR, Correlation estimators (sample, EWMA, random-matrix filtered), De-Americanization (Bjerksund-Stensland 1993 / CRR binomial), Research and educational disclaimer (+31 more)

### Community 7 - "test_review_fixes.py"
Cohesion: 0.16
Nodes (7): NoOptionData, PolygonError, PolygonNotFound, fake_chain(), EntryPercentileTests, FailureReasonTests, GexLiveShellTests

### Community 8 - "tickers.py"
Cohesion: 0.08
Nodes (24): get_current_price(), TickerMappingTests, ResolverTierTests, adr_warnings(), capital_epic_verified(), _class_parts(), _clean(), _env_float() (+16 more)

### Community 9 - "portfolio_vix.py"
Cohesion: 0.12
Nodes (13): guardar_estado(), bjerksund_stensland_call(), bjerksund_stensland_price(), bs_price(), crr_american(), _euro_call_carry(), implied_vol(), f() (+5 more)

### Community 11 - ".load"
Cohesion: 0.26
Nodes (4): clamp_iv(), PolygonMarketLoader, select_cboe_expiries(), year_fraction()

### Community 12 - ".__init__"
Cohesion: 0.23
Nodes (4): DeAmericanizer, OptionChainCleaner, PortfolioVIX, SingleAssetVIX

### Community 13 - "DataFrame"
Cohesion: 0.32
Nodes (3): PortfolioVIXCalculator, ReportPlotter, SmileFit

### Community 14 - ".load"
Cohesion: 0.21
Nodes (5): AssetMarketData, escrowed_inputs(), ExpirySlice, SyntheticMarketGenerator, YahooMarketLoader

### Community 15 - "gamma_flip_level"
Cohesion: 0.11
Nodes (6): gamma_flip_level(), ActiveManagementTests, GammaFlipTests, _load_active_management(), _load_functions(), RiskPriceHistoryTests

### Community 17 - "Working with the graphify knowledge graph"
Cohesion: 0.33
Nodes (5): Freshness check, Git hygiene, Navigating, Verify before asserting, Working with the graphify knowledge graph

### Community 18 - "Working with the graphify knowledge graph"
Cohesion: 0.33
Nodes (5): Freshness check, Git hygiene, Navigating, Verify before asserting, Working with the graphify knowledge graph

### Community 19 - "entry_signal_tool.py"
Cohesion: 0.06
Nodes (45): _activo_vacio(), calcular_espacio_walls(), calcular_expected_move(), calcular_fila_instrumento(), calcular_gex_y_zero_gamma(), calcular_indicadores_proxy(), calcular_indicadores_ticker(), calcular_iv_atm() (+37 more)

### Community 23 - "pipeline_io.py"
Cohesion: 0.20
Nodes (8): _atomic_write(), export_signals(), _flexible_fraction(), _is_nan(), _now_bogota(), parse_invested_overrides(), _percent_number(), to_jsonable()

### Community 24 - "PolygonClient"
Cohesion: 0.17
Nodes (5): PolygonClient, PolygonTruncated, PolygonBackoffTests, fake_get(), _Resp

### Community 25 - "test_international_fallback.py"
Cohesion: 0.17
Nodes (5): failure_reason(), _closes(), EntrySignalTierTests, _load_functions(), RiskScoreFallbackTests

### Community 26 - "polygon_client.py"
Cohesion: 0.18
Nodes (3): retry_after_seconds(), retry_backoff_seconds(), GexHeadlessTests

### Community 27 - "FillsGatingTests"
Cohesion: 0.33
Nodes (3): _estado(), _fills(), FillsGatingTests

### Community 28 - ".__init__"
Cohesion: 0.33
Nodes (3): calls_per_minute_configurado(), _limiter_for(), _RateLimiter

## Knowledge Gaps
- **21 isolated node(s):** `Freshness check`, `Git hygiene`, `Navigating`, `Verify before asserting`, `Freshness check` (+16 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 172 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `to_polygon()` connect `tickers.py` to `portfolio_risk_score_leverage.py`, `portfolio_gex_field.py`, `portfolio_vix.py`, `.load`, `entry_signal_tool.py`, `polygon_client.py`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **What connects `Freshness check`, `Git hygiene`, `Navigating` to the rest of the system?**
  _21 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `portfolio_risk_score_leverage.py` be split into smaller, more focused modules?**
  _Cohesion score 0.050458003415618694 - nodes in this community are weakly interconnected._
- **Why does `PolygonClient` connect `PolygonClient` to `portfolio_risk_score_leverage.py`, `portfolio_gex_field.py`, `portfolio_vix.py`, `entry_signal_tool.py`, `polygon_client.py`, `.__init__`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Should `fundamental_analysis.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07924984875983061 - nodes in this community are weakly interconnected._
- **Why does `to_yahoo()` connect `tickers.py` to `portfolio_risk_score_leverage.py`, `fundamental_analysis.py`, `portfolio_gex_field.py`, `portfolio_vix.py`, `.load`, `.load`, `entry_signal_tool.py`, `polygon_client.py`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Should `portfolio_gex_field.py` be split into smaller, more focused modules?**
  _Cohesion score 0.059227921734531994 - nodes in this community are weakly interconnected._