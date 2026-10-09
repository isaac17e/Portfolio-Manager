# Graph Report - Portfolio-Manager  (2026-10-09)

## Corpus Check
- 27 files · ~68,762 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 3)

## Summary
- 1054 nodes · 2590 edges · 64 communities (39 shown, 25 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 35 edges (avg confidence: 0.84)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `45096bb1`
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
- cargar_fills
- DataFrame
- GexExpiryFallbackTests
- gamma_flip_level
- CBOEVarianceEngine
- Working with the graphify knowledge graph
- Working with the graphify knowledge graph
- entry_signal_tool.py
- numpy
- compute_var_es
- pipeline_io.py
- viz_utils.py
- EntryTrancheLockTests
- PolygonClient
- get_portfolio_chains
- .invoke
- calcular_indicadores_proxy
- resolve_cycle_day
- ActiveManagementTests
- ._namespace
- correr_entry_signal
- polygon_client.py
- PerPortfolioEntryStateTests
- test_signal_shapes.py
- VixHorizonTests
- run_reporting_module
- price_signals.py
- .load
- .__init__
- RiskFreeRateTests
- VixWeightsArgsTests
- run_headless
- resolve_horizon
- test_horizon.py
- PickExpirationTests
- PortfolioHorizonDaysTests
- ResolveHorizonTests
- RunCyclePassesHorizonTests
- LoadPortfolioTests
- ShowOrSaveTests
- TrancheLockHelperTests
- ExportSignalsTests
- get_polygon_options_data
- exclusion_warnings
- dividend_yield_from_info
- gex_headless_requested
- calculate_gex_and_surface_forces
- _load_functions

## God Nodes (most connected - your core abstractions)
1. `to_polygon()` - 31 edges
2. `resolve_instrument()` - 28 edges
3. `to_yahoo()` - 25 edges
4. `gamma_flip_level()` - 24 edges
5. `failure_reason()` - 22 edges
6. `NoOptionData` - 21 edges
7. `run_active_management_engine()` - 20 edges
8. `correr_entry_signal()` - 19 edges
9. `DailyCalendarTests` - 19 edges
10. `PolygonClient` - 19 edges

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

## Communities (64 total, 25 thin omitted)

### Community 0 - "portfolio_risk_score_leverage.py"
Cohesion: 0.09
Nodes (31): pick_expiration(), compute_corr_cov(), compute_gex_pcr_factor(), compute_gex_profile(), compute_max_drawdown(), compute_max_pain(), compute_put_call_ratio(), compute_risk_contribution() (+23 more)

### Community 1 - "fundamental_analysis.py"
Cohesion: 0.08
Nodes (31): analizar_cartera(), calcular_corto_plazo(), _current_ratio(), calcular_historico(), calcular_info_adicional(), calcular_largo_plazo(), _roe_signal(), calcular_mediano_plazo() (+23 more)

### Community 2 - "active_management.py"
Cohesion: 0.12
Nodes (39): analyze_ticker_options(), apply_diversification_guardrail(), benchmark_implied_sigma(), benchmark_implied_sigmas(), _bsm_d1_d2(), build_risk_inputs(), calculate_expected_move(), calculate_gex() (+31 more)

### Community 3 - "portfolio_gex_field.py"
Cohesion: 0.16
Nodes (12): _bs93_american_call(), _bs93_phi(), bs_price(), build_composite_portfolio_force(), _build_gex_force_function_sigma(), calculate_macro_y_axis(), _fetch_macro_series(), generate_portfolio_potential_surface() (+4 more)

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
Cohesion: 0.06
Nodes (28): get_current_price(), _estado(), _fills(), FillsGatingTests, TickerMappingTests, ResolverTierTests, StaggeredEntryTests, adr_warnings() (+20 more)

### Community 9 - "portfolio_vix.py"
Cohesion: 0.13
Nodes (12): resolve_risk_free_rate(), bjerksund_stensland_call(), bjerksund_stensland_price(), bs_price(), crr_american(), _euro_call_carry(), implied_vol(), f() (+4 more)

### Community 11 - ".load"
Cohesion: 0.27
Nodes (3): clamp_iv(), escrowed_inputs(), PolygonMarketLoader

### Community 12 - "cargar_fills"
Cohesion: 0.20
Nodes (7): cargar_fills(), executions_dir(), load_fills(), load_portfolio_fills(), locate_fills_file(), portfolio_fills_path(), _read_fills()

### Community 13 - "DataFrame"
Cohesion: 0.32
Nodes (3): PortfolioVIXCalculator, ReportPlotter, SmileFit

### Community 14 - "GexExpiryFallbackTests"
Cohesion: 0.24
Nodes (3): _chain(), GexExpiryFallbackTests, fetch()

### Community 15 - "gamma_flip_level"
Cohesion: 0.15
Nodes (4): gamma_flip_crossings(), gamma_flip_level(), FlipRootTests, GammaFlipTests

### Community 17 - "Working with the graphify knowledge graph"
Cohesion: 0.33
Nodes (5): Freshness check, Git hygiene, Navigating, Verify before asserting, Working with the graphify knowledge graph

### Community 18 - "Working with the graphify knowledge graph"
Cohesion: 0.33
Nodes (5): Freshness check, Git hygiene, Navigating, Verify before asserting, Working with the graphify knowledge graph

### Community 19 - "entry_signal_tool.py"
Cohesion: 0.11
Nodes (28): calcular_espacio_walls(), calcular_expected_move(), calcular_gex_y_zero_gamma(), calcular_iv_atm(), calcular_skew(), calcular_smart_money(), calcular_vanna_charm_factor(), calcular_walls() (+20 more)

### Community 20 - "numpy"
Cohesion: 0.18
Nodes (18): _assemble_regions(), build_implied_correlation(), _cov_to_corr(), estimate_correlation(), _ewma_cov(), _ewma_effective_n(), _nearest_pd_corr(), _pair_weights() (+10 more)

### Community 22 - "compute_var_es"
Cohesion: 0.60
Nodes (5): compute_var_es(), cornish_fisher_es(), cornish_fisher_var(), historical_es(), historical_var()

### Community 23 - "pipeline_io.py"
Cohesion: 0.12
Nodes (16): apply_entry_fills(), _as_float(), _atomic_write(), _blank_activo(), export_signals(), _fallback_result(), _flexible_fraction(), _is_nan() (+8 more)

### Community 24 - "viz_utils.py"
Cohesion: 0.15
Nodes (10): entry_state_path(), _file_token(), pipeline_dir(), portfolio_key(), run_ts_stamp(), figure_path(), figures_dir(), headless() (+2 more)

### Community 26 - "PolygonClient"
Cohesion: 0.20
Nodes (4): PolygonClient, PolygonBackoffTests, fake_get(), _Resp

### Community 27 - "get_portfolio_chains"
Cohesion: 0.18
Nodes (7): calculate_expected_move(), campo_gamma_utilizable(), get_dynamic_strike_range(), get_portfolio_chains(), _horizonte(), _reusar_ultimo_dato(), ventanas_vencimiento()

### Community 28 - ".invoke"
Cohesion: 0.08
Nodes (7): CycleTestCase, DailyCalendarTests, FailureTests, _portfolio(), PortfolioAndCliTests, SuccessPathTests, WeeklyTests

### Community 29 - "calcular_indicadores_proxy"
Cohesion: 0.22
Nodes (7): calcular_fila_instrumento(), calcular_indicadores_proxy(), calcular_indicadores_ticker(), fila_escalonada(), _pct_entrada(), percentile_historico(), yahoo_closes()

### Community 32 - "._namespace"
Cohesion: 0.22
Nodes (4): _closes(), EntrySignalTierTests, RiskScoreFallbackTests, fake_chain()

### Community 33 - "correr_entry_signal"
Cohesion: 0.15
Nodes (12): _activo_vacio(), cargar_estado(), cargar_historial(), construir_fila_estado(), _contexto(), correr_entry_signal(), _estado_vacio(), evaluar_flujo_opciones() (+4 more)

### Community 34 - "polygon_client.py"
Cohesion: 0.10
Nodes (13): calls_per_minute_configurado(), failure_reason(), _limiter_for(), NoOptionData, PolygonError, PolygonNotFound, PolygonTruncated, _RateLimiter (+5 more)

### Community 37 - "VixHorizonTests"
Cohesion: 0.10
Nodes (7): ActiveManagementExpiryTests, _contracts_endpoint(), query(), EntryExpiryTests, _expiries(), RiskScoreExpiryTests, VixHorizonTests

### Community 38 - "run_reporting_module"
Cohesion: 0.47
Nodes (5): plot_leverage_assignment(), plot_loss_distribution(), plot_pcr_vs_weight(), print_executive_summary(), run_reporting_module()

### Community 39 - "price_signals.py"
Cohesion: 0.17
Nodes (6): fallback_components(), _num(), price_indicators(), price_scores(), rsi(), PriceSignalTests

### Community 40 - ".load"
Cohesion: 0.19
Nodes (7): AssetMarketData, ExpirySlice, select_cboe_expiries(), select_expiries_for(), SyntheticMarketGenerator, YahooMarketLoader, year_fraction()

### Community 41 - ".__init__"
Cohesion: 0.13
Nodes (6): bracket_pair(), DeAmericanizer, OptionChainCleaner, PortfolioVIX, SingleAssetVIX, VIXConfig

### Community 44 - "run_headless"
Cohesion: 0.25
Nodes (10): calculate_gradient(), get_portfolio_current_state(), plot_3d_portfolio_field(), potential_function(), run_headless(), run_live(), _senal_gex(), start_local_file_server() (+2 more)

### Community 46 - "resolve_horizon"
Cohesion: 0.21
Nodes (7): _add_months(), cycle_today(), _iso_date(), portfolio_horizon_days(), portfolio_horizon_fields(), _positive_number(), resolve_horizon()

### Community 47 - "test_horizon.py"
Cohesion: 0.13
Nodes (4): EntrySignalRecordsHorizonTests, GexHorizonTests, _loaded(), StepHorizonTests

### Community 56 - "get_polygon_options_data"
Cohesion: 0.29
Nodes (7): american_delta_gamma(), american_iv_bisection(), american_price(), clamp_iv(), get_dividend_yield(), get_polygon_options_data(), polygon()

### Community 59 - "gex_headless_requested"
Cohesion: 0.33
Nodes (3): gex_headless_requested(), main(), GexHeadlessTests

### Community 60 - "calculate_gex_and_surface_forces"
Cohesion: 0.50
Nodes (3): calculate_gex_and_surface_forces(), calculate_gex_split(), gamma_regime()

## Knowledge Gaps
- **21 isolated node(s):** `Freshness check`, `Git hygiene`, `Navigating`, `Verify before asserting`, `Freshness check` (+16 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 288 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **25 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ResolveHorizonTests` connect `ResolveHorizonTests` to `test_horizon.py`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `resolve_instrument()` (e.g. with `._namespace()` and `._namespace()`) actually correct?**
  _`resolve_instrument()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Freshness check`, `Git hygiene`, `Navigating` to the rest of the system?**
  _21 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `portfolio_risk_score_leverage.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08637873754152824 - nodes in this community are weakly interconnected._
- **Should `fundamental_analysis.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08082706766917293 - nodes in this community are weakly interconnected._
- **Should `active_management.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1178743961352657 - nodes in this community are weakly interconnected._
- **Should `run_cycle.py` be split into smaller, more focused modules?**
  _Cohesion score 0.059940059940059943 - nodes in this community are weakly interconnected._