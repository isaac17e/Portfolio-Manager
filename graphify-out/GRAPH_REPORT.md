# Graph Report - Portfolio-Manager  (2026-10-11)

## Corpus Check
- 30 files · ~76,390 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 3)

## Summary
- 1204 nodes · 2948 edges · 73 communities (50 shown, 23 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.83)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `32cfac0e`
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
- _hist
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
- _meta
- compute_var_es
- pipeline_io.py
- viz_utils.py
- EntryTrancheLockTests
- pandas
- get_portfolio_chains
- .invoke
- ._namespace
- resolve_cycle_day
- test_zero_gamma.py
- price_signals.py
- correr_entry_signal
- test_review_fixes.py
- PerPortfolioEntryStateTests
- _load_function
- VixHorizonTests
- failure_reason
- announce_signals_dir
- .generate
- .__init__
- RiskFreeRateTests
- VixWeightsArgsTests
- run_headless
- calcular_fila_instrumento
- portfolio_horizon_fields
- test_horizon.py
- PickExpirationTests
- entry_state_path
- ResolveHorizonTests
- RunCyclePassesHorizonTests
- LoadPortfolioTests
- ShowOrSaveTests
- TrancheLockHelperTests
- no_options_weight_cap
- ActiveManagementTests
- exclusion_warnings
- dividend_yield_from_info
- main
- export_signals
- _load_functions
- gex_utils.py
- AssetMarketData
- american_price
- .load
- portfolio_key
- gex_headless_requested
- GexFieldZeroGammaTests
- load_portfolio

## God Nodes (most connected - your core abstractions)
1. `to_polygon()` - 31 edges
2. `resolve_instrument()` - 28 edges
3. `to_yahoo()` - 25 edges
4. `gamma_flip_level()` - 24 edges
5. `failure_reason()` - 22 edges
6. `zero_gamma_profile()` - 21 edges
7. `run_active_management_engine()` - 20 edges
8. `correr_entry_signal()` - 20 edges
9. `main()` - 20 edges
10. `NoOptionData` - 20 edges

## Surprising Connections (you probably didn't know these)
- `fake_chain()` --calls--> `NoOptionData`  [EXTRACTED]
  tests/test_international_fallback.py → polygon_client.py
- `_profile()` --calls--> `zero_gamma_profile()`  [EXTRACTED]
  tests/test_zero_gamma.py → gex_utils.py
- `Polygon.io options API` --conceptually_related_to--> `requests`  [INFERRED]
  README.md → requirements.txt
- `3D portfolio gamma field` --conceptually_related_to--> `plotly`  [INFERRED]
  README.md → requirements.txt
- `polygon_client()` --calls--> `PolygonClient`  [EXTRACTED]
  active_management.py → polygon_client.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Signal to fills to entry state loop** — readme_entry_signal_tool, readme_pipeline_signals, readme_entry_state_and_fills, readme_portfolio_file [EXTRACTED 1.00]
- **Polygon options-chain driven scripts** — readme_active_management, readme_entry_signal_tool, readme_risk_score_dynamic_leverage, readme_portfolio_vix, readme_portfolio_gex_field, readme_polygon_io [EXTRACTED 1.00]
- **Portfolio risk aggregation via correlation and Euler attribution** — readme_correlation_estimators, readme_euler_risk_attribution, readme_implied_correlation, readme_portfolio_vix, readme_active_management [INFERRED 0.75]

## Communities (73 total, 23 thin omitted)

### Community 0 - "portfolio_risk_score_leverage.py"
Cohesion: 0.07
Nodes (37): compute_corr_cov(), compute_gex_pcr_factor(), compute_gex_profile(), compute_max_drawdown(), compute_max_pain(), compute_put_call_ratio(), compute_risk_contribution(), compute_sharpe_sortino() (+29 more)

### Community 1 - "fundamental_analysis.py"
Cohesion: 0.08
Nodes (32): analizar_cartera(), calcular_corto_plazo(), _current_ratio(), calcular_historico(), calcular_info_adicional(), calcular_largo_plazo(), _roe_signal(), calcular_mediano_plazo() (+24 more)

### Community 2 - "active_management.py"
Cohesion: 0.18
Nodes (22): analyze_ticker_options(), benchmark_implied_sigma(), benchmark_implied_sigmas(), _bsm_d1_d2(), build_risk_inputs(), calculate_expected_move(), calculate_gex(), calculate_order_flow() (+14 more)

### Community 3 - "portfolio_gex_field.py"
Cohesion: 0.15
Nodes (13): build_composite_portfolio_force(), _build_gex_force_function_sigma(), calculate_gradient(), calculate_macro_y_axis(), _fetch_macro_series(), generate_portfolio_potential_surface(), get_holdings_reference_lines(), get_macro_indicators() (+5 more)

### Community 4 - "run_cycle.py"
Cohesion: 0.05
Nodes (52): _absorb_signal(), already_ran_this_week(), _as_text(), atomic_write(), _blank_step(), build_command(), build_parser(), _calendar_failure() (+44 more)

### Community 6 - "Tactical active management engine"
Cohesion: 0.08
Nodes (39): Portfolio Manager README, Tactical active management engine, CBOE VIX methodology (model-free variance), Concentration guardrail (1.5x equal-share risk), Cornish-Fisher VaR/ES and CVaR, Correlation estimators (sample, EWMA, random-matrix filtered), De-Americanization (Bjerksund-Stensland 1993 / CRR binomial), Research and educational disclaimer (+31 more)

### Community 7 - "_hist"
Cohesion: 0.17
Nodes (5): DayFiveTrendTests, DefinitionTagTests, _hist(), _legacy_csv(), PercentileTests

### Community 8 - "tickers.py"
Cohesion: 0.06
Nodes (29): get_current_price(), _estado(), _fills(), FillsGatingTests, PolygonBackoffTests, fake_get(), _Resp, TickerMappingTests (+21 more)

### Community 9 - "portfolio_vix.py"
Cohesion: 0.14
Nodes (14): resolve_risk_free_rate(), bjerksund_stensland_call(), bjerksund_stensland_price(), bs_price(), crr_american(), DeAmericanizer, _euro_call_carry(), implied_vol() (+6 more)

### Community 11 - ".load"
Cohesion: 0.27
Nodes (3): clamp_iv(), escrowed_inputs(), PolygonMarketLoader

### Community 12 - "cargar_fills"
Cohesion: 0.20
Nodes (7): cargar_fills(), executions_dir(), load_fills(), load_portfolio_fills(), locate_fills_file(), portfolio_fills_path(), _read_fills()

### Community 13 - "DataFrame"
Cohesion: 0.32
Nodes (3): PortfolioVIXCalculator, ReportPlotter, SmileFit

### Community 14 - "GexExpiryFallbackTests"
Cohesion: 0.24
Nodes (3): _chain(), GexExpiryFallbackTests, fetch()

### Community 15 - "gamma_flip_level"
Cohesion: 0.12
Nodes (7): gamma_flip_crossings(), gamma_flip_level(), calculate_gex_and_surface_forces(), gamma_regime(), perfil_zero_gamma(), FlipRootTests, GammaFlipTests

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
Cohesion: 0.18
Nodes (18): _assemble_regions(), build_implied_correlation(), _cov_to_corr(), estimate_correlation(), _ewma_cov(), _ewma_effective_n(), _nearest_pd_corr(), _pair_weights() (+10 more)

### Community 21 - "_meta"
Cohesion: 0.07
Nodes (10): CleanEnvCase, CycleCase, ExportTests, _meta(), OverrideCycleTests, ParentChildAgreementTests, _portfolio_file(), ResolutionTests (+2 more)

### Community 22 - "compute_var_es"
Cohesion: 0.60
Nodes (5): compute_var_es(), cornish_fisher_es(), cornish_fisher_var(), historical_es(), historical_var()

### Community 23 - "pipeline_io.py"
Cohesion: 0.18
Nodes (8): apply_entry_fills(), _as_float(), _blank_activo(), _flexible_fraction(), _now_bogota(), parse_invested_overrides(), _percent_number(), stage_pending_entry()

### Community 24 - "viz_utils.py"
Cohesion: 0.29
Nodes (6): default_figures_dir(), figure_path(), figures_dir(), headless(), _in_ipython(), _interactive()

### Community 26 - "pandas"
Cohesion: 0.14
Nodes (18): apply_diversification_guardrail(), calculate_tactical_score(), cargar_historial_riesgo(), euler_risk_attribution(), evaluar_regimen_riesgo(), generate_executive_dashboard(), plot_allocation_comparison(), plot_gamma_profiles() (+10 more)

### Community 27 - "get_portfolio_chains"
Cohesion: 0.14
Nodes (11): calculate_expected_move(), calculate_gex_split(), campo_gamma_utilizable(), clamp_iv(), get_dynamic_strike_range(), get_polygon_options_data(), get_portfolio_chains(), _horizonte() (+3 more)

### Community 28 - ".invoke"
Cohesion: 0.08
Nodes (7): CycleTestCase, DailyCalendarTests, FailureTests, _portfolio(), PortfolioAndCliTests, SuccessPathTests, WeeklyTests

### Community 29 - "._namespace"
Cohesion: 0.36
Nodes (3): AdrSpotFallbackTests, _bs(), _chain()

### Community 31 - "test_zero_gamma.py"
Cohesion: 0.15
Nodes (7): zero_gamma_profile(), ConsumerZeroGammaTests, _gamma(), _gex_field_chain(), _net_gex_at_spot(), _profile(), ZeroGammaProfileTests

### Community 32 - "price_signals.py"
Cohesion: 0.17
Nodes (7): calcular_indicadores_proxy(), _num(), price_indicators(), price_scores(), rsi(), yahoo_closes(), PriceSignalTests

### Community 33 - "correr_entry_signal"
Cohesion: 0.18
Nodes (13): _activo_vacio(), cargar_estado(), _contexto(), correr_entry_signal(), _estado_vacio(), _etiquetar_definiciones(), guardar_estado(), normalizar_estado() (+5 more)

### Community 34 - "test_review_fixes.py"
Cohesion: 0.09
Nodes (11): calls_per_minute_configurado(), _limiter_for(), PolygonClient, PolygonError, PolygonNotFound, PolygonTruncated, _RateLimiter, retry_after_seconds() (+3 more)

### Community 37 - "VixHorizonTests"
Cohesion: 0.10
Nodes (7): ActiveManagementExpiryTests, _contracts_endpoint(), query(), EntryExpiryTests, _expiries(), RiskScoreExpiryTests, VixHorizonTests

### Community 38 - "failure_reason"
Cohesion: 0.14
Nodes (7): failure_reason(), NoOptionData, _closes(), EntrySignalTierTests, RiskScoreFallbackTests, fake_chain(), FailureReasonTests

### Community 39 - "announce_signals_dir"
Cohesion: 0.15
Nodes (7): announce_signals_dir(), artifact_path(), optimizer_history_path(), per_portfolio_enabled(), resolve_signals_dir(), uses_portfolio_layout(), summary_portfolio_dir()

### Community 44 - "run_headless"
Cohesion: 0.21
Nodes (9): downsample_profile(), plot_zero_gamma_profiles(), _resolve_output(), run_headless(), run_live(), _senal_gex(), start_local_file_server(), write_portfolio_data_json() (+1 more)

### Community 45 - "calcular_fila_instrumento"
Cohesion: 0.20
Nodes (7): calcular_fila_instrumento(), calcular_indicadores_ticker(), evaluar_flujo_opciones(), fila_escalonada(), _filas_misma_definicion(), _pct_entrada(), percentile_historico()

### Community 46 - "portfolio_horizon_fields"
Cohesion: 0.24
Nodes (6): _add_months(), cycle_today(), _iso_date(), portfolio_horizon_days(), portfolio_horizon_fields(), _positive_number()

### Community 47 - "test_horizon.py"
Cohesion: 0.10
Nodes (5): EntrySignalRecordsHorizonTests, GexHorizonTests, _loaded(), PortfolioHorizonDaysTests, StepHorizonTests

### Community 49 - "entry_state_path"
Cohesion: 0.20
Nodes (5): entry_state_path(), pipeline_dir(), _portfolio_identity(), portfolio_signals_dir(), signals_base_dir()

### Community 52 - "LoadPortfolioTests"
Cohesion: 0.20
Nodes (3): ExportSignalsTests, LoadPortfolioTests, _portfolio()

### Community 55 - "no_options_weight_cap"
Cohesion: 0.22
Nodes (5): construir_fila_estado(), _texto(), fallback_components(), _env_float(), no_options_weight_cap()

### Community 58 - "dividend_yield_from_info"
Cohesion: 0.32
Nodes (3): get_dividend_yield(), DividendYieldTests, dividend_yield_from_info()

### Community 59 - "main"
Cohesion: 0.22
Nodes (7): construir_senal_bloqueada(), construir_senal_entrada(), graficar_resumen(), imprimir_resumen(), main(), parse_entry_args(), _truthy()

### Community 60 - "export_signals"
Cohesion: 0.25
Nodes (6): _atomic_write(), export_signals(), _is_nan(), resolve_horizon(), to_jsonable(), _warn()

### Community 62 - "gex_utils.py"
Cohesion: 0.29
Nodes (3): bs_gamma_matrix(), _net_gex(), _valid_contracts()

### Community 63 - "AssetMarketData"
Cohesion: 0.33
Nodes (3): AssetMarketData, bracket_pair(), SingleAssetVIX

### Community 64 - "american_price"
Cohesion: 0.33
Nodes (6): american_delta_gamma(), american_iv_bisection(), american_price(), _bs93_american_call(), _bs93_phi(), bs_price()

### Community 65 - ".load"
Cohesion: 0.32
Nodes (4): select_cboe_expiries(), select_expiries_for(), YahooMarketLoader, year_fraction()

### Community 66 - "portfolio_key"
Cohesion: 0.47
Nodes (3): _file_token(), portfolio_key(), run_ts_stamp()

### Community 67 - "gex_headless_requested"
Cohesion: 0.33
Nodes (3): gex_headless_requested(), main(), GexHeadlessTests

### Community 69 - "load_portfolio"
Cohesion: 0.40
Nodes (3): _fallback_result(), load_portfolio(), _renormalize_weights()

## Knowledge Gaps
- **21 isolated node(s):** `Freshness check`, `Git hygiene`, `Navigating`, `Verify before asserting`, `Freshness check` (+16 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 325 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DailyCalendarTests` connect `.invoke` to `test_international_fallback.py`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **What connects `Freshness check`, `Git hygiene`, `Navigating` to the rest of the system?**
  _21 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `portfolio_risk_score_leverage.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07450980392156863 - nodes in this community are weakly interconnected._
- **Why does `to_polygon()` connect `tickers.py` to `portfolio_risk_score_leverage.py`, `active_management.py`, `portfolio_gex_field.py`, `portfolio_vix.py`, `.load`, `entry_signal_tool.py`, `get_portfolio_chains`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Should `fundamental_analysis.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07570621468926554 - nodes in this community are weakly interconnected._
- **Why does `gamma_flip_level()` connect `gamma_flip_level` to `portfolio_risk_score_leverage.py`, `active_management.py`, `portfolio_gex_field.py`, `test_review_fixes.py`, `test_international_fallback.py`, `GexFieldZeroGammaTests`, `_load_functions`, `numpy`, `._namespace`, `gex_utils.py`, `test_zero_gamma.py`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Should `portfolio_gex_field.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1471861471861472 - nodes in this community are weakly interconnected._