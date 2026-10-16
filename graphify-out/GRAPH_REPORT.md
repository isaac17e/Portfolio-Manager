# Graph Report - Portfolio-Manager  (2026-10-16)

## Corpus Check
- 45 files · ~111,196 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 4)

## Summary
- 1905 nodes · 4803 edges · 113 communities (72 shown, 41 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 86 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `03b98c91`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- tickers.py
- fundamental_analysis.py
- .invoke
- portfolio_risk_score_leverage.py
- os
- run
- _meta
- active_management.py
- portfolio_gex_field.py
- Fix1CumulativeFillsTests
- .run_entry
- pipeline_io.py
- sell
- portfolio_key
- .cycle
- entry_signal_tool.py
- VixHorizonTests
- universe.py
- portfolio_vix.py
- _ohlc
- gamma_flip_level
- numpy
- run_cycle.py
- run_headless
- RotationEntryCase
- .current
- export_signals
- polygon_client.py
- _as_float
- cycle_today
- correr_entry_signal
- price_signals.py
- exclusion_warnings
- ndarray
- current_holdings
- test_review_fixes.py
- _hist
- main
- date
- plan_fundamental
- EntryTrancheLockTests
- .load
- screen_candidates
- resolve_signals_dir
- run_steps
- _Helpers
- EntryToolOverridesTests
- requirements.txt
- viz_utils.py
- NoOptionData
- DataFrame
- zero_gamma_profile
- resolve_instrument
- .load
- GexExpiryFallbackTests
- _run_with_profile
- drawdown_rotation.py
- main
- verify_signal
- summarize_holdings
- daily_due
- re
- .__init__
- ._namespace
- test_international_fallback.py
- test_signal_shapes.py
- CBOEVarianceEngine
- select_rotation
- load_portfolio_file
- PerPortfolioEntryStateTests
- EntryUnitRuleTests
- test_isolation.py
- write
- test_horizon.py
- show_or_save
- RunCyclePhaseTests
- apply_entry_fills
- UniverseTests
- PickExpirationTests
- entry
- ResolveHorizonTests
- RunCyclePassesHorizonTests
- test_pipeline_io.py
- .doc
- FillsGatingTests
- RiskFreeRateTests
- calcular_fila_instrumento
- RiskRegimeSameDayTests
- VixWeightsArgsTests
- TrancheLockHelperTests
- PolygonBackoffTests
- DeAmericanizer
- InvestedFractionTests
- PolygonClient
- emit_summary
- EntryReadsRotationTests
- RunCycleEntryPhaseFunctionTests
- _closes
- GateTests
- dividend_yield_from_info
- reconcile_pending_entry
- no_options_weight_cap
- PortfolioHorizonDaysTests
- copy
- StaggeredEntryTests
- ActiveManagementOverridesTests
- FullySoldTests
- ARES executor agent

## God Nodes (most connected - your core abstractions)
1. `run()` - 35 edges
2. `to_polygon()` - 33 edges
3. `correr_entry_signal()` - 31 edges
4. `resolve_instrument()` - 28 edges
5. `to_yahoo()` - 28 edges
6. `failure_reason()` - 26 edges
7. `zero_gamma_profile()` - 26 edges
8. `main()` - 25 edges
9. `NoOptionData` - 25 edges
10. `gamma_flip_level()` - 24 edges

## Surprising Connections (you probably didn't know these)
- `resolve_horizon()` --implements--> `Portfolio options horizon per script`  [INFERRED]
  pipeline_io.py → README.md
- `PolygonBackoffTests` --uses--> `PolygonClient`  [INFERRED]
  tests/test_cycle1_fixes.py → polygon_client.py
- `PolygonBackoffTests` --uses--> `PolygonError`  [INFERRED]
  tests/test_cycle1_fixes.py → polygon_client.py
- `AdrSpotFallbackTests` --uses--> `PolygonError`  [INFERRED]
  tests/test_cycle2_fixes.py → polygon_client.py
- `AdrSpotFallbackTests` --uses--> `PolygonNotFound`  [INFERRED]
  tests/test_cycle2_fixes.py → polygon_client.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Scripts sharing zero-gamma/GEX helpers** — active_management, entry_signal_tool, portfolio_risk_score_leverage, portfolio_gex_field, gex_utils [EXTRACTED 1.00]
- **Scripts writing pipeline signals** — active_management, entry_signal_tool, portfolio_risk_score_leverage, portfolio_vix, portfolio_gex_field, fundamental_analysis, drawdown_rotation [EXTRACTED 1.00]
- **Entry phase flow** — readme_entry_phase, readme_same_day_lock, readme_entry_state_fills, drawdown_rotation, entry_signal_tool [INFERRED 0.85]

## Communities (113 total, 41 thin omitted)

### Community 0 - "tickers.py"
Cohesion: 0.16
Nodes (15): Ticker resolution tiers (adr/proxy/none), TickerMappingTests, capital_epic_verified(), _clean(), exchange_suffix(), _format_class(), has_us_options(), mapping() (+7 more)

### Community 1 - "fundamental_analysis.py"
Cohesion: 0.06
Nodes (35): analizar_cartera(), calcular_corto_plazo(), _current_ratio(), calcular_historico(), calcular_info_adicional(), calcular_largo_plazo(), _roe_signal(), calcular_mediano_plazo() (+27 more)

### Community 2 - ".invoke"
Cohesion: 0.08
Nodes (7): CycleTestCase, DailyCalendarTests, FailureTests, _portfolio(), PortfolioAndCliTests, SuccessPathTests, WeeklyTests

### Community 3 - "portfolio_risk_score_leverage.py"
Cohesion: 0.07
Nodes (42): bs_gamma(), bs_price(), compute_atm_iv(), compute_corr_cov(), compute_expected_move(), compute_gex_pcr_factor(), compute_gex_profile(), compute_max_drawdown() (+34 more)

### Community 5 - "run"
Cohesion: 0.13
Nodes (15): build_rebalances(), _custom_tickers(), decide_action(), figure_detector(), options_view(), _pct(), print_detector(), print_diagnosis() (+7 more)

### Community 6 - "_meta"
Cohesion: 0.07
Nodes (10): CleanEnvCase, CycleCase, ExportTests, _meta(), OverrideCycleTests, ParentChildAgreementTests, _portfolio_file(), ResolutionTests (+2 more)

### Community 7 - "active_management.py"
Cohesion: 0.13
Nodes (36): analyze_ticker_options(), apply_diversification_guardrail(), benchmark_implied_sigma(), benchmark_implied_sigmas(), _bsm_d1_d2(), build_risk_inputs(), calculate_expected_move(), calculate_gex() (+28 more)

### Community 8 - "portfolio_gex_field.py"
Cohesion: 0.08
Nodes (33): failure_reason(), actualizar_tenencias(), american_delta_gamma(), american_iv_bisection(), american_price(), _bs93_american_call(), _bs93_phi(), bs_price() (+25 more)

### Community 9 - "Fix1CumulativeFillsTests"
Cohesion: 0.14
Nodes (6): doc(), EntryPhaseCountTests, ExecDirCase, fill(), Fix1CumulativeFillsTests, Fix2ActiveManagementRealWeightTests

### Community 10 - ".run_entry"
Cohesion: 0.15
Nodes (6): DayFiveCompletionTests, DaysOneToFourKeepTheScheduleTests, EmptyTrancheTests, EntryCalendarDayBase, ForcedDayThenNormalDayTests, StalePendingTests

### Community 11 - "pipeline_io.py"
Cohesion: 0.14
Nodes (12): _as_float_text(), _fallback_result(), _flexible_fraction(), load_portfolio(), parse_invested_overrides(), _percent_number(), portfolio_capital(), _positive_number() (+4 more)

### Community 12 - "sell"
Cohesion: 0.15
Nodes (8): ActiveManagementHoldingsTests, buy(), buy_doc(), ExecutionsDirCase, LoadSellFillsTests, sell(), sell_doc(), SummarizeHoldingsTests

### Community 13 - "portfolio_key"
Cohesion: 0.12
Nodes (13): cargar_fills(), _empty_overrides(), executions_dir(), _fills_candidates(), holdings_snapshot_path(), load_fills(), load_portfolio_fill_docs(), load_portfolio_fills() (+5 more)

### Community 14 - ".cycle"
Cohesion: 0.17
Nodes (6): CadenceCase, FirstCycleTests, IdleRunTests, ReuseTests, RotationTests, StepsAndForceTests

### Community 15 - "entry_signal_tool.py"
Cohesion: 0.12
Nodes (24): calcular_espacio_walls(), calcular_expected_move(), calcular_gex_y_zero_gamma(), calcular_iv_atm(), calcular_skew(), calcular_smart_money(), calcular_vanna_charm_factor(), calcular_walls() (+16 more)

### Community 16 - "VixHorizonTests"
Cohesion: 0.10
Nodes (7): ActiveManagementExpiryTests, _contracts_endpoint(), query(), EntryExpiryTests, _expiries(), RiskScoreExpiryTests, VixHorizonTests

### Community 17 - "universe.py"
Cohesion: 0.15
Nodes (10): Rotation universe (top S&P500 / NASDAQ by market cap), lxml, build_universe(), clean_symbol_table(), _company_key(), index_constituents(), normalize_tickers(), parse_market_cap() (+2 more)

### Community 18 - "portfolio_vix.py"
Cohesion: 0.11
Nodes (15): actualizar_tenencias(), bjerksund_stensland_call(), bjerksund_stensland_price(), crr_american(), _euro_call_carry(), f(), _parse_args(), _phi() (+7 more)

### Community 19 - "_ohlc"
Cohesion: 0.09
Nodes (4): _ohlc(), RotationLogicTests, RotationRunTests, DrawdownPauseModeTests

### Community 20 - "gamma_flip_level"
Cohesion: 0.07
Nodes (11): gamma_flip_crossings(), gamma_flip_level(), FlipRootTests, GammaFlipTests, ConsumerZeroGammaTests, _gamma(), _gex_field_chain(), GexFieldZeroGammaTests (+3 more)

### Community 21 - "numpy"
Cohesion: 0.16
Nodes (18): _assemble_regions(), build_implied_correlation(), _cov_to_corr(), estimate_correlation(), _ewma_cov(), _ewma_effective_n(), iv_benchmark_historial(), _nearest_pd_corr() (+10 more)

### Community 22 - "run_cycle.py"
Cohesion: 0.15
Nodes (11): Cycle orchestrator (run_cycle), _as_text(), build_parser(), _cycle_env(), fundamental_state_path(), _kill_process_group(), _parse_cli_date(), _portfolio_meta() (+3 more)

### Community 23 - "run_headless"
Cohesion: 0.11
Nodes (16): downsample_profile(), calculate_gradient(), get_portfolio_current_state(), gex_headless_requested(), main(), _meta_senal(), plot_3d_portfolio_field(), plot_zero_gamma_profiles() (+8 more)

### Community 24 - "RotationEntryCase"
Cohesion: 0.09
Nodes (8): CumulativeEntryCase, EntryPhaseEntryTests, EntryUsesActiveManagementTargetsTests, write_am(), write_mark(), FullySoldIsNotBoughtAgainTests, RotationEntryCase, RotationTargetsAreTranchedTests

### Community 25 - ".current"
Cohesion: 0.10
Nodes (12): buy_doc(), FallbackChainTests, fill(), FillsTests, GexWeightsTests, HoldingsCase, ScriptCase, sell_doc() (+4 more)

### Community 26 - "export_signals"
Cohesion: 0.12
Nodes (14): _atomic_write(), empty_rotation_state(), export_signals(), _is_nan(), load_manual_overrides(), fail(), load_rotation_state(), nyse_sessions_between() (+6 more)

### Community 27 - "polygon_client.py"
Cohesion: 0.13
Nodes (8): calls_per_minute_configurado(), _limiter_for(), _RateLimiter, retry_after_seconds(), retry_backoff_seconds(), Polygon.io options chain input, Portfolio Manager scripts suite, Yahoo Finance (yfinance) data

### Community 28 - "_as_float"
Cohesion: 0.08
Nodes (19): _aplicar_overrides_manuales(), apply_buy_gate(), apply_rotation_overrides(), _as_float(), buy_gate(), _canon_ticker(), _check_override_entry(), describe_overrides() (+11 more)

### Community 29 - "cycle_today"
Cohesion: 0.13
Nodes (14): _add_months(), cycle_today(), entry_phase_info(), entry_start_date(), _fill_date(), _iso_date(), load_active_management_targets(), load_pause_mark() (+6 more)

### Community 30 - "correr_entry_signal"
Cohesion: 0.12
Nodes (16): _activo_vacio(), cargar_estado(), cargar_tenencias(), construir_fila_estado(), _contexto(), correr_entry_signal(), _estado_vacio(), _etiquetar_definiciones() (+8 more)

### Community 31 - "price_signals.py"
Cohesion: 0.16
Nodes (8): calcular_indicadores_proxy(), _num(), price_indicators(), price_scores(), rsi(), yahoo_closes(), Portfolio Manager README, PriceSignalTests

### Community 34 - "current_holdings"
Cohesion: 0.16
Nodes (8): current_holdings(), _fills_positions(), _now_bogota(), _parse_iso(), _positive_float(), _snapshot_fresh(), _snapshot_positions(), _weights_from_values()

### Community 35 - "test_review_fixes.py"
Cohesion: 0.10
Nodes (6): ActiveManagementTests, EntryPercentileTests, GexLiveShellTests, _load_active_management(), _load_functions(), RiskPriceHistoryTests

### Community 36 - "_hist"
Cohesion: 0.17
Nodes (5): DayFiveTrendTests, DefinitionTagTests, _hist(), _legacy_csv(), PercentileTests

### Community 37 - "main"
Cohesion: 0.16
Nodes (16): _calendar_failure(), _emit_or_report(), format_fundamental_line(), _fundamental_view(), main(), make_summary(), _not_due(), _portfolio_view() (+8 more)

### Community 38 - "date"
Cohesion: 0.17
Nodes (10): already_ran_this_week(), atomic_write(), entry_phase(), _iso_week(), nyse_session_dates(), read_weekly_state(), step_environment(), weekly_due() (+2 more)

### Community 39 - "plan_fundamental"
Cohesion: 0.21
Nodes (8): fundamental_next_due(), _iso_or_none(), load_saved_fundamental(), plan_fundamental(), read_fundamental_last_run(), fundamental_failed(), fundamental_ran(), saved_fundamental_tickers()

### Community 41 - ".load"
Cohesion: 0.16
Nodes (6): AssetMarketData, bracket_pair(), ExpirySlice, SingleAssetVIX, SyntheticMarketGenerator, YahooMarketLoader

### Community 42 - "screen_candidates"
Cohesion: 0.17
Nodes (7): cansancio_score(), diagnosis_score(), options_favor_score(), options_risk_score(), _pct_rank(), _ratio_score(), screen_candidates()

### Community 43 - "resolve_signals_dir"
Cohesion: 0.09
Nodes (13): artifact_path(), default_figures_dir(), entry_state_path(), manual_overrides_path(), per_portfolio_enabled(), pipeline_dir(), _portfolio_identity(), portfolio_signals_dir() (+5 more)

### Community 44 - "run_steps"
Cohesion: 0.20
Nodes (8): _absorb_signal(), _blank_step(), build_command(), rotation_proposed_tickers(), run_steps(), execute(), step_horizon_days(), _today_bogota()

### Community 45 - "_Helpers"
Cohesion: 0.32
Nodes (3): AttachedStateDayFiveTests, _Helpers, PostForceStateDayFiveTests

### Community 47 - "requirements.txt"
Cohesion: 0.20
Nodes (9): numpy, pandas, pandas_market_calendars, plotly, python-dateutil, python-dotenv, requests, scipy (+1 more)

### Community 48 - "viz_utils.py"
Cohesion: 0.31
Nodes (6): Headless figure output, figure_path(), figures_dir(), headless(), _in_ipython(), _interactive()

### Community 49 - "NoOptionData"
Cohesion: 0.26
Nodes (6): NoOptionData, PolygonError, PolygonNotFound, RiskScoreFallbackTests, fake_chain(), FailureReasonTests

### Community 50 - "DataFrame"
Cohesion: 0.29
Nodes (4): figure_top(), PortfolioVIXCalculator, ReportPlotter, SmileFit

### Community 51 - "zero_gamma_profile"
Cohesion: 0.09
Nodes (13): bs_gamma_matrix(), _grid_roots(), _linear_root(), _net_gex(), _refine_bracket(), _valid_contracts(), zero_gamma_profile(), f() (+5 more)

### Community 52 - "resolve_instrument"
Cohesion: 0.21
Nodes (5): ResolverTierTests, adr_warnings(), options_exclusion(), options_underlying(), resolve_instrument()

### Community 53 - ".load"
Cohesion: 0.20
Nodes (6): clamp_iv(), escrowed_inputs(), PolygonMarketLoader, select_cboe_expiries(), select_expiries_for(), year_fraction()

### Community 54 - "GexExpiryFallbackTests"
Cohesion: 0.24
Nodes (3): _chain(), GexExpiryFallbackTests, fetch()

### Community 56 - "drawdown_rotation.py"
Cohesion: 0.13
Nodes (15): fetch_ohlc(), main(), _ohlc_polygon(), _ohlc_yahoo(), parse_args(), pause_candidates(), polygon(), price_metrics() (+7 more)

### Community 57 - "main"
Cohesion: 0.14
Nodes (10): aplicar_compuerta(), _avisos_overrides(), construir_senal_bloqueada(), construir_senal_entrada(), graficar_resumen(), imprimir_resumen(), main(), objetivos_efectivos() (+2 more)

### Community 58 - "verify_signal"
Cohesion: 0.29
Nodes (3): CalendarUnavailable, SignalError, verify_signal()

### Community 59 - "summarize_holdings"
Cohesion: 0.24
Nodes (5): accumulate_fills(), _fill_key(), _fill_side(), _stamped_fills(), summarize_holdings()

### Community 60 - "daily_due"
Cohesion: 0.33
Nodes (4): daily_due(), _now_bogota(), _now_utc(), nyse_market_close()

### Community 61 - "re"
Cohesion: 0.19
Nodes (7): _file_token(), load_portfolio_sell_fills(), optimizer_history_path(), parse_ticker_list(), _read_sell_fills(), run_ts_stamp(), _sell_fills_candidates()

### Community 63 - "._namespace"
Cohesion: 0.36
Nodes (3): AdrSpotFallbackTests, _bs(), _chain()

### Community 67 - "select_rotation"
Cohesion: 0.29
Nodes (5): choose_combination(), covariance(), expected_excess(), portfolio_sharpe(), select_rotation()

### Community 68 - "load_portfolio_file"
Cohesion: 0.39
Nodes (6): _invalid(), load_portfolio_file(), _parse_horizon_end(), _parse_tickers(), _parse_weights(), PortfolioError

### Community 72 - "write"
Cohesion: 0.26
Nodes (5): DrawdownRotationOverridesTests, EntryImportTests, RunCycleExtrasTests, TempDirCase, write()

### Community 73 - "test_horizon.py"
Cohesion: 0.10
Nodes (4): EntrySignalRecordsHorizonTests, GexHorizonTests, _loaded(), StepHorizonTests

### Community 74 - "show_or_save"
Cohesion: 0.12
Nodes (12): _advertencias_tenencias(), main(), _peso_real(), _senal_gestion_activa(), announce_signals_dir(), fully_sold_tickers(), plot_leverage_assignment(), plot_loss_distribution() (+4 more)

### Community 76 - "apply_entry_fills"
Cohesion: 0.23
Nodes (7): apply_entry_fills(), _as_int(), _blank_activo(), entry_floor_day(), last_executed_day(), resolve_cycle_day(), suggest_cycle_day()

### Community 79 - "entry"
Cohesion: 0.29
Nodes (3): EffectiveTargetsTests, entry(), ValidatorTests

### Community 82 - "test_pipeline_io.py"
Cohesion: 0.16
Nodes (3): ExportSignalsTests, LoadPortfolioTests, _portfolio()

### Community 84 - "FillsGatingTests"
Cohesion: 0.33
Nodes (3): _estado(), _fills(), FillsGatingTests

### Community 86 - "calcular_fila_instrumento"
Cohesion: 0.20
Nodes (7): calcular_fila_instrumento(), calcular_indicadores_ticker(), evaluar_flujo_opciones(), fila_escalonada(), _filas_misma_definicion(), _pct_entrada(), percentile_historico()

### Community 90 - "PolygonBackoffTests"
Cohesion: 0.28
Nodes (3): PolygonBackoffTests, fake_get(), _Resp

### Community 91 - "DeAmericanizer"
Cohesion: 0.29
Nodes (3): bs_price(), DeAmericanizer, implied_vol()

### Community 94 - "emit_summary"
Cohesion: 0.29
Nodes (5): emit_summary(), _json_safe(), render_summary_text(), summary_latest_path(), summary_portfolio_dir()

### Community 103 - "reconcile_pending_entry"
Cohesion: 0.33
Nodes (3): close_empty_tranche(), pending_is_empty_tranche(), reconcile_pending_entry()

### Community 104 - "no_options_weight_cap"
Cohesion: 0.33
Nodes (3): fallback_components(), _env_float(), no_options_weight_cap()

## Knowledge Gaps
- **21 isolated node(s):** `Fundamental traffic-light scorecard`, `Entry conviction score (0-100, eight signals)`, `CBOE model-free variance extension`, `Cycle orchestrator (run_cycle)`, `Portfolio options horizon per script` (+16 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 510 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **41 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `EntryToolOverridesTests` connect `EntryToolOverridesTests` to `.doc`, `os`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **What connects `Fundamental traffic-light scorecard`, `Entry conviction score (0-100, eight signals)`, `CBOE model-free variance extension` to the rest of the system?**
  _21 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `fundamental_analysis.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06331976481230213 - nodes in this community are weakly interconnected._
- **Why does `exclusion_warnings()` connect `exclusion_warnings` to `test_international_fallback.py`, `tickers.py`, `portfolio_risk_score_leverage.py`, `active_management.py`, `portfolio_gex_field.py`, `show_or_save`, `entry_signal_tool.py`, `portfolio_vix.py`, `run_headless`, `correr_entry_signal`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Should `.invoke` be split into smaller, more focused modules?**
  _Cohesion score 0.07890122735242548 - nodes in this community are weakly interconnected._
- **Should `portfolio_risk_score_leverage.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0746606334841629 - nodes in this community are weakly interconnected._
- **Should `run` be split into smaller, more focused modules?**
  _Cohesion score 0.13450292397660818 - nodes in this community are weakly interconnected._