# Graph Report - Portfolio-Manager  (2026-10-12)

## Corpus Check
- 37 files · ~88,035 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 3)

## Summary
- 1453 nodes · 3559 edges · 82 communities (54 shown, 28 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 57 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d30bb6f8`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- portfolio_risk_score_leverage.py
- fundamental_analysis.py
- load_fills
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
- test_day2_fixes.py
- CBOEVarianceEngine
- Working with the graphify knowledge graph
- Working with the graphify knowledge graph
- entry_signal_tool.py
- numpy
- _meta
- compute_var_es
- pipeline_io.py
- viz_utils.py
- EntryTrancheLockTests
- active_management.py
- sell
- .invoke
- test_cycle2_fixes.py
- resolve_cycle_day
- test_zero_gamma.py
- test_international_fallback.py
- correr_entry_signal
- polygon_client.py
- PerPortfolioEntryStateTests
- test_signal_shapes.py
- VixHorizonTests
- NoOptionData
- artifact_path
- screen_candidates
- .__init__
- RiskFreeRateTests
- VixWeightsArgsTests
- RiskRegimeSameDayTests
- calcular_indicadores_proxy
- StaggeredEntryTests
- test_horizon.py
- PickExpirationTests
- export_signals
- gamma_flip_level
- RunCyclePassesHorizonTests
- os
- .load
- RotationEntryCase
- no_options_weight_cap
- RotationLogicTests
- run_reporting_module
- drawdown_rotation.py
- main
- UniverseTests
- _load_functions
- zero_gamma_profile
- AssetMarketData
- PolygonError
- fetch_ohlc
- select_rotation
- calculate_gex_and_surface_forces
- _refine_bracket
- apply_entry_fills
- FullySoldTests
- _load_active_management
- EntryReadsRotationTests
- ShowOrSaveTests
- GexLiveShellTests
- LoadPortfolioTests
- GexFieldZeroGammaTests
- __init__.py
- TrancheLockHelperTests
- cycle_today

## God Nodes (most connected - your core abstractions)
1. `to_polygon()` - 33 edges
2. `resolve_instrument()` - 28 edges
3. `run()` - 28 edges
4. `NoOptionData` - 27 edges
5. `to_yahoo()` - 27 edges
6. `failure_reason()` - 25 edges
7. `zero_gamma_profile()` - 25 edges
8. `gamma_flip_level()` - 24 edges
9. `PolygonClient` - 22 edges
10. `correr_entry_signal()` - 22 edges

## Surprising Connections (you probably didn't know these)
- `AdrSpotFallbackTests` --uses--> `NoOptionData`  [INFERRED]
  tests/test_cycle2_fixes.py → polygon_client.py
- `AdrSpotFallbackTests` --uses--> `PolygonError`  [INFERRED]
  tests/test_cycle2_fixes.py → polygon_client.py
- `AdrSpotFallbackTests` --uses--> `PolygonNotFound`  [INFERRED]
  tests/test_cycle2_fixes.py → polygon_client.py
- `PolygonBackoffTests` --uses--> `PolygonError`  [INFERRED]
  tests/test_cycle1_fixes.py → polygon_client.py
- `RiskScoreFallbackTests` --uses--> `PolygonError`  [INFERRED]
  tests/test_international_fallback.py → polygon_client.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Signal to fills to entry state loop** — readme_entry_signal_tool, readme_pipeline_signals, readme_entry_state_and_fills, readme_portfolio_file [EXTRACTED 1.00]
- **Polygon options-chain driven scripts** — readme_active_management, readme_entry_signal_tool, readme_risk_score_dynamic_leverage, readme_portfolio_vix, readme_portfolio_gex_field, readme_polygon_io [EXTRACTED 1.00]
- **Portfolio risk aggregation via correlation and Euler attribution** — readme_correlation_estimators, readme_euler_risk_attribution, readme_implied_correlation, readme_portfolio_vix, readme_active_management [INFERRED 0.75]

## Communities (82 total, 28 thin omitted)

### Community 0 - "portfolio_risk_score_leverage.py"
Cohesion: 0.08
Nodes (36): bs_gamma(), bs_price(), compute_atm_iv(), compute_corr_cov(), compute_expected_move(), compute_gex_pcr_factor(), compute_gex_profile(), compute_max_drawdown() (+28 more)

### Community 1 - "fundamental_analysis.py"
Cohesion: 0.08
Nodes (31): analizar_cartera(), calcular_corto_plazo(), _current_ratio(), calcular_historico(), calcular_info_adicional(), calcular_largo_plazo(), _roe_signal(), calcular_mediano_plazo() (+23 more)

### Community 2 - "load_fills"
Cohesion: 0.20
Nodes (7): cargar_fills(), executions_dir(), load_fills(), load_portfolio_fills(), locate_fills_file(), portfolio_fills_path(), _read_fills()

### Community 3 - "portfolio_gex_field.py"
Cohesion: 0.05
Nodes (47): downsample_profile(), failure_reason(), american_delta_gamma(), american_iv_bisection(), american_price(), _bs93_american_call(), _bs93_phi(), bs_price() (+39 more)

### Community 4 - "run_cycle.py"
Cohesion: 0.05
Nodes (53): _absorb_signal(), already_ran_this_week(), _as_text(), atomic_write(), _blank_step(), build_command(), build_parser(), _calendar_failure() (+45 more)

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
Cohesion: 0.07
Nodes (25): _estado(), _fills(), FillsGatingTests, GexHeadlessTests, TickerMappingTests, ResolverTierTests, adr_warnings(), capital_epic_verified() (+17 more)

### Community 9 - "portfolio_vix.py"
Cohesion: 0.12
Nodes (13): bjerksund_stensland_call(), bjerksund_stensland_price(), bs_price(), crr_american(), DeAmericanizer, _euro_call_carry(), implied_vol(), f() (+5 more)

### Community 11 - ".load"
Cohesion: 0.27
Nodes (3): clamp_iv(), escrowed_inputs(), PolygonMarketLoader

### Community 12 - "portfolio_key"
Cohesion: 0.22
Nodes (7): _file_token(), load_portfolio_holdings(), load_portfolio_sell_fills(), portfolio_key(), _read_sell_fills(), run_ts_stamp(), _sell_fills_candidates()

### Community 13 - "DataFrame"
Cohesion: 0.32
Nodes (3): PortfolioVIXCalculator, ReportPlotter, SmileFit

### Community 14 - "GexExpiryFallbackTests"
Cohesion: 0.24
Nodes (3): _chain(), GexExpiryFallbackTests, fetch()

### Community 17 - "Working with the graphify knowledge graph"
Cohesion: 0.33
Nodes (5): Freshness check, Git hygiene, Navigating, Verify before asserting, Working with the graphify knowledge graph

### Community 18 - "Working with the graphify knowledge graph"
Cohesion: 0.33
Nodes (5): Freshness check, Git hygiene, Navigating, Verify before asserting, Working with the graphify knowledge graph

### Community 19 - "entry_signal_tool.py"
Cohesion: 0.15
Nodes (20): calcular_espacio_walls(), calcular_expected_move(), calcular_gex_y_zero_gamma(), calcular_iv_atm(), calcular_skew(), calcular_smart_money(), calcular_vanna_charm_factor(), calcular_walls() (+12 more)

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
Cohesion: 0.13
Nodes (14): _add_months(), _fallback_result(), _flexible_fraction(), _iso_date(), load_portfolio(), parse_invested_overrides(), _percent_number(), portfolio_horizon_days() (+6 more)

### Community 24 - "viz_utils.py"
Cohesion: 0.31
Nodes (6): figure_path(), figures_dir(), headless(), _in_ipython(), _interactive(), show_or_save()

### Community 26 - "active_management.py"
Cohesion: 0.12
Nodes (34): _advertencias_tenencias(), analyze_ticker_options(), apply_diversification_guardrail(), _bsm_d1_d2(), calculate_expected_move(), calculate_gex(), calculate_order_flow(), calculate_tactical_score() (+26 more)

### Community 27 - "sell"
Cohesion: 0.15
Nodes (8): ActiveManagementHoldingsTests, buy(), buy_doc(), ExecutionsDirCase, LoadSellFillsTests, sell(), sell_doc(), SummarizeHoldingsTests

### Community 28 - ".invoke"
Cohesion: 0.08
Nodes (7): CycleTestCase, DailyCalendarTests, FailureTests, _portfolio(), PortfolioAndCliTests, SuccessPathTests, WeeklyTests

### Community 29 - "test_cycle2_fixes.py"
Cohesion: 0.30
Nodes (3): AdrSpotFallbackTests, _bs(), _chain()

### Community 31 - "test_zero_gamma.py"
Cohesion: 0.15
Nodes (7): _load_functions(), ConsumerZeroGammaTests, _gamma(), _gex_field_chain(), _net_gex_at_spot(), _profile(), ZeroGammaProfileTests

### Community 32 - "test_international_fallback.py"
Cohesion: 0.18
Nodes (7): _num(), price_indicators(), price_scores(), rsi(), yahoo_closes(), _closes(), PriceSignalTests

### Community 33 - "correr_entry_signal"
Cohesion: 0.16
Nodes (13): _activo_vacio(), cargar_estado(), cargar_tenencias(), _contexto(), correr_entry_signal(), _estado_vacio(), _etiquetar_definiciones(), guardar_estado() (+5 more)

### Community 34 - "polygon_client.py"
Cohesion: 0.09
Nodes (10): calls_per_minute_configurado(), _limiter_for(), PolygonClient, PolygonTruncated, _RateLimiter, retry_after_seconds(), retry_backoff_seconds(), PolygonBackoffTests (+2 more)

### Community 37 - "VixHorizonTests"
Cohesion: 0.10
Nodes (7): ActiveManagementExpiryTests, _contracts_endpoint(), query(), EntryExpiryTests, _expiries(), RiskScoreExpiryTests, VixHorizonTests

### Community 38 - "NoOptionData"
Cohesion: 0.19
Nodes (4): NoOptionData, EntrySignalTierTests, RiskScoreFallbackTests, fake_chain()

### Community 39 - "artifact_path"
Cohesion: 0.10
Nodes (12): artifact_path(), default_figures_dir(), entry_state_path(), optimizer_history_path(), per_portfolio_enabled(), pipeline_dir(), _portfolio_identity(), portfolio_signals_dir() (+4 more)

### Community 40 - "screen_candidates"
Cohesion: 0.17
Nodes (7): cansancio_score(), diagnosis_score(), options_favor_score(), options_risk_score(), _pct_rank(), _ratio_score(), screen_candidates()

### Community 41 - ".__init__"
Cohesion: 0.24
Nodes (3): OptionChainCleaner, PortfolioVIX, SingleAssetVIX

### Community 45 - "calcular_indicadores_proxy"
Cohesion: 0.22
Nodes (7): calcular_fila_instrumento(), calcular_indicadores_proxy(), calcular_indicadores_ticker(), fila_escalonada(), _filas_misma_definicion(), _pct_entrada(), percentile_historico()

### Community 47 - "test_horizon.py"
Cohesion: 0.08
Nodes (6): EntrySignalRecordsHorizonTests, GexHorizonTests, _loaded(), PortfolioHorizonDaysTests, ResolveHorizonTests, StepHorizonTests

### Community 49 - "export_signals"
Cohesion: 0.15
Nodes (11): _atomic_write(), empty_rotation_state(), export_signals(), _is_nan(), load_rotation_state(), _now_bogota(), prepare_artifact_path(), rotation_state_path() (+3 more)

### Community 53 - ".load"
Cohesion: 0.28
Nodes (5): ExpirySlice, select_cboe_expiries(), select_expiries_for(), YahooMarketLoader, year_fraction()

### Community 54 - "RotationEntryCase"
Cohesion: 0.21
Nodes (3): FullySoldIsNotBoughtAgainTests, RotationEntryCase, RotationTargetsAreTranchedTests

### Community 55 - "no_options_weight_cap"
Cohesion: 0.20
Nodes (6): construir_fila_estado(), evaluar_flujo_opciones(), _texto(), fallback_components(), _env_float(), no_options_weight_cap()

### Community 56 - "RotationLogicTests"
Cohesion: 0.12
Nodes (3): _ohlc(), RotationLogicTests, RotationRunTests

### Community 57 - "run_reporting_module"
Cohesion: 0.47
Nodes (5): plot_leverage_assignment(), plot_loss_distribution(), plot_pcr_vs_weight(), print_executive_summary(), run_reporting_module()

### Community 58 - "drawdown_rotation.py"
Cohesion: 0.12
Nodes (23): build_rebalances(), _custom_tickers(), decide_action(), figure_detector(), figure_top(), main(), options_view(), parse_args() (+15 more)

### Community 59 - "main"
Cohesion: 0.22
Nodes (7): construir_senal_bloqueada(), construir_senal_entrada(), graficar_resumen(), imprimir_resumen(), main(), parse_entry_args(), _truthy()

### Community 62 - "zero_gamma_profile"
Cohesion: 0.19
Nodes (7): bs_gamma_matrix(), _linear_root(), _net_gex(), _valid_contracts(), zero_gamma_profile(), f(), compute_zero_gamma_level()

### Community 63 - "AssetMarketData"
Cohesion: 0.22
Nodes (3): AssetMarketData, bracket_pair(), SyntheticMarketGenerator

### Community 64 - "PolygonError"
Cohesion: 0.40
Nodes (3): PolygonError, PolygonNotFound, FailureReasonTests

### Community 65 - "fetch_ohlc"
Cohesion: 0.40
Nodes (4): fetch_ohlc(), _ohlc_polygon(), _ohlc_yahoo(), polygon()

### Community 66 - "select_rotation"
Cohesion: 0.29
Nodes (5): choose_combination(), covariance(), expected_excess(), portfolio_sharpe(), select_rotation()

### Community 67 - "calculate_gex_and_surface_forces"
Cohesion: 0.40
Nodes (3): calculate_gex_and_surface_forces(), gamma_regime(), perfil_zero_gamma()

### Community 68 - "_refine_bracket"
Cohesion: 0.10
Nodes (6): _grid_roots(), _refine_bracket(), GridRootsTests, RefineBracketTests, _run_with_profile(), ZeroGammaProfileNeverCrashesTests

### Community 69 - "apply_entry_fills"
Cohesion: 0.20
Nodes (6): apply_entry_fills(), _as_float(), _blank_activo(), _fill_side(), stage_pending_entry(), summarize_holdings()

### Community 77 - "LoadPortfolioTests"
Cohesion: 0.20
Nodes (3): ExportSignalsTests, LoadPortfolioTests, _portfolio()

## Knowledge Gaps
- **21 isolated node(s):** `Freshness check`, `Git hygiene`, `Navigating`, `Verify before asserting`, `Freshness check` (+16 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 406 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **28 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `EntryTrancheLockTests` connect `EntryTrancheLockTests` to `os`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **What connects `Freshness check`, `Git hygiene`, `Navigating` to the rest of the system?**
  _21 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `portfolio_risk_score_leverage.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08048103607770583 - nodes in this community are weakly interconnected._
- **Why does `RotationEntryCase` connect `RotationEntryCase` to `os`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Should `fundamental_analysis.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0771478667445938 - nodes in this community are weakly interconnected._
- **Why does `zero_gamma_profile()` connect `zero_gamma_profile` to `portfolio_risk_score_leverage.py`, `portfolio_gex_field.py`, `_refine_bracket`, `calculate_gex_and_surface_forces`, `entry_signal_tool.py`, `numpy`, `active_management.py`, `test_cycle2_fixes.py`, `test_zero_gamma.py`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Should `portfolio_gex_field.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05060882800608828 - nodes in this community are weakly interconnected._