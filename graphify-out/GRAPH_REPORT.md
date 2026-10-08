# Graph Report - Portfolio-Manager  (2026-10-08)

## Corpus Check
- 23 files · ~59,125 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 3)

## Summary
- 841 nodes · 2139 edges · 36 communities (30 shown, 6 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 32 edges (avg confidence: 0.84)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `56cc0515`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- portfolio_risk_score_leverage.py
- fundamental_analysis.py
- active_management.py
- portfolio_gex_field.py
- run_cycle.py
- main
- Tactical active management engine
- test_cycle2_fixes.py
- tickers.py
- portfolio_vix.py
- ndarray
- .load
- .__init__
- DataFrame
- .load
- test_review_fixes.py
- CBOEVarianceEngine
- Working with the graphify knowledge graph
- Working with the graphify knowledge graph
- entry_signal_tool.py
- numpy
- pandas
- pipeline_io.py
- portfolio_key
- yahoo_closes
- polygon_client.py
- FillsGatingTests
- .invoke
- compute_var_es
- resolve_cycle_day
- construir_fila_estado
- test_international_fallback.py
- correr_entry_signal
- failure_reason
- entry_state_path

## God Nodes (most connected - your core abstractions)
1. `to_polygon()` - 31 edges
2. `resolve_instrument()` - 28 edges
3. `to_yahoo()` - 25 edges
4. `failure_reason()` - 22 edges
5. `NoOptionData` - 21 edges
6. `run_active_management_engine()` - 20 edges
7. `PolygonClient` - 19 edges
8. `gamma_flip_level()` - 19 edges
9. `_metricas_opciones()` - 17 edges
10. `correr_entry_signal()` - 17 edges

## Surprising Connections (you probably didn't know these)
- `NoOptionData` --uses--> `FailureReasonTests`  [INFERRED]
  polygon_client.py → tests/test_review_fixes.py
- `fake_chain()` --calls--> `NoOptionData`  [EXTRACTED]
  tests/test_international_fallback.py → polygon_client.py
- `PolygonClient` --uses--> `PolygonBackoffTests`  [INFERRED]
  polygon_client.py → tests/test_cycle1_fixes.py
- `PolygonError` --uses--> `PolygonBackoffTests`  [INFERRED]
  polygon_client.py → tests/test_cycle1_fixes.py
- `PolygonError` --uses--> `FailureReasonTests`  [INFERRED]
  polygon_client.py → tests/test_review_fixes.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Signal to fills to entry state loop** — readme_entry_signal_tool, readme_pipeline_signals, readme_entry_state_and_fills, readme_portfolio_file [EXTRACTED 1.00]
- **Polygon options-chain driven scripts** — readme_active_management, readme_entry_signal_tool, readme_risk_score_dynamic_leverage, readme_portfolio_vix, readme_portfolio_gex_field, readme_polygon_io [EXTRACTED 1.00]
- **Portfolio risk aggregation via correlation and Euler attribution** — readme_correlation_estimators, readme_euler_risk_attribution, readme_implied_correlation, readme_portfolio_vix, readme_active_management [INFERRED 0.75]

## Communities (36 total, 6 thin omitted)

### Community 0 - "portfolio_risk_score_leverage.py"
Cohesion: 0.10
Nodes (33): bs_gamma(), bs_price(), compute_atm_iv(), compute_expected_move(), compute_gex_pcr_factor(), compute_gex_profile(), compute_max_pain(), compute_put_call_ratio() (+25 more)

### Community 1 - "fundamental_analysis.py"
Cohesion: 0.08
Nodes (31): analizar_cartera(), calcular_corto_plazo(), _current_ratio(), calcular_historico(), calcular_info_adicional(), calcular_largo_plazo(), _roe_signal(), calcular_mediano_plazo() (+23 more)

### Community 2 - "active_management.py"
Cohesion: 0.14
Nodes (28): apply_diversification_guardrail(), benchmark_implied_sigma(), benchmark_implied_sigmas(), build_risk_inputs(), calculate_tactical_score(), cargar_historial_riesgo(), euler_risk_attribution(), evaluar_regimen_riesgo() (+20 more)

### Community 3 - "portfolio_gex_field.py"
Cohesion: 0.06
Nodes (40): american_delta_gamma(), american_iv_bisection(), american_price(), _bs93_american_call(), _bs93_phi(), bs_price(), build_composite_portfolio_force(), _build_gex_force_function_sigma() (+32 more)

### Community 4 - "run_cycle.py"
Cohesion: 0.06
Nodes (43): _absorb_signal(), already_ran_this_week(), _as_text(), atomic_write(), _blank_step(), build_command(), build_parser(), CalendarUnavailable (+35 more)

### Community 5 - "main"
Cohesion: 0.33
Nodes (5): construir_senal_entrada(), graficar_resumen(), imprimir_resumen(), main(), parse_entry_args()

### Community 6 - "Tactical active management engine"
Cohesion: 0.08
Nodes (39): Portfolio Manager README, Tactical active management engine, CBOE VIX methodology (model-free variance), Concentration guardrail (1.5x equal-share risk), Cornish-Fisher VaR/ES and CVaR, Correlation estimators (sample, EWMA, random-matrix filtered), De-Americanization (Bjerksund-Stensland 1993 / CRR binomial), Research and educational disclaimer (+31 more)

### Community 7 - "test_cycle2_fixes.py"
Cohesion: 0.15
Nodes (4): AdrSpotFallbackTests, _bs(), _chain(), PerPortfolioEntryStateTests

### Community 8 - "tickers.py"
Cohesion: 0.09
Nodes (22): get_current_price(), TickerMappingTests, ResolverTierTests, adr_warnings(), capital_epic_verified(), _class_parts(), _clean(), exchange_suffix() (+14 more)

### Community 9 - "portfolio_vix.py"
Cohesion: 0.15
Nodes (14): bjerksund_stensland_call(), bjerksund_stensland_price(), black76_price(), bs_price(), crr_american(), DeAmericanizer, escrowed_inputs(), _euro_call_carry() (+6 more)

### Community 12 - ".__init__"
Cohesion: 0.21
Nodes (4): OptionChainCleaner, PortfolioVIX, SingleAssetVIX, VIXConfig

### Community 13 - "DataFrame"
Cohesion: 0.32
Nodes (3): PortfolioVIXCalculator, ReportPlotter, SmileFit

### Community 14 - ".load"
Cohesion: 0.19
Nodes (6): AssetMarketData, ExpirySlice, select_cboe_expiries(), SyntheticMarketGenerator, YahooMarketLoader, year_fraction()

### Community 15 - "test_review_fixes.py"
Cohesion: 0.05
Nodes (13): gamma_flip_level(), ActiveManagementTests, DividendYieldTests, EntryPercentileTests, GammaFlipTests, GexLiveShellTests, _load_active_management(), _load_functions() (+5 more)

### Community 17 - "Working with the graphify knowledge graph"
Cohesion: 0.33
Nodes (5): Freshness check, Git hygiene, Navigating, Verify before asserting, Working with the graphify knowledge graph

### Community 18 - "Working with the graphify knowledge graph"
Cohesion: 0.33
Nodes (5): Freshness check, Git hygiene, Navigating, Verify before asserting, Working with the graphify knowledge graph

### Community 19 - "entry_signal_tool.py"
Cohesion: 0.15
Nodes (21): calcular_espacio_walls(), calcular_expected_move(), calcular_gex_y_zero_gamma(), calcular_indicadores_proxy(), calcular_indicadores_ticker(), calcular_iv_atm(), calcular_skew(), calcular_smart_money() (+13 more)

### Community 20 - "numpy"
Cohesion: 0.20
Nodes (14): _assemble_regions(), build_implied_correlation(), _cov_to_corr(), estimate_correlation(), _ewma_cov(), _ewma_effective_n(), _nearest_pd_corr(), _pair_weights() (+6 more)

### Community 22 - "pandas"
Cohesion: 0.18
Nodes (15): analyze_ticker_options(), _bsm_d1_d2(), calculate_expected_move(), calculate_gex(), calculate_order_flow(), calculate_vanna_charm(), get_options_snapshot(), _senal_gestion_activa() (+7 more)

### Community 23 - "pipeline_io.py"
Cohesion: 0.11
Nodes (18): apply_entry_fills(), _as_float(), _atomic_write(), _blank_activo(), executions_dir(), export_signals(), _fallback_result(), _flexible_fraction() (+10 more)

### Community 24 - "portfolio_key"
Cohesion: 0.17
Nodes (8): cargar_fills(), _file_token(), load_fills(), load_portfolio_fills(), portfolio_fills_path(), portfolio_key(), _read_fills(), run_ts_stamp()

### Community 25 - "yahoo_closes"
Cohesion: 0.33
Nodes (3): spot_listado_us(), spot_paridad_put_call(), yahoo_closes()

### Community 26 - "polygon_client.py"
Cohesion: 0.08
Nodes (13): calls_per_minute_configurado(), _limiter_for(), PolygonClient, PolygonError, PolygonNotFound, PolygonTruncated, _RateLimiter, retry_after_seconds() (+5 more)

### Community 27 - "FillsGatingTests"
Cohesion: 0.33
Nodes (3): _estado(), _fills(), FillsGatingTests

### Community 28 - ".invoke"
Cohesion: 0.07
Nodes (9): ExportSignalsTests, LoadPortfolioTests, _portfolio(), CycleTestCase, FailureTests, _portfolio(), PortfolioAndCliTests, SuccessPathTests (+1 more)

### Community 29 - "compute_var_es"
Cohesion: 0.60
Nodes (5): compute_var_es(), cornish_fisher_es(), cornish_fisher_var(), historical_es(), historical_var()

### Community 31 - "construir_fila_estado"
Cohesion: 0.50
Nodes (3): construir_fila_estado(), evaluar_flujo_opciones(), _texto()

### Community 32 - "test_international_fallback.py"
Cohesion: 0.08
Nodes (14): fallback_components(), _num(), price_indicators(), price_scores(), rsi(), _closes(), EntrySignalTierTests, _load_functions() (+6 more)

### Community 33 - "correr_entry_signal"
Cohesion: 0.23
Nodes (11): _activo_vacio(), cargar_estado(), cargar_historial(), _contexto(), correr_entry_signal(), _estado_vacio(), guardar_estado(), normalizar_estado() (+3 more)

### Community 34 - "failure_reason"
Cohesion: 0.33
Nodes (3): calcular_fila_instrumento(), fila_escalonada(), failure_reason()

## Knowledge Gaps
- **21 isolated node(s):** `Freshness check`, `Git hygiene`, `Navigating`, `Verify before asserting`, `Freshness check` (+16 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 211 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `to_polygon()` connect `tickers.py` to `portfolio_risk_score_leverage.py`, `active_management.py`, `portfolio_gex_field.py`, `portfolio_vix.py`, `.load`, `entry_signal_tool.py`, `pandas`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `resolve_instrument()` (e.g. with `._namespace()` and `._namespace()`) actually correct?**
  _`resolve_instrument()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Freshness check`, `Git hygiene`, `Navigating` to the rest of the system?**
  _21 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `portfolio_risk_score_leverage.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0975609756097561 - nodes in this community are weakly interconnected._
- **Why does `PolygonClient` connect `polygon_client.py` to `portfolio_risk_score_leverage.py`, `active_management.py`, `portfolio_gex_field.py`, `tickers.py`, `portfolio_vix.py`, `entry_signal_tool.py`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **Should `fundamental_analysis.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07924984875983061 - nodes in this community are weakly interconnected._
- **Should `active_management.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13825757575757575 - nodes in this community are weakly interconnected._