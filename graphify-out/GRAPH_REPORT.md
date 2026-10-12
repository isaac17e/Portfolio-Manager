# Graph Report - Portfolio-Manager  (2026-10-12)

## Corpus Check
- 37 files · ~87,760 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 3)

## Summary
- 1442 nodes · 3540 edges · 89 communities (59 shown, 30 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 60 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `15bfed07`
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
- test_zero_gamma_def.py
- tickers.py
- portfolio_vix.py
- ndarray
- .load
- pipeline_io.py
- DataFrame
- GexExpiryFallbackTests
- gamma_flip_level
- CBOEVarianceEngine
- Working with the graphify knowledge graph
- Working with the graphify knowledge graph
- entry_signal_tool.py
- numpy
- _meta
- compute_var_es
- math
- viz_utils.py
- EntryTrancheLockTests
- active_management.py
- test_sell_fills.py
- .invoke
- test_cycle2_fixes.py
- resolve_cycle_day
- test_zero_gamma.py
- price_signals.py
- correr_entry_signal
- polygon_client.py
- PerPortfolioEntryStateTests
- test_signal_shapes.py
- VixHorizonTests
- NoOptionData
- artifact_path
- drawdown_rotation.py
- .__init__
- RiskFreeRateTests
- VixWeightsArgsTests
- run_headless
- calcular_indicadores_proxy
- test_international_fallback.py
- StepHorizonTests
- PickExpirationTests
- os
- ResolveHorizonTests
- RunCyclePassesHorizonTests
- test_horizon.py
- PolygonClient
- RotationEntryCase
- no_options_weight_cap
- RotationLogicTests
- exclusion_warnings
- run
- main
- test_drawdown_rotation.py
- test_review_fixes.py
- zero_gamma_profile
- .load
- FillsGatingTests
- implied_vol
- select_rotation
- _refine_bracket
- _run_with_profile
- apply_entry_fills
- construir_fila_estado
- ActiveManagementTests
- _grid_roots
- ShowOrSaveTests
- main
- PortfolioHorizonDaysTests
- yahoo_closes
- LoadPortfolioTests
- GexHorizonTests
- GexFieldZeroGammaTests
- screen_candidates
- PipelineIsolationTests
- TrancheLockHelperTests
- ExportSignalsTests
- cycle_today
- should_trigger
- show_or_save

## God Nodes (most connected - your core abstractions)
1. `to_polygon()` - 33 edges
2. `NoOptionData` - 28 edges
3. `run()` - 28 edges
4. `resolve_instrument()` - 28 edges
5. `to_yahoo()` - 27 edges
6. `zero_gamma_profile()` - 25 edges
7. `failure_reason()` - 25 edges
8. `gamma_flip_level()` - 24 edges
9. `correr_entry_signal()` - 22 edges
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
- `_profile()` --calls--> `zero_gamma_profile()`  [EXTRACTED]
  tests/test_zero_gamma.py → gex_utils.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Signal to fills to entry state loop** — readme_entry_signal_tool, readme_pipeline_signals, readme_entry_state_and_fills, readme_portfolio_file [EXTRACTED 1.00]
- **Polygon options-chain driven scripts** — readme_active_management, readme_entry_signal_tool, readme_risk_score_dynamic_leverage, readme_portfolio_vix, readme_portfolio_gex_field, readme_polygon_io [EXTRACTED 1.00]
- **Portfolio risk aggregation via correlation and Euler attribution** — readme_correlation_estimators, readme_euler_risk_attribution, readme_implied_correlation, readme_portfolio_vix, readme_active_management [INFERRED 0.75]

## Communities (89 total, 30 thin omitted)

### Community 0 - "portfolio_risk_score_leverage.py"
Cohesion: 0.08
Nodes (37): bs_gamma(), bs_price(), compute_corr_cov(), compute_gex_pcr_factor(), compute_gex_profile(), compute_max_drawdown(), compute_max_pain(), compute_put_call_ratio() (+29 more)

### Community 1 - "fundamental_analysis.py"
Cohesion: 0.08
Nodes (31): analizar_cartera(), calcular_corto_plazo(), _current_ratio(), calcular_historico(), calcular_info_adicional(), calcular_largo_plazo(), _roe_signal(), calcular_mediano_plazo() (+23 more)

### Community 2 - "pandas"
Cohesion: 0.21
Nodes (10): apply_diversification_guardrail(), _bsm_d1_d2(), calculate_vanna_charm(), euler_risk_attribution(), print_implied_correlation(), print_risk_report(), compute_atm_iv(), compute_expected_move() (+2 more)

### Community 3 - "portfolio_gex_field.py"
Cohesion: 0.08
Nodes (35): american_delta_gamma(), american_iv_bisection(), american_price(), _bs93_american_call(), _bs93_phi(), bs_price(), build_composite_portfolio_force(), _build_gex_force_function_sigma() (+27 more)

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
Cohesion: 0.15
Nodes (16): TickerMappingTests, capital_epic_verified(), _class_parts(), _clean(), exchange_suffix(), _format_class(), has_us_options(), mapping() (+8 more)

### Community 9 - "portfolio_vix.py"
Cohesion: 0.14
Nodes (10): resolve_risk_free_rate(), bjerksund_stensland_call(), _euro_call_carry(), _parse_args(), _phi(), portfolio_tickers(), portfolio_weights(), select_cboe_expiries() (+2 more)

### Community 11 - ".load"
Cohesion: 0.26
Nodes (4): clamp_iv(), escrowed_inputs(), PolygonMarketLoader, year_fraction()

### Community 12 - "pipeline_io.py"
Cohesion: 0.10
Nodes (18): cargar_fills(), _as_float(), executions_dir(), _file_token(), _fill_side(), load_fills(), load_portfolio_fills(), load_portfolio_holdings() (+10 more)

### Community 13 - "DataFrame"
Cohesion: 0.32
Nodes (3): PortfolioVIXCalculator, ReportPlotter, SmileFit

### Community 14 - "GexExpiryFallbackTests"
Cohesion: 0.24
Nodes (3): _chain(), GexExpiryFallbackTests, fetch()

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
Cohesion: 0.17
Nodes (19): calcular_espacio_walls(), calcular_expected_move(), calcular_gex_y_zero_gamma(), calcular_iv_atm(), calcular_skew(), calcular_smart_money(), calcular_vanna_charm_factor(), calcular_walls() (+11 more)

### Community 20 - "numpy"
Cohesion: 0.23
Nodes (14): _assemble_regions(), build_implied_correlation(), _cov_to_corr(), estimate_correlation(), _ewma_cov(), _ewma_effective_n(), _nearest_pd_corr(), _pair_weights() (+6 more)

### Community 21 - "_meta"
Cohesion: 0.07
Nodes (10): CleanEnvCase, CycleCase, ExportTests, _meta(), OverrideCycleTests, ParentChildAgreementTests, _portfolio_file(), ResolutionTests (+2 more)

### Community 22 - "compute_var_es"
Cohesion: 0.60
Nodes (5): compute_var_es(), cornish_fisher_es(), cornish_fisher_var(), historical_es(), historical_var()

### Community 23 - "math"
Cohesion: 0.13
Nodes (13): _add_months(), _fallback_result(), _flexible_fraction(), _is_nan(), _iso_date(), load_portfolio(), parse_invested_overrides(), _percent_number() (+5 more)

### Community 24 - "viz_utils.py"
Cohesion: 0.19
Nodes (8): default_figures_dir(), entry_state_path(), pipeline_dir(), figure_path(), figures_dir(), headless(), _in_ipython(), _interactive()

### Community 26 - "active_management.py"
Cohesion: 0.12
Nodes (31): analyze_ticker_options(), benchmark_implied_sigma(), benchmark_implied_sigmas(), build_risk_inputs(), calculate_expected_move(), calculate_gex(), calculate_order_flow(), calculate_tactical_score() (+23 more)

### Community 27 - "test_sell_fills.py"
Cohesion: 0.14
Nodes (9): ActiveManagementHoldingsTests, buy(), buy_doc(), ExecutionsDirCase, FullySoldTests, LoadSellFillsTests, sell(), sell_doc() (+1 more)

### Community 28 - ".invoke"
Cohesion: 0.08
Nodes (7): CycleTestCase, DailyCalendarTests, FailureTests, _portfolio(), PortfolioAndCliTests, SuccessPathTests, WeeklyTests

### Community 29 - "test_cycle2_fixes.py"
Cohesion: 0.27
Nodes (3): AdrSpotFallbackTests, _bs(), _chain()

### Community 31 - "test_zero_gamma.py"
Cohesion: 0.15
Nodes (7): _load_functions(), ConsumerZeroGammaTests, _gamma(), _gex_field_chain(), _net_gex_at_spot(), _profile(), ZeroGammaProfileTests

### Community 32 - "price_signals.py"
Cohesion: 0.21
Nodes (5): _num(), price_indicators(), price_scores(), rsi(), PriceSignalTests

### Community 33 - "correr_entry_signal"
Cohesion: 0.16
Nodes (13): _activo_vacio(), cargar_estado(), cargar_tenencias(), _contexto(), correr_entry_signal(), _estado_vacio(), _etiquetar_definiciones(), guardar_estado() (+5 more)

### Community 34 - "polygon_client.py"
Cohesion: 0.14
Nodes (6): calls_per_minute_configurado(), _limiter_for(), PolygonTruncated, _RateLimiter, retry_after_seconds(), retry_backoff_seconds()

### Community 37 - "VixHorizonTests"
Cohesion: 0.10
Nodes (7): ActiveManagementExpiryTests, _contracts_endpoint(), query(), EntryExpiryTests, _expiries(), RiskScoreExpiryTests, VixHorizonTests

### Community 38 - "NoOptionData"
Cohesion: 0.16
Nodes (8): NoOptionData, PolygonError, PolygonNotFound, _closes(), EntrySignalTierTests, RiskScoreFallbackTests, fake_chain(), FailureReasonTests

### Community 39 - "artifact_path"
Cohesion: 0.12
Nodes (9): artifact_path(), optimizer_history_path(), per_portfolio_enabled(), _portfolio_identity(), portfolio_signals_dir(), resolve_signals_dir(), signals_base_dir(), uses_portfolio_layout() (+1 more)

### Community 40 - "drawdown_rotation.py"
Cohesion: 0.13
Nodes (14): cansancio_score(), diagnosis_score(), fetch_ohlc(), main(), _ohlc_polygon(), _ohlc_yahoo(), options_risk_score(), parse_args() (+6 more)

### Community 41 - ".__init__"
Cohesion: 0.19
Nodes (4): DeAmericanizer, OptionChainCleaner, PortfolioVIX, SingleAssetVIX

### Community 44 - "run_headless"
Cohesion: 0.15
Nodes (11): downsample_profile(), gex_headless_requested(), main(), plot_zero_gamma_profiles(), run_headless(), run_live(), _senal_gex(), start_local_file_server() (+3 more)

### Community 45 - "calcular_indicadores_proxy"
Cohesion: 0.22
Nodes (7): calcular_fila_instrumento(), calcular_indicadores_proxy(), calcular_indicadores_ticker(), fila_escalonada(), _filas_misma_definicion(), _pct_entrada(), percentile_historico()

### Community 46 - "test_international_fallback.py"
Cohesion: 0.15
Nodes (6): ResolverTierTests, StaggeredEntryTests, adr_warnings(), options_exclusion(), options_underlying(), resolve_instrument()

### Community 49 - "os"
Cohesion: 0.18
Nodes (9): _atomic_write(), empty_rotation_state(), export_signals(), load_rotation_state(), prepare_artifact_path(), rotation_state_path(), save_rotation_state(), to_jsonable() (+1 more)

### Community 53 - "PolygonClient"
Cohesion: 0.20
Nodes (4): PolygonClient, PolygonBackoffTests, fake_get(), _Resp

### Community 54 - "RotationEntryCase"
Cohesion: 0.21
Nodes (3): FullySoldIsNotBoughtAgainTests, RotationEntryCase, RotationTargetsAreTranchedTests

### Community 55 - "no_options_weight_cap"
Cohesion: 0.33
Nodes (3): fallback_components(), _env_float(), no_options_weight_cap()

### Community 56 - "RotationLogicTests"
Cohesion: 0.12
Nodes (3): _ohlc(), RotationLogicTests, RotationRunTests

### Community 58 - "run"
Cohesion: 0.13
Nodes (16): build_rebalances(), _custom_tickers(), decide_action(), figure_detector(), figure_top(), options_view(), _pct(), print_detector() (+8 more)

### Community 59 - "main"
Cohesion: 0.22
Nodes (7): construir_senal_bloqueada(), construir_senal_entrada(), graficar_resumen(), imprimir_resumen(), main(), parse_entry_args(), _truthy()

### Community 60 - "test_drawdown_rotation.py"
Cohesion: 0.20
Nodes (3): EntryReadsRotationTests, _table(), UniverseTests

### Community 61 - "test_review_fixes.py"
Cohesion: 0.14
Nodes (6): DividendYieldTests, EntryPercentileTests, GexLiveShellTests, _load_functions(), RiskPriceHistoryTests, dividend_yield_from_info()

### Community 62 - "zero_gamma_profile"
Cohesion: 0.25
Nodes (5): bs_gamma_matrix(), _net_gex(), _valid_contracts(), zero_gamma_profile(), f()

### Community 63 - ".load"
Cohesion: 0.19
Nodes (5): AssetMarketData, bracket_pair(), ExpirySlice, SyntheticMarketGenerator, YahooMarketLoader

### Community 64 - "FillsGatingTests"
Cohesion: 0.33
Nodes (3): _estado(), _fills(), FillsGatingTests

### Community 65 - "implied_vol"
Cohesion: 0.25
Nodes (5): bjerksund_stensland_price(), bs_price(), crr_american(), implied_vol(), f()

### Community 66 - "select_rotation"
Cohesion: 0.29
Nodes (5): choose_combination(), covariance(), expected_excess(), portfolio_sharpe(), select_rotation()

### Community 67 - "_refine_bracket"
Cohesion: 0.24
Nodes (3): _linear_root(), _refine_bracket(), RefineBracketTests

### Community 69 - "apply_entry_fills"
Cohesion: 0.33
Nodes (3): apply_entry_fills(), _blank_activo(), stage_pending_entry()

### Community 70 - "construir_fila_estado"
Cohesion: 0.50
Nodes (3): construir_fila_estado(), evaluar_flujo_opciones(), _texto()

### Community 74 - "main"
Cohesion: 0.29
Nodes (4): _advertencias_tenencias(), main(), _senal_gestion_activa(), fully_sold_tickers()

### Community 76 - "yahoo_closes"
Cohesion: 0.33
Nodes (3): spot_listado_us(), spot_paridad_put_call(), yahoo_closes()

### Community 80 - "screen_candidates"
Cohesion: 0.40
Nodes (3): options_favor_score(), _pct_rank(), screen_candidates()

## Knowledge Gaps
- **21 isolated node(s):** `Freshness check`, `Git hygiene`, `Navigating`, `Verify before asserting`, `Freshness check` (+16 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 404 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **30 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DailyCalendarTests` connect `.invoke` to `test_horizon.py`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **What connects `Freshness check`, `Git hygiene`, `Navigating` to the rest of the system?**
  _21 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `portfolio_risk_score_leverage.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08325624421831637 - nodes in this community are weakly interconnected._
- **Why does `zero_gamma_profile()` connect `zero_gamma_profile` to `portfolio_risk_score_leverage.py`, `pandas`, `portfolio_gex_field.py`, `_run_with_profile`, `_grid_roots`, `entry_signal_tool.py`, `numpy`, `active_management.py`, `test_cycle2_fixes.py`, `test_zero_gamma.py`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Should `fundamental_analysis.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07924984875983061 - nodes in this community are weakly interconnected._
- **Why does `gamma_flip_level()` connect `gamma_flip_level` to `portfolio_risk_score_leverage.py`, `portfolio_gex_field.py`, `GexFieldZeroGammaTests`, `test_review_fixes.py`, `numpy`, `test_horizon.py`, `active_management.py`, `test_cycle2_fixes.py`, `zero_gamma_profile`, `test_zero_gamma.py`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Should `portfolio_gex_field.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07624113475177305 - nodes in this community are weakly interconnected._