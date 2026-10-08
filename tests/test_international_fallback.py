"""No-network tests for the international ticker fallback (ADR -> proxy -> none)."""

import ast
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd

import entry_signal_tool as est
import pipeline_io
import portfolio_gex_field as gex
import portfolio_vix as vix
import tickers
from polygon_client import NoOptionData, PolygonError, failure_reason
from price_signals import price_indicators, price_scores
from tickers import (
    _ADR_TABLE,
    _CAPITAL_VERIFIED,
    adr_warnings,
    exclusion_warnings,
    no_options_weight_cap,
    options_exclusion,
    options_underlying,
    resolve_instrument,
)


def _load_functions(path, names, namespace):
    with open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    body = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    missing = set(names) - {node.name for node in body}
    if missing:
        raise AssertionError(f"{sorted(missing)} not found in {path}")
    exec(compile(ast.Module(body=body, type_ignores=[]), path, "exec"), namespace)
    return namespace


def _closes(n=300, start=100.0, step=0.1):
    index = pd.bdate_range("2025-01-01", periods=n)
    return pd.Series(start + step * np.arange(n), index=index)


_PROXY_METRICS = {
    "spot": 70.0, "vencimiento": None, "gex_total": 1e6, "dist_zero_gamma": 0.02,
    "call_wall": 72.0, "put_wall": 68.0, "espacio_walls": 0.5, "iv_atm": 0.18,
    "skew": 0.03, "expected_move": 0.05, "smart_money": 0.2, "volumen_relativo": 1.1,
    "vanna_charm": 0.0,
}

_UNVERIFIED_ADR = {
    "SHOP.TO": {
        "us_ticker": "SHOP", "polygon_ticker": "SHOP", "capital_epic": "SHOP",
        "currency": "USD", "listing": "NASDAQ", "ratio": 1.0,
        "verified": False, "verified_on": None,
    },
}


class ResolverTierTests(unittest.TestCase):
    def test_native_ticker(self):
        info = resolve_instrument("BRK-B")
        self.assertEqual(info["tier"], "native")
        self.assertEqual(info["polygon_ticker"], "BRK.B")
        self.assertEqual(info["capital_epic"], "BRKB")
        self.assertTrue(info["capital_epic_verified"])
        self.assertIsNone(info["proxy_etf"])
        self.assertEqual(options_underlying("GLD"), "GLD")
        self.assertIsNone(options_exclusion("GLD"))

    def test_verified_adr_keeps_local_key(self):
        info = resolve_instrument("ry.to")
        self.assertEqual(info["tier"], "adr")
        self.assertEqual(info["local"], "ry.to")
        self.assertEqual(info["yahoo_ticker"], "RY.TO")
        self.assertEqual(info["analysis_ticker"], "RY")
        self.assertEqual(info["polygon_ticker"], "RY")
        self.assertEqual(info["capital_epic"], "RY")
        self.assertTrue(info["verified"])
        self.assertTrue(info["capital_epic_verified"])
        self.assertEqual(info["verified_on"], "2026-10-06")
        self.assertEqual((info["currency"], info["listing"]), ("USD", "NYSE"))
        self.assertEqual(info["warnings"], [])
        self.assertIsNone(options_exclusion("RY.TO"))
        self.assertEqual(options_underlying("RY.TO"), "RY")

    def test_capital_verified_comes_from_verified_adrs_only(self):
        self.assertEqual(_CAPITAL_VERIFIED["RY.TO"]["epic"], _ADR_TABLE["RY.TO"]["capital_epic"])
        for local, adr in _ADR_TABLE.items():
            self.assertEqual(local in _CAPITAL_VERIFIED, bool(adr["verified"]))

    def test_unverified_adr_is_analysis_only_with_warning(self):
        with mock.patch.dict(tickers._ADR_TABLE, _UNVERIFIED_ADR):
            info = resolve_instrument("SHOP.TO")
            warns = adr_warnings(["SHOP.TO", "GLD", "RY.TO"])
        self.assertEqual(info["tier"], "adr")
        self.assertEqual(info["analysis_ticker"], "SHOP")
        self.assertIsNone(info["capital_epic"])
        self.assertFalse(info["capital_epic_verified"])
        self.assertFalse(info["verified"])
        self.assertEqual(len(info["warnings"]), 1)
        self.assertIn("not verified", info["warnings"][0])
        self.assertEqual(warns, info["warnings"])

    def test_proxy_from_exchange_suffix(self):
        for ticker, etf in (("7203.T", "EWJ"), ("VALE3.SA", "EWZ"), ("SAP.DE", "EWG"),
                            ("0700.HK", "EWH"), ("600519.SS", "MCHI"), ("2330.TW", "EWT"),
                            ("BNS.TO", "EWC")):
            info = resolve_instrument(ticker)
            self.assertEqual(info["tier"], "proxy", ticker)
            self.assertEqual(info["proxy_etf"], etf, ticker)
            self.assertIsNone(info["capital_epic"], ticker)
            self.assertEqual(info["analysis_ticker"], ticker)
            self.assertIsNone(options_underlying(ticker))

    def test_no_adr_no_proxy_is_none(self):
        info = resolve_instrument("EDP.LS")
        self.assertEqual(info["tier"], "none")
        self.assertIsNone(info["proxy_etf"])
        self.assertIsNone(info["capital_epic"])
        self.assertIn(".LS", info["reason"])
        self.assertEqual(resolve_instrument("")["tier"], "none")

    def test_options_exclusion_labels_proxy_as_reference(self):
        proxy = options_exclusion("7203.T")
        self.assertEqual(proxy["tier"], "proxy")
        self.assertEqual(proxy["proxy_etf"], "EWJ")
        self.assertIn("reference only", proxy["reason"])
        none = options_exclusion("EDP.LS")
        self.assertEqual(none["tier"], "none")
        self.assertIn("no proxy ETF", none["reason"])

    def test_weight_cap(self):
        env = {k: v for k, v in os.environ.items()
               if k not in (tickers.NO_OPTIONS_CAP_FACTOR_ENV, tickers.NO_OPTIONS_CAP_ENV)}
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertAlmostEqual(no_options_weight_cap(0.10), 0.05)
            self.assertAlmostEqual(no_options_weight_cap(0.10, factor=0.25), 0.025)
            self.assertAlmostEqual(no_options_weight_cap(0.10, absolute=0.03), 0.03)
            self.assertIsNone(no_options_weight_cap(None))
        with mock.patch.dict(os.environ, {tickers.NO_OPTIONS_CAP_FACTOR_ENV: "0.4",
                                          tickers.NO_OPTIONS_CAP_ENV: "0.02"}):
            self.assertAlmostEqual(no_options_weight_cap(0.04), 0.016)
            self.assertAlmostEqual(no_options_weight_cap(0.10), 0.02)


class PriceSignalTests(unittest.TestCase):
    def test_uptrend_indicators_and_scores(self):
        ind = price_indicators(_closes())
        self.assertGreater(ind["precio"], ind["sma50"])
        self.assertGreater(ind["sma50"], ind["sma200"])
        self.assertAlmostEqual(ind["drawdown"], 0.0)
        self.assertGreater(ind["rsi14"], 70)
        scores = price_scores(ind)
        self.assertEqual(scores["tendencia"], 100.0)
        self.assertEqual(scores["rsi"], 0.0)
        self.assertEqual(scores["drawdown"], 50.0)

    def test_short_or_empty_history_is_neutral(self):
        scores = price_scores(price_indicators(pd.Series(dtype=float)))
        self.assertEqual(set(scores.values()), {50.0})
        ind = price_indicators(_closes(n=30))
        self.assertTrue(np.isnan(ind["sma50"]))
        self.assertTrue(np.isnan(ind["sma200"]))
        self.assertFalse(np.isnan(ind["rsi14"]))
        self.assertEqual(price_scores(ind)["tendencia"], 50.0)

    def test_drawdown_scoring(self):
        self.assertEqual(price_scores({"drawdown": -0.10})["drawdown"], 100.0)
        self.assertAlmostEqual(price_scores({"drawdown": -0.20})["drawdown"], 50.0)
        self.assertEqual(price_scores({"drawdown": -0.40})["drawdown"], 0.0)


class EntrySignalTierTests(unittest.TestCase):
    def test_adr_uses_us_chain_and_local_key(self):
        calls = []

        def fake_metrics(symbol):
            calls.append(symbol)
            return dict(_PROXY_METRICS, spot=150.0)

        warns, excluded = [], []
        with mock.patch.object(est, "_metricas_opciones", side_effect=fake_metrics):
            fila = est.calcular_fila_instrumento("RY.TO", pd.DataFrame(), warns, excluded)
        self.assertEqual(calls, ["RY"])
        self.assertEqual(fila["ticker"], "RY.TO")
        self.assertEqual(fila["tier"], "adr")
        self.assertEqual(fila["analysis_ticker"], "RY")
        self.assertEqual(fila["capital_epic"], "RY")
        self.assertEqual(excluded, [])
        self.assertEqual(warns, [])

    def test_proxy_row_is_tagged_in_signals_json(self):
        warns, excluded = [], []
        with mock.patch.object(est, "yahoo_closes", return_value=_closes()) as closes, \
                mock.patch.object(est, "_metricas_opciones", return_value=dict(_PROXY_METRICS)) as metrics:
            fila = est.calcular_fila_instrumento("7203.T", pd.DataFrame(), warns, excluded)
        closes.assert_called_once_with("7203.T")
        metrics.assert_called_once_with("EWJ")
        self.assertEqual(fila["tier"], "proxy")
        self.assertEqual(fila["proxy_etf"], "EWJ")
        self.assertEqual(fila["spot_proxy"], 70.0)
        self.assertAlmostEqual(fila["spot"], float(_closes().iloc[-1]))
        self.assertTrue(0 <= fila["score_conviccion"] <= 100)
        self.assertEqual(excluded, [])
        self.assertTrue(any("proxy" in w and "EWJ" in w for w in warns))

        estado = est.construir_fila_estado(fila, 0.0, 0.08, 2, 1, pd.DataFrame())
        self.assertFalse(estado["tope_peso_aplicado"])
        self.assertEqual(estado["peso_objetivo_pct"], 8.0)
        resumen = pd.DataFrame([{
            "ticker": "7203.T", "spot": fila["spot"], "score_conviccion": 90.0,
            "pct_entrada_sugerido": 1.0, **{k: v for k, v in estado.items() if k != "ticker"},
        }])
        data = est.construir_senal_entrada(resumen)
        data["excluded"] = excluded
        entry = data["entries"][0]
        self.assertEqual(entry["tier"], "proxy")
        self.assertEqual(entry["proxy_etf"], "EWJ")
        self.assertIsNone(entry["capital_epic"])

        meta = {"weights": {"7203.T": 1.0}, "portfolio_source": "test",
                "portfolio_run_ts": None, "portfolio_optimizer": None}
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {"SIGNALS_OUT_DIR": tmp}):
                path = pipeline_io.export_signals("entry_signal_tool", data, meta, warnings=warns)
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
        self.assertEqual(payload["data"]["entries"][0]["tier"], "proxy")
        self.assertEqual(payload["data"]["entries"][0]["proxy_etf"], "EWJ")
        self.assertEqual(payload["data"]["excluded"], [])
        self.assertIn("signal", payload["data"]["entries"][0])
        self.assertTrue(payload["warnings"])

    def test_proxy_without_data_falls_back_to_staggered(self):
        warns, excluded = [], []
        with mock.patch.object(est, "yahoo_closes", return_value=_closes()), \
                mock.patch.object(est, "_metricas_opciones", side_effect=NoOptionData("no option data returned")):
            fila = est.calcular_fila_instrumento("7203.T", pd.DataFrame(), warns, excluded)
        self.assertEqual(fila["tier"], "none")
        self.assertEqual(fila["modo_entrada"], "escalonado")
        self.assertEqual(fila["proxy_etf"], "EWJ")
        self.assertTrue(any("EWJ unavailable" in w for w in warns))

    def test_none_tier_needs_no_network(self):
        warns, excluded = [], []
        with mock.patch.object(est, "yahoo_closes", side_effect=AssertionError("network")), \
                mock.patch.object(est, "_metricas_opciones", side_effect=AssertionError("network")):
            fila = est.calcular_fila_instrumento("EDP.LS", pd.DataFrame(), warns, excluded)
        self.assertEqual(fila["tier"], "none")
        self.assertTrue(np.isnan(fila["score_conviccion"]))
        self.assertTrue(any("staggered entry" in w for w in warns))


class StaggeredEntryTests(unittest.TestCase):
    def setUp(self):
        env = {k: v for k, v in os.environ.items()
               if k not in (tickers.NO_OPTIONS_CAP_FACTOR_ENV, tickers.NO_OPTIONS_CAP_ENV)}
        patcher = mock.patch.dict(os.environ, env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.fila = pd.Series(est.fila_escalonada("EDP.LS", resolve_instrument("EDP.LS")))

    def test_twenty_percent_per_day_of_capped_target(self):
        day1 = est.construir_fila_estado(self.fila, 0.0, 0.10, 1, 1, pd.DataFrame())
        self.assertEqual(day1["accion"], "ESCALONADO")
        self.assertEqual(day1["peso_objetivo_pct"], 5.0)
        self.assertEqual(day1["peso_objetivo_original_pct"], 10.0)
        self.assertEqual(day1["delta_sugerido_hoy_pct"], 20.0)
        self.assertTrue(day1["tope_peso_aplicado"])
        self.assertEqual(day1["tier"], "none")

        # Tramo fijo sobre lo ejecutado: con fills perdidos no se compra de golpe.
        day3 = est.construir_fila_estado(self.fila, 0.2, 0.10, 3, 1, pd.DataFrame())
        self.assertEqual(day3["delta_sugerido_hoy_pct"], 20.0)
        self.assertEqual(day3["pct_invertido_final_pct"], 40.0)
        late = est.construir_fila_estado(self.fila, 0.0, 0.10, 5, 1, pd.DataFrame())
        self.assertEqual(late["delta_sugerido_hoy_pct"], 20.0)

        # Dia 5 con 80% ejecutado: completa el 100%, sin decision por opciones.
        day5 = est.construir_fila_estado(self.fila, 0.8, 0.10, 5, 1, pd.DataFrame())
        self.assertEqual(day5["accion"], "ESCALONADO")
        self.assertEqual(day5["delta_sugerido_hoy_pct"], 20.0)
        self.assertEqual(day5["pct_invertido_final_pct"], 100.0)
        self.assertEqual(day5["cash_definitivo_pct"], 0.0)

        last = est.construir_fila_estado(self.fila, 0.9, 0.10, 4, 1, pd.DataFrame())
        self.assertEqual(last["delta_sugerido_hoy_pct"], 10.0)
        done = est.construir_fila_estado(self.fila, 1.0, 0.10, 4, 1, pd.DataFrame())
        self.assertEqual(done["accion"], "COMPLETO")

    def test_stagger_pct_is_configurable(self):
        with mock.patch.object(est, "ENTRADA_ESCALONADA_PCT", 0.5):
            row = est.construir_fila_estado(self.fila, 0.0, 0.10, 1, 1, pd.DataFrame())
        self.assertEqual(row["delta_sugerido_hoy_pct"], 50.0)
        with mock.patch.dict(os.environ, {"ENTRY_STAGGER_PCT": "0.25"}):
            self.assertEqual(est._pct_escalonado(), 0.25)
        with mock.patch.dict(os.environ, {"ENTRY_STAGGER_PCT": "abc"}):
            self.assertEqual(est._pct_escalonado(), 0.20)

    def test_signal_and_state_advance_only_on_fills(self):
        estado = est.construir_fila_estado(self.fila, 0.0, 0.10, 1, 1, pd.DataFrame())
        resumen = pd.DataFrame([{
            "ticker": "EDP.LS", "spot": np.nan, "score_conviccion": np.nan,
            "pct_entrada_sugerido": np.nan, **{k: v for k, v in estado.items() if k != "ticker"},
        }])
        data = est.construir_senal_entrada(resumen)
        entry = data["entries"][0]
        self.assertEqual(entry["signal"], "staggered")
        self.assertEqual(entry["tier"], "none")
        self.assertIsNone(entry["capital_epic"])
        self.assertEqual(entry["target_weight"], 0.05)
        self.assertEqual(entry["uncapped_target_weight"], 0.1)
        self.assertEqual(entry["tranche_weight"], 0.01)

        state = {"ciclo": 1, "dia_ciclo": 1, "ciclo_cerrado": False, "ultima_actualizacion": None,
                 "activos": {"EDP.LS": {"pct_ya_invertido": 0.0, "pct_cash_consolidado": 0.0,
                                        "decision_final": None}}}
        staged = pipeline_io.stage_pending_entry(
            state, "ts-1", 1, 1, {entry["ticker"]: entry["target_weight"]})
        self.assertEqual(staged["activos"]["EDP.LS"]["pct_ya_invertido"], 0.0)
        fills = {"schema_version": 1, "signal_run_ts": "ts-1", "executed_ts": "2026-10-08T15:00:00-05:00",
                 "fills": [{"ticker": "EDP.LS", "action": "BUY", "filled_weight": 0.01, "status": "filled"}]}
        updated, applied = pipeline_io.apply_entry_fills(staged, fills)
        self.assertTrue(applied)
        self.assertAlmostEqual(updated["activos"]["EDP.LS"]["pct_ya_invertido"], 0.2)
        ignored, applied = pipeline_io.apply_entry_fills(staged, dict(fills, signal_run_ts="other"))
        self.assertFalse(applied)
        self.assertEqual(ignored["activos"]["EDP.LS"]["pct_ya_invertido"], 0.0)


class RiskScoreFallbackTests(unittest.TestCase):
    def _namespace(self, fake_chain):
        return _load_functions(
            "portfolio_risk_score_leverage.py",
            {"options_source", "run_options_module", "fallback_components", "_senal_riesgo",
             "_fallback_warnings"},
            {
                "np": np, "pd": pd, "resolve_instrument": resolve_instrument,
                "run_options_module_for_ticker": fake_chain,
                "log_warn": lambda msg: None, "log_error": lambda msg: None,
                "NoOptionData": NoOptionData, "PolygonError": PolygonError,
                "failure_reason": failure_reason, "price_indicators": price_indicators,
                "no_options_weight_cap": lambda w: no_options_weight_cap(w, factor=0.5),
                "risk_score_weights": {"hv": 0.30, "cvar": 0.30, "iv": 0.25, "gex_pcr": 0.15},
                "leverage_min": 2.0, "leverage_max": 5.0,
            },
        )

    def test_tiers_feed_options_module_and_outputs(self):
        calls = []

        def fake_chain(symbol, hv, horizon, api_key, spot_fallback=np.nan, rf_annual=0):
            calls.append((symbol, spot_fallback))
            if symbol == "EWZ":
                raise NoOptionData("no option data returned")
            return {"ticker": symbol, "expiration": None, "days_to_expiry": 30, "spot": 50.0,
                    "atm_iv": 0.2, "hv_annual": hv, "iv_hv_ratio": 1.0, "expected_move_usd": 1.0,
                    "expected_move_pct": 0.02, "pcr_volume": 1.0, "pcr_oi": 0.9,
                    "gex_profile": pd.DataFrame(), "zero_gamma_level": np.nan,
                    "max_pain_strike": 50.0}

        ns = self._namespace(fake_chain)
        tickers_ = ["GLD", "RY.TO", "7203.T", "VALE3.SA", "EDP.LS"]
        weights = {"GLD": 0.4, "RY.TO": 0.2, "7203.T": 0.2, "VALE3.SA": 0.1, "EDP.LS": 0.1}
        module = ns["run_options_module"](
            tickers_, {tk: 0.2 for tk in tickers_}, weights, 21, "key",
            spot_by_asset={tk: 100.0 for tk in tickers_},
        )
        self.assertEqual(calls[0], ("GLD", 100.0))
        self.assertEqual([c[0] for c in calls], ["GLD", "RY", "EWJ", "EWZ"])
        self.assertTrue(all(np.isnan(c[1]) for c in calls[1:]))
        self.assertEqual(set(module["by_asset"]), {"GLD", "RY.TO", "7203.T"})
        self.assertEqual(module["by_asset"]["RY.TO"]["ticker"], "RY.TO")
        self.assertEqual(module["by_asset"]["7203.T"]["proxy_etf"], "EWJ")
        self.assertEqual(list(module["summary"]["Activo"]), ["GLD", "RY.TO", "7203.T"])
        excluded = {item["ticker"]: item for item in module["excluded"]}
        self.assertEqual(excluded["VALE3.SA"]["tier"], "none")
        self.assertIn("proxy EWZ", excluded["VALE3.SA"]["reason"])
        self.assertEqual(excluded["EDP.LS"]["tier"], "none")
        self.assertEqual(module["instruments"]["VALE3.SA"]["tier"], "none")

        prices = pd.DataFrame({tk: _closes().values for tk in tickers_}, index=_closes().index)
        signals, caps = ns["fallback_components"](module["instruments"], prices, weights)
        self.assertEqual(set(signals), {"7203.T", "VALE3.SA", "EDP.LS"})
        self.assertEqual(caps, {"VALE3.SA": 0.05, "EDP.LS": 0.05})
        module["price_signals"], module["weight_caps"] = signals, caps

        summary = pd.DataFrame([
            {"Activo": tk, "Peso_Inicial": weights[tk], "Risk_Score": 50.0 + i,
             "Apalancamiento": 3.0, "Exposicion_Efectiva": weights[tk] * 3.0}
            for i, tk in enumerate(tickers_)
        ])
        detail = summary.copy()
        for col in ("HV", "CVaR", "IV", "gex_total", "pcr_oi"):
            detail[col] = 0.1
        data = ns["_senal_riesgo"]({"summary": summary, "detail": detail}, module)
        rows = {row["ticker"]: row for row in data["components"]["by_ticker"]}
        self.assertEqual(rows["GLD"]["tier"], "native")
        self.assertNotIn("weight_cap", rows["GLD"])
        self.assertEqual(rows["RY.TO"]["tier"], "adr")
        self.assertEqual(rows["RY.TO"]["analysis_ticker"], "RY")
        self.assertEqual(rows["7203.T"]["tier"], "proxy")
        self.assertEqual(rows["7203.T"]["proxy_etf"], "EWJ")
        self.assertIn("rsi14", rows["7203.T"]["price_signals"])
        self.assertEqual(rows["EDP.LS"]["weight_cap"], 0.05)
        self.assertAlmostEqual(rows["EDP.LS"]["effective_exposure_capped"], 0.15)
        self.assertEqual(rows["EDP.LS"]["weight"], 0.1)
        json.dumps(pipeline_io.to_jsonable(data), allow_nan=False)

        warns = ns["_fallback_warnings"](data)
        self.assertTrue(any("7203.T" in w and "EWJ" in w for w in warns))
        self.assertTrue(any("EDP.LS" in w and "capped" in w for w in warns))


class GexVixWarningTests(unittest.TestCase):
    def test_gex_excludes_proxy_and_none_and_uses_adr(self):
        seen = []

        def fake_price(symbol):
            seen.append(symbol)
            return None

        holdings = {"GLD": 0.4, "RY.TO": 0.3, "7203.T": 0.2, "EDP.LS": 0.1}
        with mock.patch.object(gex, "get_current_price", side_effect=fake_price), \
                mock.patch.object(gex, "_reusar_ultimo_dato", return_value=None):
            data = gex.get_portfolio_chains(holdings)
        self.assertEqual(data, {})
        self.assertEqual(seen, ["GLD", "RY"])
        excluded = {item["ticker"]: item for item in gex._LAST_EXCLUDED}
        self.assertEqual(excluded["7203.T"]["tier"], "proxy")
        self.assertEqual(excluded["7203.T"]["proxy_etf"], "EWJ")
        self.assertIn("reference only", excluded["7203.T"]["reason"])
        self.assertEqual(excluded["EDP.LS"]["tier"], "none")
        self.assertEqual(excluded["RY.TO"]["reason"], "no spot price returned")
        signal = gex._senal_gex({}, list(gex._LAST_EXCLUDED))
        self.assertEqual(signal["holdings"], [])
        warns = exclusion_warnings(signal["excluded"])
        self.assertTrue(any(w.startswith("7203.T:") and "EWJ" in w for w in warns))
        self.assertTrue(any(w.startswith("EDP.LS:") for w in warns))

    def test_vix_loaders_exclude_proxy_and_none_and_use_adr(self):
        seen = []

        def fake_history(symbol, lookback):
            seen.append(symbol)
            raise RuntimeError("offline")

        loader = vix.PolygonMarketLoader(api_key="test", verbose=False)
        with mock.patch.object(loader, "_history", side_effect=fake_history), \
                self.assertWarns(RuntimeWarning):
            assets, prices = loader.load(["GLD", "RY.TO", "7203.T", "EDP.LS"])
        self.assertEqual(assets, [])
        self.assertEqual(seen, ["GLD", "RY"])
        excluded = {item["ticker"]: item for item in loader.excluded}
        self.assertEqual(excluded["7203.T"]["tier"], "proxy")
        self.assertIn("reference only", excluded["7203.T"]["reason"])
        self.assertEqual(excluded["EDP.LS"]["tier"], "none")
        self.assertNotIn("tier", excluded["RY.TO"])
        warns = exclusion_warnings(loader.excluded)
        self.assertEqual(len(warns), 4)

        symbols = []

        class FakeTicker:
            def __init__(self, symbol):
                symbols.append(symbol)
                raise RuntimeError("offline")

        yahoo = vix.YahooMarketLoader(verbose=False)
        with mock.patch.object(vix.yf, "Ticker", FakeTicker), self.assertWarns(RuntimeWarning):
            yahoo.load(["RY.TO", "VALE3.SA"])
        self.assertEqual(symbols, ["RY"])
        self.assertEqual(yahoo.excluded[1]["tier"], "proxy")
        self.assertEqual(yahoo.excluded[1]["proxy_etf"], "EWZ")


if __name__ == "__main__":
    unittest.main()
