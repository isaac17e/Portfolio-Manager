# Graph Report - Portfolio-Manager  (2026-10-09)

## Corpus Check
- 29 files · ~73,202 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 3)

## Summary
- 1125 nodes · 2768 edges · 68 communities (41 shown, 27 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 35 edges (avg confidence: 0.83)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8cde501e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- portfolio_risk_score_leverage.py
- fundamental_analysis.py
- active_management.py
- portfolio_gex_field.py
- run_cycle.py
- test_international_fallback.py
- Tactical active management engine
- test_zero_gamma_def.py
- tickers.py
- portfolio_vix.py
- ndarray
- .load
- cargar_fills
- DataFrame
- GexExpiryFallbackTests
- gamma_flip_level
- CBOEVarianceEngine
- Working with the graphify knowledge graph
- Working with the graphify knowledge graph
- entry_signal_tool.py
- numpy
- compute_var_es
- pipeline_io.py
- viz_utils.py
- EntryTrancheLockTests
- pandas
- get_portfolio_chains
- .invoke
- ._namespace
- resolve_cycle_day
- zero_gamma_profile
- price_signals.py
- correr_entry_signal
- polygon_client.py
- PerPortfolioEntryStateTests
- test_signal_shapes.py
- VixHorizonTests
- GexHorizonTests
- yahoo_closes
- AssetMarketData
- .__init__
- RiskFreeRateTests
- VixWeightsArgsTests
- run_headless
- pick_expiration
- StepHorizonTests
- PickExpirationTests
- PortfolioHorizonDaysTests
- ResolveHorizonTests
- RunCyclePassesHorizonTests
- LoadPortfolioTests
- ShowOrSaveTests
- TrancheLockHelperTests
- get_portfolio_current_state
- ActiveManagementTests
- exclusion_warnings
- dividend_yield_from_info
- main
- calculate_gex_and_surface_forces
- test_review_fixes.py
- get_polygon_options_data
- .load
- ExportSignalsTests
- EntrySignalRecordsHorizonTests

## God Nodes (most connected - your core abstractions)
1. `to_polygon()` - 31 edges
2. `resolve_instrument()` - 28 edges
3. `to_yahoo()` - 25 edges
4. `gamma_flip_level()` - 24 edges
5. `failure_reason()` - 22 edges
6. `zero_gamma_profile()` - 21 edges
7. `correr_entry_signal()` - 20 edges
8. `NoOptionData` - 20 edges
9. `run_active_management_engine()` - 20 edges
10. `PolygonClient` - 19 edges

## Surprising Connections (you probably didn't know these)
- `fake_chain()` --calls--> `NoOptionData`  [EXTRACTED]
  tests/test_international_fallback.py → polygon_client.py
- `PolygonClient` --uses--> `PolygonBackoffTests`  [INFERRED]
  polygon_client.py → tests/test_cycle1_fixes.py
- `PolygonError` --uses--> `PolygonBackoffTests`  [INFERRED]
  polygon_client.py → tests/test_cycle1_fixes.py
- `cargar_estado()` --indirect_call--> `f()`  [INFERRED]
  entry_signal_tool.py → gex_utils.py
- `guardar_estado()` --indirect_call--> `f()`  [INFERRED]
  entry_signal_tool.py → gex_utils.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Signal to fills to entry state loop** — readme_entry_signal_tool, readme_pipeline_signals, readme_entry_state_and_fills, readme_portfolio_file [EXTRACTED 1.00]
- **Polygon options-chain driven scripts** — readme_active_management, readme_entry_signal_tool, readme_risk_score_dynamic_leverage, readme_portfolio_vix, readme_portfolio_gex_field, readme_polygon_io [EXTRACTED 1.00]
- **Portfolio risk aggregation via correlation and Euler attribution** — readme_correlation_estimators, readme_euler_risk_attribution, readme_implied_correlation, readme_portfolio_vix, readme_active_management [INFERRED 0.75]

## Communities (68 total, 27 thin omitted)

### Community 0 - "portfolio_risk_score_leverage.py"
Cohesion: 0.09
Nodes (32): bs_gamma(), bs_price(), compute_gex_pcr_factor(), compute_gex_profile(), compute_max_pain(), compute_put_call_ratio(), compute_strike_balance_level(), compute_zero_gamma_level() (+24 more)

### Community 1 - "fundamental_analysis.py"
Cohesion: 0.08
Nodes (31): analizar_cartera(), calcular_corto_plazo(), _current_ratio(), calcular_historico(), calcular_info_adicional(), calcular_largo_plazo(), _roe_signal(), calcular_mediano_plazo() (+23 more)

### Community 2 - "active_management.py"
Cohesion: 0.13
Nodes (30): analyze_ticker_options(), benchmark_implied_sigma(), benchmark_implied_sigmas(), build_risk_inputs(), calculate_expected_move(), calculate_gex(), calculate_order_flow(), calculate_tactical_score() (+22 more)

### Community 3 - "portfolio_gex_field.py"
Cohesion: 0.16
Nodes (12): _bs93_american_call(), _bs93_phi(), bs_price(), build_composite_portfolio_force(), _build_gex_force_function_sigma(), calculate_macro_y_axis(), _fetch_macro_series(), generate_portfolio_potential_surface() (+4 more)

### Community 4 - "run_cycle.py"
Cohesion: 0.06
Nodes (49): _absorb_signal(), already_ran_this_week(), _as_text(), atomic_write(), _blank_step(), build_command(), build_parser(), _calendar_failure() (+41 more)

### Community 6 - "Tactical active management engine"
Cohesion: 0.08
Nodes (39): Portfolio Manager README, Tactical active management engine, CBOE VIX methodology (model-free variance), Concentration guardrail (1.5x equal-share risk), Cornish-Fisher VaR/ES and CVaR, Correlation estimators (sample, EWMA, random-matrix filtered), De-Americanization (Bjerksund-Stensland 1993 / CRR binomial), Research and educational disclaimer (+31 more)

### Community 7 - "test_zero_gamma_def.py"
Cohesion: 0.17
Nodes (5): DayFiveTrendTests, DefinitionTagTests, _hist(), _legacy_csv(), PercentileTests

### Community 8 - "tickers.py"
Cohesion: 0.07
Nodes (25): get_current_price(), TickerMappingTests, ResolverTierTests, StaggeredEntryTests, adr_warnings(), capital_epic_verified(), _class_parts(), _clean() (+17 more)

### Community 9 - "portfolio_vix.py"
Cohesion: 0.12
Nodes (12): bjerksund_stensland_call(), bjerksund_stensland_price(), bs_price(), crr_american(), _euro_call_carry(), implied_vol(), f(), _parse_args() (+4 more)

### Community 11 - ".load"
Cohesion: 0.27
Nodes (3): clamp_iv(), escrowed_inputs(), PolygonMarketLoader

### Community 12 - "cargar_fills"
Cohesion: 0.33
Nodes (4): cargar_fills(), load_fills(), load_portfolio_fills(), _read_fills()

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
Cohesion: 0.10
Nodes (30): calcular_espacio_walls(), calcular_expected_move(), calcular_fila_instrumento(), calcular_gex_y_zero_gamma(), calcular_indicadores_proxy(), calcular_indicadores_ticker(), calcular_iv_atm(), calcular_skew() (+22 more)

### Community 20 - "numpy"
Cohesion: 0.23
Nodes (14): _assemble_regions(), build_implied_correlation(), _cov_to_corr(), estimate_correlation(), _ewma_cov(), _ewma_effective_n(), _nearest_pd_corr(), _pair_weights() (+6 more)

### Community 22 - "compute_var_es"
Cohesion: 0.60
Nodes (5): compute_var_es(), cornish_fisher_es(), cornish_fisher_var(), historical_es(), historical_var()

### Community 23 - "pipeline_io.py"
Cohesion: 0.08
Nodes (26): apply_entry_fills(), _as_float(), _atomic_write(), _blank_activo(), executions_dir(), export_signals(), _fallback_result(), _file_token() (+18 more)

### Community 24 - "viz_utils.py"
Cohesion: 0.26
Nodes (7): pipeline_dir(), figure_path(), figures_dir(), headless(), _in_ipython(), _interactive(), show_or_save()

### Community 26 - "pandas"
Cohesion: 0.16
Nodes (16): apply_diversification_guardrail(), _bsm_d1_d2(), calculate_vanna_charm(), euler_risk_attribution(), print_implied_correlation(), print_risk_report(), _senal_gestion_activa(), compute_atm_iv() (+8 more)

### Community 27 - "get_portfolio_chains"
Cohesion: 0.18
Nodes (7): calculate_expected_move(), campo_gamma_utilizable(), get_dynamic_strike_range(), get_portfolio_chains(), _horizonte(), _reusar_ultimo_dato(), ventanas_vencimiento()

### Community 28 - ".invoke"
Cohesion: 0.08
Nodes (7): CycleTestCase, DailyCalendarTests, FailureTests, _portfolio(), PortfolioAndCliTests, SuccessPathTests, WeeklyTests

### Community 29 - "._namespace"
Cohesion: 0.36
Nodes (3): AdrSpotFallbackTests, _bs(), _chain()

### Community 31 - "zero_gamma_profile"
Cohesion: 0.09
Nodes (12): bs_gamma_matrix(), _net_gex(), _valid_contracts(), zero_gamma_profile(), f(), ConsumerZeroGammaTests, _gamma(), _gex_field_chain() (+4 more)

### Community 32 - "price_signals.py"
Cohesion: 0.10
Nodes (10): fallback_components(), _num(), price_indicators(), price_scores(), rsi(), _closes(), EntrySignalTierTests, PriceSignalTests (+2 more)

### Community 33 - "correr_entry_signal"
Cohesion: 0.16
Nodes (13): _activo_vacio(), cargar_estado(), _contexto(), correr_entry_signal(), _estado_vacio(), _etiquetar_definiciones(), guardar_estado(), normalizar_estado() (+5 more)

### Community 34 - "polygon_client.py"
Cohesion: 0.06
Nodes (16): calls_per_minute_configurado(), _limiter_for(), PolygonClient, PolygonError, PolygonNotFound, PolygonTruncated, _RateLimiter, retry_after_seconds() (+8 more)

### Community 37 - "VixHorizonTests"
Cohesion: 0.10
Nodes (7): ActiveManagementExpiryTests, _contracts_endpoint(), query(), EntryExpiryTests, _expiries(), RiskScoreExpiryTests, VixHorizonTests

### Community 39 - "yahoo_closes"
Cohesion: 0.33
Nodes (3): spot_listado_us(), spot_paridad_put_call(), yahoo_closes()

### Community 40 - "AssetMarketData"
Cohesion: 0.20
Nodes (4): AssetMarketData, bracket_pair(), ExpirySlice, SyntheticMarketGenerator

### Community 41 - ".__init__"
Cohesion: 0.23
Nodes (4): DeAmericanizer, OptionChainCleaner, PortfolioVIX, SingleAssetVIX

### Community 44 - "run_headless"
Cohesion: 0.17
Nodes (10): downsample_profile(), gex_headless_requested(), main(), plot_zero_gamma_profiles(), run_headless(), run_live(), _senal_gex(), start_local_file_server() (+2 more)

### Community 46 - "pick_expiration"
Cohesion: 0.25
Nodes (5): _add_months(), cycle_today(), _iso_date(), pick_expiration(), portfolio_horizon_days()

### Community 55 - "get_portfolio_current_state"
Cohesion: 0.67
Nodes (4): calculate_gradient(), get_portfolio_current_state(), plot_3d_portfolio_field(), potential_function()

### Community 59 - "main"
Cohesion: 0.22
Nodes (7): construir_senal_bloqueada(), construir_senal_entrada(), graficar_resumen(), imprimir_resumen(), main(), parse_entry_args(), _truthy()

### Community 60 - "calculate_gex_and_surface_forces"
Cohesion: 0.33
Nodes (4): calculate_gex_and_surface_forces(), calculate_gex_split(), gamma_regime(), perfil_zero_gamma()

### Community 61 - "test_review_fixes.py"
Cohesion: 0.17
Nodes (5): EntryPercentileTests, FailureReasonTests, GexLiveShellTests, _load_functions(), RiskPriceHistoryTests

### Community 64 - "get_polygon_options_data"
Cohesion: 0.29
Nodes (7): american_delta_gamma(), american_iv_bisection(), american_price(), clamp_iv(), get_dividend_yield(), get_polygon_options_data(), polygon()

### Community 65 - ".load"
Cohesion: 0.32
Nodes (4): select_cboe_expiries(), select_expiries_for(), YahooMarketLoader, year_fraction()

## Knowledge Gaps
- **21 isolated node(s):** `Freshness check`, `Git hygiene`, `Navigating`, `Verify before asserting`, `Freshness check` (+16 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 299 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **27 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `EntryTrancheLockTests` connect `EntryTrancheLockTests` to `test_international_fallback.py`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **What connects `Freshness check`, `Git hygiene`, `Navigating` to the rest of the system?**
  _21 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `portfolio_risk_score_leverage.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08970099667774087 - nodes in this community are weakly interconnected._
- **Why does `GexExpiryFallbackTests` connect `GexExpiryFallbackTests` to `test_international_fallback.py`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Should `fundamental_analysis.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07924984875983061 - nodes in this community are weakly interconnected._
- **Why does `SmileBuilder` connect `ndarray` to `portfolio_vix.py`, `.__init__`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **Should `active_management.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._