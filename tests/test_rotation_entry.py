"""entry_signal_tool after drawdown_rotation: a name the rotation adds is bought in
tranches (also once the previous entry cycle is closed), and a name that was
fully sold is not bought again. Real drawdown_rotation state helpers; tier "none"
(.LS) tickers so the entry tool runs without network."""

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import drawdown_rotation as dr
import entry_signal_tool as est
import pipeline_io

OPT, RUN_TS = "minimum_variance", "2026-10-05T16:40:12-05:00"
STAMP = "20261005T164012"
META = {"weights": {"EDP.LS": 0.5, "JMT.LS": 0.5}, "portfolio_source": "mv.json",
        "portfolio_run_ts": RUN_TS, "portfolio_optimizer": OPT}
NEW = "GALP.LS"
DAYS = ["2026-10-06", "2026-10-07", "2026-10-08", "2026-10-09", "2026-10-12",
        "2026-10-13", "2026-10-14", "2026-10-15", "2026-10-16", "2026-10-19"]
_ENTRY_ENV = ("ENTRY_CYCLE_DAY", "ENTRY_INVESTED_PCT", "ENTRY_FORCE_NEW_TRANCHE",
              "ENTRY_STATE_FILE", "PIPELINE_DIR", "CYCLE_DATE", "ROTATION_STATE_FILE")


class RotationEntryCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.signals = self.root / "signals"
        self.executions = self.root / "executions"
        self.executions.mkdir()
        env = {k: v for k, v in os.environ.items() if k not in _ENTRY_ENV}
        env.update({"SIGNALS_OUT_DIR": str(self.signals), "EXECUTIONS_DIR": str(self.executions)})
        patcher = mock.patch.dict(os.environ, env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.rotation = pipeline_io.empty_rotation_state(META)
        self.holdings_qty = {}
        for name, value in (
            ("_PORTFOLIO_META", META),
            ("HIST_PATH", str(self.root / "history.csv")),
            ("LEGACY_STATE_PATH", str(self.root / "entry_state.json")),
            ("graficar_resumen", lambda resumen: None),
        ):
            patch = mock.patch.object(est, name, value)
            patch.start()
            self.addCleanup(patch.stop)
        self.apply_rotation_state()

    def apply_rotation_state(self):
        """What entry_signal_tool computes at import from the rotation state."""
        weights, notes = pipeline_io.apply_rotation_overrides(META["weights"], self.rotation)
        recortados = sorted(t for t, w in weights.items()
                            if t in META["weights"] and w < META["weights"][t] - 1e-9)
        for name, value in (("PESOS_OBJETIVO", weights), ("TICKERS", list(weights)), ("NOTAS_ROTACION", notes),
                            ("RECORTADOS_POR_ROTACION", recortados), ("ESTADO_ROTACION", self.rotation)):
            patch = mock.patch.object(est, name, value)
            patch.start()
            self.addCleanup(patch.stop)

    def rotate(self, day, sold, bought, weight_each, action="LIQUIDAR"):
        """drawdown_rotation's own state update, as run() does it."""
        triggers = [{"ticker": sold, "precio": 10.0, "ret_5d": -0.08, "accion": action, "recorte_pct": 1.0,
                     "peso_actual": 0.5, "peso_nuevo": 0.0, "peso_liberado": 0.5,
                     "diagnostico": {"total": 80.0}}]
        self.rotation = dr.update_state(self.rotation, triggers, bought, weight_each, day)
        self.apply_rotation_state()

    def run_entry(self, day, *argv):
        with mock.patch.dict(os.environ, {"CYCLE_DATE": day}):
            with redirect_stdout(io.StringIO()):
                est.main(list(argv))
        folder = self.signals / f"{OPT}_{STAMP}"
        return json.loads((folder / "entry_signal_tool.json").read_text(encoding="utf-8"))

    def write_buys(self, signal):
        """The executor fills every entry of ``signal`` completely."""
        run_ts = signal["run_ts"]
        fills = []
        for e in signal["data"]["entries"]:
            qty = round(e["tranche_weight"] * 1000, 6)
            self.holdings_qty[e["ticker"]] = self.holdings_qty.get(e["ticker"], 0.0) + qty
            fills.append({"ticker": e["ticker"], "action": "BUY", "filled_weight": e["tranche_weight"],
                          "filled_qty": qty, "status": "filled"})
        (self.executions / f"fills_{OPT}_{STAMP}.json").write_text(json.dumps({
            "schema_version": 1, "signal_run_ts": run_ts, "executed_ts": run_ts, "fills": fills,
        }), encoding="utf-8")

    def write_sale(self, ticker, qty, name="sell_fills_%s_20261012T150000.json" % OPT):
        (self.executions / name).write_text(json.dumps({
            "schema_version": 1, "script": "drawdown_rotation", "portfolio_optimizer": OPT,
            "portfolio_run_ts": RUN_TS, "executed_ts": "2026-10-12T15:00:00-05:00",
            "fills": [{"ticker": ticker, "action": "SELL", "filled_qty": qty, "filled_weight": 0.1,
                       "status": "filled", "reason": "ROTACION_SALIDA"}],
        }), encoding="utf-8")

    def state(self):
        return json.loads(Path(pipeline_io.entry_state_path(META)).read_text(encoding="utf-8"))

    def full_cycle(self, days):
        """Run entry for ``days`` filling each signal; returns the signals."""
        signals = []
        for day in days:
            signal = self.run_entry(day)
            self.write_buys(signal)
            signals.append(signal)
        return signals


class RotationTargetsAreTranchedTests(RotationEntryCase):
    def test_new_name_added_after_day_5_is_bought_in_tranches(self):
        cycle1 = self.full_cycle(DAYS[:5])
        self.assertEqual([s["data"]["cycle_day"] for s in cycle1], [1, 2, 3, 4, 5])
        # Day 6 run applies the day 5 fills: cycle 1 closed.
        self.rotate(DAYS[5], sold="JMT.LS", bought=[NEW], weight_each=0.5)
        self.assertEqual(est.PESOS_OBJETIVO, {"EDP.LS": 0.5, NEW: 0.5})
        self.assertNotIn("JMT.LS", est.TICKERS)

        cycle2 = self.full_cycle(DAYS[5:10])
        self.assertEqual([s["data"]["cycle"] for s in cycle2], [2] * 5)
        self.assertEqual([s["data"]["cycle_day"] for s in cycle2], [1, 2, 3, 4, 5])
        for signal in cycle2:
            tickers = [e["ticker"] for e in signal["data"]["entries"]]
            self.assertEqual(tickers, [NEW])  # EDP.LS is complete, JMT.LS was sold
            entry = signal["data"]["entries"][0]
            self.assertEqual(entry["action"], "BUY")
            self.assertEqual(entry["signal"], "staggered")
            self.assertAlmostEqual(entry["target_weight"], est.no_options_weight_cap(0.5))
        # The five tranches add up to the whole target; the last one is still waiting for its fills.
        tranches = [s["data"]["entries"][0]["tranche_weight"] for s in cycle2]
        self.assertAlmostEqual(sum(tranches), est.no_options_weight_cap(0.5), places=5)
        self.assertAlmostEqual(self.state()["activos"][NEW]["pct_ya_invertido"], 0.8)
        self.assertEqual(est.ESTADO_ROTACION["target_overrides"][NEW], 0.5)

    def test_new_name_added_mid_cycle_enters_with_the_running_cycle(self):
        self.full_cycle(DAYS[:2])
        self.rotate(DAYS[2], sold="JMT.LS", bought=[NEW], weight_each=0.5)
        signal = self.run_entry(DAYS[2])
        self.assertEqual(signal["data"]["cycle_day"], 3)
        entries = {e["ticker"]: e for e in signal["data"]["entries"]}
        self.assertIn(NEW, entries)
        self.assertNotIn("JMT.LS", entries)

    def test_trimmed_name_is_not_topped_up(self):
        self.full_cycle(DAYS[:5])
        triggers = [{"ticker": "JMT.LS", "precio": 10.0, "ret_5d": -0.08, "accion": "RECORTAR",
                     "recorte_pct": 0.5, "peso_actual": 0.5, "peso_nuevo": 0.25, "peso_liberado": 0.25,
                     "diagnostico": {"total": 55.0}}]
        self.rotation = dr.update_state(self.rotation, triggers, [NEW], 0.25, DAYS[5])
        self.apply_rotation_state()
        signal = self.run_entry(DAYS[5])
        self.assertEqual([e["ticker"] for e in signal["data"]["entries"]], [NEW])
        self.assertTrue(any("target 0.5000 -> 0.2500" in w for w in signal["warnings"]))


class FullySoldIsNotBoughtAgainTests(RotationEntryCase):
    def test_fully_sold_name_still_in_targets_is_skipped(self):
        first = self.run_entry(DAYS[0])
        self.write_buys(first)
        self.assertIn("JMT.LS", [e["ticker"] for e in first["data"]["entries"]])
        # The whole JMT.LS position is sold (rotation state did not reach this run).
        self.write_sale("JMT.LS", self.holdings_qty["JMT.LS"])
        second = self.run_entry(DAYS[1])
        self.assertEqual([e["ticker"] for e in second["data"]["entries"]], ["EDP.LS"])
        self.assertNotIn("JMT.LS", [w["ticker"] for w in second["data"]["waiting"]])
        self.assertTrue(any("JMT.LS: fully sold" in w for w in second["warnings"]))
        self.assertEqual(second["data"]["net_holdings"]["JMT.LS"], 0)
        self.assertGreater(second["data"]["net_holdings"]["EDP.LS"], 0)

    def test_partly_sold_name_keeps_filling(self):
        first = self.run_entry(DAYS[0])
        self.write_buys(first)
        self.write_sale("JMT.LS", self.holdings_qty["JMT.LS"] / 2)
        second = self.run_entry(DAYS[1])
        self.assertIn("JMT.LS", [e["ticker"] for e in second["data"]["entries"]])
        self.assertFalse(any("fully sold" in w for w in second["warnings"]))

    def test_liquidated_name_leaves_the_targets_and_is_not_bought(self):
        first = self.run_entry(DAYS[0])
        self.write_buys(first)
        self.rotate(DAYS[1], sold="JMT.LS", bought=[NEW], weight_each=0.5)
        self.write_sale("JMT.LS", self.holdings_qty["JMT.LS"])
        second = self.run_entry(DAYS[1])
        self.assertEqual(sorted(e["ticker"] for e in second["data"]["entries"]), ["EDP.LS", NEW])

    def test_name_the_rotation_picks_again_after_selling_it_is_bought_again(self):
        first = self.run_entry(DAYS[0])
        self.write_buys(first)
        self.write_sale("JMT.LS", self.holdings_qty["JMT.LS"])
        # JMT.LS dropped and was sold on 10-07, then chosen again by a later rotation.
        self.rotation["triggers"]["JMT.LS"] = {"date": DAYS[1], "close": 10.0, "action": "LIQUIDAR"}
        self.rotation["history"].append({"date": DAYS[2], "triggers": [], "bought": ["JMT.LS"],
                                         "weight_each": 0.5})
        self.apply_rotation_state()
        second = self.run_entry(DAYS[3])
        entry = {e["ticker"]: e for e in second["data"]["entries"]}["JMT.LS"]
        # Day 2 of the cycle, but the 20% already invested before the sale is not counted.
        self.assertAlmostEqual(entry["tranche_weight"], round(0.2 * entry["target_weight"], 6))
        self.assertFalse(any("fully sold" in w for w in second["warnings"]))


if __name__ == "__main__":
    unittest.main()
