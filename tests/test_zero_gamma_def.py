"""entry_signal_history.csv tags dist_zero_gamma with the definition behind it."""

import os
import tempfile
import unittest
from unittest import mock

import numpy as np
import pandas as pd

import entry_signal_tool as es
from gex_utils import ZERO_GAMMA_DEF, ZERO_GAMMA_DEF_LEGACY

LEGACY_COLUMNS = ["fecha", "ticker", "gex_total", "dist_zero_gamma", "smart_money"]


def _legacy_csv(path, n=2):
    pd.DataFrame({
        "fecha": pd.date_range("2026-01-01", periods=n),
        "ticker": "X",
        "gex_total": 1.0,
        "dist_zero_gamma": 0.05,
        "smart_money": 1.0,
    })[LEGACY_COLUMNS].to_csv(path, index=False)


def _hist(dists, definiciones, ticker="X"):
    return pd.DataFrame({
        "fecha": pd.date_range("2026-03-02", periods=len(dists)),
        "ticker": ticker,
        "dist_zero_gamma": dists,
        "smart_money": 1.0,
        "zero_gamma_def": definiciones,
    })


class DefinitionTagTests(unittest.TestCase):
    def test_legacy_csv_loads_as_strike_balance_and_keeps_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "hist.csv")
            _legacy_csv(path)
            with mock.patch.object(es, "HIST_PATH", path):
                hist = es.cargar_historial()
        self.assertEqual(list(hist.columns), LEGACY_COLUMNS + ["zero_gamma_def"])
        self.assertEqual(set(hist["zero_gamma_def"]), {ZERO_GAMMA_DEF_LEGACY})
        self.assertEqual(ZERO_GAMMA_DEF_LEGACY, "strike_balance")
        self.assertEqual(list(hist["dist_zero_gamma"]), [0.05, 0.05])

    def test_blank_definition_values_are_legacy(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "hist.csv")
            _legacy_csv(path, n=3)
            raw = pd.read_csv(path)
            raw["zero_gamma_def"] = [np.nan, ZERO_GAMMA_DEF, np.nan]
            raw.to_csv(path, index=False)
            with mock.patch.object(es, "HIST_PATH", path):
                hist = es.cargar_historial()
        self.assertEqual(list(hist["zero_gamma_def"]),
                         [ZERO_GAMMA_DEF_LEGACY, ZERO_GAMMA_DEF, ZERO_GAMMA_DEF_LEGACY])

    def test_new_rows_are_tagged_and_appended_after_legacy_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "hist.csv")
            _legacy_csv(path)
            with mock.patch.object(es, "HIST_PATH", path):
                hist = es.cargar_historial()
            nuevas = pd.DataFrame([
                {"fecha": pd.Timestamp("2026-02-01"), "ticker": "X", "gex_total": 2.0,
                 "dist_zero_gamma": 0.02, "smart_money": 1.0},
                # proxy-style row and row with NaN distance
                {"fecha": pd.Timestamp("2026-02-01"), "ticker": "Y", "gex_total": 2.0,
                 "dist_zero_gamma": np.nan, "smart_money": 1.0, "tier": "proxy"},
            ])
            todo = pd.concat([hist, es._etiquetar_definiciones(nuevas)], ignore_index=True)
        self.assertEqual(list(todo.columns[:len(LEGACY_COLUMNS)]), LEGACY_COLUMNS)
        self.assertEqual(todo.columns[len(LEGACY_COLUMNS)], "zero_gamma_def")
        self.assertEqual(list(todo["zero_gamma_def"]),
                         [ZERO_GAMMA_DEF_LEGACY] * 2 + [ZERO_GAMMA_DEF] * 2)
        self.assertEqual(ZERO_GAMMA_DEF, "zero_gamma_grid")

    def test_other_columns_use_every_row(self):
        hist = _hist([0.05] * 6, [ZERO_GAMMA_DEF_LEGACY] * 6)
        self.assertEqual(len(es._filas_misma_definicion(hist, "gex_total")), 6)
        self.assertEqual(len(es._filas_misma_definicion(hist, "dist_zero_gamma")), 0)


class PercentileTests(unittest.TestCase):
    def test_legacy_rows_are_excluded_from_the_percentile(self):
        hist = _hist([0.01, 0.02, 0.03, 0.04, 0.05], [ZERO_GAMMA_DEF_LEGACY] * 5)
        self.assertEqual(es.percentile_historico(hist, "X", "dist_zero_gamma", 0.045, absoluto=True), 50.0)

    def test_new_rows_give_a_real_percentile(self):
        hist = _hist([0.01, 0.02, 0.03, 0.04, 0.05], [ZERO_GAMMA_DEF] * 5)
        self.assertEqual(es.percentile_historico(hist, "X", "dist_zero_gamma", 0.045, absoluto=True), 80.0)

    def test_mixed_history_counts_only_new_rows(self):
        hist = _hist([0.50] * 4 + [0.01, 0.02, 0.03, 0.04, 0.05],
                     [ZERO_GAMMA_DEF_LEGACY] * 4 + [ZERO_GAMMA_DEF] * 5)
        self.assertEqual(es.percentile_historico(hist, "X", "dist_zero_gamma", 0.045, absoluto=True), 80.0)

    def test_other_metrics_still_use_legacy_rows(self):
        hist = _hist([0.05] * 5, [ZERO_GAMMA_DEF_LEGACY] * 5)
        hist["gex_total"] = [1.0, 2.0, 3.0, 4.0, 5.0]
        self.assertEqual(es.percentile_historico(hist, "X", "gex_total", 3.5), 60.0)


class DayFiveTrendTests(unittest.TestCase):
    def _decide(self, dists, definiciones, smart_money):
        hist = _hist(dists, definiciones)
        hist["smart_money"] = smart_money
        return es.evaluar_flujo_opciones("X", hist)

    def test_old_definition_first_row_gives_no_spurious_shortening(self):
        # Legacy first row is far from spot; the new-definition rows get farther.
        decision, detalle = self._decide(
            [0.10, 0.02, 0.03, 0.04, 0.05],
            [ZERO_GAMMA_DEF_LEGACY] + [ZERO_GAMMA_DEF] * 4,
            [-1.0] * 5,
        )
        self.assertIn("alejandose", detalle)
        self.assertNotIn("acortamiento", detalle)
        self.assertEqual(decision, "CASH")

    def test_trend_uses_only_new_definition_rows(self):
        decision, detalle = self._decide(
            [0.01, 0.10, 0.05, 0.04, 0.03],
            [ZERO_GAMMA_DEF_LEGACY] + [ZERO_GAMMA_DEF] * 4,
            [1.0] * 5,
        )
        self.assertIn("acortamiento", detalle)
        self.assertEqual(decision, "ENTRAR")

    def test_fewer_than_two_new_rows_skips_the_subsignal(self):
        # Only smart_money counts; the zero-gamma sub-signal adds nothing to señales_totales.
        decision, detalle = self._decide(
            [0.10, 0.09, 0.08, 0.07, 0.01],
            [ZERO_GAMMA_DEF_LEGACY] * 4 + [ZERO_GAMMA_DEF],
            [-1.0] * 5,
        )
        self.assertNotIn("zero-gamma", detalle)
        self.assertEqual(detalle, "smart money desfavorable (put/call >= 1)")
        self.assertEqual(decision, "CASH")

    def test_no_new_rows_and_no_other_signal_is_cash(self):
        hist = _hist([0.10, 0.05, 0.04, 0.03, 0.02], [ZERO_GAMMA_DEF_LEGACY] * 5)
        hist["smart_money"] = np.nan
        decision, detalle = es.evaluar_flujo_opciones("X", hist)
        self.assertEqual(decision, "CASH")
        self.assertIn("sin señales", detalle)


if __name__ == "__main__":
    unittest.main()
