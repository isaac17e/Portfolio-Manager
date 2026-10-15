# Graph Report - Portfolio-Manager  (2026-10-15)

## Corpus Check
- 44 files · ~104,996 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 4)

## Summary
- 1791 nodes · 4494 edges · 102 communities (65 shown, 37 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 88 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `de3abee2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- tickers.py
- fundamental_analysis.py
- .invoke
- portfolio_risk_score_leverage.py
- os
- drawdown_rotation.py
- _meta
- active_management.py
- portfolio_gex_field.py
- Fix1CumulativeFillsTests
- .run_entry
- pipeline_io.py
- test_sell_fills.py
- portfolio_key
- .cycle
- entry_signal_tool.py
- VixHorizonTests
- universe.py
- portfolio_vix.py
- _ohlc
- test_zero_gamma.py
- numpy
- run_cycle.py
- run_headless
- RotationEntryCase
- .current
- math
- polygon_client.py
- get_portfolio_chains
- cycle_today
- gamma_flip_level
- price_signals.py
- exclusion_warnings
- ndarray
- current_holdings
- test_review_fixes.py
- test_zero_gamma_def.py
- main
- date
- plan_fundamental
- EntryTrancheLockTests
- AssetMarketData
- screen_candidates
- resolve_signals_dir
- run_steps
- _Helpers
- zero_gamma_profile
- requirements.txt
- viz_utils.py
- test_international_fallback.py
- DataFrame
- _refine_bracket
- export_signals
- .load
- GexExpiryFallbackTests
- _run_with_profile
- run_pause
- fetch_ohlc
- verify_signal
- _as_float
- daily_due
- _grid_roots
- .__init__
- test_cycle2_fixes.py
- ShowOrSaveTests
- test_signal_shapes.py
- CBOEVarianceEngine
- select_rotation
- load_portfolio_file
- PerPortfolioEntryStateTests
- EntryUnitRuleTests
- __init__.py
- VixWeightsTests
- StepHorizonTests
- run_reporting_module
- RunCyclePhaseTests
- calculate_gex_and_surface_forces
- UniverseTests
- PickExpirationTests
- artifact_path
- ResolveHorizonTests
- RunCyclePassesHorizonTests
- LoadPortfolioTests
- GexFieldZeroGammaTests
- compute_var_es
- RiskFreeRateTests
- GexHorizonTests
- fundamental_state_path
- VixWeightsArgsTests
- TrancheLockHelperTests
- ExportSignalsTests
- .generate
- InvestedFractionTests
- EntrySignalRecordsHorizonTests
- _senal_gestion_activa
- EntryReadsRotationTests
- RunCycleEntryPhaseFunctionTests

## God Nodes (most connected - your core abstractions)
1. `to_polygon()` - 33 edges
2. `run()` - 31 edges
3. `resolve_instrument()` - 28 edges
4. `to_yahoo()` - 28 edges
5. `correr_entry_signal()` - 28 edges
6. `NoOptionData` - 26 edges
7. `zero_gamma_profile()` - 26 edges
8. `failure_reason()` - 26 edges
9. `main()` - 25 edges
10. `gamma_flip_level()` - 24 edges

## Surprising Connections (you probably didn't know these)
- `resolve_horizon()` --implements--> `Portfolio options horizon per script`  [INFERRED]
  pipeline_io.py → README.md
- `PolygonBackoffTests` --uses--> `PolygonError`  [INFERRED]
  tests/test_cycle1_fixes.py → polygon_client.py
- `AdrSpotFallbackTests` --uses--> `NoOptionData`  [INFERRED]
  tests/test_cycle2_fixes.py → polygon_client.py
- `FailureReasonTests` --uses--> `NoOptionData`  [INFERRED]
  tests/test_review_fixes.py → polygon_client.py
- `AdrSpotFallbackTests` --uses--> `PolygonError`  [INFERRED]
  tests/test_cycle2_fixes.py → polygon_client.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Scripts sharing zero-gamma/GEX helpers** — active_management, entry_signal_tool, portfolio_risk_score_leverage, portfolio_gex_field, gex_utils [EXTRACTED 1.00]
- **Scripts writing pipeline signals** — active_management, entry_signal_tool, portfolio_risk_score_leverage, portfolio_vix, portfolio_gex_field, fundamental_analysis, drawdown_rotation [EXTRACTED 1.00]
- **Entry phase flow** — readme_entry_phase, readme_same_day_lock, readme_entry_state_fills, drawdown_rotation, entry_signal_tool [INFERRED 0.85]

## Communities (102 total, 37 thin omitted)

### Community 0 - "tickers.py"
Cohesion: 0.05
Nodes (29): fallback_components(), Ticker resolution tiers (adr/proxy/none), _estado(), _fills(), FillsGatingTests, GexHeadlessTests, TickerMappingTests, ResolverTierTests (+21 more)

### Community 1 - "fundamental_analysis.py"
Cohesion: 0.06
Nodes (35): analizar_cartera(), calcular_corto_plazo(), _current_ratio(), calcular_historico(), calcular_info_adicional(), calcular_largo_plazo(), _roe_signal(), calcular_mediano_plazo() (+27 more)

### Community 2 - ".invoke"
Cohesion: 0.08
Nodes (7): CycleTestCase, DailyCalendarTests, FailureTests, _portfolio(), PortfolioAndCliTests, SuccessPathTests, WeeklyTests

### Community 3 - "portfolio_risk_score_leverage.py"
Cohesion: 0.09
Nodes (31): bs_gamma(), bs_price(), compute_atm_iv(), compute_expected_move(), compute_gex_pcr_factor(), compute_gex_profile(), compute_max_pain(), compute_put_call_ratio() (+23 more)

### Community 5 - "drawdown_rotation.py"
Cohesion: 0.13
Nodes (21): build_rebalances(), _custom_tickers(), decide_action(), figure_detector(), figure_top(), main(), options_view(), parse_args() (+13 more)

### Community 6 - "_meta"
Cohesion: 0.07
Nodes (10): CleanEnvCase, CycleCase, ExportTests, _meta(), OverrideCycleTests, ParentChildAgreementTests, _portfolio_file(), ResolutionTests (+2 more)

### Community 7 - "active_management.py"
Cohesion: 0.14
Nodes (32): analyze_ticker_options(), apply_diversification_guardrail(), _bsm_d1_d2(), calculate_expected_move(), calculate_gex(), calculate_order_flow(), calculate_tactical_score(), calculate_vanna_charm() (+24 more)

### Community 8 - "portfolio_gex_field.py"
Cohesion: 0.16
Nodes (19): american_delta_gamma(), american_iv_bisection(), american_price(), _bs93_american_call(), _bs93_phi(), bs_price(), build_composite_portfolio_force(), _build_gex_force_function_sigma() (+11 more)

### Community 9 - "Fix1CumulativeFillsTests"
Cohesion: 0.14
Nodes (6): doc(), EntryPhaseCountTests, ExecDirCase, fill(), Fix1CumulativeFillsTests, Fix2ActiveManagementRealWeightTests

### Community 10 - ".run_entry"
Cohesion: 0.15
Nodes (6): DayFiveCompletionTests, DaysOneToFourKeepTheScheduleTests, EmptyTrancheTests, EntryCalendarDayBase, ForcedDayThenNormalDayTests, StalePendingTests

### Community 11 - "pipeline_io.py"
Cohesion: 0.08
Nodes (20): apply_entry_fills(), _as_float_text(), _as_int(), _blank_activo(), close_empty_tranche(), entry_floor_day(), fully_sold_tickers(), last_executed_day() (+12 more)

### Community 12 - "test_sell_fills.py"
Cohesion: 0.07
Nodes (12): ActiveManagementTests, _load_active_management(), RiskRegimeSameDayTests, ActiveManagementHoldingsTests, buy(), buy_doc(), ExecutionsDirCase, FullySoldTests (+4 more)

### Community 13 - "portfolio_key"
Cohesion: 0.11
Nodes (13): cargar_fills(), cargar_tenencias(), executions_dir(), _fills_candidates(), holdings_snapshot_path(), load_fills(), load_portfolio_fill_docs(), load_portfolio_fills() (+5 more)

### Community 14 - ".cycle"
Cohesion: 0.17
Nodes (6): CadenceCase, FirstCycleTests, IdleRunTests, ReuseTests, RotationTests, StepsAndForceTests

### Community 15 - "entry_signal_tool.py"
Cohesion: 0.06
Nodes (55): _activo_vacio(), calcular_espacio_walls(), calcular_expected_move(), calcular_fila_instrumento(), calcular_gex_y_zero_gamma(), calcular_indicadores_proxy(), calcular_indicadores_ticker(), calcular_iv_atm() (+47 more)

### Community 16 - "VixHorizonTests"
Cohesion: 0.10
Nodes (7): ActiveManagementExpiryTests, _contracts_endpoint(), query(), EntryExpiryTests, _expiries(), RiskScoreExpiryTests, VixHorizonTests

### Community 17 - "universe.py"
Cohesion: 0.15
Nodes (10): Rotation universe (top S&P500 / NASDAQ by market cap), lxml, build_universe(), clean_symbol_table(), _company_key(), index_constituents(), normalize_tickers(), parse_market_cap() (+2 more)

### Community 18 - "portfolio_vix.py"
Cohesion: 0.09
Nodes (19): actualizar_tenencias(), bjerksund_stensland_call(), bjerksund_stensland_price(), crr_american(), _euro_call_carry(), f(), _parse_args(), _phi() (+11 more)

### Community 19 - "_ohlc"
Cohesion: 0.09
Nodes (4): _ohlc(), RotationLogicTests, RotationRunTests, DrawdownPauseModeTests

### Community 20 - "test_zero_gamma.py"
Cohesion: 0.17
Nodes (6): ConsumerZeroGammaTests, _gamma(), _gex_field_chain(), _net_gex_at_spot(), _profile(), ZeroGammaProfileTests

### Community 21 - "numpy"
Cohesion: 0.16
Nodes (21): _assemble_regions(), benchmark_implied_sigma(), benchmark_implied_sigmas(), build_implied_correlation(), build_risk_inputs(), _cov_to_corr(), estimate_correlation(), _ewma_cov() (+13 more)

### Community 22 - "run_cycle.py"
Cohesion: 0.12
Nodes (15): Cycle orchestrator (run_cycle), _as_text(), atomic_write(), build_parser(), emit_summary(), _json_safe(), _kill_process_group(), _parse_cli_date() (+7 more)

### Community 23 - "run_headless"
Cohesion: 0.14
Nodes (13): downsample_profile(), actualizar_tenencias(), gex_headless_requested(), main(), _meta_senal(), plot_zero_gamma_profiles(), run_headless(), run_live() (+5 more)

### Community 24 - "RotationEntryCase"
Cohesion: 0.09
Nodes (8): CumulativeEntryCase, EntryPhaseEntryTests, EntryUsesActiveManagementTargetsTests, write_am(), write_mark(), FullySoldIsNotBoughtAgainTests, RotationEntryCase, RotationTargetsAreTranchedTests

### Community 25 - ".current"
Cohesion: 0.12
Nodes (11): buy_doc(), FallbackChainTests, fill(), FillsTests, GexWeightsTests, HoldingsCase, ScriptCase, sell_doc() (+3 more)

### Community 26 - "math"
Cohesion: 0.08
Nodes (19): _atomic_write(), empty_rotation_state(), _fallback_result(), _flexible_fraction(), _is_nan(), load_portfolio(), load_rotation_state(), nyse_sessions_between() (+11 more)

### Community 27 - "polygon_client.py"
Cohesion: 0.08
Nodes (13): calls_per_minute_configurado(), _limiter_for(), PolygonClient, PolygonTruncated, _RateLimiter, retry_after_seconds(), retry_backoff_seconds(), Polygon.io options chain input (+5 more)

### Community 28 - "get_portfolio_chains"
Cohesion: 0.14
Nodes (12): calculate_expected_move(), campo_gamma_utilizable(), clamp_iv(), get_current_price(), get_dividend_yield(), get_dynamic_strike_range(), get_polygon_options_data(), get_portfolio_chains() (+4 more)

### Community 29 - "cycle_today"
Cohesion: 0.15
Nodes (12): _add_months(), cycle_today(), entry_phase_info(), entry_start_date(), _fill_date(), _iso_date(), load_active_management_targets(), load_pause_mark() (+4 more)

### Community 30 - "gamma_flip_level"
Cohesion: 0.16
Nodes (4): gamma_flip_crossings(), gamma_flip_level(), FlipRootTests, GammaFlipTests

### Community 31 - "price_signals.py"
Cohesion: 0.19
Nodes (6): _num(), price_indicators(), price_scores(), rsi(), Portfolio Manager README, PriceSignalTests

### Community 34 - "current_holdings"
Cohesion: 0.10
Nodes (14): current_holdings(), _file_token(), _fills_positions(), load_portfolio_sell_fills(), optimizer_history_path(), _parse_iso(), parse_ticker_list(), _positive_float() (+6 more)

### Community 35 - "test_review_fixes.py"
Cohesion: 0.16
Nodes (8): failure_reason(), PolygonError, PolygonNotFound, EntryPercentileTests, FailureReasonTests, GexLiveShellTests, _load_functions(), RiskPriceHistoryTests

### Community 36 - "test_zero_gamma_def.py"
Cohesion: 0.17
Nodes (5): DayFiveTrendTests, DefinitionTagTests, _hist(), _legacy_csv(), PercentileTests

### Community 37 - "main"
Cohesion: 0.16
Nodes (16): _calendar_failure(), _emit_or_report(), format_fundamental_line(), _fundamental_view(), main(), make_summary(), _not_due(), _portfolio_view() (+8 more)

### Community 38 - "date"
Cohesion: 0.21
Nodes (8): already_ran_this_week(), entry_phase(), _iso_week(), nyse_session_dates(), read_weekly_state(), step_environment(), weekly_due(), write_weekly_state()

### Community 39 - "plan_fundamental"
Cohesion: 0.21
Nodes (8): fundamental_next_due(), _iso_or_none(), load_saved_fundamental(), plan_fundamental(), read_fundamental_last_run(), fundamental_failed(), fundamental_ran(), saved_fundamental_tickers()

### Community 41 - "AssetMarketData"
Cohesion: 0.25
Nodes (4): AssetMarketData, bracket_pair(), escrowed_inputs(), SingleAssetVIX

### Community 42 - "screen_candidates"
Cohesion: 0.17
Nodes (7): cansancio_score(), diagnosis_score(), options_favor_score(), options_risk_score(), _pct_rank(), _ratio_score(), screen_candidates()

### Community 43 - "resolve_signals_dir"
Cohesion: 0.13
Nodes (9): default_figures_dir(), entry_state_path(), per_portfolio_enabled(), pipeline_dir(), _portfolio_identity(), portfolio_signals_dir(), resolve_signals_dir(), signals_base_dir() (+1 more)

### Community 44 - "run_steps"
Cohesion: 0.20
Nodes (8): _absorb_signal(), _blank_step(), build_command(), rotation_proposed_tickers(), run_steps(), execute(), step_horizon_days(), _today_bogota()

### Community 45 - "_Helpers"
Cohesion: 0.32
Nodes (3): AttachedStateDayFiveTests, _Helpers, PostForceStateDayFiveTests

### Community 46 - "zero_gamma_profile"
Cohesion: 0.19
Nodes (7): bs_gamma_matrix(), _net_gex(), _valid_contracts(), zero_gamma_profile(), Gamma exposure (GEX), Strike-balance level (old gamma flip), Zero-gamma level (spot grid)

### Community 47 - "requirements.txt"
Cohesion: 0.20
Nodes (9): numpy, pandas, pandas_market_calendars, plotly, python-dateutil, python-dotenv, requests, scipy (+1 more)

### Community 48 - "viz_utils.py"
Cohesion: 0.27
Nodes (7): Headless figure output, figure_path(), figures_dir(), headless(), _in_ipython(), _interactive(), show_or_save()

### Community 49 - "test_international_fallback.py"
Cohesion: 0.18
Nodes (6): NoOptionData, _closes(), EntrySignalTierTests, _load_functions(), RiskScoreFallbackTests, fake_chain()

### Community 50 - "DataFrame"
Cohesion: 0.32
Nodes (3): PortfolioVIXCalculator, ReportPlotter, SmileFit

### Community 51 - "_refine_bracket"
Cohesion: 0.21
Nodes (3): _linear_root(), _refine_bracket(), RefineBracketTests

### Community 52 - "export_signals"
Cohesion: 0.25
Nodes (5): _advertencias_tenencias(), main(), announce_signals_dir(), export_signals(), _now_bogota()

### Community 53 - ".load"
Cohesion: 0.17
Nodes (5): bs_price(), clamp_iv(), DeAmericanizer, implied_vol(), PolygonMarketLoader

### Community 54 - "GexExpiryFallbackTests"
Cohesion: 0.24
Nodes (3): _chain(), GexExpiryFallbackTests, fetch()

### Community 56 - "run_pause"
Cohesion: 0.25
Nodes (5): pause_candidates(), price_metrics(), _ret(), run_pause(), _wilder_atr()

### Community 57 - "fetch_ohlc"
Cohesion: 0.40
Nodes (4): fetch_ohlc(), _ohlc_polygon(), _ohlc_yahoo(), polygon()

### Community 58 - "verify_signal"
Cohesion: 0.29
Nodes (3): CalendarUnavailable, SignalError, verify_signal()

### Community 59 - "_as_float"
Cohesion: 0.17
Nodes (8): accumulate_fills(), apply_rotation_overrides(), _as_float(), _fill_key(), _fill_side(), invested_fraction_from_holdings(), _stamped_fills(), summarize_holdings()

### Community 60 - "daily_due"
Cohesion: 0.33
Nodes (4): daily_due(), _now_bogota(), _now_utc(), nyse_market_close()

### Community 62 - ".__init__"
Cohesion: 0.24
Nodes (3): OptionChainCleaner, PortfolioVIX, VIXConfig

### Community 63 - "test_cycle2_fixes.py"
Cohesion: 0.30
Nodes (3): AdrSpotFallbackTests, _bs(), _chain()

### Community 67 - "select_rotation"
Cohesion: 0.29
Nodes (5): choose_combination(), covariance(), expected_excess(), portfolio_sharpe(), select_rotation()

### Community 68 - "load_portfolio_file"
Cohesion: 0.39
Nodes (6): _invalid(), load_portfolio_file(), _parse_horizon_end(), _parse_tickers(), _parse_weights(), PortfolioError

### Community 74 - "run_reporting_module"
Cohesion: 0.38
Nodes (6): plot_gex_profile(), plot_leverage_assignment(), plot_loss_distribution(), plot_pcr_vs_weight(), print_executive_summary(), run_reporting_module()

### Community 76 - "calculate_gex_and_surface_forces"
Cohesion: 0.33
Nodes (4): calculate_gex_and_surface_forces(), calculate_gex_split(), gamma_regime(), perfil_zero_gamma()

### Community 79 - "artifact_path"
Cohesion: 0.33
Nodes (3): artifact_path(), prepare_artifact_path(), _resolve_output()

### Community 84 - "compute_var_es"
Cohesion: 0.22
Nodes (11): compute_corr_cov(), compute_max_drawdown(), compute_risk_contribution(), compute_sharpe_sortino(), compute_var_es(), compute_volatility(), cornish_fisher_es(), cornish_fisher_var() (+3 more)

### Community 87 - "fundamental_state_path"
Cohesion: 0.40
Nodes (4): _cycle_env(), fundamental_state_path(), _portfolio_meta(), rotation_held_extras()

## Knowledge Gaps
- **21 isolated node(s):** `Fundamental traffic-light scorecard`, `Entry conviction score (0-100, eight signals)`, `numpy`, `pandas`, `plotly` (+16 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 481 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **37 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DailyCalendarTests` connect `.invoke` to `os`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **What connects `Fundamental traffic-light scorecard`, `Entry conviction score (0-100, eight signals)`, `numpy` to the rest of the system?**
  _21 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `tickers.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0519311911716975 - nodes in this community are weakly interconnected._
- **Why does `PerPortfolioEntryStateTests` connect `PerPortfolioEntryStateTests` to `test_cycle2_fixes.py`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Should `fundamental_analysis.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06189640035118525 - nodes in this community are weakly interconnected._
- **Why does `zero_gamma_profile()` connect `zero_gamma_profile` to `portfolio_risk_score_leverage.py`, `active_management.py`, `portfolio_gex_field.py`, `calculate_gex_and_surface_forces`, `entry_signal_tool.py`, `_refine_bracket`, `test_zero_gamma.py`, `numpy`, `_run_with_profile`, `_grid_roots`, `test_cycle2_fixes.py`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Should `.invoke` be split into smaller, more focused modules?**
  _Cohesion score 0.07890122735242548 - nodes in this community are weakly interconnected._