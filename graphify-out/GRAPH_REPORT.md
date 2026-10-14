# Graph Report - Portfolio-Manager  (2026-10-14)

## Corpus Check
- 43 files · ~101,607 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 4)

## Summary
- 1704 nodes · 4265 edges · 91 communities (60 shown, 31 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 62 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d3610b33`
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
- DataFrame
- GexExpiryFallbackTests
- test_review_fixes.py
- CBOEVarianceEngine
- run_headless
- .cycle
- entry_signal_tool.py
- build_implied_correlation
- _meta
- load_rotation_state
- _as_float
- run_steps
- EntryTrancheLockTests
- pandas
- test_sell_fills.py
- .invoke
- RotationEntryCase
- EntryUsesActiveManagementTargetsTests
- test_zero_gamma.py
- price_signals.py
- json
- polygon_client.py
- PerPortfolioEntryStateTests
- test_signal_shapes.py
- VixHorizonTests
- _load_active_management
- viz_utils.py
- RiskRegimeSameDayTests
- NoOptionData
- RiskFreeRateTests
- VixWeightsArgsTests
- main
- cargar_estado
- EntryUnitRuleTests
- StepHorizonTests
- PickExpirationTests
- resolve_instrument
- RunCyclePhaseTests
- RunCyclePassesHorizonTests
- os
- escrowed_inputs
- .run_entry
- calcular_fila_instrumento
- _ohlc
- _run_with_profile
- drawdown_rotation.py
- .__init__
- test_drawdown_rotation.py
- implied_vol
- yahoo_closes
- .load
- GexFieldZeroGammaTests
- argparse
- select_rotation
- verify_signal
- numpy
- load_portfolio
- FillsGatingTests
- fundamental_state_path
- pipeline_io.py
- ShowOrSaveTests
- daily_due
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
- ExportSignalsTests
- active_management.py
- StaggeredEntryTests
- correr_entry_signal
- apply_entry_fills

## God Nodes (most connected - your core abstractions)
1. `to_polygon()` - 33 edges
2. `run()` - 31 edges
3. `NoOptionData` - 29 edges
4. `correr_entry_signal()` - 28 edges
5. `resolve_instrument()` - 28 edges
6. `to_yahoo()` - 27 edges
7. `failure_reason()` - 26 edges
8. `zero_gamma_profile()` - 25 edges
9. `main()` - 25 edges
10. `gamma_flip_level()` - 24 edges

## Surprising Connections (you probably didn't know these)
- `RiskScoreFallbackTests` --uses--> `PolygonError`  [INFERRED]
  tests/test_international_fallback.py → polygon_client.py
- `AdrSpotFallbackTests` --uses--> `NoOptionData`  [INFERRED]
  tests/test_cycle2_fixes.py → polygon_client.py
- `FailureReasonTests` --uses--> `NoOptionData`  [INFERRED]
  tests/test_review_fixes.py → polygon_client.py
- `_profile()` --calls--> `zero_gamma_profile()`  [EXTRACTED]
  tests/test_zero_gamma.py → gex_utils.py
- `_run_with_profile()` --calls--> `zero_gamma_profile()`  [EXTRACTED]
  tests/test_zero_gamma_robust.py → gex_utils.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Signal to fills to entry state loop** — readme_entry_signal_tool, readme_pipeline_signals, readme_entry_state_and_fills, readme_portfolio_file [EXTRACTED 1.00]
- **Polygon options-chain driven scripts** — readme_active_management, readme_entry_signal_tool, readme_risk_score_dynamic_leverage, readme_portfolio_vix, readme_portfolio_gex_field, readme_polygon_io [EXTRACTED 1.00]
- **Portfolio risk aggregation via correlation and Euler attribution** — readme_correlation_estimators, readme_euler_risk_attribution, readme_implied_correlation, readme_portfolio_vix, readme_active_management [INFERRED 0.75]

## Communities (91 total, 31 thin omitted)

### Community 0 - "portfolio_risk_score_leverage.py"
Cohesion: 0.07
Nodes (44): bs_gamma(), bs_price(), compute_corr_cov(), compute_gex_pcr_factor(), compute_gex_profile(), compute_max_drawdown(), compute_max_pain(), compute_put_call_ratio() (+36 more)

### Community 1 - "fundamental_analysis.py"
Cohesion: 0.07
Nodes (33): analizar_cartera(), calcular_corto_plazo(), _current_ratio(), calcular_historico(), calcular_info_adicional(), calcular_largo_plazo(), _roe_signal(), calcular_mediano_plazo() (+25 more)

### Community 2 - "Fix1CumulativeFillsTests"
Cohesion: 0.14
Nodes (6): doc(), EntryPhaseCountTests, ExecDirCase, fill(), Fix1CumulativeFillsTests, Fix2ActiveManagementRealWeightTests

### Community 3 - "portfolio_gex_field.py"
Cohesion: 0.08
Nodes (34): failure_reason(), american_delta_gamma(), american_iv_bisection(), american_price(), _bs93_american_call(), _bs93_phi(), bs_price(), build_composite_portfolio_force() (+26 more)

### Community 4 - "run_cycle.py"
Cohesion: 0.18
Nodes (11): _as_text(), _invalid(), _kill_process_group(), load_portfolio_file(), _parse_horizon_end(), _parse_tickers(), _parse_weights(), PortfolioError (+3 more)

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
Nodes (15): get_current_price(), TickerMappingTests, capital_epic_verified(), _clean(), exchange_suffix(), _format_class(), has_us_options(), mapping() (+7 more)

### Community 9 - "portfolio_vix.py"
Cohesion: 0.13
Nodes (15): resolve_horizon(), resolve_risk_free_rate(), bjerksund_stensland_call(), bjerksund_stensland_price(), crr_american(), _euro_call_carry(), f(), _parse_args() (+7 more)

### Community 12 - "portfolio_key"
Cohesion: 0.15
Nodes (9): per_portfolio_enabled(), portfolio_key(), emit_summary(), _json_safe(), render_summary_text(), _resolve_path(), resolve_weekly_state_path(), summary_latest_path() (+1 more)

### Community 13 - "DataFrame"
Cohesion: 0.32
Nodes (3): PortfolioVIXCalculator, ReportPlotter, SmileFit

### Community 14 - "GexExpiryFallbackTests"
Cohesion: 0.24
Nodes (3): _chain(), GexExpiryFallbackTests, fetch()

### Community 15 - "test_review_fixes.py"
Cohesion: 0.09
Nodes (8): gamma_flip_crossings(), gamma_flip_level(), FlipRootTests, EntryPercentileTests, GammaFlipTests, GexLiveShellTests, _load_functions(), RiskPriceHistoryTests

### Community 17 - "run_headless"
Cohesion: 0.15
Nodes (11): gex_headless_requested(), main(), plot_zero_gamma_profiles(), _resolve_output(), run_headless(), run_live(), _senal_gex(), start_local_file_server() (+3 more)

### Community 18 - ".cycle"
Cohesion: 0.11
Nodes (9): tickers_a_analizar(), parse_ticker_list(), CadenceCase, FirstCycleTests, IdleRunTests, ReuseTests, RotationTests, StepsAndForceTests (+1 more)

### Community 19 - "entry_signal_tool.py"
Cohesion: 0.15
Nodes (20): calcular_espacio_walls(), calcular_expected_move(), calcular_gex_y_zero_gamma(), calcular_iv_atm(), calcular_skew(), calcular_smart_money(), calcular_vanna_charm_factor(), calcular_walls() (+12 more)

### Community 20 - "build_implied_correlation"
Cohesion: 0.14
Nodes (19): _assemble_regions(), benchmark_implied_sigma(), benchmark_implied_sigmas(), build_implied_correlation(), build_risk_inputs(), _cov_to_corr(), estimate_correlation(), _ewma_cov() (+11 more)

### Community 21 - "_meta"
Cohesion: 0.07
Nodes (10): CleanEnvCase, CycleCase, ExportTests, _meta(), OverrideCycleTests, ParentChildAgreementTests, _portfolio_file(), ResolutionTests (+2 more)

### Community 22 - "load_rotation_state"
Cohesion: 0.15
Nodes (7): empty_rotation_state(), load_rotation_state(), pipeline_dir(), _portfolio_identity(), portfolio_signals_dir(), rotation_state_path(), signals_base_dir()

### Community 23 - "_as_float"
Cohesion: 0.31
Nodes (5): apply_rotation_overrides(), _as_float(), _fill_key(), _fill_side(), summarize_holdings()

### Community 24 - "run_steps"
Cohesion: 0.12
Nodes (15): _absorb_signal(), _blank_step(), build_command(), fundamental_next_due(), _iso_or_none(), load_saved_fundamental(), plan_fundamental(), rotation_proposed_tickers() (+7 more)

### Community 26 - "pandas"
Cohesion: 0.19
Nodes (17): analyze_ticker_options(), apply_diversification_guardrail(), _bsm_d1_d2(), calculate_expected_move(), calculate_gex(), calculate_order_flow(), calculate_vanna_charm(), euler_risk_attribution() (+9 more)

### Community 27 - "test_sell_fills.py"
Cohesion: 0.13
Nodes (9): ActiveManagementHoldingsTests, buy(), buy_doc(), ExecutionsDirCase, FullySoldTests, LoadSellFillsTests, sell(), sell_doc() (+1 more)

### Community 28 - ".invoke"
Cohesion: 0.08
Nodes (7): CycleTestCase, DailyCalendarTests, FailureTests, _portfolio(), PortfolioAndCliTests, SuccessPathTests, WeeklyTests

### Community 29 - "RotationEntryCase"
Cohesion: 0.21
Nodes (3): FullySoldIsNotBoughtAgainTests, RotationEntryCase, RotationTargetsAreTranchedTests

### Community 30 - "EntryUsesActiveManagementTargetsTests"
Cohesion: 0.17
Nodes (5): CumulativeEntryCase, EntryPhaseEntryTests, EntryUsesActiveManagementTargetsTests, write_am(), write_mark()

### Community 31 - "test_zero_gamma.py"
Cohesion: 0.15
Nodes (7): _load_functions(), ConsumerZeroGammaTests, _gamma(), _gex_field_chain(), _net_gex_at_spot(), _profile(), ZeroGammaProfileTests

### Community 32 - "price_signals.py"
Cohesion: 0.21
Nodes (5): _num(), price_indicators(), price_scores(), rsi(), PriceSignalTests

### Community 33 - "json"
Cohesion: 0.15
Nodes (11): already_ran_this_week(), atomic_write(), entry_phase(), _iso_week(), nyse_session_dates(), read_fundamental_last_run(), read_weekly_state(), step_environment() (+3 more)

### Community 34 - "polygon_client.py"
Cohesion: 0.07
Nodes (15): calls_per_minute_configurado(), _limiter_for(), PolygonClient, PolygonError, PolygonNotFound, PolygonTruncated, _RateLimiter, retry_after_seconds() (+7 more)

### Community 37 - "VixHorizonTests"
Cohesion: 0.10
Nodes (7): ActiveManagementExpiryTests, _contracts_endpoint(), query(), EntryExpiryTests, _expiries(), RiskScoreExpiryTests, VixHorizonTests

### Community 39 - "viz_utils.py"
Cohesion: 0.12
Nodes (14): default_figures_dir(), _file_token(), load_portfolio_sell_fills(), optimizer_history_path(), _read_sell_fills(), run_ts_stamp(), _sell_fills_candidates(), uses_portfolio_layout() (+6 more)

### Community 41 - "NoOptionData"
Cohesion: 0.20
Nodes (5): NoOptionData, _closes(), EntrySignalTierTests, RiskScoreFallbackTests, fake_chain()

### Community 44 - "main"
Cohesion: 0.20
Nodes (14): _calendar_failure(), _emit_or_report(), format_fundamental_line(), _fundamental_view(), main(), make_summary(), _not_due(), _portfolio_view() (+6 more)

### Community 45 - "cargar_estado"
Cohesion: 0.31
Nodes (8): _activo_vacio(), cargar_estado(), _estado_vacio(), guardar_estado(), normalizar_estado(), _portafolio_del_estado(), ruta_estado(), entry_state_path()

### Community 49 - "resolve_instrument"
Cohesion: 0.16
Nodes (7): ResolverTierTests, adr_warnings(), _env_float(), no_options_weight_cap(), options_exclusion(), options_underlying(), resolve_instrument()

### Community 52 - "os"
Cohesion: 0.10
Nodes (4): InvestedFractionTests, _row(), EntrySignalRecordsHorizonTests, RunCycleEntryPhaseFunctionTests

### Community 53 - "escrowed_inputs"
Cohesion: 0.33
Nodes (3): bracket_pair(), escrowed_inputs(), SingleAssetVIX

### Community 54 - ".run_entry"
Cohesion: 0.11
Nodes (9): AttachedStateDayFiveTests, _Helpers, PostForceStateDayFiveTests, DayFiveCompletionTests, DaysOneToFourKeepTheScheduleTests, EmptyTrancheTests, EntryCalendarDayBase, ForcedDayThenNormalDayTests (+1 more)

### Community 55 - "calcular_fila_instrumento"
Cohesion: 0.22
Nodes (7): calcular_fila_instrumento(), calcular_indicadores_proxy(), calcular_indicadores_ticker(), fila_escalonada(), _filas_misma_definicion(), _pct_entrada(), percentile_historico()

### Community 56 - "_ohlc"
Cohesion: 0.09
Nodes (4): _ohlc(), RotationLogicTests, RotationRunTests, DrawdownPauseModeTests

### Community 58 - "drawdown_rotation.py"
Cohesion: 0.07
Nodes (35): build_rebalances(), cansancio_score(), _custom_tickers(), decide_action(), diagnosis_score(), fetch_ohlc(), figure_detector(), figure_top() (+27 more)

### Community 60 - "test_drawdown_rotation.py"
Cohesion: 0.20
Nodes (3): EntryReadsRotationTests, _table(), UniverseTests

### Community 61 - "implied_vol"
Cohesion: 0.29
Nodes (3): bs_price(), DeAmericanizer, implied_vol()

### Community 62 - "yahoo_closes"
Cohesion: 0.33
Nodes (3): spot_listado_us(), spot_paridad_put_call(), yahoo_closes()

### Community 63 - ".load"
Cohesion: 0.27
Nodes (4): AssetMarketData, ExpirySlice, SyntheticMarketGenerator, YahooMarketLoader

### Community 66 - "select_rotation"
Cohesion: 0.29
Nodes (5): choose_combination(), covariance(), expected_excess(), portfolio_sharpe(), select_rotation()

### Community 67 - "verify_signal"
Cohesion: 0.29
Nodes (3): CalendarUnavailable, SignalError, verify_signal()

### Community 68 - "numpy"
Cohesion: 0.09
Nodes (13): bs_gamma_matrix(), downsample_profile(), _grid_roots(), _linear_root(), _net_gex(), _refine_bracket(), _valid_contracts(), zero_gamma_profile() (+5 more)

### Community 70 - "FillsGatingTests"
Cohesion: 0.33
Nodes (3): _estado(), _fills(), FillsGatingTests

### Community 71 - "fundamental_state_path"
Cohesion: 0.40
Nodes (4): _cycle_env(), fundamental_state_path(), _portfolio_meta(), rotation_held_extras()

### Community 72 - "pipeline_io.py"
Cohesion: 0.07
Nodes (27): accumulate_fills(), _as_float_text(), _atomic_write(), executions_dir(), export_signals(), _fallback_result(), _fills_candidates(), _flexible_fraction() (+19 more)

### Community 74 - "daily_due"
Cohesion: 0.33
Nodes (4): daily_due(), _now_bogota(), _now_utc(), nyse_market_close()

### Community 76 - "dividend_yield_from_info"
Cohesion: 0.32
Nodes (3): get_dividend_yield(), DividendYieldTests, dividend_yield_from_info()

### Community 79 - "main"
Cohesion: 0.22
Nodes (7): construir_senal_bloqueada(), construir_senal_entrada(), graficar_resumen(), imprimir_resumen(), main(), parse_entry_args(), _truthy()

### Community 81 - "cycle_today"
Cohesion: 0.14
Nodes (13): _add_months(), cycle_today(), entry_phase_info(), entry_start_date(), _fill_date(), _iso_date(), load_active_management_targets(), load_pause_mark() (+5 more)

### Community 95 - "active_management.py"
Cohesion: 0.12
Nodes (22): _advertencias_tenencias(), calculate_tactical_score(), cargar_historial_riesgo(), evaluar_regimen_riesgo(), generate_executive_dashboard(), iv_benchmark_historial(), main(), _peso_real() (+14 more)

### Community 98 - "correr_entry_signal"
Cohesion: 0.11
Nodes (12): cargar_fills(), cargar_tenencias(), construir_fila_estado(), _contexto(), correr_entry_signal(), _etiquetar_definiciones(), evaluar_flujo_opciones(), _texto() (+4 more)

### Community 99 - "apply_entry_fills"
Cohesion: 0.14
Nodes (10): apply_entry_fills(), _as_int(), _blank_activo(), close_empty_tranche(), entry_floor_day(), last_executed_day(), pending_is_empty_tranche(), reconcile_pending_entry() (+2 more)

## Knowledge Gaps
- **13 isolated node(s):** `CBOE VIX methodology (model-free variance)`, `Cornish-Fisher VaR/ES and CVaR`, `Research and educational disclaimer`, `Excluded tickers and warnings (no US-listed options)`, `Macro stress axis (VIX, 10Y yield, dollar index percentiles)` (+8 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 454 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **31 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `EntryTrancheLockTests` connect `EntryTrancheLockTests` to `os`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **What connects `CBOE VIX methodology (model-free variance)`, `Cornish-Fisher VaR/ES and CVaR`, `Research and educational disclaimer` to the rest of the system?**
  _13 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `portfolio_risk_score_leverage.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06883116883116883 - nodes in this community are weakly interconnected._
- **Why does `RotationEntryCase` connect `RotationEntryCase` to `os`, `EntryUsesActiveManagementTargetsTests`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Should `fundamental_analysis.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07244843997884717 - nodes in this community are weakly interconnected._
- **Why does `EntryUnitRuleTests` connect `EntryUnitRuleTests` to `os`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Should `Fix1CumulativeFillsTests` be split into smaller, more focused modules?**
  _Cohesion score 0.1371794871794872 - nodes in this community are weakly interconnected._