# Graph Report - Portfolio-Manager  (2026-10-14)

## Corpus Check
- 43 files · ~101,607 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 4)

## Summary
- 1705 nodes · 4253 edges · 102 communities (63 shown, 39 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 51 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8aef1127`
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
- .cycle
- entry_signal_tool.py
- numpy
- _meta
- resolve_signals_dir
- export_signals
- run_steps
- EntryTrancheLockTests
- drawdown_rotation.py
- test_sell_fills.py
- .invoke
- RotationEntryCase
- get_portfolio_chains
- test_zero_gamma.py
- price_signals.py
- date
- polygon_client.py
- PerPortfolioEntryStateTests
- _load_function
- VixHorizonTests
- _load_active_management
- viz_utils.py
- RiskRegimeSameDayTests
- _Helpers
- RiskFreeRateTests
- VixWeightsArgsTests
- main
- cargar_estado
- EntryUnitRuleTests
- StepHorizonTests
- PickExpirationTests
- zero_gamma_profile
- RunCyclePhaseTests
- RunCyclePassesHorizonTests
- os
- screen_candidates
- .run_entry
- calcular_fila_instrumento
- _ohlc
- _run_with_profile
- run
- .__init__
- UniverseTests
- implied_vol
- compute_var_es
- .load
- GexFieldZeroGammaTests
- _grid_roots
- select_rotation
- verify_signal
- _refine_bracket
- load_portfolio
- failure_reason
- fundamental_state_path
- pipeline_io.py
- ShowOrSaveTests
- make_summary
- .test_vix_loaders_exclude_proxy_and_none_and_use_adr
- dividend_yield_from_info
- LoadPortfolioTests
- PortfolioHorizonDaysTests
- main
- ResolveHorizonTests
- resolve_horizon
- TrancheLockHelperTests
- PipelineIsolationTests
- load_portfolio_file
- reconcile_pending_entry
- calculate_gex_and_surface_forces
- cycle_today
- _load_functions
- EntryReadsRotationTests
- InvestedFractionTests
- EntrySignalRecordsHorizonTests
- RunCycleEntryPhaseFunctionTests
- pandas
- EntryPercentileTests
- GexLiveShellTests
- correr_entry_signal
- entry_floor_day

## God Nodes (most connected - your core abstractions)
1. `to_polygon()` - 33 edges
2. `run()` - 31 edges
3. `correr_entry_signal()` - 28 edges
4. `resolve_instrument()` - 28 edges
5. `to_yahoo()` - 27 edges
6. `failure_reason()` - 26 edges
7. `main()` - 25 edges
8. `zero_gamma_profile()` - 25 edges
9. `NoOptionData` - 24 edges
10. `gamma_flip_level()` - 24 edges

## Surprising Connections (you probably didn't know these)
- `PolygonBackoffTests` --uses--> `PolygonClient`  [INFERRED]
  tests/test_cycle1_fixes.py → polygon_client.py
- `PolygonBackoffTests` --uses--> `PolygonError`  [INFERRED]
  tests/test_cycle1_fixes.py → polygon_client.py
- `AdrSpotFallbackTests` --uses--> `PolygonError`  [INFERRED]
  tests/test_cycle2_fixes.py → polygon_client.py
- `RiskScoreFallbackTests` --uses--> `PolygonError`  [INFERRED]
  tests/test_international_fallback.py → polygon_client.py
- `FailureReasonTests` --uses--> `PolygonError`  [INFERRED]
  tests/test_review_fixes.py → polygon_client.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Signal to fills to entry state loop** — readme_entry_signal_tool, readme_pipeline_signals, readme_entry_state_and_fills, readme_portfolio_file [EXTRACTED 1.00]
- **Polygon options-chain driven scripts** — readme_active_management, readme_entry_signal_tool, readme_risk_score_dynamic_leverage, readme_portfolio_vix, readme_portfolio_gex_field, readme_polygon_io [EXTRACTED 1.00]
- **Portfolio risk aggregation via correlation and Euler attribution** — readme_correlation_estimators, readme_euler_risk_attribution, readme_implied_correlation, readme_portfolio_vix, readme_active_management [INFERRED 0.75]

## Communities (102 total, 39 thin omitted)

### Community 0 - "portfolio_risk_score_leverage.py"
Cohesion: 0.09
Nodes (35): bs_gamma(), bs_price(), compute_atm_iv(), compute_expected_move(), compute_gex_pcr_factor(), compute_gex_profile(), compute_max_pain(), compute_put_call_ratio() (+27 more)

### Community 1 - "fundamental_analysis.py"
Cohesion: 0.06
Nodes (34): analizar_cartera(), calcular_corto_plazo(), _current_ratio(), calcular_historico(), calcular_info_adicional(), calcular_largo_plazo(), _roe_signal(), calcular_mediano_plazo() (+26 more)

### Community 2 - "Fix1CumulativeFillsTests"
Cohesion: 0.14
Nodes (6): doc(), EntryPhaseCountTests, ExecDirCase, fill(), Fix1CumulativeFillsTests, Fix2ActiveManagementRealWeightTests

### Community 3 - "portfolio_gex_field.py"
Cohesion: 0.16
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
Nodes (27): get_current_price(), fallback_components(), _estado(), _fills(), FillsGatingTests, TickerMappingTests, ResolverTierTests, StaggeredEntryTests (+19 more)

### Community 9 - "portfolio_vix.py"
Cohesion: 0.13
Nodes (15): _is_nan(), resolve_risk_free_rate(), bjerksund_stensland_call(), bjerksund_stensland_price(), crr_american(), escrowed_inputs(), _euro_call_carry(), f() (+7 more)

### Community 12 - "portfolio_key"
Cohesion: 0.15
Nodes (10): executions_dir(), _file_token(), _fills_candidates(), locate_fills_file(), optimizer_history_path(), portfolio_fills_path(), portfolio_key(), _read_sell_fills() (+2 more)

### Community 13 - "DataFrame"
Cohesion: 0.32
Nodes (3): PortfolioVIXCalculator, ReportPlotter, SmileFit

### Community 14 - "GexExpiryFallbackTests"
Cohesion: 0.24
Nodes (3): _chain(), GexExpiryFallbackTests, fetch()

### Community 15 - "gamma_flip_level"
Cohesion: 0.16
Nodes (4): gamma_flip_crossings(), gamma_flip_level(), FlipRootTests, GammaFlipTests

### Community 17 - "run_headless"
Cohesion: 0.13
Nodes (12): downsample_profile(), gex_headless_requested(), main(), plot_zero_gamma_profiles(), _resolve_output(), run_headless(), run_live(), _senal_gex() (+4 more)

### Community 18 - ".cycle"
Cohesion: 0.17
Nodes (6): CadenceCase, FirstCycleTests, IdleRunTests, ReuseTests, RotationTests, StepsAndForceTests

### Community 19 - "entry_signal_tool.py"
Cohesion: 0.14
Nodes (20): calcular_espacio_walls(), calcular_expected_move(), calcular_gex_y_zero_gamma(), calcular_iv_atm(), calcular_skew(), calcular_smart_money(), calcular_vanna_charm_factor(), calcular_walls() (+12 more)

### Community 20 - "numpy"
Cohesion: 0.16
Nodes (21): _assemble_regions(), benchmark_implied_sigma(), benchmark_implied_sigmas(), build_implied_correlation(), build_risk_inputs(), _cov_to_corr(), estimate_correlation(), _ewma_cov() (+13 more)

### Community 21 - "_meta"
Cohesion: 0.07
Nodes (10): CleanEnvCase, CycleCase, ExportTests, _meta(), OverrideCycleTests, ParentChildAgreementTests, _portfolio_file(), ResolutionTests (+2 more)

### Community 22 - "resolve_signals_dir"
Cohesion: 0.12
Nodes (10): artifact_path(), default_figures_dir(), entry_state_path(), per_portfolio_enabled(), pipeline_dir(), _portfolio_identity(), portfolio_signals_dir(), resolve_signals_dir() (+2 more)

### Community 23 - "export_signals"
Cohesion: 0.15
Nodes (11): _atomic_write(), empty_rotation_state(), export_signals(), load_rotation_state(), _now_bogota(), prepare_artifact_path(), rotation_state_path(), save_rotation_state() (+3 more)

### Community 24 - "run_steps"
Cohesion: 0.11
Nodes (16): _absorb_signal(), _blank_step(), build_command(), fundamental_next_due(), _iso_or_none(), load_saved_fundamental(), plan_fundamental(), read_fundamental_last_run() (+8 more)

### Community 26 - "drawdown_rotation.py"
Cohesion: 0.16
Nodes (10): decide_action(), main(), _ohlc_polygon(), parse_args(), polygon(), price_metrics(), _ret(), should_trigger() (+2 more)

### Community 27 - "test_sell_fills.py"
Cohesion: 0.13
Nodes (9): ActiveManagementHoldingsTests, buy(), buy_doc(), ExecutionsDirCase, FullySoldTests, LoadSellFillsTests, sell(), sell_doc() (+1 more)

### Community 28 - ".invoke"
Cohesion: 0.08
Nodes (7): CycleTestCase, DailyCalendarTests, FailureTests, _portfolio(), PortfolioAndCliTests, SuccessPathTests, WeeklyTests

### Community 29 - "RotationEntryCase"
Cohesion: 0.09
Nodes (8): CumulativeEntryCase, EntryPhaseEntryTests, EntryUsesActiveManagementTargetsTests, write_am(), write_mark(), FullySoldIsNotBoughtAgainTests, RotationEntryCase, RotationTargetsAreTranchedTests

### Community 30 - "get_portfolio_chains"
Cohesion: 0.14
Nodes (11): calculate_expected_move(), campo_gamma_utilizable(), clamp_iv(), get_dividend_yield(), get_dynamic_strike_range(), get_polygon_options_data(), get_portfolio_chains(), _horizonte() (+3 more)

### Community 31 - "test_zero_gamma.py"
Cohesion: 0.17
Nodes (6): ConsumerZeroGammaTests, _gamma(), _gex_field_chain(), _net_gex_at_spot(), _profile(), ZeroGammaProfileTests

### Community 32 - "price_signals.py"
Cohesion: 0.16
Nodes (7): _num(), price_indicators(), price_scores(), rsi(), yahoo_closes(), _closes(), PriceSignalTests

### Community 33 - "date"
Cohesion: 0.15
Nodes (11): already_ran_this_week(), daily_due(), entry_phase(), _iso_week(), _now_utc(), nyse_market_close(), nyse_session_dates(), read_weekly_state() (+3 more)

### Community 34 - "polygon_client.py"
Cohesion: 0.05
Nodes (20): calls_per_minute_configurado(), _limiter_for(), NoOptionData, PolygonClient, PolygonError, PolygonNotFound, PolygonTruncated, _RateLimiter (+12 more)

### Community 37 - "VixHorizonTests"
Cohesion: 0.10
Nodes (7): ActiveManagementExpiryTests, _contracts_endpoint(), query(), EntryExpiryTests, _expiries(), RiskScoreExpiryTests, VixHorizonTests

### Community 39 - "viz_utils.py"
Cohesion: 0.31
Nodes (6): figure_path(), figures_dir(), headless(), _in_ipython(), _interactive(), show_or_save()

### Community 41 - "_Helpers"
Cohesion: 0.32
Nodes (3): AttachedStateDayFiveTests, _Helpers, PostForceStateDayFiveTests

### Community 44 - "main"
Cohesion: 0.20
Nodes (13): _calendar_failure(), _emit_or_report(), format_fundamental_line(), main(), _not_due(), _preview_steps(), _print_plan(), resolve_cycle_signals() (+5 more)

### Community 45 - "cargar_estado"
Cohesion: 0.43
Nodes (7): _activo_vacio(), cargar_estado(), _estado_vacio(), guardar_estado(), normalizar_estado(), _portafolio_del_estado(), ruta_estado()

### Community 49 - "zero_gamma_profile"
Cohesion: 0.21
Nodes (5): bs_gamma_matrix(), _net_gex(), _valid_contracts(), zero_gamma_profile(), f()

### Community 53 - "screen_candidates"
Cohesion: 0.17
Nodes (7): cansancio_score(), diagnosis_score(), options_favor_score(), options_risk_score(), _pct_rank(), _ratio_score(), screen_candidates()

### Community 54 - ".run_entry"
Cohesion: 0.15
Nodes (6): DayFiveCompletionTests, DaysOneToFourKeepTheScheduleTests, EmptyTrancheTests, EntryCalendarDayBase, ForcedDayThenNormalDayTests, StalePendingTests

### Community 55 - "calcular_fila_instrumento"
Cohesion: 0.22
Nodes (7): calcular_fila_instrumento(), calcular_indicadores_proxy(), calcular_indicadores_ticker(), fila_escalonada(), _filas_misma_definicion(), _pct_entrada(), percentile_historico()

### Community 56 - "_ohlc"
Cohesion: 0.09
Nodes (4): _ohlc(), RotationLogicTests, RotationRunTests, DrawdownPauseModeTests

### Community 58 - "run"
Cohesion: 0.14
Nodes (15): build_rebalances(), _custom_tickers(), figure_detector(), figure_top(), options_view(), _pct(), print_detector(), print_diagnosis() (+7 more)

### Community 59 - ".__init__"
Cohesion: 0.24
Nodes (3): OptionChainCleaner, PortfolioVIX, VIXConfig

### Community 61 - "implied_vol"
Cohesion: 0.29
Nodes (3): bs_price(), DeAmericanizer, implied_vol()

### Community 62 - "compute_var_es"
Cohesion: 0.22
Nodes (11): compute_corr_cov(), compute_max_drawdown(), compute_risk_contribution(), compute_sharpe_sortino(), compute_var_es(), compute_volatility(), cornish_fisher_es(), cornish_fisher_var() (+3 more)

### Community 63 - ".load"
Cohesion: 0.16
Nodes (6): AssetMarketData, bracket_pair(), ExpirySlice, SingleAssetVIX, SyntheticMarketGenerator, YahooMarketLoader

### Community 66 - "select_rotation"
Cohesion: 0.29
Nodes (5): choose_combination(), covariance(), expected_excess(), portfolio_sharpe(), select_rotation()

### Community 67 - "verify_signal"
Cohesion: 0.29
Nodes (3): CalendarUnavailable, SignalError, verify_signal()

### Community 68 - "_refine_bracket"
Cohesion: 0.24
Nodes (3): _linear_root(), _refine_bracket(), RefineBracketTests

### Community 69 - "load_portfolio"
Cohesion: 0.40
Nodes (3): _fallback_result(), load_portfolio(), _renormalize_weights()

### Community 70 - "failure_reason"
Cohesion: 0.25
Nodes (5): fetch_ohlc(), _ohlc_yahoo(), pause_candidates(), run_pause(), failure_reason()

### Community 71 - "fundamental_state_path"
Cohesion: 0.40
Nodes (4): _cycle_env(), fundamental_state_path(), _portfolio_meta(), rotation_held_extras()

### Community 72 - "pipeline_io.py"
Cohesion: 0.08
Nodes (22): cargar_fills(), accumulate_fills(), apply_entry_fills(), _as_float(), _as_float_text(), _blank_activo(), _fill_key(), _fill_side() (+14 more)

### Community 74 - "make_summary"
Cohesion: 0.40
Nodes (4): _fundamental_view(), make_summary(), _now_bogota(), _portfolio_view()

### Community 79 - "main"
Cohesion: 0.22
Nodes (7): construir_senal_bloqueada(), construir_senal_entrada(), graficar_resumen(), imprimir_resumen(), main(), parse_entry_args(), _truthy()

### Community 81 - "resolve_horizon"
Cohesion: 0.13
Nodes (12): _add_months(), entry_start_date(), _fill_date(), _iso_date(), load_active_management_targets(), load_pause_mark(), nyse_sessions_between(), portfolio_horizon_days() (+4 more)

### Community 83 - "PipelineIsolationTests"
Cohesion: 0.13
Nodes (3): GexHorizonTests, PipelineIsolationTests, ExportSignalsTests

### Community 84 - "load_portfolio_file"
Cohesion: 0.39
Nodes (6): _invalid(), load_portfolio_file(), _parse_horizon_end(), _parse_tickers(), _parse_weights(), PortfolioError

### Community 87 - "reconcile_pending_entry"
Cohesion: 0.33
Nodes (3): close_empty_tranche(), pending_is_empty_tranche(), reconcile_pending_entry()

### Community 88 - "calculate_gex_and_surface_forces"
Cohesion: 0.33
Nodes (4): calculate_gex_and_surface_forces(), calculate_gex_split(), gamma_regime(), perfil_zero_gamma()

### Community 95 - "pandas"
Cohesion: 0.11
Nodes (37): _advertencias_tenencias(), analyze_ticker_options(), apply_diversification_guardrail(), _bsm_d1_d2(), calculate_expected_move(), calculate_gex(), calculate_order_flow(), calculate_tactical_score() (+29 more)

### Community 98 - "correr_entry_signal"
Cohesion: 0.12
Nodes (11): cargar_tenencias(), construir_fila_estado(), _contexto(), correr_entry_signal(), _etiquetar_definiciones(), evaluar_flujo_opciones(), _texto(), _tramo_de_dia_anterior() (+3 more)

### Community 99 - "entry_floor_day"
Cohesion: 0.33
Nodes (5): _as_int(), entry_floor_day(), last_executed_day(), resolve_cycle_day(), suggest_cycle_day()

## Knowledge Gaps
- **13 isolated node(s):** `CBOE VIX methodology (model-free variance)`, `Cornish-Fisher VaR/ES and CVaR`, `Research and educational disclaimer`, `Excluded tickers and warnings (no US-listed options)`, `Macro stress axis (VIX, 10Y yield, dollar index percentiles)` (+8 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 456 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **39 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `EntryTrancheLockTests` connect `EntryTrancheLockTests` to `os`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **What connects `CBOE VIX methodology (model-free variance)`, `Cornish-Fisher VaR/ES and CVaR`, `Research and educational disclaimer` to the rest of the system?**
  _13 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `portfolio_risk_score_leverage.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08599033816425121 - nodes in this community are weakly interconnected._
- **Why does `SmileBuilder` connect `ndarray` to `portfolio_vix.py`, `.__init__`, `implied_vol`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Should `fundamental_analysis.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05962732919254658 - nodes in this community are weakly interconnected._
- **Why does `EntryUnitRuleTests` connect `EntryUnitRuleTests` to `os`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Should `Fix1CumulativeFillsTests` be split into smaller, more focused modules?**
  _Cohesion score 0.1371794871794872 - nodes in this community are weakly interconnected._