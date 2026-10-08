"""No-network tests for the cycle 2 fixes: ADR spot fallback, portfolio_iv
coverage, and per-portfolio entry fills / state."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd
from scipy.stats import norm

import entry_signal_tool as est
import pipeline_io
from gex_utils import gamma_flip_level
from polygon_client import NO_OPTION_DATA, NoOptionData, PolygonError, PolygonNotFound, failure_reason
from tests.test_international_fallback import _load_functions
from tickers import resolve_instrument

_RISK_FUNCS = {
    "bs_price", "bs_gamma", "implied_vol_bisection", "fill_missing_iv_greeks", "compute_atm_iv",
    "compute_expected_move", "compute_put_call_ratio", "compute_gex_profile",
    "compute_zero_gamma_level", "compute_max_pain", "spot_paridad_put_call", "spot_listado_us",
    "run_options_module_for_ticker", "options_source", "run_options_module", "_senal_riesgo",
    "_fallback_warnings", "pct",
}

S0, SIGMA, RF, DIAS = 100.0, 0.25, 0.05, 30


def _bs(S, K, T, r, sigma, is_call):
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if is_call:
        return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)


def _chain(spot=np.nan):
    """Cadena como la deja get_option_chain_snapshot cuando Polygon no trae spot ni IV."""
    rows = []
    for K in (90.0, 95.0, 100.0, 105.0, 110.0):
        for kind in ("call", "put"):
            rows.append({
                "contract_ticker": f"O:RY{kind[0]}{K}", "contract_type": kind, "strike": K,
                "expiration": None, "iv": np.nan, "delta": np.nan, "gamma": np.nan,
                "theta": np.nan, "vega": np.nan, "volume": 10.0, "open_interest": 100.0,
                "spot": spot, "day_close": np.nan,
                "last_quote_mid": _bs(S0, K, DIAS / 365, RF, SIGMA, kind == "call"),
            })
    return pd.DataFrame(rows)


class AdrSpotFallbackTests(unittest.TestCase):
    def _namespace(self, chain, yahoo):
        self.logs = []
        return _load_functions("portfolio_risk_score_leverage.py", _RISK_FUNCS, {
            "np": np, "pd": pd, "norm": norm, "gamma_flip_level": gamma_flip_level,
            "log_info": self.logs.append, "log_warn": self.logs.append, "log_error": self.logs.append,
            "yahoo_closes": yahoo,
            "get_target_expiration": lambda tk, h, key: {"expiration": "2026-11-07", "days_to_expiry": DIAS},
            "get_option_chain_snapshot": lambda tk, exp, key: chain.copy(),
            "NoOptionData": NoOptionData, "NO_OPTION_DATA": NO_OPTION_DATA,
            "PolygonNotFound": PolygonNotFound, "PolygonError": PolygonError,
            "failure_reason": failure_reason, "resolve_instrument": resolve_instrument,
            "risk_score_weights": {"hv": 0.30, "cvar": 0.30, "iv": 0.25, "gex_pcr": 0.15},
            "leverage_min": 2.0, "leverage_max": 5.0,
        })

    def test_adr_without_polygon_spot_uses_yfinance_of_us_symbol(self):
        yahoo = mock.Mock(return_value=pd.Series([98.0, S0]))
        ns = self._namespace(_chain(), yahoo)
        out = ns["run_options_module_for_ticker"]("RY", 0.2, 21, "key", rf_annual=RF)
        yahoo.assert_called_once_with("RY", period="5d")
        self.assertAlmostEqual(out["spot"], S0)
        self.assertAlmostEqual(out["atm_iv"], SIGMA, places=3)
        self.assertEqual(out["spot_source"], "yfinance RY (ultimo cierre)")
        self.assertTrue(any("yfinance RY" in msg for msg in self.logs))

    def test_put_call_parity_when_yfinance_fails(self):
        ns = self._namespace(_chain(), mock.Mock(side_effect=RuntimeError("offline")))
        out = ns["run_options_module_for_ticker"]("RY", 0.2, 21, "key", rf_annual=RF)
        self.assertAlmostEqual(out["spot"], S0, places=6)
        self.assertAlmostEqual(out["atm_iv"], SIGMA, places=3)
        self.assertEqual(out["spot_source"], "paridad put-call de la cadena Polygon")

    def test_polygon_spot_wins_and_skips_yfinance(self):
        yahoo = mock.Mock(side_effect=AssertionError("network"))
        ns = self._namespace(_chain(spot=S0), yahoo)
        out = ns["run_options_module_for_ticker"]("RY", 0.2, 21, "key", rf_annual=RF)
        yahoo.assert_not_called()
        self.assertEqual(out["spot_source"], "polygon underlying_asset.price")

    def test_one_nan_iv_ticker_does_not_null_portfolio_iv(self):
        def fake_chain(symbol, hv, horizon, api_key, spot_fallback=np.nan, rf_annual=0):
            return {"ticker": symbol, "expiration": None, "days_to_expiry": 30, "spot": 50.0,
                    "atm_iv": np.nan if symbol == "RY" else {"GLD": 0.2, "KO": 0.3}[symbol],
                    "hv_annual": hv, "iv_hv_ratio": np.nan, "expected_move_usd": np.nan,
                    "expected_move_pct": np.nan, "pcr_volume": 1.0, "pcr_oi": 1.0,
                    "gex_profile": pd.DataFrame(), "zero_gamma_level": np.nan, "max_pain_strike": 50.0}

        ns = self._namespace(_chain(), mock.Mock())
        ns["run_options_module_for_ticker"] = fake_chain
        weights = {"GLD": 0.5, "KO": 0.25, "RY.TO": 0.25}
        module = ns["run_options_module"](list(weights), {tk: 0.2 for tk in weights}, weights, 21, "key")
        self.assertAlmostEqual(module["portfolio_iv"], (0.5 * 0.2 + 0.25 * 0.3) / 0.75)
        coverage = module["iv_coverage"]
        self.assertEqual(coverage["tickers_without_iv"], ["RY.TO"])
        self.assertEqual(coverage["tickers_with_iv"], ["GLD", "KO"])
        self.assertAlmostEqual(coverage["weight_coverage"], 0.75)
        self.assertTrue(any("RY.TO" in msg and "portfolio_iv" in msg for msg in self.logs))

        summary = pd.DataFrame([{"Activo": tk, "Peso_Inicial": w, "Risk_Score": 50.0,
                                 "Apalancamiento": 3.0, "Exposicion_Efectiva": 3 * w}
                                for tk, w in weights.items()])
        detail = summary.assign(HV=0.1, CVaR=0.1, IV=0.1, gex_total=0.1, pcr_oi=0.1)
        data = ns["_senal_riesgo"]({"summary": summary, "detail": detail}, module)
        self.assertAlmostEqual(data["components"]["portfolio_iv"], module["portfolio_iv"])
        self.assertEqual(data["components"]["portfolio_iv_coverage"]["tickers_without_iv"], ["RY.TO"])
        warns = ns["_fallback_warnings"](data)
        self.assertTrue(any(w.startswith("portfolio_iv excludes RY.TO") for w in warns))


_META_MV = {"weights": {}, "portfolio_source": "mv.json",
            "portfolio_run_ts": "2026-10-08T11:05:16-05:00", "portfolio_optimizer": "minimum_variance"}
_META_QU = {"weights": {}, "portfolio_source": "qu.json",
            "portfolio_run_ts": "2026-10-08T11:20:03-05:00", "portfolio_optimizer": "quadratic_utility"}


class PerPortfolioEntryStateTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.executions = self.root / "executions"
        self.executions.mkdir()
        env = {k: v for k, v in os.environ.items() if k not in ("ENTRY_STATE_FILE", "PIPELINE_DIR")}
        env.update({"EXECUTIONS_DIR": str(self.executions),
                    "SIGNALS_OUT_DIR": str(self.root / "signals")})
        patcher = mock.patch.dict(os.environ, env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        legacy = mock.patch.object(est, "LEGACY_STATE_PATH", str(self.root / "entry_state.json"))
        legacy.start()
        self.addCleanup(legacy.stop)

    def _write_fills(self, name, signal_run_ts):
        (self.executions / name).write_text(json.dumps({
            "schema_version": 1, "signal_run_ts": signal_run_ts,
            "executed_ts": "2026-10-08T15:00:00-05:00",
            "fills": [{"ticker": "GLD", "action": "BUY", "filled_weight": 0.01, "status": "filled"}],
        }), encoding="utf-8")

    def test_run_ts_stamp_and_paths(self):
        self.assertEqual(pipeline_io.run_ts_stamp("2026-10-08T11:05:16-05:00"), "20261008T110516")
        self.assertEqual(pipeline_io.run_ts_stamp("2026-10-08T16:05:16Z"), "20261008T160516")
        self.assertEqual(pipeline_io.run_ts_stamp("run 1/2"), "run_1_2")
        self.assertEqual(pipeline_io.portfolio_key(_META_MV), "minimum_variance_20261008T110516")
        self.assertIsNone(pipeline_io.portfolio_key({"portfolio_optimizer": "x", "portfolio_run_ts": None}))
        self.assertEqual(pipeline_io.portfolio_fills_path(_META_MV),
                         str(self.executions / "fills_minimum_variance_20261008T110516.json"))
        self.assertEqual(pipeline_io.entry_state_path(_META_QU),
                         str(self.root / "state" / "entry_state_quadratic_utility_20261008T112003.json"))
        with mock.patch.dict(os.environ, {"PIPELINE_DIR": str(self.root / "p")}):
            self.assertEqual(pipeline_io.entry_state_path(None),
                             str(self.root / "p" / "state" / "entry_state_hardcoded_fallback.json"))
        with mock.patch.dict(os.environ, {"ENTRY_STATE_FILE": "/x/state.json"}):
            self.assertEqual(pipeline_io.entry_state_path(_META_MV), "/x/state.json")

    def test_two_portfolios_do_not_share_fills_or_state(self):
        self._write_fills("fills_minimum_variance_20261008T110516.json", "sig-mv")
        self._write_fills("fills_quadratic_utility_20261008T112003.json", "sig-qu")
        # Un fills_* mas reciente de otro portafolio no debe leerse.
        self._write_fills("fills_black_litterman_20261009T090000.json", "sig-bl")

        saved = {}
        for meta, signal in ((_META_MV, "sig-mv"), (_META_QU, "sig-qu")):
            with mock.patch.object(est, "_PORTFOLIO_META", meta):
                self.assertEqual(est.cargar_fills()["signal_run_ts"], signal)
                estado = pipeline_io.stage_pending_entry(
                    est.cargar_estado(), signal, 1, 1, {"GLD": 0.05})
                est.guardar_estado(estado)
                saved[signal] = est.ruta_estado()

        self.assertNotEqual(saved["sig-mv"], saved["sig-qu"])
        for signal, path in saved.items():
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            self.assertEqual(data["pending_signal_run_ts"], signal)

        # Cada portafolio avanza solo con sus propios fills.
        with mock.patch.object(est, "_PORTFOLIO_META", _META_MV):
            estado, applied = pipeline_io.apply_entry_fills(est.cargar_estado(), est.cargar_fills())
            self.assertTrue(applied)
            est.guardar_estado(estado)
        with mock.patch.object(est, "_PORTFOLIO_META", _META_QU):
            qu = est.cargar_estado()
        self.assertEqual(qu["pending_signal_run_ts"], "sig-qu")
        self.assertEqual(qu["activos"]["GLD"]["pct_ya_invertido"], 0.0)
        self.assertEqual(qu["portfolio"]["optimizer"], "quadratic_utility")
        self.assertFalse((self.root / "entry_state.json").exists())

    def test_missing_own_fills_reads_nothing(self):
        self._write_fills("fills_quadratic_utility_20261008T112003.json", "sig-qu")
        with mock.patch.object(est, "_PORTFOLIO_META", _META_MV):
            self.assertIsNone(est.cargar_fills())

    def test_legacy_state_migrates_only_for_the_same_portfolio(self):
        legacy = self.root / "entry_state.json"
        text = json.dumps({
            "ciclo": 2, "dia_ciclo": 3, "ciclo_cerrado": False, "ultima_actualizacion": "2026-10-07",
            "portfolio": {"optimizer": "minimum_variance", "run_ts": "2026-10-08T11:05:16-05:00"},
            "activos": {"GLD": {"pct_ya_invertido": 0.4, "pct_cash_consolidado": 0.0,
                                "decision_final": None}},
        })
        legacy.write_text(text, encoding="utf-8")
        with mock.patch.object(est, "_PORTFOLIO_META", _META_QU):
            fresh = est.cargar_estado()
        self.assertEqual(fresh["ciclo"], 1)
        self.assertEqual(fresh["activos"]["GLD"]["pct_ya_invertido"], 0.0)
        with mock.patch.object(est, "_PORTFOLIO_META", _META_MV):
            migrated = est.cargar_estado()
            est.guardar_estado(migrated)
            self.assertTrue(Path(est.ruta_estado()).is_file())
        self.assertEqual((migrated["ciclo"], migrated["dia_ciclo"]), (2, 3))
        self.assertEqual(migrated["activos"]["GLD"]["pct_ya_invertido"], 0.4)
        self.assertEqual(legacy.read_text(encoding="utf-8"), text)

    def test_legacy_state_without_portfolio_block_starts_fresh(self):
        (self.root / "entry_state.json").write_text(json.dumps({
            "ciclo": 4, "dia_ciclo": 2, "activos": {}}), encoding="utf-8")
        with mock.patch.object(est, "_PORTFOLIO_META", _META_MV):
            self.assertEqual(est.cargar_estado()["ciclo"], 1)


if __name__ == "__main__":
    unittest.main()
