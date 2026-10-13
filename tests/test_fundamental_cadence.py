"""fundamental_analysis cadence in run_cycle: first cycle, then every 30 days within the
horizon, otherwise the saved result is reused. No network; step scripts are fakes."""

import json
import os
import unittest
from datetime import date
from pathlib import Path

import pipeline_io
import run_cycle
from fundamental_analysis import EXTRA_TICKERS_ENV, tickers_a_analizar
from tests import test_run_cycle as base

DAY1 = "2026-10-07"      # Wednesday
DAY2 = "2026-10-08"
DAY29 = "2026-11-05"
DAY30 = "2026-11-06"     # DAY1 + 30 calendar days
HOLIDAY = "2026-11-26"   # Thanksgiving

HORIZON_LONG = {"horizon_end": "2027-03-31"}
HORIZON_SHORT = {"horizon_end": "2026-10-30"}


class CadenceCase(base.CycleTestCase):
    def cycle(self, *args, day=DAY1, env=None, **portfolio_overrides):
        payload = base._portfolio(**portfolio_overrides) if portfolio_overrides else None
        return self.invoke(*args, "--date", day, env=env, payload=payload)

    def fundamental(self, result):
        return self.summary(result)["fundamental"]

    def state_file(self, result):
        key = pipeline_io.portfolio_key({
            "portfolio_optimizer": "black_litterman", "portfolio_run_ts": base.PORTFOLIO_RUN_TS,
        })
        return os.path.join(self.tmp, "state", f"fundamental_state_{key}.json")

    def saved(self, result):
        return os.path.join(result["signals"], "fundamental_analysis.json")

    def step_status(self, result, script="fundamental_analysis"):
        return {step["script"]: step["status"] for step in self.summary(result)["steps"]}[script]


class FirstCycleTests(CadenceCase):
    def test_first_cycle_runs_and_reports_status_dates_and_log(self):
        result = self.cycle(**HORIZON_LONG)
        self.assertEqual(result["code"], 0, result["stderr"])
        self.assertEqual(self.commands[0], "fundamental_analysis")
        block = self.fundamental(result)
        self.assertEqual(block["status"], "ran")
        self.assertEqual(block["reason"], "first_cycle")
        self.assertEqual(block["result_date"], DAY1)
        self.assertEqual(block["next_due_date"], "2026-11-06")
        self.assertEqual(block["new_tickers"], [])
        self.assertFalse(block["forced"])
        self.assertEqual(block["result_file"], self.saved(result))
        self.assertIn(
            "[cycle] fundamental: status=ran result_date=2026-10-07 next_due_date=2026-11-06 "
            "reason=first_cycle",
            result["stdout"],
        )
        text = Path(result["summary"], "cycle_summary_latest.txt").read_text(encoding="utf-8")
        self.assertIn("fundamental:\n  status: ran\n  result_date: 2026-10-07\n  next_due_date: 2026-11-06", text)
        state = json.loads(Path(self.state_file(result)).read_text(encoding="utf-8"))
        self.assertEqual(state["last_run_date"], DAY1)
        self.assertEqual(state["portfolio_run_ts"], base.PORTFOLIO_RUN_TS)
        self.assertEqual(state["tickers"], ["AAA", "BBB"])

    def test_horizon_of_a_month_or_less_has_no_next_due_date(self):
        result = self.cycle(**HORIZON_SHORT)
        block = self.fundamental(result)
        self.assertEqual((block["status"], block["next_due_date"]), ("ran", None))
        self.assertIn("next_due_date=None", result["stdout"])
        result = self.cycle(day=DAY30, **HORIZON_SHORT)
        block = self.fundamental(result)
        self.assertEqual((block["status"], block["reason"], block["next_due_date"]),
                         ("reused", "not_due", None))
        self.assertEqual(block["result_date"], DAY1)

    def test_second_portfolio_run_does_not_reuse_the_first_ones_result(self):
        self.cycle(**HORIZON_LONG)
        result = self.cycle(day=DAY2, run_ts="2026-10-08T09:00:00-05:00", **HORIZON_LONG)
        self.assertEqual(self.fundamental(result)["status"], "ran")
        self.assertEqual(self.fundamental(result)["reason"], "first_cycle")


class ReuseTests(CadenceCase):
    def test_other_days_reuse_the_saved_result_untouched(self):
        first = self.cycle(**HORIZON_LONG)
        path = self.saved(first)
        before = Path(path).read_bytes()
        mtime = os.stat(path).st_mtime_ns
        for day in (DAY2, "2026-10-20", DAY29):
            result = self.cycle(day=day, **HORIZON_LONG)
            self.assertEqual(result["code"], 0, result["stderr"])
            self.assertNotIn("fundamental_analysis", self.commands)
            self.assertEqual(self.step_status(result), "reused")
            block = self.fundamental(result)
            self.assertEqual(
                (block["status"], block["reason"], block["result_date"], block["next_due_date"]),
                ("reused", "not_due", DAY1, "2026-11-06"),
            )
            self.assertIn(
                "[cycle] fundamental: status=reused result_date=2026-10-07 "
                "next_due_date=2026-11-06 reason=not_due",
                result["stdout"],
            )
            self.assertEqual(Path(path).read_bytes(), before)
            self.assertEqual(os.stat(path).st_mtime_ns, mtime)
            self.assertEqual(self.summary(result)["scalars"]["n_tickers"], 2)
            self.assertEqual(self.step_status(result, "entry_signal_tool"), "success")
        self.assertEqual(
            json.loads(Path(self.state_file(first)).read_text(encoding="utf-8"))["last_run_date"], DAY1,
        )

    def test_reused_step_record_points_at_the_saved_file(self):
        self.cycle(**HORIZON_LONG)
        result = self.cycle(day=DAY2, **HORIZON_LONG)
        step = self.summary(result)["steps"][0]
        self.assertEqual(step["script"], "fundamental_analysis")
        self.assertEqual((step["status"], step["output_file"], step["result_date"]),
                         ("reused", self.saved(result), DAY1))
        self.assertIsNone(step["exit_code"])

    def test_runs_again_after_30_days_and_restarts_the_clock(self):
        self.cycle(**HORIZON_LONG)
        result = self.cycle(day=DAY30, **HORIZON_LONG)
        self.assertEqual(self.commands[0], "fundamental_analysis")
        block = self.fundamental(result)
        self.assertEqual(
            (block["status"], block["reason"], block["result_date"], block["next_due_date"]),
            ("ran", "due", DAY30, "2026-12-06"),
        )
        result = self.cycle(day="2026-11-09", **HORIZON_LONG)
        self.assertNotIn("fundamental_analysis", self.commands)
        self.assertEqual(self.fundamental(result)["result_date"], DAY30)

    def test_no_second_run_when_the_due_date_is_past_the_horizon(self):
        self.cycle()                       # horizon_end 2026-12-05
        result = self.cycle(day=DAY30)     # due, within the horizon
        self.assertEqual(self.fundamental(result)["status"], "ran")
        self.assertIsNone(self.fundamental(result)["next_due_date"])
        result = self.cycle(day="2026-12-07")
        self.assertNotIn("fundamental_analysis", self.commands)
        self.assertEqual(self.fundamental(result)["status"], "reused")

    def test_missing_saved_result_runs_again(self):
        first = self.cycle(**HORIZON_LONG)
        os.remove(self.saved(first))
        result = self.cycle(day=DAY2, **HORIZON_LONG)
        self.assertEqual(self.commands[0], "fundamental_analysis")
        block = self.fundamental(result)
        self.assertEqual((block["status"], block["reason"], block["result_date"]),
                         ("ran", "saved_result_missing", DAY2))

    def test_failed_run_keeps_no_state_and_is_retried(self):
        result = self.cycle(env={"FAKE_FAIL_ON": "fundamental_analysis"}, **HORIZON_LONG)
        self.assertEqual(result["code"], 1)
        block = self.fundamental(result)
        self.assertEqual((block["status"], block["reason"]), (None, "step_failed"))
        self.assertFalse(os.path.exists(self.state_file(result)))
        result = self.cycle(day=DAY2, **HORIZON_LONG)
        self.assertEqual(self.fundamental(result)["status"], "ran")


class StepsAndForceTests(CadenceCase):
    ROUTINE = "fundamental,gex,vix,rotation"

    def test_steps_flag_keeps_the_gating(self):
        self.cycle(**HORIZON_LONG)
        before = Path(self.saved(self.cycle(day=DAY2, **HORIZON_LONG))).read_bytes()
        result = self.cycle("--steps", self.ROUTINE, day="2026-10-09", **HORIZON_LONG)
        self.assertEqual(result["code"], 0, result["stderr"])
        self.assertEqual(self.commands, ["portfolio_gex_field", "portfolio_vix", "drawdown_rotation"])
        self.assertEqual(self.step_status(result), "reused")
        block = self.fundamental(result)
        self.assertEqual((block["status"], block["reason"], block["result_date"]),
                         ("reused", "not_due", DAY1))
        self.assertFalse(block["forced"])
        self.assertIn("status=reused", result["stdout"])
        self.assertEqual(Path(self.saved(result)).read_bytes(), before)

    def test_steps_flag_runs_the_step_only_when_due(self):
        first = self.cycle("--steps", self.ROUTINE, **HORIZON_LONG)
        self.assertEqual(self.commands[0], "fundamental_analysis")
        self.assertEqual(self.fundamental(first)["reason"], "first_cycle")
        self.cycle("--steps", "fundamental", day=DAY2, **HORIZON_LONG)
        self.assertEqual(self.commands, [])
        self.assertEqual(self.fundamental(self.cycle("--steps", "fundamental", day=DAY29,
                                                     **HORIZON_LONG))["status"], "reused")
        result = self.cycle("--steps", self.ROUTINE, day=DAY30, **HORIZON_LONG)
        self.assertEqual(self.commands[0], "fundamental_analysis")
        block = self.fundamental(result)
        self.assertEqual((block["status"], block["reason"], block["result_date"]), ("ran", "due", DAY30))

    def test_force_fundamental_forces_a_run(self):
        self.cycle(**HORIZON_LONG)
        result = self.cycle("--force-fundamental", day=DAY2, **HORIZON_LONG)
        self.assertEqual(result["code"], 0, result["stderr"])
        self.assertEqual(self.commands[0], "fundamental_analysis")
        block = self.fundamental(result)
        self.assertEqual(
            (block["status"], block["reason"], block["forced"], block["result_date"], block["next_due_date"]),
            ("ran", "forced", True, DAY2, "2026-11-07"),
        )

    def test_force_fundamental_with_steps(self):
        self.cycle(**HORIZON_LONG)
        result = self.cycle("--steps", "fundamental,gex", "--force-fundamental", day=DAY2, **HORIZON_LONG)
        self.assertEqual(self.commands, ["fundamental_analysis", "portfolio_gex_field"])
        self.assertEqual(self.fundamental(result)["reason"], "forced")

    def test_force_fundamental_needs_the_step(self):
        for args in (("--steps", "gex", "--force-fundamental"), ("--weekly", "--force-fundamental")):
            result = self.cycle(*args)
            self.assertEqual(result["code"], 2)
            self.assertIn("--force-fundamental", result["stderr"])
            self.assertEqual(self.commands, [])

    def test_dry_run_prints_the_plan_and_writes_nothing(self):
        first = self.cycle(**HORIZON_LONG)
        state = Path(self.state_file(first)).read_bytes()
        result = self.cycle("--dry-run", day=DAY2, **HORIZON_LONG)
        self.assertEqual(result["code"], 0, result["stderr"])
        self.assertIn("fundamental: status=reused result_date=2026-10-07 next_due_date=2026-11-06", result["stdout"])
        self.assertIn("reuse saved result (not executed)", result["stdout"])
        self.assertEqual(Path(self.state_file(first)).read_bytes(), state)
        plan = self.cycle("--dry-run", "--force-fundamental", day=DAY2, **HORIZON_LONG)
        self.assertIn("fundamental: status=ran result_date=2026-10-08", plan["stdout"])


class RotationTests(CadenceCase):
    def test_new_rotation_ticker_runs_fundamental_after_rotation(self):
        self.cycle(**HORIZON_LONG)
        result = self.cycle(day=DAY2, env={"FAKE_ROTATION_BUY": "NEWCO"}, **HORIZON_LONG)
        self.assertEqual(result["code"], 0, result["stderr"])
        self.assertEqual(
            self.commands,
            ["portfolio_risk_score_leverage", "portfolio_gex_field", "portfolio_vix",
             "drawdown_rotation", "fundamental_analysis", "entry_signal_tool"],
        )
        body = self.summary(result)
        scripts = [(step["script"], step["status"]) for step in body["steps"]]
        self.assertEqual(scripts[0], ("fundamental_analysis", "reused"))
        self.assertEqual(scripts[5], ("fundamental_analysis", "success"))
        extra = body["steps"][5]
        self.assertEqual((extra["trigger"], extra["new_tickers"]), ("new_ticker", ["NEWCO"]))
        block = body["fundamental"]
        self.assertEqual(
            (block["status"], block["reason"], block["new_tickers"], block["result_date"],
             block["next_due_date"]),
            ("ran_for_new_ticker", "new_ticker", ["NEWCO"], DAY2, "2026-11-07"),
        )
        self.assertIn("status=ran_for_new_ticker", result["stdout"])
        self.assertIn("new_tickers=NEWCO", result["stdout"])
        saved = json.loads(Path(self.saved(result)).read_text(encoding="utf-8"))
        self.assertEqual(saved["data"]["extra_tickers_env"], "NEWCO")
        self.assertEqual([h["ticker"] for h in saved["data"]["holdings"]], ["AAA", "BBB", "NEWCO"])
        state = json.loads(Path(self.state_file(result)).read_text(encoding="utf-8"))
        self.assertEqual((state["last_run_date"], state["tickers"]), (DAY2, ["AAA", "BBB", "NEWCO"]))

    def test_rotation_ticker_already_covered_does_not_trigger_a_run(self):
        self.cycle(**HORIZON_LONG)
        result = self.cycle(day=DAY2, env={"FAKE_ROTATION_BUY": "AAA"}, **HORIZON_LONG)
        self.assertNotIn("fundamental_analysis", self.commands)
        self.assertEqual(self.fundamental(result)["status"], "reused")

    def test_a_covered_new_ticker_is_not_run_twice(self):
        self.cycle(**HORIZON_LONG)
        self.cycle(day=DAY2, env={"FAKE_ROTATION_BUY": "NEWCO"}, **HORIZON_LONG)
        result = self.cycle(day="2026-10-09", env={"FAKE_ROTATION_BUY": "NEWCO"}, **HORIZON_LONG)
        self.assertNotIn("fundamental_analysis", self.commands)
        block = self.fundamental(result)
        self.assertEqual((block["status"], block["result_date"]), ("reused", DAY2))

    def test_scheduled_run_keeps_covering_rotation_tickers(self):
        self.cycle(**HORIZON_LONG)
        key = pipeline_io.portfolio_key({
            "portfolio_optimizer": "black_litterman", "portfolio_run_ts": base.PORTFOLIO_RUN_TS,
        })
        meta = {"portfolio_optimizer": "black_litterman", "portfolio_run_ts": base.PORTFOLIO_RUN_TS}
        pipeline_io.save_rotation_state(
            {**pipeline_io.empty_rotation_state(meta), "target_overrides": {"NEWCO": 0.1, "BBB": 0.0}},
            meta, os.path.join(self.tmp, "state", f"rotation_state_{key}.json"),
        )
        result = self.cycle(day=DAY30, **HORIZON_LONG)
        saved = json.loads(Path(self.saved(result)).read_text(encoding="utf-8"))
        self.assertEqual(saved["data"]["extra_tickers_env"], "NEWCO")
        self.assertEqual(self.fundamental(result)["status"], "ran")


class IdleRunTests(CadenceCase):
    def test_not_due_summary_still_states_fundamental(self):
        self.cycle(**HORIZON_LONG)
        result = self.cycle(day=HOLIDAY, **HORIZON_LONG)
        self.assertEqual(self.commands, [])
        body = self.summary(result)
        self.assertEqual(body["status"], "not_due")
        block = body["fundamental"]
        self.assertEqual(
            (block["status"], block["reason"], block["result_date"], block["next_due_date"]),
            ("reused", "cycle_not_due", DAY1, "2026-11-06"),
        )
        self.assertIn("fundamental: status=reused", result["stdout"])

    def test_weekly_summary_reports_the_result_in_force(self):
        self.cycle(**HORIZON_LONG)
        result = self.cycle("--weekly", day="2026-10-12", **HORIZON_LONG)
        self.assertEqual(self.commands, ["active_management"])
        block = self.fundamental(result)
        self.assertEqual((block["status"], block["reason"], block["result_date"]),
                         ("reused", "step_not_selected", DAY1))


class UnitTests(unittest.TestCase):
    def test_next_due(self):
        self.assertEqual(run_cycle.fundamental_next_due(date(2026, 10, 7), None), date(2026, 11, 6))
        self.assertEqual(run_cycle.fundamental_next_due(date(2026, 10, 7), date(2026, 11, 6)), date(2026, 11, 6))
        self.assertIsNone(run_cycle.fundamental_next_due(date(2026, 10, 7), date(2026, 11, 5)))

    def test_rotation_proposed_tickers(self):
        payload = {"data": {
            "selection": {"tickers": ["X", "Y"]},
            "rebalances": [{"ticker": "Y", "action": "BUY"}, {"ticker": "Z", "action": "SELL"},
                           {"ticker": "W", "action": "buy"}],
        }}
        self.assertEqual(run_cycle.rotation_proposed_tickers(payload), ["X", "Y", "W"])
        self.assertEqual(run_cycle.rotation_proposed_tickers({"data": {"selection": None}}), [])
        self.assertEqual(run_cycle.rotation_proposed_tickers({}), [])

    def test_step_environment_passes_extra_tickers_only_to_fundamental(self):
        env = run_cycle.step_environment("/p.json", "/s", "fundamental_analysis", extra_tickers=["A", "B"])
        self.assertEqual(env[run_cycle.FUNDAMENTAL_EXTRA_ENV], "A,B")
        env = run_cycle.step_environment("/p.json", "/s", "portfolio_vix", extra_tickers=["A"])
        self.assertNotIn(run_cycle.FUNDAMENTAL_EXTRA_ENV, env)

    def test_fundamental_script_adds_extra_tickers(self):
        self.assertEqual(pipeline_io.parse_ticker_list(" A, B  A,,C "), ["A", "B", "C"])
        self.assertEqual(tickers_a_analizar(["A", "B"], {EXTRA_TICKERS_ENV: "B,C"}), ["A", "B", "C"])
        self.assertEqual(tickers_a_analizar(["A"], {}), ["A"])


if __name__ == "__main__":
    unittest.main()
