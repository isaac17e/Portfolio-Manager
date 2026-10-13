# Graph Report - Portfolio-Manager  (2026-10-13)

## Corpus Check
- 37 files · ~97,355 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 4)

## Summary
- 1636 nodes · 4052 edges · 91 communities (59 shown, 32 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 59 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c0e140f4`
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
- pipeline_io.py
- ._load
- GexExpiryFallbackTests
- gamma_flip_level
- CBOEVarianceEngine
- run_headless
- .cycle
- entry_signal_tool.py
- numpy
- _meta
- resolve_signals_dir
- _as_float
- run_steps
- EntryTrancheLockTests
- active_management.py
- sell
- .invoke
- PolygonClient
- EntryUsesActiveManagementTargetsTests
- test_zero_gamma.py
- price_signals.py
- date
- polygon_client.py
- PerPortfolioEntryStateTests
- test_signal_shapes.py
- VixHorizonTests
- test_review_fixes.py
- viz_utils.py
- screen_candidates
- test_international_fallback.py
- RiskFreeRateTests
- VixWeightsArgsTests
- main
- get_portfolio_chains
- EntryUnitRuleTests
- StepHorizonTests
- PickExpirationTests
- export_signals
- RunCyclePhaseTests
- RunCyclePassesHorizonTests
- os
- test_cycle2_fixes.py
- RotationEntryCase
- compute_var_es
- _ohlc
- _run_with_profile
- run
- .__init__
- UniverseTests
- implied_vol
- load_portfolio_file
- .load
- drawdown_rotation.py
- select_rotation
- verify_signal
- zero_gamma_profile
- calculate_gex_and_surface_forces
- fundamental_state_path
- resolve_horizon
- ShowOrSaveTests
- make_summary
- exclusion_warnings
- dividend_yield_from_info
- LoadPortfolioTests
- PortfolioHorizonDaysTests
- load_portfolio
- ResolveHorizonTests
- cycle_today
- TrancheLockHelperTests
- GexHorizonTests
- PipelineIsolationTests
- load_rotation_state
- ExportSignalsTests
- FullySoldTests

## God Nodes (most connected - your core abstractions)
1. `to_polygon()` - 33 edges
2. `run()` - 31 edges
3. `resolve_instrument()` - 28 edges
4. `to_yahoo()` - 27 edges
5. `NoOptionData` - 26 edges
6. `correr_entry_signal()` - 26 edges
7. `failure_reason()` - 26 edges
8. `main()` - 25 edges
9. `zero_gamma_profile()` - 25 edges
10. `gamma_flip_level()` - 24 edges

## Surprising Connections (you probably didn't know these)
- `AdrSpotFallbackTests` --uses--> `NoOptionData`  [INFERRED]
  tests/test_cycle2_fixes.py → polygon_client.py
- `AdrSpotFallbackTests` --uses--> `PolygonError`  [INFERRED]
  tests/test_cycle2_fixes.py → polygon_client.py
- `AdrSpotFallbackTests` --uses--> `PolygonNotFound`  [INFERRED]
  tests/test_cycle2_fixes.py → polygon_client.py
- `PolygonBackoffTests` --uses--> `PolygonError`  [INFERRED]
  tests/test_cycle1_fixes.py → polygon_client.py
- `FailureReasonTests` --uses--> `NoOptionData`  [INFERRED]
  tests/test_review_fixes.py → polygon_client.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Signal to fills to entry state loop** — readme_entry_signal_tool, readme_pipeline_signals, readme_entry_state_and_fills, readme_portfolio_file [EXTRACTED 1.00]
- **Polygon options-chain driven scripts** — readme_active_management, readme_entry_signal_tool, readme_risk_score_dynamic_leverage, readme_portfolio_vix, readme_portfolio_gex_field, readme_polygon_io [EXTRACTED 1.00]
- **Portfolio risk aggregation via correlation and Euler attribution** — readme_correlation_estimators, readme_euler_risk_attribution, readme_implied_correlation, readme_portfolio_vix, readme_active_management [INFERRED 0.75]

## Communities (91 total, 32 thin omitted)

### Community 0 - "portfolio_risk_score_leverage.py"
Cohesion: 0.07
Nodes (43): bs_gamma(), bs_price(), compute_atm_iv(), compute_corr_cov(), compute_expected_move(), compute_gex_pcr_factor(), compute_gex_profile(), compute_max_drawdown() (+35 more)

### Community 1 - "fundamental_analysis.py"
Cohesion: 0.07
Nodes (34): analizar_cartera(), calcular_corto_plazo(), _current_ratio(), calcular_historico(), calcular_info_adicional(), calcular_largo_plazo(), _roe_signal(), calcular_mediano_plazo() (+26 more)

### Community 2 - "Fix1CumulativeFillsTests"
Cohesion: 0.14
Nodes (6): doc(), EntryPhaseCountTests, ExecDirCase, fill(), Fix1CumulativeFillsTests, Fix2ActiveManagementRealWeightTests

### Community 3 - "portfolio_gex_field.py"
Cohesion: 0.13
Nodes (19): american_delta_gamma(), american_iv_bisection(), american_price(), _bs93_american_call(), _bs93_phi(), bs_price(), build_composite_portfolio_force(), _build_gex_force_function_sigma() (+11 more)

### Community 4 - "run_cycle.py"
Cohesion: 0.12
Nodes (14): _as_text(), atomic_write(), build_parser(), emit_summary(), _json_safe(), _kill_process_group(), _parse_cli_date(), render_summary_text() (+6 more)

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
Cohesion: 0.06
Nodes (27): get_current_price(), _estado(), _fills(), FillsGatingTests, TickerMappingTests, ResolverTierTests, StaggeredEntryTests, adr_warnings() (+19 more)

### Community 9 - "portfolio_vix.py"
Cohesion: 0.13
Nodes (14): resolve_risk_free_rate(), bjerksund_stensland_call(), bjerksund_stensland_price(), crr_american(), escrowed_inputs(), _euro_call_carry(), f(), _parse_args() (+6 more)

### Community 12 - "pipeline_io.py"
Cohesion: 0.08
Nodes (24): cargar_fills(), _as_float_text(), executions_dir(), _file_token(), _fills_candidates(), _flexible_fraction(), load_fills(), load_portfolio_fill_docs() (+16 more)

### Community 13 - "._load"
Cohesion: 0.32
Nodes (3): PortfolioVIXCalculator, ReportPlotter, SmileFit

### Community 14 - "GexExpiryFallbackTests"
Cohesion: 0.24
Nodes (3): _chain(), GexExpiryFallbackTests, fetch()

### Community 15 - "gamma_flip_level"
Cohesion: 0.16
Nodes (4): gamma_flip_crossings(), gamma_flip_level(), FlipRootTests, GammaFlipTests

### Community 17 - "run_headless"
Cohesion: 0.15
Nodes (11): gex_headless_requested(), main(), plot_zero_gamma_profiles(), _resolve_output(), run_headless(), run_live(), _senal_gex(), start_local_file_server() (+3 more)

### Community 18 - ".cycle"
Cohesion: 0.17
Nodes (6): CadenceCase, FirstCycleTests, IdleRunTests, ReuseTests, RotationTests, StepsAndForceTests

### Community 19 - "entry_signal_tool.py"
Cohesion: 0.05
Nodes (55): _activo_vacio(), calcular_espacio_walls(), calcular_expected_move(), calcular_fila_instrumento(), calcular_gex_y_zero_gamma(), calcular_indicadores_proxy(), calcular_indicadores_ticker(), calcular_iv_atm() (+47 more)

### Community 20 - "numpy"
Cohesion: 0.18
Nodes (20): _assemble_regions(), benchmark_implied_sigma(), benchmark_implied_sigmas(), build_implied_correlation(), build_risk_inputs(), _cov_to_corr(), estimate_correlation(), _ewma_cov() (+12 more)

### Community 21 - "_meta"
Cohesion: 0.07
Nodes (10): CleanEnvCase, CycleCase, ExportTests, _meta(), OverrideCycleTests, ParentChildAgreementTests, _portfolio_file(), ResolutionTests (+2 more)

### Community 22 - "resolve_signals_dir"
Cohesion: 0.12
Nodes (9): artifact_path(), entry_state_path(), per_portfolio_enabled(), pipeline_dir(), portfolio_signals_dir(), resolve_signals_dir(), rotation_state_path(), signals_base_dir() (+1 more)

### Community 23 - "_as_float"
Cohesion: 0.25
Nodes (6): accumulate_fills(), _as_float(), _fill_key(), _fill_side(), _stamped_fills(), summarize_holdings()

### Community 24 - "run_steps"
Cohesion: 0.11
Nodes (16): _absorb_signal(), _blank_step(), build_command(), fundamental_next_due(), _iso_or_none(), load_saved_fundamental(), plan_fundamental(), read_fundamental_last_run() (+8 more)

### Community 26 - "active_management.py"
Cohesion: 0.10
Nodes (36): _advertencias_tenencias(), analyze_ticker_options(), apply_diversification_guardrail(), _bsm_d1_d2(), calculate_expected_move(), calculate_gex(), calculate_order_flow(), calculate_tactical_score() (+28 more)

### Community 27 - "sell"
Cohesion: 0.15
Nodes (8): ActiveManagementHoldingsTests, buy(), buy_doc(), ExecutionsDirCase, LoadSellFillsTests, sell(), sell_doc(), SummarizeHoldingsTests

### Community 28 - ".invoke"
Cohesion: 0.08
Nodes (7): CycleTestCase, DailyCalendarTests, FailureTests, _portfolio(), PortfolioAndCliTests, SuccessPathTests, WeeklyTests

### Community 29 - "PolygonClient"
Cohesion: 0.20
Nodes (4): PolygonClient, PolygonBackoffTests, fake_get(), _Resp

### Community 30 - "EntryUsesActiveManagementTargetsTests"
Cohesion: 0.17
Nodes (5): CumulativeEntryCase, EntryPhaseEntryTests, EntryUsesActiveManagementTargetsTests, write_am(), write_mark()

### Community 31 - "test_zero_gamma.py"
Cohesion: 0.07
Nodes (10): ActiveManagementTests, _load_active_management(), RiskRegimeSameDayTests, ConsumerZeroGammaTests, _gamma(), _gex_field_chain(), GexFieldZeroGammaTests, _net_gex_at_spot() (+2 more)

### Community 32 - "price_signals.py"
Cohesion: 0.25
Nodes (3): fallback_components(), price_indicators(), rsi()

### Community 33 - "date"
Cohesion: 0.15
Nodes (11): already_ran_this_week(), daily_due(), entry_phase(), _iso_week(), _now_utc(), nyse_market_close(), nyse_session_dates(), read_weekly_state() (+3 more)

### Community 34 - "polygon_client.py"
Cohesion: 0.16
Nodes (6): calls_per_minute_configurado(), _limiter_for(), PolygonTruncated, _RateLimiter, retry_after_seconds(), retry_backoff_seconds()

### Community 37 - "VixHorizonTests"
Cohesion: 0.10
Nodes (7): ActiveManagementExpiryTests, _contracts_endpoint(), query(), EntryExpiryTests, _expiries(), RiskScoreExpiryTests, VixHorizonTests

### Community 38 - "test_review_fixes.py"
Cohesion: 0.15
Nodes (8): failure_reason(), PolygonError, PolygonNotFound, EntryPercentileTests, FailureReasonTests, GexLiveShellTests, _load_functions(), RiskPriceHistoryTests

### Community 39 - "viz_utils.py"
Cohesion: 0.26
Nodes (7): default_figures_dir(), figure_path(), figures_dir(), headless(), _in_ipython(), _interactive(), show_or_save()

### Community 40 - "screen_candidates"
Cohesion: 0.17
Nodes (7): cansancio_score(), diagnosis_score(), options_favor_score(), options_risk_score(), _pct_rank(), _ratio_score(), screen_candidates()

### Community 41 - "test_international_fallback.py"
Cohesion: 0.13
Nodes (8): NoOptionData, _num(), price_scores(), _closes(), EntrySignalTierTests, PriceSignalTests, RiskScoreFallbackTests, fake_chain()

### Community 44 - "main"
Cohesion: 0.20
Nodes (13): _calendar_failure(), _emit_or_report(), format_fundamental_line(), main(), _not_due(), _preview_steps(), _print_plan(), resolve_cycle_signals() (+5 more)

### Community 45 - "get_portfolio_chains"
Cohesion: 0.15
Nodes (10): calculate_expected_move(), campo_gamma_utilizable(), clamp_iv(), get_dynamic_strike_range(), get_polygon_options_data(), get_portfolio_chains(), _horizonte(), polygon() (+2 more)

### Community 49 - "export_signals"
Cohesion: 0.15
Nodes (10): _atomic_write(), export_signals(), _is_nan(), locate_fills_file(), nyse_sessions_between(), prepare_artifact_path(), save_rotation_state(), to_jsonable() (+2 more)

### Community 52 - "os"
Cohesion: 0.11
Nodes (3): EntryReadsRotationTests, EntrySignalRecordsHorizonTests, RunCycleEntryPhaseFunctionTests

### Community 53 - "test_cycle2_fixes.py"
Cohesion: 0.25
Nodes (4): AdrSpotFallbackTests, _bs(), _chain(), _load_functions()

### Community 54 - "RotationEntryCase"
Cohesion: 0.21
Nodes (3): FullySoldIsNotBoughtAgainTests, RotationEntryCase, RotationTargetsAreTranchedTests

### Community 55 - "compute_var_es"
Cohesion: 0.60
Nodes (5): compute_var_es(), cornish_fisher_es(), cornish_fisher_var(), historical_es(), historical_var()

### Community 56 - "_ohlc"
Cohesion: 0.09
Nodes (4): _ohlc(), RotationLogicTests, RotationRunTests, DrawdownPauseModeTests

### Community 58 - "run"
Cohesion: 0.12
Nodes (16): build_rebalances(), _custom_tickers(), figure_detector(), figure_top(), options_view(), _pct(), print_detector(), print_diagnosis() (+8 more)

### Community 59 - ".__init__"
Cohesion: 0.24
Nodes (3): OptionChainCleaner, PortfolioVIX, VIXConfig

### Community 61 - "implied_vol"
Cohesion: 0.29
Nodes (3): bs_price(), DeAmericanizer, implied_vol()

### Community 62 - "load_portfolio_file"
Cohesion: 0.39
Nodes (6): _invalid(), load_portfolio_file(), _parse_horizon_end(), _parse_tickers(), _parse_weights(), PortfolioError

### Community 63 - ".load"
Cohesion: 0.16
Nodes (6): AssetMarketData, bracket_pair(), ExpirySlice, SingleAssetVIX, SyntheticMarketGenerator, YahooMarketLoader

### Community 65 - "drawdown_rotation.py"
Cohesion: 0.14
Nodes (13): decide_action(), fetch_ohlc(), main(), _ohlc_polygon(), _ohlc_yahoo(), parse_args(), pause_candidates(), polygon() (+5 more)

### Community 66 - "select_rotation"
Cohesion: 0.29
Nodes (5): choose_combination(), covariance(), expected_excess(), portfolio_sharpe(), select_rotation()

### Community 67 - "verify_signal"
Cohesion: 0.29
Nodes (3): CalendarUnavailable, SignalError, verify_signal()

### Community 68 - "zero_gamma_profile"
Cohesion: 0.10
Nodes (11): bs_gamma_matrix(), downsample_profile(), _grid_roots(), _linear_root(), _net_gex(), _refine_bracket(), _valid_contracts(), zero_gamma_profile() (+3 more)

### Community 70 - "calculate_gex_and_surface_forces"
Cohesion: 0.33
Nodes (4): calculate_gex_and_surface_forces(), calculate_gex_split(), gamma_regime(), perfil_zero_gamma()

### Community 71 - "fundamental_state_path"
Cohesion: 0.40
Nodes (4): _cycle_env(), fundamental_state_path(), _portfolio_meta(), rotation_held_extras()

### Community 72 - "resolve_horizon"
Cohesion: 0.15
Nodes (11): _add_months(), entry_start_date(), _fill_date(), _iso_date(), load_active_management_targets(), load_pause_mark(), portfolio_horizon_days(), portfolio_horizon_fields() (+3 more)

### Community 74 - "make_summary"
Cohesion: 0.40
Nodes (4): _fundamental_view(), make_summary(), _now_bogota(), _portfolio_view()

### Community 76 - "dividend_yield_from_info"
Cohesion: 0.32
Nodes (3): get_dividend_yield(), DividendYieldTests, dividend_yield_from_info()

### Community 79 - "load_portfolio"
Cohesion: 0.40
Nodes (3): _fallback_result(), load_portfolio(), _renormalize_weights()

## Knowledge Gaps
- **13 isolated node(s):** `CBOE VIX methodology (model-free variance)`, `Cornish-Fisher VaR/ES and CVaR`, `Research and educational disclaimer`, `Excluded tickers and warnings (no US-listed options)`, `Macro stress axis (VIX, 10Y yield, dollar index percentiles)` (+8 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 443 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **32 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DailyCalendarTests` connect `.invoke` to `os`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **What connects `CBOE VIX methodology (model-free variance)`, `Cornish-Fisher VaR/ES and CVaR`, `Research and educational disclaimer` to the rest of the system?**
  _13 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `portfolio_risk_score_leverage.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06704260651629072 - nodes in this community are weakly interconnected._
- **Why does `RotationEntryCase` connect `RotationEntryCase` to `os`, `EntryUsesActiveManagementTargetsTests`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Should `fundamental_analysis.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06526806526806526 - nodes in this community are weakly interconnected._
- **Why does `TwoPortfolioCycleTests` connect `_meta` to `os`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Should `Fix1CumulativeFillsTests` be split into smaller, more focused modules?**
  _Cohesion score 0.1371794871794872 - nodes in this community are weakly interconnected._