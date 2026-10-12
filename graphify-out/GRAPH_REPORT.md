# Graph Report - Portfolio-Manager  (2026-10-12)

## Corpus Check
- 36 files · ~93,960 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 4)

## Summary
- 1569 nodes · 3876 edges · 81 communities (54 shown, 27 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 61 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `716ca9ee`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- portfolio_risk_score_leverage.py
- fundamental_analysis.py
- Fix1CumulativeFillsTests
- portfolio_gex_field.py
- run_cycle.py
- universe.py
- Tactical active management engine
- test_zero_gamma_def.py
- tickers.py
- portfolio_vix.py
- ndarray
- .load
- portfolio_key
- DataFrame
- GexExpiryFallbackTests
- gamma_flip_level
- CBOEVarianceEngine
- run_headless
- get_portfolio_chains
- entry_signal_tool.py
- numpy
- _meta
- compute_var_es
- pipeline_io.py
- viz_utils.py
- EntryTrancheLockTests
- active_management.py
- test_sell_fills.py
- .invoke
- ._namespace
- EntryUsesActiveManagementTargetsTests
- _profile
- price_signals.py
- correr_entry_signal
- polygon_client.py
- PerPortfolioEntryStateTests
- test_signal_shapes.py
- VixHorizonTests
- test_review_fixes.py
- resolve_signals_dir
- screen_candidates
- .__init__
- RiskFreeRateTests
- VixWeightsArgsTests
- RiskRegimeSameDayTests
- FillsGatingTests
- EntryUnitRuleTests
- StepHorizonTests
- PickExpirationTests
- export_signals
- RunCyclePhaseTests
- RunCyclePassesHorizonTests
- os
- .load
- RotationEntryCase
- gex_headless_requested
- _ohlc
- run_reporting_module
- run
- fully_sold_tickers
- UniverseTests
- EntryReadsRotationTests
- zero_gamma_profile
- AssetMarketData
- drawdown_rotation.py
- failure_reason
- select_rotation
- calculate_gex_and_surface_forces
- _refine_bracket
- cycle_today
- ShowOrSaveTests
- exclusion_warnings
- dividend_yield_from_info
- test_pipeline_io.py
- PortfolioHorizonDaysTests
- ResolveHorizonTests
- __init__.py
- TrancheLockHelperTests
- GexHorizonTests
- EntrySignalRecordsHorizonTests

## God Nodes (most connected - your core abstractions)
1. `to_polygon()` - 33 edges
2. `run()` - 31 edges
3. `NoOptionData` - 28 edges
4. `resolve_instrument()` - 28 edges
5. `to_yahoo()` - 27 edges
6. `correr_entry_signal()` - 26 edges
7. `failure_reason()` - 26 edges
8. `zero_gamma_profile()` - 25 edges
9. `gamma_flip_level()` - 24 edges
10. `PolygonClient` - 22 edges

## Surprising Connections (you probably didn't know these)
- `AdrSpotFallbackTests` --uses--> `NoOptionData`  [INFERRED]
  tests/test_cycle2_fixes.py → polygon_client.py
- `AdrSpotFallbackTests` --uses--> `PolygonError`  [INFERRED]
  tests/test_cycle2_fixes.py → polygon_client.py
- `AdrSpotFallbackTests` --uses--> `PolygonNotFound`  [INFERRED]
  tests/test_cycle2_fixes.py → polygon_client.py
- `PolygonBackoffTests` --uses--> `PolygonError`  [INFERRED]
  tests/test_cycle1_fixes.py → polygon_client.py
- `PolygonBackoffTests` --uses--> `PolygonClient`  [INFERRED]
  tests/test_cycle1_fixes.py → polygon_client.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Signal to fills to entry state loop** — readme_entry_signal_tool, readme_pipeline_signals, readme_entry_state_and_fills, readme_portfolio_file [EXTRACTED 1.00]
- **Polygon options-chain driven scripts** — readme_active_management, readme_entry_signal_tool, readme_risk_score_dynamic_leverage, readme_portfolio_vix, readme_portfolio_gex_field, readme_polygon_io [EXTRACTED 1.00]
- **Portfolio risk aggregation via correlation and Euler attribution** — readme_correlation_estimators, readme_euler_risk_attribution, readme_implied_correlation, readme_portfolio_vix, readme_active_management [INFERRED 0.75]

## Communities (81 total, 27 thin omitted)

### Community 0 - "portfolio_risk_score_leverage.py"
Cohesion: 0.08
Nodes (36): bs_gamma(), bs_price(), compute_atm_iv(), compute_corr_cov(), compute_expected_move(), compute_gex_pcr_factor(), compute_gex_profile(), compute_max_drawdown() (+28 more)

### Community 1 - "fundamental_analysis.py"
Cohesion: 0.08
Nodes (31): analizar_cartera(), calcular_corto_plazo(), _current_ratio(), calcular_historico(), calcular_info_adicional(), calcular_largo_plazo(), _roe_signal(), calcular_mediano_plazo() (+23 more)

### Community 2 - "Fix1CumulativeFillsTests"
Cohesion: 0.14
Nodes (6): doc(), EntryPhaseCountTests, ExecDirCase, fill(), Fix1CumulativeFillsTests, Fix2ActiveManagementRealWeightTests

### Community 3 - "portfolio_gex_field.py"
Cohesion: 0.13
Nodes (19): american_delta_gamma(), american_iv_bisection(), american_price(), _bs93_american_call(), _bs93_phi(), bs_price(), build_composite_portfolio_force(), _build_gex_force_function_sigma() (+11 more)

### Community 4 - "run_cycle.py"
Cohesion: 0.05
Nodes (54): _absorb_signal(), already_ran_this_week(), _as_text(), atomic_write(), _blank_step(), build_command(), build_parser(), _calendar_failure() (+46 more)

### Community 5 - "universe.py"
Cohesion: 0.18
Nodes (8): build_universe(), clean_symbol_table(), _company_key(), index_constituents(), normalize_tickers(), parse_market_cap(), scrape_table(), take_top()

### Community 6 - "Tactical active management engine"
Cohesion: 0.08
Nodes (39): Portfolio Manager README, Tactical active management engine, CBOE VIX methodology (model-free variance), Concentration guardrail (1.5x equal-share risk), Cornish-Fisher VaR/ES and CVaR, Correlation estimators (sample, EWMA, random-matrix filtered), De-Americanization (Bjerksund-Stensland 1993 / CRR binomial), Research and educational disclaimer (+31 more)

### Community 7 - "test_zero_gamma_def.py"
Cohesion: 0.17
Nodes (5): DayFiveTrendTests, DefinitionTagTests, _hist(), _legacy_csv(), PercentileTests

### Community 8 - "tickers.py"
Cohesion: 0.08
Nodes (24): TickerMappingTests, ResolverTierTests, StaggeredEntryTests, adr_warnings(), capital_epic_verified(), _class_parts(), _clean(), _env_float() (+16 more)

### Community 9 - "portfolio_vix.py"
Cohesion: 0.13
Nodes (13): _is_nan(), bjerksund_stensland_call(), bjerksund_stensland_price(), bs_price(), crr_american(), _euro_call_carry(), implied_vol(), f() (+5 more)

### Community 11 - ".load"
Cohesion: 0.27
Nodes (3): clamp_iv(), escrowed_inputs(), PolygonMarketLoader

### Community 12 - "portfolio_key"
Cohesion: 0.10
Nodes (16): cargar_fills(), executions_dir(), _file_token(), _fills_candidates(), load_fills(), load_portfolio_fill_docs(), load_portfolio_fills(), load_portfolio_holdings() (+8 more)

### Community 13 - "DataFrame"
Cohesion: 0.32
Nodes (3): PortfolioVIXCalculator, ReportPlotter, SmileFit

### Community 14 - "GexExpiryFallbackTests"
Cohesion: 0.24
Nodes (3): _chain(), GexExpiryFallbackTests, fetch()

### Community 15 - "gamma_flip_level"
Cohesion: 0.12
Nodes (6): gamma_flip_crossings(), gamma_flip_level(), FlipRootTests, GammaFlipTests, _load_functions(), RiskPriceHistoryTests

### Community 17 - "run_headless"
Cohesion: 0.16
Nodes (10): downsample_profile(), prepare_artifact_path(), plot_zero_gamma_profiles(), _resolve_output(), run_headless(), run_live(), _senal_gex(), start_local_file_server() (+2 more)

### Community 18 - "get_portfolio_chains"
Cohesion: 0.14
Nodes (12): calculate_expected_move(), campo_gamma_utilizable(), clamp_iv(), get_current_price(), get_dividend_yield(), get_dynamic_strike_range(), get_polygon_options_data(), get_portfolio_chains() (+4 more)

### Community 19 - "entry_signal_tool.py"
Cohesion: 0.08
Nodes (36): calcular_espacio_walls(), calcular_expected_move(), calcular_fila_instrumento(), calcular_gex_y_zero_gamma(), calcular_indicadores_proxy(), calcular_indicadores_ticker(), calcular_iv_atm(), calcular_skew() (+28 more)

### Community 20 - "numpy"
Cohesion: 0.18
Nodes (20): _assemble_regions(), benchmark_implied_sigma(), benchmark_implied_sigmas(), build_implied_correlation(), build_risk_inputs(), _cov_to_corr(), estimate_correlation(), _ewma_cov() (+12 more)

### Community 21 - "_meta"
Cohesion: 0.07
Nodes (10): CleanEnvCase, CycleCase, ExportTests, _meta(), OverrideCycleTests, ParentChildAgreementTests, _portfolio_file(), ResolutionTests (+2 more)

### Community 22 - "compute_var_es"
Cohesion: 0.60
Nodes (5): compute_var_es(), cornish_fisher_es(), cornish_fisher_var(), historical_es(), historical_var()

### Community 23 - "pipeline_io.py"
Cohesion: 0.08
Nodes (20): accumulate_fills(), apply_entry_fills(), _as_float(), _as_float_text(), _blank_activo(), _fallback_result(), _fill_key(), _fill_side() (+12 more)

### Community 24 - "viz_utils.py"
Cohesion: 0.31
Nodes (6): figure_path(), figures_dir(), headless(), _in_ipython(), _interactive(), show_or_save()

### Community 26 - "active_management.py"
Cohesion: 0.12
Nodes (33): _advertencias_tenencias(), analyze_ticker_options(), apply_diversification_guardrail(), _bsm_d1_d2(), calculate_expected_move(), calculate_order_flow(), calculate_tactical_score(), calculate_vanna_charm() (+25 more)

### Community 27 - "test_sell_fills.py"
Cohesion: 0.09
Nodes (11): ActiveManagementTests, _load_active_management(), ActiveManagementHoldingsTests, buy(), buy_doc(), ExecutionsDirCase, FullySoldTests, LoadSellFillsTests (+3 more)

### Community 28 - ".invoke"
Cohesion: 0.08
Nodes (7): CycleTestCase, DailyCalendarTests, FailureTests, _portfolio(), PortfolioAndCliTests, SuccessPathTests, WeeklyTests

### Community 29 - "._namespace"
Cohesion: 0.36
Nodes (3): AdrSpotFallbackTests, _bs(), _chain()

### Community 30 - "EntryUsesActiveManagementTargetsTests"
Cohesion: 0.16
Nodes (5): CumulativeEntryCase, EntryPhaseEntryTests, EntryUsesActiveManagementTargetsTests, write_am(), write_mark()

### Community 31 - "_profile"
Cohesion: 0.14
Nodes (7): ConsumerZeroGammaTests, _gamma(), _gex_field_chain(), GexFieldZeroGammaTests, _net_gex_at_spot(), _profile(), ZeroGammaProfileTests

### Community 32 - "price_signals.py"
Cohesion: 0.17
Nodes (6): fallback_components(), _num(), price_indicators(), price_scores(), rsi(), PriceSignalTests

### Community 33 - "correr_entry_signal"
Cohesion: 0.11
Nodes (18): _activo_vacio(), cargar_estado(), cargar_tenencias(), construir_fila_estado(), _contexto(), correr_entry_signal(), _estado_vacio(), _etiquetar_definiciones() (+10 more)

### Community 34 - "polygon_client.py"
Cohesion: 0.09
Nodes (10): calls_per_minute_configurado(), _limiter_for(), PolygonClient, PolygonTruncated, _RateLimiter, retry_after_seconds(), retry_backoff_seconds(), PolygonBackoffTests (+2 more)

### Community 37 - "VixHorizonTests"
Cohesion: 0.10
Nodes (7): ActiveManagementExpiryTests, _contracts_endpoint(), query(), EntryExpiryTests, _expiries(), RiskScoreExpiryTests, VixHorizonTests

### Community 38 - "test_review_fixes.py"
Cohesion: 0.11
Nodes (10): NoOptionData, PolygonError, PolygonNotFound, _closes(), EntrySignalTierTests, RiskScoreFallbackTests, fake_chain(), EntryPercentileTests (+2 more)

### Community 39 - "resolve_signals_dir"
Cohesion: 0.11
Nodes (11): artifact_path(), default_figures_dir(), entry_state_path(), optimizer_history_path(), per_portfolio_enabled(), pipeline_dir(), _portfolio_identity(), portfolio_signals_dir() (+3 more)

### Community 40 - "screen_candidates"
Cohesion: 0.17
Nodes (7): cansancio_score(), diagnosis_score(), options_favor_score(), options_risk_score(), _pct_rank(), _ratio_score(), screen_candidates()

### Community 41 - ".__init__"
Cohesion: 0.23
Nodes (4): DeAmericanizer, OptionChainCleaner, PortfolioVIX, SingleAssetVIX

### Community 45 - "FillsGatingTests"
Cohesion: 0.33
Nodes (3): _estado(), _fills(), FillsGatingTests

### Community 49 - "export_signals"
Cohesion: 0.16
Nodes (10): _atomic_write(), empty_rotation_state(), export_signals(), load_rotation_state(), nyse_sessions_between(), rotation_state_path(), save_rotation_state(), to_jsonable() (+2 more)

### Community 53 - ".load"
Cohesion: 0.32
Nodes (4): select_cboe_expiries(), select_expiries_for(), YahooMarketLoader, year_fraction()

### Community 54 - "RotationEntryCase"
Cohesion: 0.21
Nodes (3): FullySoldIsNotBoughtAgainTests, RotationEntryCase, RotationTargetsAreTranchedTests

### Community 55 - "gex_headless_requested"
Cohesion: 0.33
Nodes (3): gex_headless_requested(), main(), GexHeadlessTests

### Community 56 - "_ohlc"
Cohesion: 0.09
Nodes (4): _ohlc(), RotationLogicTests, RotationRunTests, DrawdownPauseModeTests

### Community 57 - "run_reporting_module"
Cohesion: 0.47
Nodes (5): plot_leverage_assignment(), plot_loss_distribution(), plot_pcr_vs_weight(), print_executive_summary(), run_reporting_module()

### Community 58 - "run"
Cohesion: 0.12
Nodes (10): build_rebalances(), _custom_tickers(), decide_action(), figure_detector(), options_view(), run(), should_trigger(), update_state() (+2 more)

### Community 62 - "zero_gamma_profile"
Cohesion: 0.16
Nodes (7): calculate_gex(), bs_gamma_matrix(), _linear_root(), _net_gex(), _valid_contracts(), zero_gamma_profile(), compute_zero_gamma_level()

### Community 63 - "AssetMarketData"
Cohesion: 0.20
Nodes (4): AssetMarketData, bracket_pair(), ExpirySlice, SyntheticMarketGenerator

### Community 64 - "drawdown_rotation.py"
Cohesion: 0.23
Nodes (12): figure_top(), main(), _ohlc_polygon(), parse_args(), _pct(), polygon(), print_detector(), print_diagnosis() (+4 more)

### Community 65 - "failure_reason"
Cohesion: 0.17
Nodes (8): fetch_ohlc(), _ohlc_yahoo(), pause_candidates(), price_metrics(), _ret(), run_pause(), _wilder_atr(), failure_reason()

### Community 66 - "select_rotation"
Cohesion: 0.29
Nodes (5): choose_combination(), covariance(), expected_excess(), portfolio_sharpe(), select_rotation()

### Community 67 - "calculate_gex_and_surface_forces"
Cohesion: 0.33
Nodes (4): calculate_gex_and_surface_forces(), calculate_gex_split(), gamma_regime(), perfil_zero_gamma()

### Community 68 - "_refine_bracket"
Cohesion: 0.10
Nodes (6): _grid_roots(), _refine_bracket(), GridRootsTests, RefineBracketTests, _run_with_profile(), ZeroGammaProfileNeverCrashesTests

### Community 72 - "cycle_today"
Cohesion: 0.14
Nodes (13): _add_months(), cycle_today(), entry_phase_info(), entry_start_date(), _fill_date(), _iso_date(), load_active_management_targets(), load_pause_mark() (+5 more)

### Community 77 - "test_pipeline_io.py"
Cohesion: 0.16
Nodes (3): ExportSignalsTests, LoadPortfolioTests, _portfolio()

## Knowledge Gaps
- **13 isolated node(s):** `CBOE VIX methodology (model-free variance)`, `Cornish-Fisher VaR/ES and CVaR`, `Research and educational disclaimer`, `Excluded tickers and warnings (no US-listed options)`, `Macro stress axis (VIX, 10Y yield, dollar index percentiles)` (+8 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 428 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **27 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `RotationEntryCase` connect `RotationEntryCase` to `os`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **What connects `CBOE VIX methodology (model-free variance)`, `Cornish-Fisher VaR/ES and CVaR`, `Research and educational disclaimer` to the rest of the system?**
  _13 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `portfolio_risk_score_leverage.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08048103607770583 - nodes in this community are weakly interconnected._
- **Why does `EntryTrancheLockTests` connect `EntryTrancheLockTests` to `os`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Should `fundamental_analysis.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08082706766917293 - nodes in this community are weakly interconnected._
- **Why does `DailyCalendarTests` connect `.invoke` to `os`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Should `Fix1CumulativeFillsTests` be split into smaller, more focused modules?**
  _Cohesion score 0.1371794871794872 - nodes in this community are weakly interconnected._