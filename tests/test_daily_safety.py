"""No-network tests for the same-day entry tranche lock and RISK_FREE_RATE.

entry_signal_tool runs end to end on one "tier none" ticker (staggered entry,
no network), with state, signals, fills and history in a temp directory.
"""

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path
from unittest import mock

import entry_signal_tool as est
import pipeline_io
import run_cycle

TICKER = "EDP.LS"
META = {
    "weights": {TICKER: 1.0},
    "portfolio_source": "/pipeline/portfolio/portfolio_latest.json",
    "portfolio_run_ts": "2026-10-05T16:40:12-05:00",
    "portfolio_optimizer": "black_litterman",
}
FILLS_NAME = "fills_black_litterman_20261005T164012.json"
DAY1, DAY2 = "2026-10-07", "2026-10-08"

_ENTRY_ENV = ("ENTRY_CYCLE_DAY", "ENTRY_INVESTED_PCT", "ENTRY_FORCE_NEW_TRANCHE",
              "ENTRY_STATE_FILE", "PIPELINE_DIR", "CYCLE_DATE", "RISK_FREE_RATE")


class EntryTrancheLockTests(unittest.TestCase):
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
        for name, value in (
            ("_PORTFOLIO_META", META),
            ("TICKERS", [TICKER]),
            ("PESOS_OBJETIVO", {TICKER: 0.10}),
            ("HIST_PATH", str(self.root / "history.csv")),
            ("LEGACY_STATE_PATH", str(self.root / "entry_state.json")),
            ("graficar_resumen", lambda resumen: None),
        ):
            patch = mock.patch.object(est, name, value)
            patch.start()
            self.addCleanup(patch.stop)

    def run_entry(self, day, *argv, **env):
        overlay = {"CYCLE_DATE": day, **env}
        with mock.patch.dict(os.environ, overlay):
            with redirect_stdout(io.StringIO()):
                est.main(list(argv))
        return self.signal()

    def signal(self):
        return json.loads((self.signals / "entry_signal_tool.json").read_text(encoding="utf-8"))

    def state(self):
        path = pipeline_io.entry_state_path(META)
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def write_fills(self, signal_run_ts):
        (self.executions / FILLS_NAME).write_text(json.dumps({
            "schema_version": 1, "signal_run_ts": signal_run_ts,
            "executed_ts": "2026-10-07T15:00:00-05:00",
            "fills": [{"ticker": TICKER, "action": "BUY", "filled_weight": 0.01, "status": "filled"}],
        }), encoding="utf-8")

    def test_first_run_prepares_a_tranche_and_records_the_date(self):
        payload = self.run_entry(DAY1)
        data = payload["data"]
        self.assertEqual(data["signal"], "new_tranche")
        self.assertEqual(data["cycle_day"], 1)
        self.assertEqual(len(data["entries"]), 1)
        state = self.state()
        self.assertEqual(state["last_tranche_date"], DAY1)
        self.assertEqual(state["pending_signal_run_ts"], payload["run_ts"])
        self.assertEqual(state["last_tranche"]["signal_run_ts"], payload["run_ts"])
        self.assertEqual(state["last_tranche"]["entries"], data["entries"])

    def test_second_run_same_day_with_pending_tranche_is_locked(self):
        first = self.run_entry(DAY1)
        before = self.state()
        second = self.run_entry(DAY1)

        data = second["data"]
        self.assertEqual(data["signal"], "already_prepared_today")
        self.assertEqual(data["tranche_status"], "pending")
        self.assertEqual(data["prepared_date"], DAY1)
        self.assertEqual(data["existing_signal_run_ts"], first["run_ts"])
        self.assertEqual(data["entries"], [])
        self.assertEqual(data["existing_tranche"]["entries"], first["data"]["entries"])
        self.assertEqual(data["cycle_day"], 1)
        self.assertTrue(any("already_prepared_today" in w for w in second["warnings"]))
        # Still a valid envelope for run_cycle.
        self.assertEqual(second["portfolio_source"], META["portfolio_source"])
        self.assertEqual(second["portfolio_run_ts"], META["portfolio_run_ts"])
        # The pending tranche keeps its signal_run_ts, so its fills still apply.
        self.assertEqual(self.state(), before)

    def test_second_run_same_day_after_fills_does_not_open_day_two(self):
        first = self.run_entry(DAY1)
        self.write_fills(first["run_ts"])
        second = self.run_entry(DAY1)

        data = second["data"]
        self.assertEqual(data["signal"], "already_prepared_today")
        self.assertEqual(data["tranche_status"], "executed")
        self.assertEqual(data["entries"], [])
        state = self.state()
        # The fills were applied...
        self.assertAlmostEqual(state["activos"][TICKER]["pct_ya_invertido"], 0.2)
        self.assertEqual(state["dia_ciclo"], 1)
        self.assertIsNone(state["pending_signal_run_ts"])
        # ...but no day-2 tranche was prepared.
        self.assertEqual(state["last_tranche_date"], DAY1)
        self.assertEqual(state["last_tranche"]["signal_run_ts"], first["run_ts"])

    def test_next_session_day_prepares_the_next_tranche(self):
        first = self.run_entry(DAY1)
        self.write_fills(first["run_ts"])
        self.run_entry(DAY1)
        third = self.run_entry(DAY2)

        self.assertEqual(third["data"]["signal"], "new_tranche")
        self.assertEqual(third["data"]["cycle_day"], 2)
        self.assertEqual(self.state()["last_tranche_date"], DAY2)

    def test_force_new_tranche_flag_and_env_bypass_the_lock(self):
        first = self.run_entry(DAY1)
        self.write_fills(first["run_ts"])
        forced = self.run_entry(DAY1, "--force-new-tranche")
        self.assertEqual(forced["data"]["signal"], "new_tranche")
        self.assertEqual(forced["data"]["cycle_day"], 2)

        again = self.run_entry(DAY1, ENTRY_FORCE_NEW_TRANCHE="1")
        self.assertEqual(again["data"]["signal"], "new_tranche")

    def test_explicit_cycle_day_bypasses_the_lock(self):
        self.run_entry(DAY1)
        by_flag = self.run_entry(DAY1, "--cycle-day", "3")
        self.assertEqual(by_flag["data"]["signal"], "new_tranche")
        self.assertEqual(by_flag["data"]["cycle_day"], 3)
        by_env = self.run_entry(DAY1, ENTRY_CYCLE_DAY="2")
        self.assertEqual(by_env["data"]["signal"], "new_tranche")
        self.assertEqual(by_env["data"]["cycle_day"], 2)

    def test_invalid_or_blank_cycle_day_does_not_bypass(self):
        self.run_entry(DAY1)
        for value in ("abc", "9", ""):
            with self.subTest(value=value):
                payload = self.run_entry(DAY1, ENTRY_CYCLE_DAY=value)
                self.assertEqual(payload["data"]["signal"], "already_prepared_today")

    def test_run_without_data_does_not_lock_the_day(self):
        with mock.patch.object(est, "calcular_fila_instrumento", return_value=None):
            payload = self.run_entry(DAY1)
        self.assertEqual(payload["data"]["entries"], [])
        self.assertIsNone(self.state().get("last_tranche_date"))
        retry = self.run_entry(DAY1)
        self.assertEqual(retry["data"]["signal"], "new_tranche")
        self.assertEqual(len(retry["data"]["entries"]), 1)

    def test_state_without_a_recorded_date_is_not_locked(self):
        first = self.run_entry(DAY1)
        state = self.state()
        for key in ("last_tranche_date", "last_tranche"):
            state.pop(key)
        Path(pipeline_io.entry_state_path(META)).write_text(json.dumps(state), encoding="utf-8")
        self.write_fills(first["run_ts"])
        again = self.run_entry(DAY1)
        self.assertEqual(again["data"]["signal"], "new_tranche")

    def test_locked_signal_passes_run_cycle_validation(self):
        self.run_entry(DAY1)
        step_start = run_cycle._now_bogota()
        self.run_entry(DAY1)
        payload = run_cycle.verify_signal(
            str(self.signals / "entry_signal_tool.json"), "entry_signal_tool",
            META["portfolio_source"], META["portfolio_run_ts"], step_start,
        )
        scalars, warnings, excluded = {}, {}, {}
        run_cycle._absorb_signal("entry_signal_tool", payload, scalars, warnings, excluded)
        self.assertEqual(scalars["entry_signal"], "already_prepared_today")
        self.assertEqual(scalars["entry_tranche_status"], "pending")
        self.assertEqual(scalars["n_entries"], 0)

    def test_locked_run_does_not_touch_history(self):
        self.run_entry(DAY1)
        history = Path(est.HIST_PATH).read_text(encoding="utf-8")
        self.run_entry(DAY1)
        self.assertEqual(Path(est.HIST_PATH).read_text(encoding="utf-8"), history)


class TrancheLockHelperTests(unittest.TestCase):
    def test_tranche_lock_statuses(self):
        staged = pipeline_io.stage_pending_entry(
            {}, "ts-1", 1, 1, {"GLD": 0.1}, prepared_date="2026-10-07",
            tranche={"entries": [{"ticker": "GLD"}], "waiting": [], "cycle_day": 1, "cycle": 1},
        )
        pending = pipeline_io.tranche_lock(staged, date(2026, 10, 7))
        self.assertEqual(pending["status"], "pending")
        self.assertEqual(pending["signal_run_ts"], "ts-1")
        self.assertEqual(pending["tranche"]["entries"], [{"ticker": "GLD"}])
        fills = {"schema_version": 1, "signal_run_ts": "ts-1", "fills": []}
        executed, applied = pipeline_io.apply_entry_fills(staged, fills, today="2026-10-07")
        self.assertTrue(applied)
        self.assertEqual(pipeline_io.tranche_lock(executed, "2026-10-07")["status"], "executed")
        self.assertIsNone(pipeline_io.tranche_lock(executed, "2026-10-08"))
        self.assertIsNone(pipeline_io.tranche_lock({}, "2026-10-07"))
        self.assertIsNone(pipeline_io.tranche_lock(None, "2026-10-07"))

    def test_stage_without_date_keeps_the_previous_lock(self):
        staged = pipeline_io.stage_pending_entry({}, "ts-1", 1, 1, prepared_date="2026-10-07")
        restaged = pipeline_io.stage_pending_entry(staged, "ts-2", 1, 1)
        self.assertEqual(restaged["last_tranche_date"], "2026-10-07")

    def test_cycle_today(self):
        with mock.patch.dict(os.environ, {"CYCLE_DATE": "2026-09-07"}):
            self.assertEqual(pipeline_io.cycle_today(), date(2026, 9, 7))
        env = {k: v for k, v in os.environ.items() if k != "CYCLE_DATE"}
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(pipeline_io.cycle_today(), pipeline_io._now_bogota().date())
        with mock.patch.dict(os.environ, {"CYCLE_DATE": "07/09/2026"}):
            with self.assertRaisesRegex(ValueError, "CYCLE_DATE"):
                pipeline_io.cycle_today()


class RiskFreeRateTests(unittest.TestCase):
    def test_default_when_unset_or_blank(self):
        self.assertEqual(pipeline_io.resolve_risk_free_rate(0.046, env={}), 0.046)
        self.assertEqual(pipeline_io.resolve_risk_free_rate(0.05, env={"RISK_FREE_RATE": "  "}), 0.05)

    def test_env_overrides_the_default(self):
        self.assertEqual(pipeline_io.resolve_risk_free_rate(0.046, env={"RISK_FREE_RATE": "0.052"}), 0.052)
        self.assertEqual(pipeline_io.resolve_risk_free_rate(0.046, env={"RISK_FREE_RATE": "0"}), 0.0)
        with mock.patch.dict(os.environ, {"RISK_FREE_RATE": "0.031"}):
            self.assertEqual(pipeline_io.resolve_risk_free_rate(0.045), 0.031)

    def test_invalid_values_raise_a_clear_error(self):
        for raw in ("abc", "0.5", "-0.01", "5.2", "nan", "inf"):
            with self.subTest(raw=raw):
                with self.assertRaisesRegex(ValueError, "RISK_FREE_RATE"):
                    pipeline_io.resolve_risk_free_rate(0.046, env={"RISK_FREE_RATE": raw})

    def test_scripts_read_the_env_with_their_old_defaults(self):
        root = Path(__file__).resolve().parent.parent
        expected = {
            "active_management.py": "risk_free_rate           = resolve_risk_free_rate(0.046)",
            "portfolio_risk_score_leverage.py": "risk_free_rate_annual = resolve_risk_free_rate(0.046)",
            "portfolio_gex_field.py": "RISK_FREE_RATE = resolve_risk_free_rate(0.05)",
            "portfolio_vix.py": "RISK_FREE_RATE: float = resolve_risk_free_rate(0.045)",
        }
        for name, line in expected.items():
            with self.subTest(script=name):
                self.assertIn(line, (root / name).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
