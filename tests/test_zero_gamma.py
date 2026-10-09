"""Zero-gamma level on a spot grid (gex_utils.zero_gamma_profile) and its use
in portfolio_gex_field, active_management, entry_signal_tool and
portfolio_risk_score_leverage. No network: chains are synthetic."""

import os
import tempfile
import unittest
from datetime import date, timedelta
from unittest import mock

import numpy as np
import pandas as pd
from scipy.stats import norm

import entry_signal_tool as es
import portfolio_gex_field as gex
import viz_utils
from gex_utils import (
    ZERO_GAMMA_EXPORT_POINTS, ZERO_GAMMA_GRID_POINTS, downsample_profile, gamma_flip_level,
    zero_gamma_profile,
)
from tests.test_review_fixes import _load_active_management

R, IV, DAYS, S0 = 0.05, 0.25, 30, 100.0


def _gamma(S, K, T, r, sigma, q=0.0):
    """Scalar Black-Scholes gamma, written independently of gex_utils."""
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    return np.exp(-q * T) * norm.pdf(d1) / (S * sigma * np.sqrt(T))


def _profile(rows, spot=S0, T=DAYS / 365, iv=IV, r=R, **kw):
    k = [x[0] for x in rows]
    return zero_gamma_profile(k, [x[1] == "call" for x in rows], [x[2] for x in rows],
                              [iv] * len(k), [T] * len(k), spot, r, **kw)


def _net_gex_at_spot(rows, spot=S0, T=DAYS / 365, r=R):
    return sum((1 if t == "call" else -1) * _gamma(spot, k, T, r, IV) * oi * 100 * spot ** 2 * 0.01
               for k, t, oi in rows)


CALLS_ONLY = [(95, "call", 500), (100, "call", 800), (105, "call", 600), (110, "call", 400)]
PUTS_BELOW_CALLS_ABOVE = [(85, "put", 1000), (115, "call", 1000)]
# Local gammas (10 days): - near 80, + near 95, - near 105, + near 120.
ALTERNATING = [(80, "put", 1000), (95, "call", 1000), (105, "put", 1000), (120, "call", 1000)]
# Day-2 pattern: mostly OTM OI; puts dominate the strikes up to spot, so the
# cumulative strike sum turns positive only above spot, while GEX re-evaluated
# at spot is positive and its zero is below spot.
DAY2 = [(90, "put", 1000), (95, "put", 300), (105, "call", 700), (110, "call", 900), (115, "call", 500)]


class ZeroGammaProfileTests(unittest.TestCase):
    def test_grid_and_scaling(self):
        zg = _profile(PUTS_BELOW_CALLS_ABOVE)
        self.assertEqual(len(zg["grid"]), ZERO_GAMMA_GRID_POINTS)
        self.assertAlmostEqual(zg["grid"][0], S0 * 0.7)
        self.assertAlmostEqual(zg["grid"][-1], S0 * 1.3)
        self.assertAlmostEqual(zg["grid"][ZERO_GAMMA_GRID_POINTS // 2], S0)
        self.assertEqual(zg["model"], "sticky_strike")
        # GEX_total(S0) is the at-spot net GEX of the same contracts.
        self.assertAlmostEqual(zg["gex_at_spot"] / _net_gex_at_spot(PUTS_BELOW_CALLS_ABOVE), 1.0, places=10)
        # Every grid point is the same sum re-evaluated at that spot (S^2 too).
        i = 17
        s = zg["grid"][i]
        expected = sum((1 if t == "call" else -1) * _gamma(s, k, DAYS / 365, R, IV) * oi * 100 * s ** 2 * 0.01
                       for k, t, oi in PUTS_BELOW_CALLS_ABOVE)
        self.assertAlmostEqual(zg["gex"][i] / expected, 1.0, places=10)

    def test_dividend_yield_enters_gamma(self):
        zg = zero_gamma_profile([100.0], [True], [10], [IV], [0.5], S0, R, q=0.03)
        expected = _gamma(S0, 100.0, 0.5, R, IV, q=0.03) * 10 * 100 * S0 ** 2 * 0.01
        self.assertAlmostEqual(zg["gex_at_spot"] / expected, 1.0, places=10)

    def test_call_heavy_chain_has_no_crossing(self):
        zg = _profile(CALLS_ONLY)
        self.assertIsNone(zg["zero_gamma_level"])
        self.assertEqual(zg["zero_gamma_crossings"], [])
        self.assertEqual(zg["zero_gamma_status"], "no_crossing_in_grid")
        self.assertEqual(zg["grid_sign"], "all_positive")
        self.assertTrue((zg["gex"] > 0).all())
        puts = _profile([(k, "put", oi) for k, _, oi in CALLS_ONLY])
        self.assertEqual(puts["grid_sign"], "all_negative")

    def test_puts_below_calls_above_one_crossing(self):
        zg = _profile(PUTS_BELOW_CALLS_ABOVE, spot=105.0)
        self.assertEqual(zg["zero_gamma_status"], "ok")
        self.assertEqual(len(zg["zero_gamma_crossings"]), 1)
        level = zg["zero_gamma_level"]
        self.assertTrue(85 < level < 115)
        self.assertLess(level, 105.0)
        self.assertGreater(zg["gex_at_spot"], 0)
        self.assertEqual((zg["zero_gamma_below"], zg["zero_gamma_above"]), (level, None))
        # The refined root is a real zero of the re-evaluated sum.
        at_level = _profile(PUTS_BELOW_CALLS_ABOVE, spot=level)["gex_at_spot"]
        self.assertLess(abs(at_level), 1e-6 * abs(zg["gex_at_spot"]))
        regime = gex.gamma_regime(zg["gex_at_spot"], 105.0, zg)
        self.assertEqual(regime["regime"], gex.REGIME_POSITIVE)
        self.assertFalse(regime["regime_conflict"])

    def test_multiple_crossings_nearest_is_chosen(self):
        zg = _profile(ALTERNATING, spot=90.0, T=10 / 365)
        crossings = zg["zero_gamma_crossings"]
        self.assertEqual(len(crossings), 3)
        self.assertEqual(crossings, sorted(crossings))
        self.assertEqual(zg["zero_gamma_level"], min(crossings, key=lambda c: abs(c - 90.0)))
        self.assertTrue(80 < zg["zero_gamma_level"] < 90)
        self.assertEqual(zg["zero_gamma_above"], crossings[1])
        regime = gex.gamma_regime(zg["gex_at_spot"], 90.0, zg)
        self.assertEqual(regime["regime"], gex.REGIME_POSITIVE)
        self.assertFalse(regime["regime_conflict"])

    def test_downward_nearest_crossing_is_the_only_conflict(self):
        # Spot 101 sits just above the middle (downward) crossing: GEX < 0 at
        # spot although spot > nearest level.
        zg = _profile(ALTERNATING, spot=101.0, T=10 / 365)
        self.assertLess(zg["zero_gamma_level"], 101.0)
        self.assertLess(zg["gex_at_spot"], 0)
        regime = gex.gamma_regime(zg["gex_at_spot"], 101.0, zg)
        self.assertEqual(regime["regime"], gex.REGIME_NEGATIVE)
        self.assertEqual(regime["regime_by_zero_gamma"], gex.REGIME_POSITIVE)
        self.assertTrue(regime["regime_conflict"])

    def test_regime_matches_the_curve(self):
        zg = _profile(PUTS_BELOW_CALLS_ABOVE, spot=100.0)
        level = zg["zero_gamma_level"]
        for spot in np.linspace(80, 120, 21):
            at = _profile(PUTS_BELOW_CALLS_ABOVE, spot=spot)
            self.assertEqual(at["gex_at_spot"] > 0, spot > level, spot)
            self.assertFalse(gex.gamma_regime(at["gex_at_spot"], spot, at)["regime_conflict"])

    def test_invalid_contracts_are_skipped_and_counted(self):
        base = _profile(PUTS_BELOW_CALLS_ABOVE)
        k = [85, 115, 100, 100, 100, 100]
        calls = [False, True, True, False, True, True]
        oi = [1000, 1000, 500, 500, 300, 0]
        iv = [IV, IV, np.nan, 0.0, IV, np.nan]
        T = [DAYS / 365, DAYS / 365, DAYS / 365, DAYS / 365, 0.0, DAYS / 365]
        zg = zero_gamma_profile(k, calls, oi, iv, T, S0, R)
        # NaN IV, zero IV and T = 0 with OI are skipped; the no-OI contract is not counted.
        self.assertEqual(zg["n_skipped"], 3)
        self.assertEqual(zg["n_contracts"], 2)
        np.testing.assert_allclose(zg["gex"], base["gex"])
        none = zero_gamma_profile([100], [True], [10], [np.nan], [0.1], S0, R)
        self.assertEqual(none["zero_gamma_status"], "no_valid_contracts")
        self.assertIsNone(none["gex_at_spot"])
        self.assertEqual(zero_gamma_profile([100], [True], [10], [IV], [0.1], np.nan, R)["zero_gamma_status"],
                         "no_spot")

    def test_grid_is_overridable_and_downsampled(self):
        zg = _profile(PUTS_BELOW_CALLS_ABOVE, half_width=0.1, n_points=41)
        self.assertEqual(len(zg["grid"]), 41)
        self.assertAlmostEqual(zg["grid"][0], 90.0)
        compact = downsample_profile(_profile(PUTS_BELOW_CALLS_ABOVE))
        self.assertEqual(len(compact), ZERO_GAMMA_EXPORT_POINTS)
        self.assertIn(S0, [p[0] for p in compact])
        self.assertEqual(downsample_profile({}), [])


def _gex_field_chain(rows, spot=S0, days=DAYS, q=0.01):
    T_eff = max(days / 365, 1 / 365 / 24)
    return pd.DataFrame([{
        "strike": float(k), "expiration": "2026-11-08", "type": t, "open_interest": oi,
        "implied_volatility": IV, "gamma": _gamma(spot, k, T_eff, gex.RISK_FREE_RATE, IV, q),
        "delta": 0.5, "moneyness": (k - spot) / spot, "days_to_exp": days, "dividend_yield": q,
    } for k, t, oi in rows])


class GexFieldZeroGammaTests(unittest.TestCase):
    def metrics(self, rows, spot=S0):
        with mock.patch("builtins.print"):
            return gex.calculate_gex_and_surface_forces(_gex_field_chain(rows, spot), spot, "t")

    def test_grid_at_spot_equals_net_gex_at_spot(self):
        _, _, m = self.metrics(DAY2)
        self.assertAlmostEqual(m["gex_at_spot_grid"] / m["total_gex"], 1.0, places=9)

    def test_day2_pattern_positive_without_conflict(self):
        df_gex, flip, m = self.metrics(DAY2)
        self.assertGreater(m["strike_balance_level"], S0)
        self.assertLess(m["zero_gamma_level"], S0)
        self.assertEqual(flip, m["zero_gamma_level"])
        self.assertEqual(m["regime"], gex.REGIME_POSITIVE)
        self.assertEqual(m["regime_basis"], "zero_gamma_grid")
        self.assertEqual(m["regime_by_zero_gamma"], gex.REGIME_POSITIVE)
        self.assertFalse(m["regime_conflict"])
        self.assertAlmostEqual(m["strike_balance_level"],
                               gamma_flip_level(df_gex["strike"], df_gex["net_gex"], spot=S0, max_distance_pct=0.3))

        data = {"price": S0, "weight": 1.0, "metrics_structural": m}
        holding = gex._senal_gex({"portfolio_data": {"AVGO": data}})["holdings"][0]
        self.assertEqual(holding["zero_gamma_level"], m["zero_gamma_level"])
        self.assertEqual(holding["gamma_flip"], holding["zero_gamma_level"])
        self.assertEqual(holding["strike_balance_level"], m["strike_balance_level"])
        self.assertEqual(holding["zero_gamma_status"], "ok")
        self.assertEqual(holding["regime_basis"], "zero_gamma_grid")
        self.assertFalse(holding["regime_conflict"])
        self.assertAlmostEqual(holding["zero_gamma_distance_pct"], (S0 - m["zero_gamma_level"]) / S0)
        self.assertEqual(len(holding["gex_profile_grid"]), ZERO_GAMMA_EXPORT_POINTS)
        self.assertNotIn("regime_by_flip", holding)

        lines = gex.get_holdings_reference_lines({"AVGO": {**data, "expected_move": 0.1}})
        self.assertIn("Zero Gamma", [line["label"] for line in lines])

    def test_no_crossing_reports_status_and_sign(self):
        _, flip, m = self.metrics(CALLS_ONLY)
        self.assertIsNone(flip)
        self.assertEqual((m["zero_gamma_status"], m["zero_gamma_grid_sign"]), ("no_crossing_in_grid", "all_positive"))
        self.assertEqual(m["regime"], gex.REGIME_POSITIVE)
        self.assertFalse(m["regime_conflict"])

    def test_profile_figure_is_saved_headless(self):
        _, _, m = self.metrics(DAY2)
        fig = gex.plot_zero_gamma_profiles({"AVGO": {"price": S0, "metrics_structural": m}})
        self.assertEqual(len(fig.data), 1)
        self.assertIsNone(gex.plot_zero_gamma_profiles({"X": {"price": S0, "metrics_structural": {}}}))
        tmp = tempfile.mkdtemp()
        with mock.patch("builtins.print"):
            path = viz_utils.show_or_save(fig, "portfolio_gex_field", "zero_gamma",
                                          env={"HEADLESS": "1", "FIGURES_DIR": tmp})
        self.assertTrue(os.path.isfile(path))


class ConsumerZeroGammaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.am = _load_active_management()

    def _am_chain(self, rows, spot=S0):
        exp = (date.today() + timedelta(days=DAYS)).isoformat()
        r = self.am["risk_free_rate"]
        return pd.DataFrame([{"strike": float(k), "type": t, "open_interest": oi, "iv": IV, "expiration": exp,
                              "gamma": _gamma(spot, k, DAYS / 365, r, IV)} for k, t, oi in rows])

    def test_active_management_flip_is_the_zero_gamma_level(self):
        res = self.am["calculate_gex"](self._am_chain(DAY2), S0)
        zg = _profile(DAY2, r=self.am["risk_free_rate"])
        self.assertAlmostEqual(res["gex_flip_level"], zg["zero_gamma_level"])
        self.assertAlmostEqual(zg["gex_at_spot"] / res["total_gex"], 1.0, places=9)
        self.assertGreater(res["gex_strike_balance_level"], S0)
        self.assertLess(res["gex_flip_level"], S0)

    def test_active_management_no_crossing_scores_like_a_far_level(self):
        res = self.am["calculate_gex"](self._am_chain(CALLS_ONLY), S0)
        self.assertTrue(np.isnan(res["gex_flip_level"]))
        analysis = {"ticker": "X", "status": "OK", "spot_price": S0, "gex": res,
                    "flow": None, "expected_move": None, "vanna_charm": None}
        no_crossing = self.am["calculate_tactical_score"](analysis)
        far_below = self.am["calculate_tactical_score"]({**analysis, "gex": {**res, "gex_flip_level": 50.0}})
        self.assertEqual(no_crossing["score"], far_below["score"])
        self.assertIn("Sin zero gamma", no_crossing["rationale"])

    def test_entry_signal_distance_uses_the_zero_gamma_level(self):
        hoy = date(2026, 10, 9)
        rows = [{"strike": float(k), "tipo": t, "oi": oi, "iv": IV,
                 "vencimiento": (hoy + timedelta(days=DAYS)).isoformat(),
                 "gamma": _gamma(S0, k, DAYS / 365, es.RISK_FREE_RATE, IV)} for k, t, oi in DAY2]
        gex_total, dist = es.calcular_gex_y_zero_gamma(pd.DataFrame(rows), S0, hoy=hoy)
        zg = _profile(DAY2, r=es.RISK_FREE_RATE)
        self.assertAlmostEqual(dist, (S0 - zg["zero_gamma_level"]) / S0)
        self.assertGreater(dist, 0)
        self.assertAlmostEqual(zg["gex_at_spot"] / gex_total, 1.0, places=9)
        calls = [{**row, "tipo": "call"} for row in rows]
        self.assertTrue(np.isnan(es.calcular_gex_y_zero_gamma(pd.DataFrame(calls), S0, hoy=hoy)[1]))

    def test_risk_score_zero_gamma_level(self):
        from tests.test_cycle2_fixes import _RISK_FUNCS
        from tests.test_international_fallback import _load_functions
        ns = _load_functions("portfolio_risk_score_leverage.py", _RISK_FUNCS,
                             {"np": np, "pd": pd, "norm": norm, "zero_gamma_profile": zero_gamma_profile})
        chain = pd.DataFrame([{"strike": float(k), "contract_type": t, "open_interest": oi, "iv": IV,
                               "gamma": _gamma(S0, k, DAYS / 365, R, IV), "spot": S0} for k, t, oi in DAY2])
        level = ns["compute_zero_gamma_level"](chain, DAYS, R)
        self.assertAlmostEqual(level, _profile(DAY2)["zero_gamma_level"])
        profile = ns["compute_gex_profile"](chain)
        self.assertAlmostEqual(_profile(DAY2)["gex_at_spot"] / profile["GEX_neto"].sum(), 1.0, places=9)
        self.assertTrue(np.isnan(ns["compute_zero_gamma_level"](chain.assign(spot=np.nan), DAYS, R)))


if __name__ == "__main__":
    unittest.main()
