# Graph Report - Portfolio-Manager  (2026-10-08)

## Corpus Check
- 24 files · ~62,270 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 3)

## Summary
- 908 nodes · 2296 edges · 46 communities (31 shown, 15 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 32 edges (avg confidence: 0.84)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6793e96b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- portfolio_risk_score_leverage.py
- fundamental_analysis.py
- active_management.py
- portfolio_gex_field.py
- run_cycle.py
- test_pipeline_io.py
- Tactical active management engine
- ._namespace
- tickers.py
- portfolio_vix.py
- ndarray
- .load
- .__init__
- DataFrame
- .load
- test_review_fixes.py
- CBOEVarianceEngine
- Working with the graphify knowledge graph
- Working with the graphify knowledge graph
- entry_signal_tool.py
- numpy
- compute_var_es
- pipeline_io.py
- cargar_fills
- EntryTrancheLockTests
- PolygonClient
- FillsGatingTests
- .invoke
- calcular_indicadores_proxy
- resolve_cycle_day
- ActiveManagementTests
- price_indicators
- correr_entry_signal
- test_international_fallback.py
- PerPortfolioEntryStateTests
- test_signal_shapes.py
- apply_entry_fills
- plot_loss_distribution
- .__init__
- .generate
- OptionChainCleaner
- RiskFreeRateTests
- VixWeightsArgsTests

## God Nodes (most connected - your core abstractions)
1. `to_polygon()` - 31 edges
2. `resolve_instrument()` - 28 edges
3. `to_yahoo()` - 25 edges
4. `failure_reason()` - 22 edges
5. `NoOptionData` - 21 edges
6. `run_active_management_engine()` - 20 edges
7. `correr_entry_signal()` - 19 edges
8. `DailyCalendarTests` - 19 edges
9. `PolygonClient` - 19 edges
10. `gamma_flip_level()` - 19 edges

## Surprising Connections (you probably didn't know these)
- `fake_chain()` --calls--> `NoOptionData`  [EXTRACTED]
  tests/test_international_fallback.py → polygon_client.py
- `PolygonError` --uses--> `PolygonBackoffTests`  [INFERRED]
  polygon_client.py → tests/test_cycle1_fixes.py
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

## Communities (46 total, 15 thin omitted)

### Community 0 - "portfolio_risk_score_leverage.py"
Cohesion: 0.10
Nodes (30): bs_gamma(), bs_price(), compute_atm_iv(), compute_expected_move(), compute_gex_pcr_factor(), compute_gex_profile(), compute_max_pain(), compute_put_call_ratio() (+22 more)

### Community 1 - "fundamental_analysis.py"
Cohesion: 0.08
Nodes (31): analizar_cartera(), calcular_corto_plazo(), _current_ratio(), calcular_historico(), calcular_info_adicional(), calcular_largo_plazo(), _roe_signal(), calcular_mediano_plazo() (+23 more)

### Community 2 - "active_management.py"
Cohesion: 0.14
Nodes (31): analyze_ticker_options(), apply_diversification_guardrail(), _bsm_d1_d2(), calculate_expected_move(), calculate_gex(), calculate_order_flow(), calculate_tactical_score(), calculate_vanna_charm() (+23 more)

### Community 3 - "portfolio_gex_field.py"
Cohesion: 0.05
Nodes (42): american_delta_gamma(), american_iv_bisection(), american_price(), _bs93_american_call(), _bs93_phi(), bs_price(), build_composite_portfolio_force(), _build_gex_force_function_sigma() (+34 more)

### Community 4 - "run_cycle.py"
Cohesion: 0.06
Nodes (48): _absorb_signal(), already_ran_this_week(), _as_text(), atomic_write(), _blank_step(), build_command(), build_parser(), _calendar_failure() (+40 more)

### Community 5 - "test_pipeline_io.py"
Cohesion: 0.10
Nodes (4): TrancheLockHelperTests, ExportSignalsTests, LoadPortfolioTests, _portfolio()

### Community 6 - "Tactical active management engine"
Cohesion: 0.08
Nodes (39): Portfolio Manager README, Tactical active management engine, CBOE VIX methodology (model-free variance), Concentration guardrail (1.5x equal-share risk), Cornish-Fisher VaR/ES and CVaR, Correlation estimators (sample, EWMA, random-matrix filtered), De-Americanization (Bjerksund-Stensland 1993 / CRR binomial), Research and educational disclaimer (+31 more)

### Community 7 - "._namespace"
Cohesion: 0.36
Nodes (3): AdrSpotFallbackTests, _bs(), _chain()

### Community 8 - "tickers.py"
Cohesion: 0.06
Nodes (27): get_current_price(), rsi(), yahoo_closes(), TickerMappingTests, ResolverTierTests, StaggeredEntryTests, adr_warnings(), capital_epic_verified() (+19 more)

### Community 9 - "portfolio_vix.py"
Cohesion: 0.18
Nodes (14): resolve_risk_free_rate(), bjerksund_stensland_call(), bjerksund_stensland_price(), black76_price(), bs_price(), crr_american(), escrowed_inputs(), _euro_call_carry() (+6 more)

### Community 12 - ".__init__"
Cohesion: 0.16
Nodes (5): AssetMarketData, DeAmericanizer, implied_vol(), PortfolioVIX, SingleAssetVIX

### Community 13 - "DataFrame"
Cohesion: 0.32
Nodes (3): PortfolioVIXCalculator, ReportPlotter, SmileFit

### Community 14 - ".load"
Cohesion: 0.38
Nodes (3): select_cboe_expiries(), YahooMarketLoader, year_fraction()

### Community 15 - "test_review_fixes.py"
Cohesion: 0.12
Nodes (6): gamma_flip_level(), EntryPercentileTests, GammaFlipTests, GexLiveShellTests, _load_functions(), RiskPriceHistoryTests

### Community 17 - "Working with the graphify knowledge graph"
Cohesion: 0.33
Nodes (5): Freshness check, Git hygiene, Navigating, Verify before asserting, Working with the graphify knowledge graph

### Community 18 - "Working with the graphify knowledge graph"
Cohesion: 0.33
Nodes (5): Freshness check, Git hygiene, Navigating, Verify before asserting, Working with the graphify knowledge graph

### Community 19 - "entry_signal_tool.py"
Cohesion: 0.12
Nodes (26): calcular_espacio_walls(), calcular_expected_move(), calcular_gex_y_zero_gamma(), calcular_iv_atm(), calcular_skew(), calcular_smart_money(), calcular_vanna_charm_factor(), calcular_walls() (+18 more)

### Community 20 - "numpy"
Cohesion: 0.18
Nodes (20): _assemble_regions(), benchmark_implied_sigma(), benchmark_implied_sigmas(), build_implied_correlation(), build_risk_inputs(), _cov_to_corr(), estimate_correlation(), _ewma_cov() (+12 more)

### Community 22 - "compute_var_es"
Cohesion: 0.22
Nodes (11): compute_corr_cov(), compute_max_drawdown(), compute_risk_contribution(), compute_sharpe_sortino(), compute_var_es(), compute_volatility(), cornish_fisher_es(), cornish_fisher_var() (+3 more)

### Community 23 - "pipeline_io.py"
Cohesion: 0.09
Nodes (20): _atomic_write(), entry_state_path(), executions_dir(), export_signals(), _fallback_result(), _file_token(), _flexible_fraction(), _is_nan() (+12 more)

### Community 24 - "cargar_fills"
Cohesion: 0.33
Nodes (4): cargar_fills(), load_fills(), load_portfolio_fills(), _read_fills()

### Community 26 - "PolygonClient"
Cohesion: 0.14
Nodes (6): PolygonClient, retry_after_seconds(), retry_backoff_seconds(), PolygonBackoffTests, fake_get(), _Resp

### Community 27 - "FillsGatingTests"
Cohesion: 0.33
Nodes (3): _estado(), _fills(), FillsGatingTests

### Community 28 - ".invoke"
Cohesion: 0.08
Nodes (7): CycleTestCase, DailyCalendarTests, FailureTests, _portfolio(), PortfolioAndCliTests, SuccessPathTests, WeeklyTests

### Community 29 - "calcular_indicadores_proxy"
Cohesion: 0.28
Nodes (6): calcular_fila_instrumento(), calcular_indicadores_proxy(), calcular_indicadores_ticker(), fila_escalonada(), _pct_entrada(), percentile_historico()

### Community 32 - "price_indicators"
Cohesion: 0.12
Nodes (9): fallback_components(), _num(), price_indicators(), price_scores(), _closes(), EntrySignalTierTests, PriceSignalTests, RiskScoreFallbackTests (+1 more)

### Community 33 - "correr_entry_signal"
Cohesion: 0.12
Nodes (13): _activo_vacio(), cargar_estado(), cargar_historial(), construir_fila_estado(), _contexto(), correr_entry_signal(), _estado_vacio(), evaluar_flujo_opciones() (+5 more)

### Community 34 - "test_international_fallback.py"
Cohesion: 0.18
Nodes (7): failure_reason(), NoOptionData, PolygonError, PolygonNotFound, PolygonTruncated, _load_functions(), FailureReasonTests

### Community 37 - "apply_entry_fills"
Cohesion: 0.29
Nodes (4): apply_entry_fills(), _as_float(), _blank_activo(), stage_pending_entry()

### Community 38 - "plot_loss_distribution"
Cohesion: 0.47
Nodes (5): plot_leverage_assignment(), plot_loss_distribution(), plot_pcr_vs_weight(), print_executive_summary(), run_reporting_module()

### Community 39 - ".__init__"
Cohesion: 0.33
Nodes (3): calls_per_minute_configurado(), _limiter_for(), _RateLimiter

## Knowledge Gaps
- **21 isolated node(s):** `Freshness check`, `Git hygiene`, `Navigating`, `Verify before asserting`, `Freshness check` (+16 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 230 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `EntryTrancheLockTests` connect `EntryTrancheLockTests` to `test_pipeline_io.py`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `resolve_instrument()` (e.g. with `._namespace()` and `._namespace()`) actually correct?**
  _`resolve_instrument()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Freshness check`, `Git hygiene`, `Navigating` to the rest of the system?**
  _21 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `portfolio_risk_score_leverage.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09615384615384616 - nodes in this community are weakly interconnected._
- **Why does `to_polygon()` connect `tickers.py` to `portfolio_risk_score_leverage.py`, `active_management.py`, `portfolio_gex_field.py`, `portfolio_vix.py`, `.load`, `entry_signal_tool.py`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Should `fundamental_analysis.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07924984875983061 - nodes in this community are weakly interconnected._
- **Should `active_management.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1422475106685633 - nodes in this community are weakly interconnected._