# Graph Report - Portfolio-Manager  (2026-10-08)

## Corpus Check
- 22 files · ~57,118 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 3)

## Summary
- 799 nodes · 2025 edges · 42 communities (27 shown, 15 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 28 edges (avg confidence: 0.84)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `de21b47d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- portfolio_risk_score_leverage.py
- fundamental_analysis.py
- portfolio_gex_field.py
- run_cycle.py
- main
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
- _load_function
- pipeline_io.py
- PolygonBackoffTests
- _closes
- polygon_client.py
- FillsGatingTests
- .invoke
- VixWeightsArgsTests
- resolve_cycle_day
- StaggeredEntryTests
- price_signals.py
- correr_entry_signal
- calcular_indicadores_proxy
- ActiveManagementTests
- implied_vol
- PolygonClient
- dividend_yield_from_info
- LoadPortfolioTests
- ._namespace
- GexHeadlessTests

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
- `PolygonClient` --uses--> `PolygonBackoffTests`  [INFERRED]
  polygon_client.py → tests/test_cycle1_fixes.py
- `PolygonError` --uses--> `PolygonBackoffTests`  [INFERRED]
  polygon_client.py → tests/test_cycle1_fixes.py
- `fake_chain()` --calls--> `NoOptionData`  [EXTRACTED]
  tests/test_international_fallback.py → polygon_client.py
- `NoOptionData` --uses--> `FailureReasonTests`  [INFERRED]
  polygon_client.py → tests/test_review_fixes.py
- `PolygonError` --uses--> `FailureReasonTests`  [INFERRED]
  polygon_client.py → tests/test_review_fixes.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Signal to fills to entry state loop** — readme_entry_signal_tool, readme_pipeline_signals, readme_entry_state_and_fills, readme_portfolio_file [EXTRACTED 1.00]
- **Polygon options-chain driven scripts** — readme_active_management, readme_entry_signal_tool, readme_risk_score_dynamic_leverage, readme_portfolio_vix, readme_portfolio_gex_field, readme_polygon_io [EXTRACTED 1.00]
- **Portfolio risk aggregation via correlation and Euler attribution** — readme_correlation_estimators, readme_euler_risk_attribution, readme_implied_correlation, readme_portfolio_vix, readme_active_management [INFERRED 0.75]

## Communities (42 total, 15 thin omitted)

### Community 0 - "portfolio_risk_score_leverage.py"
Cohesion: 0.05
Nodes (94): analyze_ticker_options(), apply_diversification_guardrail(), _assemble_regions(), benchmark_implied_sigma(), benchmark_implied_sigmas(), _bsm_d1_d2(), build_implied_correlation(), build_risk_inputs() (+86 more)

### Community 1 - "fundamental_analysis.py"
Cohesion: 0.08
Nodes (31): analizar_cartera(), calcular_corto_plazo(), _current_ratio(), calcular_historico(), calcular_info_adicional(), calcular_largo_plazo(), _roe_signal(), calcular_mediano_plazo() (+23 more)

### Community 3 - "portfolio_gex_field.py"
Cohesion: 0.07
Nodes (41): failure_reason(), american_delta_gamma(), american_iv_bisection(), american_price(), _bs93_american_call(), _bs93_phi(), bs_price(), build_composite_portfolio_force() (+33 more)

### Community 4 - "run_cycle.py"
Cohesion: 0.06
Nodes (43): _absorb_signal(), already_ran_this_week(), _as_text(), atomic_write(), _blank_step(), build_command(), build_parser(), CalendarUnavailable (+35 more)

### Community 5 - "main"
Cohesion: 0.22
Nodes (6): construir_senal_entrada(), graficar_resumen(), imprimir_resumen(), main(), parse_entry_args(), stage_pending_entry()

### Community 6 - "Tactical active management engine"
Cohesion: 0.08
Nodes (39): Portfolio Manager README, Tactical active management engine, CBOE VIX methodology (model-free variance), Concentration guardrail (1.5x equal-share risk), Cornish-Fisher VaR/ES and CVaR, Correlation estimators (sample, EWMA, random-matrix filtered), De-Americanization (Bjerksund-Stensland 1993 / CRR binomial), Research and educational disclaimer (+31 more)

### Community 7 - "test_review_fixes.py"
Cohesion: 0.19
Nodes (6): NoOptionData, PolygonError, PolygonNotFound, EntryPercentileTests, FailureReasonTests, GexLiveShellTests

### Community 8 - "tickers.py"
Cohesion: 0.08
Nodes (24): fallback_components(), TickerMappingTests, ResolverTierTests, adr_warnings(), capital_epic_verified(), _class_parts(), _clean(), _env_float() (+16 more)

### Community 9 - "portfolio_vix.py"
Cohesion: 0.18
Nodes (4): clamp_iv(), _parse_args(), portfolio_tickers(), portfolio_weights()

### Community 11 - ".load"
Cohesion: 0.27
Nodes (4): escrowed_inputs(), PolygonMarketLoader, select_cboe_expiries(), year_fraction()

### Community 12 - ".__init__"
Cohesion: 0.24
Nodes (3): OptionChainCleaner, PortfolioVIX, VIXConfig

### Community 13 - "DataFrame"
Cohesion: 0.32
Nodes (3): PortfolioVIXCalculator, ReportPlotter, SmileFit

### Community 14 - ".load"
Cohesion: 0.19
Nodes (6): AssetMarketData, bjerksund_stensland_price(), ExpirySlice, SingleAssetVIX, SyntheticMarketGenerator, YahooMarketLoader

### Community 15 - "gamma_flip_level"
Cohesion: 0.21
Nodes (4): gamma_flip_level(), GammaFlipTests, _load_functions(), RiskPriceHistoryTests

### Community 17 - "Working with the graphify knowledge graph"
Cohesion: 0.33
Nodes (5): Freshness check, Git hygiene, Navigating, Verify before asserting, Working with the graphify knowledge graph

### Community 18 - "Working with the graphify knowledge graph"
Cohesion: 0.33
Nodes (5): Freshness check, Git hygiene, Navigating, Verify before asserting, Working with the graphify knowledge graph

### Community 19 - "entry_signal_tool.py"
Cohesion: 0.16
Nodes (19): calcular_espacio_walls(), calcular_expected_move(), calcular_gex_y_zero_gamma(), calcular_iv_atm(), calcular_skew(), calcular_smart_money(), calcular_vanna_charm_factor(), calcular_walls() (+11 more)

### Community 23 - "pipeline_io.py"
Cohesion: 0.11
Nodes (21): apply_entry_fills(), _as_float(), _atomic_write(), _blank_activo(), executions_dir(), export_signals(), _fallback_result(), _flexible_fraction() (+13 more)

### Community 24 - "PolygonBackoffTests"
Cohesion: 0.28
Nodes (3): PolygonBackoffTests, fake_get(), _Resp

### Community 26 - "polygon_client.py"
Cohesion: 0.16
Nodes (5): calls_per_minute_configurado(), _limiter_for(), _RateLimiter, retry_after_seconds(), retry_backoff_seconds()

### Community 27 - "FillsGatingTests"
Cohesion: 0.33
Nodes (3): _estado(), _fills(), FillsGatingTests

### Community 28 - ".invoke"
Cohesion: 0.11
Nodes (6): CycleTestCase, FailureTests, _portfolio(), PortfolioAndCliTests, SuccessPathTests, WeeklyTests

### Community 32 - "price_signals.py"
Cohesion: 0.18
Nodes (6): _num(), price_indicators(), price_scores(), rsi(), yahoo_closes(), PriceSignalTests

### Community 33 - "correr_entry_signal"
Cohesion: 0.21
Nodes (11): _activo_vacio(), cargar_estado(), cargar_historial(), _contexto(), correr_entry_signal(), _estado_vacio(), guardar_estado(), normalizar_estado() (+3 more)

### Community 34 - "calcular_indicadores_proxy"
Cohesion: 0.28
Nodes (6): calcular_fila_instrumento(), calcular_indicadores_proxy(), calcular_indicadores_ticker(), fila_escalonada(), _pct_entrada(), percentile_historico()

### Community 36 - "implied_vol"
Cohesion: 0.29
Nodes (3): bs_price(), DeAmericanizer, implied_vol()

### Community 40 - "._namespace"
Cohesion: 0.50
Nodes (3): _load_functions(), RiskScoreFallbackTests, fake_chain()

## Knowledge Gaps
- **21 isolated node(s):** `Freshness check`, `Git hygiene`, `Navigating`, `Verify before asserting`, `Freshness check` (+16 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 197 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `to_polygon()` connect `tickers.py` to `portfolio_risk_score_leverage.py`, `test_international_fallback.py`, `portfolio_gex_field.py`, `portfolio_vix.py`, `.load`, `entry_signal_tool.py`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **What connects `Freshness check`, `Git hygiene`, `Navigating` to the rest of the system?**
  _21 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `portfolio_risk_score_leverage.py` be split into smaller, more focused modules?**
  _Cohesion score 0.050458003415618694 - nodes in this community are weakly interconnected._
- **Why does `PolygonClient` connect `PolygonClient` to `portfolio_risk_score_leverage.py`, `test_international_fallback.py`, `portfolio_gex_field.py`, `implied_vol`, `portfolio_vix.py`, `entry_signal_tool.py`, `PolygonBackoffTests`, `polygon_client.py`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Should `fundamental_analysis.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07924984875983061 - nodes in this community are weakly interconnected._
- **Why does `WeeklyTests` connect `.invoke` to `test_international_fallback.py`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Should `portfolio_gex_field.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06948051948051948 - nodes in this community are weakly interconnected._