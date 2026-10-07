"""Regression tests for the code-review fixes (gamma flip, scoring, cash, exclusions)."""

import ast
import os
import sys
import types
import unittest
import warnings
from unittest import mock

import numpy as np
import pandas as pd

from gex_utils import gamma_flip_level
from polygon_client import NO_OPTION_DATA, NoOptionData, PolygonError, PolygonNotFound, failure_reason
from tickers import dividend_yield_from_info


def _load_functions(path, names, namespace):
    """Exec only the named top-level functions/assignments of a script."""
    with open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    wanted = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            wanted.append(node)
        elif isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id in names for t in node.targets
        ):
            wanted.append(node)
    exec(compile(ast.Module(body=wanted, type_ignores=[]), path, "exec"), namespace)
    return namespace


def _load_active_management():
    """active_management.py runs the engine at import; exec everything before BLOQUE 9."""
    path = os.path.abspath("active_management.py")
    with open(path, encoding="utf-8") as handle:
        source = handle.read().split("# BLOQUE 9: EJECUCION")[0]
    namespace = {"__name__": "active_management_under_test", "__file__": path}
    with mock.patch.dict(os.environ, {"PORTFOLIO_FILE": "/nonexistent/portfolio.json"}):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            exec(compile(source, path, "exec"), namespace)
    return namespace


# Strikes 90-94 without open interest, real (all positive) gamma from 96 up.
_STRIKES = [90, 92, 94, 96, 98, 100, 102, 104]
_OI = [0, 0, 0, 500, 800, 1200, 900, 400]


class GammaFlipTests(unittest.TestCase):
    def test_zero_exposure_strikes_do_not_create_a_flip(self):
        net = [o * 0.05 for o in _OI]
        self.assertTrue(np.isnan(gamma_flip_level(_STRIKES, net)))

    def test_real_crossing_is_interpolated(self):
        # cumulative -10, -10, +10; the 100 strike has no exposure and is skipped,
        # so the crossing is interpolated between 95 (-10) and 105 (+10).
        self.assertAlmostEqual(gamma_flip_level([95, 100, 105], [-10, 0, 20]), 100.0)
        self.assertAlmostEqual(gamma_flip_level([95, 100, 105], [-10, 15, 5]), 95 + 10 * 5 / 15)

    def test_crossing_detected_in_both_directions(self):
        self.assertFalse(np.isnan(gamma_flip_level([1, 2, 3], [5, -10, 1])))
        self.assertFalse(np.isnan(gamma_flip_level([1, 2, 3], [-5, 10, -1])))

    def test_unsorted_input_and_short_series(self):
        self.assertAlmostEqual(gamma_flip_level([105, 95], [20, -10]), 100.0)
        self.assertTrue(np.isnan(gamma_flip_level([100], [5])))

    def test_gex_field_uses_the_filter(self):
        import portfolio_gex_field as gx

        df = pd.DataFrame({"strike": _STRIKES, "type": "call", "gamma": 0.05, "open_interest": _OI})
        _, flip, metrics = gx.calculate_gex_and_surface_forces(df, 100.0, "test")
        self.assertIsNone(flip)
        self.assertIsNone(metrics["gamma_flip"])

    def test_risk_score_zero_gamma_uses_the_filter(self):
        ns = _load_functions("portfolio_risk_score_leverage.py", {"compute_zero_gamma_level"},
                             {"np": np, "gamma_flip_level": gamma_flip_level})
        profile = pd.DataFrame({"strike": _STRIKES, "GEX_neto": [o * 0.05 for o in _OI]})
        self.assertTrue(np.isnan(ns["compute_zero_gamma_level"](profile)))


class EntryPercentileTests(unittest.TestCase):
    def test_absolute_percentile_compares_magnitudes(self):
        import entry_signal_tool as es

        hist = pd.DataFrame({"ticker": "X",
                             "dist_zero_gamma": [-0.05, -0.04, -0.06, -0.03, -0.05, -0.04, -0.05, -0.06]})
        # |-0.045| sits in the middle of the |history| (0.03..0.06), not at the top.
        self.assertEqual(es.percentile_historico(hist, "X", "dist_zero_gamma", -0.045, absoluto=True), 37.5)
        # The signed comparison is unchanged when absoluto is not requested.
        self.assertEqual(es.percentile_historico(hist, "X", "dist_zero_gamma", -0.045), 62.5)


class ActiveManagementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.am = _load_active_management()

    def _scores(self, portfolio, action="MANTENER", score=10.0):
        rows = [{"ticker": t, "score": score, "action": action, "recorte_pct": np.nan,
                 "expected_move_lower": 1.0, "expected_move_upper": 2.0, "expected_move_pct": 0.05,
                 "rationale": ""} for t in portfolio]
        return pd.DataFrame(rows, columns=self.am["SCORE_COLUMNS"])

    def test_missing_gamma_is_not_a_negative_signal(self):
        chain = pd.DataFrame({"strike": [95, 100, 105], "type": ["call", "call", "put"],
                              "gamma": [np.nan] * 3, "open_interest": [0, 0, 0]})
        self.assertIsNone(self.am["calculate_gex"](chain, 100.0))
        analysis = {"ticker": "X", "status": "OK", "spot_price": 100.0, "gex": None,
                    "flow": None, "expected_move": None, "vanna_charm": None}
        result = self.am["calculate_tactical_score"](analysis)
        self.assertEqual(result["score"], 0.0)
        self.assertEqual(result["action"], "MANTENER")
        self.assertEqual(result["liquidity_confidence"], "SIN_DATOS")
        self.assertIn("Sin datos de gamma", result["rationale"])

    def test_all_tickers_without_data_do_not_crash_the_rebalance(self):
        portfolio = {"GLD": 0.5, "SLV": 0.5}
        rows = [self.am["calculate_tactical_score"]({"ticker": t, "status": "ERROR", "error_message": "x"})
                for t in portfolio]
        scores = pd.DataFrame(rows, columns=self.am["SCORE_COLUMNS"])
        table = self.am["rebalance_portfolio"](portfolio, scores, 0.30)
        signal = self.am["_senal_gestion_activa"]({"tabla_rebalanceo": table, "regimen_riesgo": {},
                                                   "excluded": []})
        self.assertEqual({r["action"] for r in signal["rebalances"]}, {"HOLD"})

    def test_weights_below_one_are_initial_cash(self):
        portfolio = {"GLD": 0.18, "DHR": 0.18, "CASY": 0.18, "IBKR": 0.1443, "CDNS": 0.1014,
                     "SLV": 0.096, "PDBC": 0.0722, "CME": 0.0385}
        table = self.am["rebalance_portfolio"](portfolio, self._scores(portfolio), 0.30)
        cash = table[table["Ticker"] == "CASH"].iloc[0]
        self.assertAlmostEqual(cash["Peso_Inicial"], 0.0076, places=9)
        self.assertAlmostEqual(cash["Nuevo_Peso"], 0.0076, places=9)
        self.assertAlmostEqual(table["Nuevo_Peso"].sum(), 1.0, places=9)
        signal = self.am["_senal_gestion_activa"]({"tabla_rebalanceo": table, "regimen_riesgo": {},
                                                   "excluded": []})
        self.assertEqual({r["action"] for r in signal["rebalances"]}, {"HOLD"})

    def test_freed_weight_adds_to_initial_cash(self):
        portfolio = {"A": 0.5, "B": 0.4}
        scores = self._scores(portfolio)
        scores.loc[scores["ticker"] == "A", "action"] = "LIQUIDAR"
        table = self.am["rebalance_portfolio"](portfolio, scores, 0.30)
        cash = table[table["Ticker"] == "CASH"].iloc[0]
        self.assertAlmostEqual(cash["Peso_Inicial"], 0.1)
        # 0.5 freed: 0.30 to cash by the limit, the rest also to cash (no AUMENTAR names).
        self.assertAlmostEqual(cash["Nuevo_Peso"], 0.6)
        self.assertAlmostEqual(table["Nuevo_Peso"].sum(), 1.0)


class FailureReasonTests(unittest.TestCase):
    def test_reasons(self):
        self.assertEqual(failure_reason(None), NO_OPTION_DATA)
        self.assertEqual(failure_reason(PolygonNotFound("404")), NO_OPTION_DATA)
        self.assertEqual(failure_reason(NoOptionData(NO_OPTION_DATA)), NO_OPTION_DATA)
        self.assertEqual(failure_reason(PolygonError("HTTP 429 en /x tras 4 reintentos")),
                         "api error: HTTP 429 en /x tras 4 reintentos")
        self.assertEqual(failure_reason(KeyError("c")), "error: KeyError: 'c'")


class DividendYieldTests(unittest.TestCase):
    def test_percent_field_is_scaled(self):
        self.assertAlmostEqual(dividend_yield_from_info({"dividendYield": 0.2}), 0.002)
        self.assertAlmostEqual(dividend_yield_from_info({"dividendYield": 2.8}), 0.028)

    def test_fraction_fields_win(self):
        info = {"trailingAnnualDividendYield": 0.0045, "dividendYield": 0.45}
        self.assertAlmostEqual(dividend_yield_from_info(info), 0.0045)
        self.assertAlmostEqual(dividend_yield_from_info({"yield": 0.031}), 0.031)

    def test_missing_or_implausible(self):
        self.assertIsNone(dividend_yield_from_info({}))
        self.assertIsNone(dividend_yield_from_info({"dividendYield": 40.0}))

    def test_gex_field_dividend_yield(self):
        import portfolio_gex_field as gx

        gx.get_dividend_yield.cache_clear()
        fake = types.SimpleNamespace(info={"dividendYield": 0.2})
        with mock.patch.object(gx.yf, "Ticker", return_value=fake):
            self.assertAlmostEqual(gx.get_dividend_yield("ZZZ"), 0.002)
        gx.get_dividend_yield.cache_clear()


class RiskPriceHistoryTests(unittest.TestCase):
    def test_ticker_without_prices_is_excluded(self):
        idx = pd.date_range("2025-01-01", periods=5)
        data = pd.concat({"Adj Close": pd.DataFrame({"AAA": np.arange(1.0, 6.0), "BBB": np.nan}, index=idx)},
                         axis=1)
        logs = []
        ns = {"pd": pd, "yf": types.SimpleNamespace(download=lambda *a, **k: data),
              "to_yahoo": lambda t: t, "log_info": logs.append, "log_warn": logs.append}
        _load_functions("portfolio_risk_score_leverage.py", {"get_price_data"}, ns)
        prices, excluded = ns["get_price_data"](["AAA", "BBB"], None, None)
        self.assertEqual(list(prices.columns), ["AAA"])
        self.assertEqual(len(prices), 5)
        self.assertEqual(excluded, [{"ticker": "BBB", "reason": "no price history returned"}])


class GexLiveShellTests(unittest.TestCase):
    def test_shell_is_written_on_first_successful_iteration(self):
        import portfolio_gex_field as gx

        results = iter([None, {"X": 0, "Y": 0, "Z": 0, "current_state": None, "reference_lines": [],
                               "portfolio_data": {}, "surface_data": None}])
        with mock.patch.object(gx, "start_local_file_server", return_value=8765), \
                mock.patch.object(gx, "run_once", side_effect=lambda: next(results)), \
                mock.patch.object(gx, "export_signals"), \
                mock.patch.object(gx, "plot_3d_portfolio_field", return_value=object()), \
                mock.patch.object(gx, "write_portfolio_data_json"), \
                mock.patch.object(gx, "write_portfolio_html_shell") as shell, \
                mock.patch.object(gx.webbrowser, "open") as browser:
            gx.run_live(refresh_seconds=0, max_iterations=2, open_browser=True)
        self.assertEqual(shell.call_count, 1)
        self.assertEqual(browser.call_count, 1)


class VixWeightsArgsTests(unittest.TestCase):
    def _parse(self, argv):
        import portfolio_vix as pv

        with mock.patch.object(sys, "argv", ["portfolio_vix.py", *argv]):
            return pv._parse_args()

    def test_mismatched_weights_are_rejected(self):
        with mock.patch("sys.stderr"):
            with self.assertRaises(SystemExit):
                self._parse(["--tickers", "SPY", "QQQ", "GLD", "--weights", "0.5", "0.5"])

    def test_negative_weights_are_rejected(self):
        with mock.patch("sys.stderr"):
            with self.assertRaises(SystemExit):
                self._parse(["--tickers", "SPY", "QQQ", "--weights", "1.2", "-0.2"])

    def test_matching_weights_are_accepted(self):
        cfg = self._parse(["--tickers", "SPY", "QQQ", "--weights", "0.6", "0.4"])
        self.assertEqual(cfg.weights, [0.6, 0.4])


if __name__ == "__main__":
    unittest.main()
