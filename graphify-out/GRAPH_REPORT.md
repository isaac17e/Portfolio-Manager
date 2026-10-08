# Graph Report - Portfolio-Manager  (2026-10-08)

## Corpus Check
- 25 files · ~66,361 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 3)

## Summary
- 1006 nodes · 2482 edges · 57 communities (33 shown, 24 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 34 edges (avg confidence: 0.84)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8e8470c0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- portfolio_risk_score_leverage.py
- fundamental_analysis.py
- active_management.py
- portfolio_gex_field.py
- run_cycle.py
- test_international_fallback.py
- Tactical active management engine
- ._namespace
- tickers.py
- portfolio_vix.py
- ndarray
- .load
- implied_vol
- DataFrame
- YahooMarketLoader
- gamma_flip_level
- CBOEVarianceEngine
- Working with the graphify knowledge graph
- Working with the graphify knowledge graph
- entry_signal_tool.py
- numpy
- compute_var_es
- pipeline_io.py
- portfolio_key
- EntryTrancheLockTests
- PolygonClient
- FillsGatingTests
- .invoke
- calcular_indicadores_proxy
- resolve_cycle_day
- ActiveManagementTests
- failure_reason
- correr_entry_signal
- polygon_client.py
- PerPortfolioEntryStateTests
- test_signal_shapes.py
- VixHorizonTests
- plotly_graph_objects
- price_signals.py
- AssetMarketData
- .__init__
- RiskFreeRateTests
- VixWeightsArgsTests
- resolve_horizon
- StepHorizonTests
- PickExpirationTests
- PortfolioHorizonDaysTests
- ResolveHorizonTests
- RunCyclePassesHorizonTests
- LoadPortfolioTests
- GexHorizonTests
- TrancheLockHelperTests
- ExportSignalsTests
- EntrySignalRecordsHorizonTests

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
- `PolygonError` --uses--> `PolygonBackoffTests`  [INFERRED]
  polygon_client.py → tests/test_cycle1_fixes.py
- `fake_chain()` --calls--> `NoOptionData`  [EXTRACTED]
  tests/test_international_fallback.py → polygon_client.py
- `PolygonClient` --uses--> `PolygonBackoffTests`  [INFERRED]
  polygon_client.py → tests/test_cycle1_fixes.py
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

## Communities (57 total, 24 thin omitted)

### Community 0 - "portfolio_risk_score_leverage.py"
Cohesion: 0.08
Nodes (33): pick_expiration(), compute_atm_iv(), compute_corr_cov(), compute_expected_move(), compute_gex_pcr_factor(), compute_gex_profile(), compute_max_drawdown(), compute_max_pain() (+25 more)

### Community 1 - "fundamental_analysis.py"
Cohesion: 0.08
Nodes (31): analizar_cartera(), calcular_corto_plazo(), _current_ratio(), calcular_historico(), calcular_info_adicional(), calcular_largo_plazo(), _roe_signal(), calcular_mediano_plazo() (+23 more)

### Community 2 - "active_management.py"
Cohesion: 0.14
Nodes (35): analyze_ticker_options(), apply_diversification_guardrail(), benchmark_implied_sigma(), benchmark_implied_sigmas(), _bsm_d1_d2(), build_risk_inputs(), calculate_expected_move(), calculate_gex() (+27 more)

### Community 3 - "portfolio_gex_field.py"
Cohesion: 0.05
Nodes (43): american_delta_gamma(), american_iv_bisection(), american_price(), _bs93_american_call(), _bs93_phi(), bs_price(), build_composite_portfolio_force(), _build_gex_force_function_sigma() (+35 more)

### Community 4 - "run_cycle.py"
Cohesion: 0.06
Nodes (49): _absorb_signal(), already_ran_this_week(), _as_text(), atomic_write(), _blank_step(), build_command(), build_parser(), _calendar_failure() (+41 more)

### Community 6 - "Tactical active management engine"
Cohesion: 0.08
Nodes (39): Portfolio Manager README, Tactical active management engine, CBOE VIX methodology (model-free variance), Concentration guardrail (1.5x equal-share risk), Cornish-Fisher VaR/ES and CVaR, Correlation estimators (sample, EWMA, random-matrix filtered), De-Americanization (Bjerksund-Stensland 1993 / CRR binomial), Research and educational disclaimer (+31 more)

### Community 7 - "._namespace"
Cohesion: 0.36
Nodes (3): AdrSpotFallbackTests, _bs(), _chain()

### Community 8 - "tickers.py"
Cohesion: 0.07
Nodes (25): get_current_price(), TickerMappingTests, ResolverTierTests, StaggeredEntryTests, adr_warnings(), capital_epic_verified(), _class_parts(), _clean() (+17 more)

### Community 9 - "portfolio_vix.py"
Cohesion: 0.14
Nodes (10): resolve_risk_free_rate(), bjerksund_stensland_call(), bjerksund_stensland_price(), crr_american(), _euro_call_carry(), f(), _parse_args(), _phi() (+2 more)

### Community 11 - ".load"
Cohesion: 0.20
Nodes (6): clamp_iv(), escrowed_inputs(), PolygonMarketLoader, select_cboe_expiries(), select_expiries_for(), year_fraction()

### Community 12 - "implied_vol"
Cohesion: 0.29
Nodes (3): bs_price(), DeAmericanizer, implied_vol()

### Community 13 - "DataFrame"
Cohesion: 0.32
Nodes (3): PortfolioVIXCalculator, ReportPlotter, SmileFit

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
Cohesion: 0.10
Nodes (28): calcular_espacio_walls(), calcular_expected_move(), calcular_gex_y_zero_gamma(), calcular_iv_atm(), calcular_skew(), calcular_smart_money(), calcular_vanna_charm_factor(), calcular_walls() (+20 more)

### Community 20 - "numpy"
Cohesion: 0.16
Nodes (18): _assemble_regions(), build_implied_correlation(), _cov_to_corr(), estimate_correlation(), _ewma_cov(), _ewma_effective_n(), _nearest_pd_corr(), _pair_weights() (+10 more)

### Community 22 - "compute_var_es"
Cohesion: 0.60
Nodes (5): compute_var_es(), cornish_fisher_es(), cornish_fisher_var(), historical_es(), historical_var()

### Community 23 - "pipeline_io.py"
Cohesion: 0.11
Nodes (19): apply_entry_fills(), _as_float(), _atomic_write(), _blank_activo(), executions_dir(), export_signals(), _fallback_result(), _flexible_fraction() (+11 more)

### Community 24 - "portfolio_key"
Cohesion: 0.15
Nodes (8): cargar_fills(), entry_state_path(), _file_token(), load_portfolio_fills(), pipeline_dir(), portfolio_fills_path(), portfolio_key(), run_ts_stamp()

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

### Community 32 - "failure_reason"
Cohesion: 0.18
Nodes (5): failure_reason(), _closes(), EntrySignalTierTests, RiskScoreFallbackTests, fake_chain()

### Community 33 - "correr_entry_signal"
Cohesion: 0.15
Nodes (12): _activo_vacio(), cargar_estado(), cargar_historial(), construir_fila_estado(), _contexto(), correr_entry_signal(), _estado_vacio(), evaluar_flujo_opciones() (+4 more)

### Community 34 - "polygon_client.py"
Cohesion: 0.11
Nodes (10): calls_per_minute_configurado(), _limiter_for(), NoOptionData, PolygonError, PolygonNotFound, PolygonTruncated, _RateLimiter, EntryPercentileTests (+2 more)

### Community 37 - "VixHorizonTests"
Cohesion: 0.10
Nodes (7): ActiveManagementExpiryTests, _contracts_endpoint(), query(), EntryExpiryTests, _expiries(), RiskScoreExpiryTests, VixHorizonTests

### Community 38 - "plotly_graph_objects"
Cohesion: 0.27
Nodes (8): plot_allocation_comparison(), plot_risk_attribution(), plot_gex_profile(), plot_leverage_assignment(), plot_loss_distribution(), plot_pcr_vs_weight(), print_executive_summary(), run_reporting_module()

### Community 39 - "price_signals.py"
Cohesion: 0.17
Nodes (6): fallback_components(), _num(), price_indicators(), price_scores(), rsi(), PriceSignalTests

### Community 40 - "AssetMarketData"
Cohesion: 0.20
Nodes (5): AssetMarketData, bracket_pair(), ExpirySlice, SingleAssetVIX, SyntheticMarketGenerator

### Community 41 - ".__init__"
Cohesion: 0.24
Nodes (3): OptionChainCleaner, PortfolioVIX, VIXConfig

### Community 46 - "resolve_horizon"
Cohesion: 0.21
Nodes (7): _add_months(), cycle_today(), _iso_date(), portfolio_horizon_days(), portfolio_horizon_fields(), _positive_number(), resolve_horizon()

## Knowledge Gaps
- **21 isolated node(s):** `Freshness check`, `Git hygiene`, `Navigating`, `Verify before asserting`, `Freshness check` (+16 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 268 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **24 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DailyCalendarTests` connect `.invoke` to `test_international_fallback.py`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `resolve_instrument()` (e.g. with `._namespace()` and `._namespace()`) actually correct?**
  _`resolve_instrument()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Freshness check`, `Git hygiene`, `Navigating` to the rest of the system?**
  _21 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `portfolio_risk_score_leverage.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08019323671497584 - nodes in this community are weakly interconnected._
- **Why does `to_polygon()` connect `tickers.py` to `portfolio_risk_score_leverage.py`, `active_management.py`, `portfolio_gex_field.py`, `portfolio_vix.py`, `.load`, `entry_signal_tool.py`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Should `fundamental_analysis.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07924984875983061 - nodes in this community are weakly interconnected._
- **Why does `PolygonClient` connect `PolygonClient` to `portfolio_risk_score_leverage.py`, `active_management.py`, `portfolio_gex_field.py`, `polygon_client.py`, `tickers.py`, `portfolio_vix.py`, `implied_vol`, `entry_signal_tool.py`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._