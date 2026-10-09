"""Day-2 fixes: headless figures, GEX expiry fallback, flip root and regime
conflict. No network: figures and option chains are fakes."""

import os
import re
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd
import plotly.graph_objects as go

import portfolio_gex_field as gex
import portfolio_vix as vix
import viz_utils
from gex_utils import gamma_flip_crossings, gamma_flip_level
from tests.test_international_fallback import _load_functions


# ------------------------------------------------------------------------------
# 1. Headless figures
# ------------------------------------------------------------------------------

class ShowOrSaveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.env = {"HEADLESS": "1", "FIGURES_DIR": self.tmp}

    def test_headless_writes_html_and_never_shows(self):
        fig = go.Figure(go.Scatter(x=[1, 2], y=[3, 4]))
        with mock.patch.object(go.Figure, "show") as show, mock.patch("builtins.print"):
            path = viz_utils.show_or_save(fig, "entry_signal_tool", "resumen", env=self.env)
        show.assert_not_called()
        self.assertTrue(os.path.isfile(path))
        self.assertEqual(os.path.dirname(path), self.tmp)
        self.assertRegex(os.path.basename(path), r"^entry_signal_tool_resumen_\d{8}T\d{6}\.html$")
        self.assertIn("plotly", Path(path).read_text(encoding="utf-8").lower())

    def test_mock_figure_headless_and_interactive(self):
        fig = mock.MagicMock()
        with mock.patch("builtins.print"):
            path = viz_utils.show_or_save(fig, "s", "n", env=self.env)
        fig.show.assert_not_called()
        fig.write_html.assert_called_once()
        self.assertEqual(fig.write_html.call_args[0][0], path)

        fig = mock.MagicMock()
        self.assertIsNone(viz_utils.show_or_save(fig, "s", env={"HEADLESS": "0", "FIGURES_DIR": self.tmp}))
        fig.show.assert_called_once()
        fig.write_html.assert_not_called()
        self.assertIsNone(viz_utils.show_or_save(None, "s", env=self.env))

    def test_headless_decision(self):
        self.assertTrue(viz_utils.headless({"HEADLESS": "true"}, interactive=True))
        self.assertFalse(viz_utils.headless({"HEADLESS": "0"}, interactive=False))
        self.assertTrue(viz_utils.headless({"DISPLAY": ":0"}, interactive=False))
        with mock.patch.object(viz_utils.sys, "platform", "linux"):
            self.assertTrue(viz_utils.headless({}, interactive=True))
            self.assertFalse(viz_utils.headless({"DISPLAY": ":0"}, interactive=True))
        with mock.patch.object(viz_utils.sys, "platform", "darwin"):
            self.assertFalse(viz_utils.headless({}, interactive=True))

    def test_default_figures_dir_is_under_the_pipeline_dir(self):
        with mock.patch.dict(os.environ, {"PIPELINE_DIR": self.tmp}):
            self.assertEqual(viz_utils.figures_dir({}), os.path.join(self.tmp, "figures"))

    def test_risk_report_saves_every_plot_headless(self):
        figs = {name: mock.MagicMock(name=name) for name in ("pcr", "gex", "lev")}
        ns = _load_functions("portfolio_risk_score_leverage.py", {"run_reporting_module"}, {
            "print_executive_summary": lambda *a: None,
            "plot_pcr_vs_weight": lambda *a: figs["pcr"],
            "plot_gex_profile": lambda *a: figs["gex"],
            "plot_loss_distribution": lambda *a: None,
            "plot_leverage_assignment": lambda *a: figs["lev"],
            "show_or_save": viz_utils.show_or_save,
        })
        expost = {"var_es": pd.DataFrame({"Activo": ["A"]}), "risk_contribution": None}
        with mock.patch.dict(os.environ, self.env), mock.patch("builtins.print"):
            ns["run_reporting_module"](expost, {"by_asset": {}}, {"summary": None}, None, 2, 5)
        for fig in figs.values():
            fig.show.assert_not_called()
            fig.write_html.assert_called_once()

    def test_vix_report_is_not_shown_headless(self):
        fig = mock.MagicMock()
        html = os.path.join(self.tmp, "vix.html")
        with mock.patch.dict(os.environ, {"HEADLESS": "1"}), mock.patch("builtins.print"), \
                mock.patch.object(vix.webbrowser, "open") as browser:
            out = vix.ReportPlotter.plot({}, None, {}, None, html_file=html, show=True, fig=fig)
        self.assertEqual(out, html)
        fig.write_html.assert_called_once()
        fig.show.assert_not_called()
        browser.assert_not_called()

    def test_scripts_do_not_call_show_directly(self):
        for script in ("entry_signal_tool.py", "portfolio_risk_score_leverage.py",
                       "active_management.py", "portfolio_gex_field.py"):
            text = Path(script).read_text(encoding="utf-8")
            self.assertIsNone(re.search(r"\.show\(\)", text), script)
            self.assertNotIn("plt.show", text, script)
        for script in ("entry_signal_tool.py", "portfolio_risk_score_leverage.py", "active_management.py"):
            self.assertIn("show_or_save(", Path(script).read_text(encoding="utf-8"), script)


# ------------------------------------------------------------------------------
# 2. GEX expiry fallback
# ------------------------------------------------------------------------------

def _chain(days_list, spot=100.0):
    today = datetime.now(timezone.utc).date()
    rows = []
    for d in days_list:
        exp = (today + timedelta(days=d)).isoformat()
        for k, typ, oi in ((95, "put", 50), (100, "call", 80), (100, "put", 30), (105, "call", 60)):
            rows.append({"strike": float(k), "expiration": exp, "type": typ, "open_interest": oi,
                         "implied_volatility": 0.2, "gamma": 0.05, "delta": 0.5,
                         "moneyness": (k - spot) / spot, "days_to_exp": d})
    return pd.DataFrame(rows)


class GexExpiryFallbackTests(unittest.TestCase):
    """Day 2: 30 days left; RY / AEP list only monthlies at 7 and 42 days."""

    def run_chains(self, available, ticker="AEP", fail=None, fail_from=0):
        calls = []

        def fetch(simbolo, price, horizon_months=None, strike_range_pct=None,
                  horizon_days=None, retry_default=True):
            calls.append((horizon_days, retry_default))
            if fail and horizon_days >= fail_from:
                gex._ULTIMO_FALLO_CADENA[simbolo] = fail
                return pd.DataFrame()
            days = [d for d in available if d <= horizon_days]
            return _chain(days) if days else pd.DataFrame()

        with mock.patch.object(gex, "get_polygon_options_data", fetch), \
                mock.patch.object(gex, "get_current_price", lambda s: 100.0), \
                mock.patch.dict(gex._ultimo_dato_valido, clear=True), \
                mock.patch("builtins.print"):
            data = gex.get_portfolio_chains({ticker: 1.0}, horizon_days=30)
        return data, calls, list(gex._LAST_EXCLUDED)

    def test_ladder(self):
        self.assertEqual(gex.ventanas_vencimiento(30), [30, 60, 90, 120, 180])
        self.assertEqual(gex.ventanas_vencimiento(61), [61, 90, 120, 180])
        self.assertEqual(gex.ventanas_vencimiento(200), [200])

    def test_only_a_7_day_expiry_in_the_horizon_falls_back_to_the_next_usable(self):
        data, calls, excluded = self.run_chains([7, 42])
        self.assertEqual(excluded, [])
        self.assertEqual([c[0] for c in calls][:2], [30, 60])
        self.assertTrue(all(retry is False for _, retry in calls))
        aep = data["AEP"]
        self.assertEqual(aep["expiry_window_days"], 60)
        self.assertTrue(aep["expiry_fallback"])
        self.assertEqual(aep["expirations"], [(datetime.now(timezone.utc).date() + timedelta(days=42)).isoformat()])
        holding = gex._senal_gex({"portfolio_data": data})["holdings"][0]
        self.assertEqual((holding["expiry_window_days"], holding["expiry_fallback"]), (60, True))
        self.assertEqual(holding["expirations"], aep["expirations"])

    def test_beyond_the_old_60_day_cap(self):
        data, calls, excluded = self.run_chains([7, 75])
        self.assertEqual(excluded, [])
        self.assertEqual([c[0] for c in calls][:3], [30, 60, 90])
        self.assertEqual(data["AEP"]["expiry_window_days"], 90)

    def test_usable_horizon_is_not_a_fallback(self):
        data, calls, _ = self.run_chains([14, 42])
        self.assertEqual(calls[0][0], 30)
        self.assertEqual(data["AEP"]["expiry_window_days"], 30)
        self.assertFalse(data["AEP"]["expiry_fallback"])

    def test_excluded_only_when_no_window_gives_a_field(self):
        data, calls, excluded = self.run_chains([3, 7])
        self.assertEqual(data, {})
        self.assertEqual([c[0] for c in calls], [30, 60, 90, 120, 180])
        self.assertEqual(excluded, [{"ticker": "AEP", "reason": "no usable gamma field"}])

    def test_api_failure_stops_the_ladder(self):
        data, calls, excluded = self.run_chains([42], fail="rate_limited")
        self.assertEqual(calls, [(30, False)])
        self.assertEqual(excluded, [{"ticker": "AEP", "reason": "rate_limited"}])
        # A failure on a wider window reports the API error, not "no usable field".
        data, calls, excluded = self.run_chains([7, 42], fail="rate_limited", fail_from=60)
        self.assertEqual([c[0] for c in calls], [30, 60])
        self.assertEqual(excluded, [{"ticker": "AEP", "reason": "rate_limited"}])
        self.assertNotIn("AEP", gex._ULTIMO_FALLO_CADENA)

    def test_zero_exposure_is_not_usable(self):
        flat = pd.DataFrame({"strike": [95.0, 100.0], "net_gex": [0.0, 0.0]})
        self.assertFalse(gex.campo_gamma_utilizable(flat, 0.05))
        self.assertFalse(gex.campo_gamma_utilizable(None, 0.05))
        live = pd.DataFrame({"strike": [95.0, 100.0], "net_gex": [-1.0, 2.0]})
        self.assertFalse(gex.campo_gamma_utilizable(live, float("nan")))
        self.assertTrue(gex.campo_gamma_utilizable(live, 0.05))


# ------------------------------------------------------------------------------
# 3. Strike-balance root selection and regime
# ------------------------------------------------------------------------------

class FlipRootTests(unittest.TestCase):
    # Cumulative: +1, -2, -4, +2, +3 -> crossings at 71.67 (window edge) and 100.
    STRIKES = [70, 75, 90, 105, 110]
    NET = [1, -3, -2, 6, 1]

    def test_single_crossing(self):
        # Cumulative -2, -3, +2: one crossing at 100 + 3 / 5 * 10 = 106.
        self.assertAlmostEqual(gamma_flip_level([90, 100, 110], [-2, -1, 5], spot=104), 106.0)
        self.assertAlmostEqual(gamma_flip_level([90, 100, 110], [-2, -1, 5]), 106.0)
        self.assertEqual(len(gamma_flip_crossings([90, 100, 110], [-2, -1, 5])), 1)

    def test_multiple_crossings_pick_the_one_nearest_spot(self):
        crossings = gamma_flip_crossings(self.STRIKES, self.NET)
        self.assertEqual(len(crossings), 2)
        self.assertAlmostEqual(crossings[0], 70 + 5 / 3)
        self.assertAlmostEqual(crossings[1], 100.0)
        # Old rule (no spot): the first crossing from the bottom of the window.
        self.assertAlmostEqual(gamma_flip_level(self.STRIKES, self.NET), 70 + 5 / 3)
        self.assertAlmostEqual(gamma_flip_level(self.STRIKES, self.NET, spot=98.0), 100.0)
        self.assertAlmostEqual(gamma_flip_level(self.STRIKES, self.NET, spot=73.0), 70 + 5 / 3)

    def test_band_drops_far_crossings(self):
        # Crossings at 141.67 and 147, both more than 30% above spot 100.
        self.assertTrue(np.isnan(gamma_flip_level([140, 145, 150], [1, -3, 5], spot=100.0, max_distance_pct=0.30)))
        self.assertAlmostEqual(gamma_flip_level([140, 145, 150], [1, -3, 5], spot=100.0), 140 + 5 / 3)

    def test_regime_definition(self):
        # Regime from the zero-gamma profile (tests/test_zero_gamma.py covers the grid).
        pos, neg = gex.REGIME_POSITIVE, gex.REGIME_NEGATIVE

        def zg(at_spot, level):
            return {"gex_at_spot": at_spot, "zero_gamma_level": level}

        self.assertEqual(gex.gamma_regime(5.0, 105.0, zg(5.0, 100.0)),
                         {"regime": pos, "regime_basis": "zero_gamma_grid",
                          "regime_by_zero_gamma": pos, "regime_conflict": False})
        self.assertEqual(gex.gamma_regime(-5.0, 95.0, zg(-5.0, 100.0))["regime_conflict"], False)
        # The profile decides, not the strike sum: AVGO day 2 had net GEX > 0 at spot.
        self.assertEqual(gex.gamma_regime(21_899_385.0, 362.55, zg(2e7, 340.0))["regime"], pos)
        # Only a downward nearest crossing (positive below, negative above) conflicts.
        self.assertTrue(gex.gamma_regime(-5.0, 105.0, zg(-5.0, 100.0))["regime_conflict"])
        # No crossing in the grid: sign at spot, nothing to compare.
        self.assertEqual(gex.gamma_regime(1.0, 100.0, zg(3.0, None)),
                         {"regime": pos, "regime_basis": "zero_gamma_grid",
                          "regime_by_zero_gamma": None, "regime_conflict": False})
        # No profile at all (no IV): falls back to net GEX at spot.
        self.assertEqual(gex.gamma_regime(-1.0, 100.0, None),
                         {"regime": neg, "regime_basis": "net_gex_at_spot",
                          "regime_by_zero_gamma": None, "regime_conflict": False})

    def _profile(self):
        # gamma 1, OI = |net| -> net GEX per strike proportional to NET. No IV:
        # the zero-gamma profile cannot be built.
        rows = [{"strike": float(k), "type": "call" if n > 0 else "put", "open_interest": abs(n),
                 "gamma": 1.0} for k, n in zip(self.STRIKES, self.NET)]
        return pd.DataFrame(rows)

    def test_field_keeps_the_nearest_strike_balance_level(self):
        with mock.patch("builtins.print"):
            _, flip, metrics = gex.calculate_gex_and_surface_forces(self._profile(), 98.0, "t")
        self.assertAlmostEqual(metrics["strike_balance_level"], 100.0)
        self.assertEqual(metrics["strike_balance_crossings"], 2)
        self.assertIsNone(flip)
        self.assertIsNone(metrics["zero_gamma_level"])
        self.assertEqual(metrics["zero_gamma_status"], "no_valid_contracts")
        self.assertEqual(metrics["regime"], gex.REGIME_POSITIVE)
        self.assertFalse(metrics["regime_conflict"])

        holding = gex._senal_gex({"portfolio_data": {"X": {"metrics_structural": metrics}}})["holdings"][0]
        self.assertFalse(holding["regime_conflict"])
        self.assertEqual(holding["regime_basis"], "net_gex_at_spot")
        self.assertEqual(holding["strike_balance_crossings"], 2)
        self.assertIsNone(holding["gamma_flip"])


if __name__ == "__main__":
    unittest.main()
