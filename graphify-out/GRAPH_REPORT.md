# Graph Report - Portfolio-Manager  (2026-10-12)

## Corpus Check
- 33 files · ~83,352 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 3)

## Summary
- 1311 nodes · 3228 edges · 80 communities (54 shown, 26 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 59 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `aea48eeb`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- portfolio_risk_score_leverage.py
- fundamental_analysis.py
- pandas
- portfolio_gex_field.py
- run_cycle.py
- universe.py
- Tactical active management engine
- tempfile
- to_polygon
- portfolio_vix.py
- ndarray
- .load
- portfolio_key
- DataFrame
- GexExpiryFallbackTests
- gamma_flip_level
- CBOEVarianceEngine
- Working with the graphify knowledge graph
- Working with the graphify knowledge graph
- entry_signal_tool.py
- numpy
- test_signals_layout.py
- compute_var_es
- pipeline_io.py
- viz_utils.py
- EntryTrancheLockTests
- active_management.py
- get_portfolio_chains
- .invoke
- test_cycle2_fixes.py
- correr_entry_signal
- test_zero_gamma.py
- test_international_fallback.py
- cargar_estado
- polygon_client.py
- PerPortfolioEntryStateTests
- unittest
- VixHorizonTests
- NoOptionData
- artifact_path
- drawdown_rotation.py
- .__init__
- RiskFreeRateTests
- VixWeightsArgsTests
- run_headless
- calcular_fila_instrumento
- resolve_instrument
- test_horizon.py
- PickExpirationTests
- load_rotation_state
- ResolveHorizonTests
- RunCyclePassesHorizonTests
- test_pipeline_io.py
- PolygonClient
- tickers.py
- no_options_weight_cap
- RotationLogicTests
- exclusion_warnings
- dividend_yield_from_info
- announce_signals_dir
- test_drawdown_rotation.py
- test_review_fixes.py
- gex_utils.py
- escrowed_inputs
- FillsGatingTests
- implied_vol
- select_rotation
- RotationRunTests
- ._fn
- apply_entry_fills
- construir_fila_estado
- run_reporting_module
- calculate_gex_and_surface_forces
- ._fn
- ._select
- PortfolioHorizonDaysTests
- DayFiveTrendTests
- _hist
- GexHorizonTests
- StaggeredEntryTests

## God Nodes (most connected - your core abstractions)
1. `to_polygon()` - 33 edges
2. `NoOptionData` - 29 edges
3. `run()` - 28 edges
4. `resolve_instrument()` - 28 edges
5. `to_yahoo()` - 27 edges
6. `failure_reason()` - 25 edges
7. `gamma_flip_level()` - 24 edges
8. `PolygonError` - 23 edges
9. `PolygonClient` - 22 edges
10. `run_active_management_engine()` - 21 edges

## Surprising Connections (you probably didn't know these)
- `PolygonBackoffTests` --uses--> `PolygonError`  [INFERRED]
  tests/test_cycle1_fixes.py → polygon_client.py
- `AdrSpotFallbackTests` --uses--> `PolygonError`  [INFERRED]
  tests/test_cycle2_fixes.py → polygon_client.py
- `RiskScoreFallbackTests` --uses--> `PolygonError`  [INFERRED]
  tests/test_international_fallback.py → polygon_client.py
- `AdrSpotFallbackTests` --uses--> `PolygonNotFound`  [INFERRED]
  tests/test_cycle2_fixes.py → polygon_client.py
- `AdrSpotFallbackTests` --uses--> `NoOptionData`  [INFERRED]
  tests/test_cycle2_fixes.py → polygon_client.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Signal to fills to entry state loop** — readme_entry_signal_tool, readme_pipeline_signals, readme_entry_state_and_fills, readme_portfolio_file [EXTRACTED 1.00]
- **Polygon options-chain driven scripts** — readme_active_management, readme_entry_signal_tool, readme_risk_score_dynamic_leverage, readme_portfolio_vix, readme_portfolio_gex_field, readme_polygon_io [EXTRACTED 1.00]
- **Portfolio risk aggregation via correlation and Euler attribution** — readme_correlation_estimators, readme_euler_risk_attribution, readme_implied_correlation, readme_portfolio_vix, readme_active_management [INFERRED 0.75]

## Communities (80 total, 26 thin omitted)

### Community 0 - "portfolio_risk_score_leverage.py"
Cohesion: 0.08
Nodes (31): pick_expiration(), bs_gamma(), bs_price(), compute_gex_pcr_factor(), compute_gex_profile(), compute_max_pain(), compute_put_call_ratio(), compute_strike_balance_level() (+23 more)

### Community 1 - "fundamental_analysis.py"
Cohesion: 0.08
Nodes (31): analizar_cartera(), calcular_corto_plazo(), _current_ratio(), calcular_historico(), calcular_info_adicional(), calcular_largo_plazo(), _roe_signal(), calcular_mediano_plazo() (+23 more)

### Community 2 - "pandas"
Cohesion: 0.19
Nodes (12): _bsm_d1_d2(), calculate_vanna_charm(), compute_atm_iv(), compute_corr_cov(), compute_expected_move(), compute_max_drawdown(), compute_risk_contribution(), compute_sharpe_sortino() (+4 more)

### Community 3 - "portfolio_gex_field.py"
Cohesion: 0.16
Nodes (15): _bs93_american_call(), _bs93_phi(), bs_price(), build_composite_portfolio_force(), _build_gex_force_function_sigma(), calculate_gradient(), calculate_macro_y_axis(), _fetch_macro_series() (+7 more)

### Community 4 - "run_cycle.py"
Cohesion: 0.05
Nodes (53): _absorb_signal(), already_ran_this_week(), _as_text(), atomic_write(), _blank_step(), build_command(), build_parser(), _calendar_failure() (+45 more)

### Community 5 - "universe.py"
Cohesion: 0.17
Nodes (8): build_universe(), clean_symbol_table(), _company_key(), index_constituents(), normalize_tickers(), parse_market_cap(), scrape_table(), take_top()

### Community 6 - "Tactical active management engine"
Cohesion: 0.08
Nodes (39): Portfolio Manager README, Tactical active management engine, CBOE VIX methodology (model-free variance), Concentration guardrail (1.5x equal-share risk), Cornish-Fisher VaR/ES and CVaR, Correlation estimators (sample, EWMA, random-matrix filtered), De-Americanization (Bjerksund-Stensland 1993 / CRR binomial), Research and educational disclaimer (+31 more)

### Community 8 - "to_polygon"
Cohesion: 0.22
Nodes (9): get_current_price(), TickerMappingTests, capital_epic_verified(), _format_class(), has_us_options(), mapping(), to_capital_epic(), to_polygon() (+1 more)

### Community 9 - "portfolio_vix.py"
Cohesion: 0.19
Nodes (8): bjerksund_stensland_call(), bjerksund_stensland_price(), _euro_call_carry(), _parse_args(), _phi(), portfolio_tickers(), portfolio_weights(), VIXConfig

### Community 11 - ".load"
Cohesion: 0.21
Nodes (5): clamp_iv(), PolygonMarketLoader, select_cboe_expiries(), select_expiries_for(), year_fraction()

### Community 12 - "portfolio_key"
Cohesion: 0.22
Nodes (5): cargar_fills(), entry_state_path(), load_portfolio_fills(), portfolio_fills_path(), portfolio_key()

### Community 13 - "DataFrame"
Cohesion: 0.17
Nodes (7): AssetMarketData, ExpirySlice, PortfolioVIXCalculator, ReportPlotter, SmileFit, SyntheticMarketGenerator, YahooMarketLoader

### Community 15 - "gamma_flip_level"
Cohesion: 0.16
Nodes (4): gamma_flip_crossings(), gamma_flip_level(), FlipRootTests, GammaFlipTests

### Community 17 - "Working with the graphify knowledge graph"
Cohesion: 0.33
Nodes (5): Freshness check, Git hygiene, Navigating, Verify before asserting, Working with the graphify knowledge graph

### Community 18 - "Working with the graphify knowledge graph"
Cohesion: 0.33
Nodes (5): Freshness check, Git hygiene, Navigating, Verify before asserting, Working with the graphify knowledge graph

### Community 19 - "entry_signal_tool.py"
Cohesion: 0.20
Nodes (16): calcular_espacio_walls(), calcular_expected_move(), calcular_iv_atm(), calcular_skew(), calcular_smart_money(), calcular_vanna_charm_factor(), calcular_walls(), dias_a_opex() (+8 more)

### Community 20 - "numpy"
Cohesion: 0.18
Nodes (20): _assemble_regions(), benchmark_implied_sigma(), benchmark_implied_sigmas(), build_implied_correlation(), build_risk_inputs(), _cov_to_corr(), estimate_correlation(), _ewma_cov() (+12 more)

### Community 21 - "test_signals_layout.py"
Cohesion: 0.08
Nodes (10): CleanEnvCase, CycleCase, ExportTests, _meta(), OverrideCycleTests, ParentChildAgreementTests, _portfolio_file(), ResolutionTests (+2 more)

### Community 22 - "compute_var_es"
Cohesion: 0.60
Nodes (5): compute_var_es(), cornish_fisher_es(), cornish_fisher_var(), historical_es(), historical_var()

### Community 23 - "pipeline_io.py"
Cohesion: 0.09
Nodes (26): _add_months(), apply_rotation_overrides(), _as_float(), _atomic_write(), executions_dir(), export_signals(), _fallback_result(), _flexible_fraction() (+18 more)

### Community 24 - "viz_utils.py"
Cohesion: 0.20
Nodes (9): default_figures_dir(), _file_token(), run_ts_stamp(), figure_path(), figures_dir(), headless(), _in_ipython(), _interactive() (+1 more)

### Community 26 - "active_management.py"
Cohesion: 0.13
Nodes (29): analyze_ticker_options(), apply_diversification_guardrail(), calculate_expected_move(), calculate_gex(), calculate_order_flow(), calculate_tactical_score(), cargar_historial_riesgo(), euler_risk_attribution() (+21 more)

### Community 27 - "get_portfolio_chains"
Cohesion: 0.12
Nodes (14): american_delta_gamma(), american_iv_bisection(), american_price(), calculate_expected_move(), campo_gamma_utilizable(), clamp_iv(), get_dividend_yield(), get_dynamic_strike_range() (+6 more)

### Community 28 - ".invoke"
Cohesion: 0.08
Nodes (7): CycleTestCase, DailyCalendarTests, FailureTests, _portfolio(), PortfolioAndCliTests, SuccessPathTests, WeeklyTests

### Community 29 - "test_cycle2_fixes.py"
Cohesion: 0.23
Nodes (4): failure_reason(), AdrSpotFallbackTests, _bs(), _chain()

### Community 30 - "correr_entry_signal"
Cohesion: 0.14
Nodes (9): cargar_historial(), _contexto(), correr_entry_signal(), _etiquetar_definiciones(), _normalizar_definiciones(), resolve_cycle_day(), signal_cycle_number(), suggest_cycle_day() (+1 more)

### Community 31 - "test_zero_gamma.py"
Cohesion: 0.06
Nodes (14): calcular_gex_y_zero_gamma(), _valid_contracts(), zero_gamma_profile(), ShowOrSaveTests, _load_functions(), ActiveManagementTests, _load_active_management(), ConsumerZeroGammaTests (+6 more)

### Community 32 - "test_international_fallback.py"
Cohesion: 0.18
Nodes (6): _num(), price_indicators(), price_scores(), rsi(), _closes(), PriceSignalTests

### Community 33 - "cargar_estado"
Cohesion: 0.39
Nodes (8): _activo_vacio(), cargar_estado(), _estado_vacio(), guardar_estado(), normalizar_estado(), _portafolio_del_estado(), ruta_estado(), f()

### Community 34 - "polygon_client.py"
Cohesion: 0.14
Nodes (6): calls_per_minute_configurado(), _limiter_for(), PolygonTruncated, _RateLimiter, retry_after_seconds(), retry_backoff_seconds()

### Community 38 - "NoOptionData"
Cohesion: 0.21
Nodes (4): NoOptionData, EntrySignalTierTests, RiskScoreFallbackTests, fake_chain()

### Community 39 - "artifact_path"
Cohesion: 0.11
Nodes (10): artifact_path(), optimizer_history_path(), per_portfolio_enabled(), _portfolio_identity(), portfolio_signals_dir(), prepare_artifact_path(), resolve_signals_dir(), signals_base_dir() (+2 more)

### Community 40 - "drawdown_rotation.py"
Cohesion: 0.08
Nodes (32): build_rebalances(), cansancio_score(), _custom_tickers(), decide_action(), diagnosis_score(), fetch_ohlc(), figure_detector(), figure_top() (+24 more)

### Community 44 - "run_headless"
Cohesion: 0.14
Nodes (12): downsample_profile(), gex_headless_requested(), main(), plot_3d_portfolio_field(), plot_zero_gamma_profiles(), run_headless(), run_live(), _senal_gex() (+4 more)

### Community 45 - "calcular_fila_instrumento"
Cohesion: 0.28
Nodes (6): calcular_fila_instrumento(), calcular_indicadores_proxy(), calcular_indicadores_ticker(), fila_escalonada(), _pct_entrada(), percentile_historico()

### Community 46 - "resolve_instrument"
Cohesion: 0.21
Nodes (5): ResolverTierTests, adr_warnings(), options_exclusion(), options_underlying(), resolve_instrument()

### Community 47 - "test_horizon.py"
Cohesion: 0.18
Nodes (3): EntrySignalRecordsHorizonTests, _loaded(), StepHorizonTests

### Community 49 - "load_rotation_state"
Cohesion: 0.29
Nodes (4): empty_rotation_state(), load_rotation_state(), pipeline_dir(), rotation_state_path()

### Community 52 - "test_pipeline_io.py"
Cohesion: 0.10
Nodes (4): TrancheLockHelperTests, ExportSignalsTests, LoadPortfolioTests, _portfolio()

### Community 53 - "PolygonClient"
Cohesion: 0.20
Nodes (4): PolygonClient, PolygonBackoffTests, fake_get(), _Resp

### Community 54 - "tickers.py"
Cohesion: 0.24
Nodes (8): _class_parts(), _clean(), exchange_suffix(), no_us_options_reason(), partition_us_options(), proxy_etf(), _split_listing(), _upper()

### Community 55 - "no_options_weight_cap"
Cohesion: 0.33
Nodes (3): fallback_components(), _env_float(), no_options_weight_cap()

### Community 59 - "announce_signals_dir"
Cohesion: 0.14
Nodes (9): construir_senal_bloqueada(), construir_senal_entrada(), graficar_resumen(), imprimir_resumen(), main(), parse_entry_args(), _truthy(), announce_signals_dir() (+1 more)

### Community 60 - "test_drawdown_rotation.py"
Cohesion: 0.20
Nodes (3): EntryReadsRotationTests, _table(), UniverseTests

### Community 61 - "test_review_fixes.py"
Cohesion: 0.17
Nodes (7): PolygonError, PolygonNotFound, EntryPercentileTests, FailureReasonTests, GexLiveShellTests, _load_functions(), RiskPriceHistoryTests

### Community 63 - "escrowed_inputs"
Cohesion: 0.33
Nodes (3): bracket_pair(), escrowed_inputs(), SingleAssetVIX

### Community 64 - "FillsGatingTests"
Cohesion: 0.33
Nodes (3): _estado(), _fills(), FillsGatingTests

### Community 65 - "implied_vol"
Cohesion: 0.24
Nodes (5): bs_price(), crr_american(), DeAmericanizer, implied_vol(), f()

### Community 66 - "select_rotation"
Cohesion: 0.29
Nodes (5): choose_combination(), covariance(), expected_excess(), portfolio_sharpe(), select_rotation()

### Community 68 - "._fn"
Cohesion: 0.36
Nodes (3): _contracts_endpoint(), query(), RiskScoreExpiryTests

### Community 69 - "apply_entry_fills"
Cohesion: 0.33
Nodes (3): apply_entry_fills(), _blank_activo(), stage_pending_entry()

### Community 70 - "construir_fila_estado"
Cohesion: 0.33
Nodes (4): construir_fila_estado(), evaluar_flujo_opciones(), _filas_misma_definicion(), _texto()

### Community 71 - "run_reporting_module"
Cohesion: 0.47
Nodes (5): plot_leverage_assignment(), plot_loss_distribution(), plot_pcr_vs_weight(), print_executive_summary(), run_reporting_module()

### Community 72 - "calculate_gex_and_surface_forces"
Cohesion: 0.33
Nodes (4): calculate_gex_and_surface_forces(), calculate_gex_split(), gamma_regime(), perfil_zero_gamma()

## Knowledge Gaps
- **21 isolated node(s):** `Navigating`, `Verify before asserting`, `Freshness check`, `Git hygiene`, `Navigating` (+16 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 364 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **26 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `EntryTrancheLockTests` connect `EntryTrancheLockTests` to `test_pipeline_io.py`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **What connects `Navigating`, `Verify before asserting`, `Freshness check` to the rest of the system?**
  _21 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `portfolio_risk_score_leverage.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07922705314009662 - nodes in this community are weakly interconnected._
- **Why does `GexExpiryFallbackTests` connect `GexExpiryFallbackTests` to `pandas`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Should `fundamental_analysis.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07924984875983061 - nodes in this community are weakly interconnected._
- **Why does `to_polygon()` connect `to_polygon` to `portfolio_risk_score_leverage.py`, `portfolio_gex_field.py`, `drawdown_rotation.py`, `portfolio_vix.py`, `.load`, `resolve_instrument`, `entry_signal_tool.py`, `tickers.py`, `active_management.py`, `get_portfolio_chains`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Should `run_cycle.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05238095238095238 - nodes in this community are weakly interconnected._