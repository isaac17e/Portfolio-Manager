# Graph Report - Portfolio-Manager  (2026-10-13)

## Corpus Check
- 43 files · ~101,915 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 4)

## Summary
- 1654 nodes · 4101 edges · 105 communities (62 shown, 43 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 59 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `91afe3e5`
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
- _hist
- tickers.py
- portfolio_vix.py
- ndarray
- .load
- portfolio_key
- ._load
- GexExpiryFallbackTests
- gamma_flip_level
- CBOEVarianceEngine
- run_headless
- .cycle
- entry_signal_tool.py
- numpy
- _meta
- entry_state_path
- _as_float
- run_steps
- EntryTrancheLockTests
- active_management.py
- sell
- .invoke
- PolygonClient
- RotationEntryCase
- _profile
- price_signals.py
- date
- polygon_client.py
- PerPortfolioEntryStateTests
- test_signal_shapes.py
- VixHorizonTests
- test_review_fixes.py
- viz_utils.py
- cansancio_score
- NoOptionData
- RiskFreeRateTests
- VixWeightsArgsTests
- main
- correr_entry_signal
- EntryUnitRuleTests
- StepHorizonTests
- PickExpirationTests
- resolve_instrument
- RunCyclePhaseTests
- RunCyclePassesHorizonTests
- os
- ._namespace
- _Helpers
- calcular_fila_instrumento
- _ohlc
- _run_with_profile
- drawdown_rotation.py
- .__init__
- UniverseTests
- implied_vol
- load_portfolio_file
- .load
- failure_reason
- select_rotation
- verify_signal
- zero_gamma_profile
- FillsGatingTests
- fundamental_state_path
- pipeline_io.py
- ShowOrSaveTests
- make_summary
- exclusion_warnings
- dividend_yield_from_info
- LoadPortfolioTests
- PortfolioHorizonDaysTests
- main
- ResolveHorizonTests
- cycle_today
- TrancheLockHelperTests
- GexHorizonTests
- PipelineIsolationTests
- export_signals
- ExportSignalsTests
- FullySoldTests
- screen_candidates
- tickers_a_analizar
- price_scores
- fully_sold_tickers
- StaggeredEntryTests
- _senal_gestion_activa
- construir_fila_estado
- resolve_cycle_day
- no_options_weight_cap
- cargar_historial
- EntryReadsRotationTests
- EntrySignalRecordsHorizonTests
- RunCycleEntryPhaseFunctionTests

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
- `PolygonBackoffTests` --uses--> `PolygonError`  [INFERRED]
  tests/test_cycle1_fixes.py → polygon_client.py
- `AdrSpotFallbackTests` --uses--> `PolygonError`  [INFERRED]
  tests/test_cycle2_fixes.py → polygon_client.py
- `RiskScoreFallbackTests` --uses--> `PolygonError`  [INFERRED]
  tests/test_international_fallback.py → polygon_client.py
- `AdrSpotFallbackTests` --uses--> `PolygonNotFound`  [INFERRED]
  tests/test_cycle2_fixes.py → polygon_client.py
- `FailureReasonTests` --uses--> `NoOptionData`  [INFERRED]
  tests/test_review_fixes.py → polygon_client.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Signal to fills to entry state loop** — readme_entry_signal_tool, readme_pipeline_signals, readme_entry_state_and_fills, readme_portfolio_file [EXTRACTED 1.00]
- **Polygon options-chain driven scripts** — readme_active_management, readme_entry_signal_tool, readme_risk_score_dynamic_leverage, readme_portfolio_vix, readme_portfolio_gex_field, readme_polygon_io [EXTRACTED 1.00]
- **Portfolio risk aggregation via correlation and Euler attribution** — readme_correlation_estimators, readme_euler_risk_attribution, readme_implied_correlation, readme_portfolio_vix, readme_active_management [INFERRED 0.75]

## Communities (105 total, 43 thin omitted)

### Community 0 - "portfolio_risk_score_leverage.py"
Cohesion: 0.07
Nodes (45): bs_gamma(), bs_price(), compute_atm_iv(), compute_corr_cov(), compute_expected_move(), compute_gex_pcr_factor(), compute_gex_profile(), compute_max_drawdown() (+37 more)

### Community 1 - "fundamental_analysis.py"
Cohesion: 0.08
Nodes (31): analizar_cartera(), calcular_corto_plazo(), _current_ratio(), calcular_historico(), calcular_info_adicional(), calcular_largo_plazo(), _roe_signal(), calcular_mediano_plazo() (+23 more)

### Community 2 - "Fix1CumulativeFillsTests"
Cohesion: 0.14
Nodes (6): doc(), EntryPhaseCountTests, ExecDirCase, fill(), Fix1CumulativeFillsTests, Fix2ActiveManagementRealWeightTests

### Community 3 - "portfolio_gex_field.py"
Cohesion: 0.08
Nodes (35): american_delta_gamma(), american_iv_bisection(), american_price(), _bs93_american_call(), _bs93_phi(), bs_price(), build_composite_portfolio_force(), _build_gex_force_function_sigma() (+27 more)

### Community 4 - "run_cycle.py"
Cohesion: 0.12
Nodes (14): _as_text(), atomic_write(), build_parser(), emit_summary(), _json_safe(), _kill_process_group(), _parse_cli_date(), render_summary_text() (+6 more)

### Community 5 - "universe.py"
Cohesion: 0.18
Nodes (8): build_universe(), clean_symbol_table(), _company_key(), index_constituents(), normalize_tickers(), parse_market_cap(), scrape_table(), take_top()

### Community 6 - "Tactical active management engine"
Cohesion: 0.08
Nodes (39): Portfolio Manager README, Tactical active management engine, CBOE VIX methodology (model-free variance), Concentration guardrail (1.5x equal-share risk), Cornish-Fisher VaR/ES and CVaR, Correlation estimators (sample, EWMA, random-matrix filtered), De-Americanization (Bjerksund-Stensland 1993 / CRR binomial), Research and educational disclaimer (+31 more)

### Community 7 - "_hist"
Cohesion: 0.17
Nodes (5): DayFiveTrendTests, DefinitionTagTests, _hist(), _legacy_csv(), PercentileTests

### Community 8 - "tickers.py"
Cohesion: 0.16
Nodes (15): TickerMappingTests, capital_epic_verified(), _class_parts(), _clean(), exchange_suffix(), _format_class(), has_us_options(), mapping() (+7 more)

### Community 9 - "portfolio_vix.py"
Cohesion: 0.13
Nodes (14): resolve_risk_free_rate(), bjerksund_stensland_call(), bjerksund_stensland_price(), crr_american(), escrowed_inputs(), _euro_call_carry(), f(), _parse_args() (+6 more)

### Community 12 - "portfolio_key"
Cohesion: 0.09
Nodes (19): cargar_fills(), _atomic_write(), executions_dir(), _fills_candidates(), _is_nan(), load_fills(), load_portfolio_fill_docs(), load_portfolio_fills() (+11 more)

### Community 13 - "._load"
Cohesion: 0.32
Nodes (3): PortfolioVIXCalculator, ReportPlotter, SmileFit

### Community 14 - "GexExpiryFallbackTests"
Cohesion: 0.24
Nodes (3): _chain(), GexExpiryFallbackTests, fetch()

### Community 15 - "gamma_flip_level"
Cohesion: 0.12
Nodes (5): gamma_flip_crossings(), gamma_flip_level(), FlipRootTests, GammaFlipTests, GexFieldZeroGammaTests

### Community 17 - "run_headless"
Cohesion: 0.13
Nodes (12): artifact_path(), gex_headless_requested(), main(), plot_zero_gamma_profiles(), _resolve_output(), run_headless(), run_live(), _senal_gex() (+4 more)

### Community 18 - ".cycle"
Cohesion: 0.17
Nodes (6): CadenceCase, FirstCycleTests, IdleRunTests, ReuseTests, RotationTests, StepsAndForceTests

### Community 19 - "entry_signal_tool.py"
Cohesion: 0.17
Nodes (18): calcular_espacio_walls(), calcular_expected_move(), calcular_gex_y_zero_gamma(), calcular_iv_atm(), calcular_skew(), calcular_smart_money(), calcular_vanna_charm_factor(), calcular_walls() (+10 more)

### Community 20 - "numpy"
Cohesion: 0.20
Nodes (15): _assemble_regions(), build_implied_correlation(), _cov_to_corr(), estimate_correlation(), _ewma_cov(), _ewma_effective_n(), _nearest_pd_corr(), _pair_weights() (+7 more)

### Community 21 - "_meta"
Cohesion: 0.07
Nodes (10): CleanEnvCase, CycleCase, ExportTests, _meta(), OverrideCycleTests, ParentChildAgreementTests, _portfolio_file(), ResolutionTests (+2 more)

### Community 22 - "entry_state_path"
Cohesion: 0.20
Nodes (5): entry_state_path(), pipeline_dir(), _portfolio_identity(), portfolio_signals_dir(), signals_base_dir()

### Community 23 - "_as_float"
Cohesion: 0.25
Nodes (6): accumulate_fills(), _as_float(), _fill_key(), _fill_side(), _stamped_fills(), summarize_holdings()

### Community 24 - "run_steps"
Cohesion: 0.11
Nodes (16): _absorb_signal(), _blank_step(), build_command(), fundamental_next_due(), _iso_or_none(), load_saved_fundamental(), plan_fundamental(), read_fundamental_last_run() (+8 more)

### Community 26 - "active_management.py"
Cohesion: 0.13
Nodes (36): analyze_ticker_options(), apply_diversification_guardrail(), benchmark_implied_sigma(), benchmark_implied_sigmas(), _bsm_d1_d2(), build_risk_inputs(), calculate_expected_move(), calculate_gex() (+28 more)

### Community 27 - "sell"
Cohesion: 0.16
Nodes (8): ActiveManagementHoldingsTests, buy(), buy_doc(), ExecutionsDirCase, LoadSellFillsTests, sell(), sell_doc(), SummarizeHoldingsTests

### Community 28 - ".invoke"
Cohesion: 0.08
Nodes (7): CycleTestCase, DailyCalendarTests, FailureTests, _portfolio(), PortfolioAndCliTests, SuccessPathTests, WeeklyTests

### Community 29 - "PolygonClient"
Cohesion: 0.20
Nodes (4): PolygonClient, PolygonBackoffTests, fake_get(), _Resp

### Community 30 - "RotationEntryCase"
Cohesion: 0.09
Nodes (8): CumulativeEntryCase, EntryPhaseEntryTests, EntryUsesActiveManagementTargetsTests, write_am(), write_mark(), FullySoldIsNotBoughtAgainTests, RotationEntryCase, RotationTargetsAreTranchedTests

### Community 31 - "_profile"
Cohesion: 0.07
Nodes (9): ActiveManagementTests, _load_active_management(), RiskRegimeSameDayTests, ConsumerZeroGammaTests, _gamma(), _gex_field_chain(), _net_gex_at_spot(), _profile() (+1 more)

### Community 32 - "price_signals.py"
Cohesion: 0.15
Nodes (6): fallback_components(), spot_listado_us(), spot_paridad_put_call(), price_indicators(), rsi(), yahoo_closes()

### Community 33 - "date"
Cohesion: 0.15
Nodes (11): already_ran_this_week(), daily_due(), entry_phase(), _iso_week(), _now_utc(), nyse_market_close(), nyse_session_dates(), read_weekly_state() (+3 more)

### Community 34 - "polygon_client.py"
Cohesion: 0.14
Nodes (6): calls_per_minute_configurado(), _limiter_for(), PolygonTruncated, _RateLimiter, retry_after_seconds(), retry_backoff_seconds()

### Community 37 - "VixHorizonTests"
Cohesion: 0.10
Nodes (7): ActiveManagementExpiryTests, _contracts_endpoint(), query(), EntryExpiryTests, _expiries(), RiskScoreExpiryTests, VixHorizonTests

### Community 38 - "test_review_fixes.py"
Cohesion: 0.16
Nodes (7): PolygonError, PolygonNotFound, EntryPercentileTests, FailureReasonTests, GexLiveShellTests, _load_functions(), RiskPriceHistoryTests

### Community 39 - "viz_utils.py"
Cohesion: 0.09
Nodes (16): default_figures_dir(), _file_token(), load_portfolio_sell_fills(), optimizer_history_path(), parse_ticker_list(), per_portfolio_enabled(), _read_sell_fills(), run_ts_stamp() (+8 more)

### Community 40 - "cansancio_score"
Cohesion: 0.29
Nodes (4): cansancio_score(), diagnosis_score(), options_risk_score(), _ratio_score()

### Community 41 - "NoOptionData"
Cohesion: 0.20
Nodes (5): NoOptionData, _closes(), EntrySignalTierTests, RiskScoreFallbackTests, fake_chain()

### Community 44 - "main"
Cohesion: 0.20
Nodes (13): _calendar_failure(), _emit_or_report(), format_fundamental_line(), main(), _not_due(), _preview_steps(), _print_plan(), resolve_cycle_signals() (+5 more)

### Community 45 - "correr_entry_signal"
Cohesion: 0.16
Nodes (13): _activo_vacio(), cargar_estado(), cargar_tenencias(), _contexto(), correr_entry_signal(), _estado_vacio(), _etiquetar_definiciones(), guardar_estado() (+5 more)

### Community 49 - "resolve_instrument"
Cohesion: 0.21
Nodes (5): ResolverTierTests, adr_warnings(), options_exclusion(), options_underlying(), resolve_instrument()

### Community 53 - "._namespace"
Cohesion: 0.36
Nodes (3): AdrSpotFallbackTests, _bs(), _chain()

### Community 54 - "_Helpers"
Cohesion: 0.32
Nodes (3): AttachedStateDayFiveTests, _Helpers, PostForceStateDayFiveTests

### Community 55 - "calcular_fila_instrumento"
Cohesion: 0.22
Nodes (7): calcular_fila_instrumento(), calcular_indicadores_proxy(), calcular_indicadores_ticker(), fila_escalonada(), _filas_misma_definicion(), _pct_entrada(), percentile_historico()

### Community 56 - "_ohlc"
Cohesion: 0.09
Nodes (4): _ohlc(), RotationLogicTests, RotationRunTests, DrawdownPauseModeTests

### Community 58 - "drawdown_rotation.py"
Cohesion: 0.17
Nodes (16): build_rebalances(), _custom_tickers(), decide_action(), figure_detector(), options_view(), _pct(), print_detector(), print_diagnosis() (+8 more)

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

### Community 65 - "failure_reason"
Cohesion: 0.14
Nodes (10): fetch_ohlc(), _ohlc_polygon(), _ohlc_yahoo(), pause_candidates(), polygon(), price_metrics(), _ret(), run_pause() (+2 more)

### Community 66 - "select_rotation"
Cohesion: 0.29
Nodes (5): choose_combination(), covariance(), expected_excess(), portfolio_sharpe(), select_rotation()

### Community 67 - "verify_signal"
Cohesion: 0.29
Nodes (3): CalendarUnavailable, SignalError, verify_signal()

### Community 68 - "zero_gamma_profile"
Cohesion: 0.11
Nodes (10): bs_gamma_matrix(), _grid_roots(), _linear_root(), _net_gex(), _refine_bracket(), _valid_contracts(), zero_gamma_profile(), f() (+2 more)

### Community 70 - "FillsGatingTests"
Cohesion: 0.33
Nodes (3): _estado(), _fills(), FillsGatingTests

### Community 71 - "fundamental_state_path"
Cohesion: 0.40
Nodes (4): _cycle_env(), fundamental_state_path(), _portfolio_meta(), rotation_held_extras()

### Community 72 - "pipeline_io.py"
Cohesion: 0.08
Nodes (24): _add_months(), apply_entry_fills(), _as_float_text(), _blank_activo(), entry_start_date(), _fallback_result(), _fill_date(), _flexible_fraction() (+16 more)

### Community 74 - "make_summary"
Cohesion: 0.40
Nodes (4): _fundamental_view(), make_summary(), _now_bogota(), _portfolio_view()

### Community 79 - "main"
Cohesion: 0.22
Nodes (7): construir_senal_bloqueada(), construir_senal_entrada(), graficar_resumen(), imprimir_resumen(), main(), parse_entry_args(), _truthy()

### Community 85 - "export_signals"
Cohesion: 0.15
Nodes (9): main(), main(), parse_args(), announce_signals_dir(), empty_rotation_state(), export_signals(), load_pause_mark(), load_rotation_state() (+1 more)

### Community 92 - "screen_candidates"
Cohesion: 0.29
Nodes (4): figure_top(), options_favor_score(), _pct_rank(), screen_candidates()

### Community 94 - "price_scores"
Cohesion: 0.38
Nodes (3): _num(), price_scores(), PriceSignalTests

### Community 95 - "fully_sold_tickers"
Cohesion: 0.33
Nodes (3): _advertencias_tenencias(), fully_sold_tickers(), rotation_reentered()

### Community 98 - "construir_fila_estado"
Cohesion: 0.50
Nodes (3): construir_fila_estado(), evaluar_flujo_opciones(), _texto()

## Knowledge Gaps
- **13 isolated node(s):** `CBOE VIX methodology (model-free variance)`, `Cornish-Fisher VaR/ES and CVaR`, `Research and educational disclaimer`, `Excluded tickers and warnings (no US-listed options)`, `Macro stress axis (VIX, 10Y yield, dollar index percentiles)` (+8 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 447 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **43 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PerPortfolioEntryStateTests` connect `PerPortfolioEntryStateTests` to `os`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **What connects `CBOE VIX methodology (model-free variance)`, `Cornish-Fisher VaR/ES and CVaR`, `Research and educational disclaimer` to the rest of the system?**
  _13 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `portfolio_risk_score_leverage.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07077922077922078 - nodes in this community are weakly interconnected._
- **Why does `EntryTrancheLockTests` connect `EntryTrancheLockTests` to `os`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Should `fundamental_analysis.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08145363408521303 - nodes in this community are weakly interconnected._
- **Why does `RiskRegimeSameDayTests` connect `_profile` to `test_review_fixes.py`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Should `Fix1CumulativeFillsTests` be split into smaller, more focused modules?**
  _Cohesion score 0.1371794871794872 - nodes in this community are weakly interconnected._