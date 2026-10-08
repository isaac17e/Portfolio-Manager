"""Orchestrator tests. No network. Step scripts are fakes."""

import io
import json
import os
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date, datetime
from pathlib import Path
from unittest import mock
from zoneinfo import ZoneInfo

import run_cycle


BOGOTA = ZoneInfo("America/Bogota")
PORTFOLIO_RUN_TS = "2026-10-05T16:40:12-05:00"

FAKE_STEP = r'''
import json
import os
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo

script = sys.argv[1]
mode = os.environ.get("FAKE_MODE", "ok")
fail_on = os.environ.get("FAKE_FAIL_ON", "")
log_path = os.environ.get("FAKE_LOG")
if log_path:
    with open(log_path, "a", encoding="utf-8") as handle:
        handle.write(script + "\n")

if mode == "stdin":
    incoming = sys.stdin.read()
    if incoming:
        sys.stderr.write("stdin was not closed\n")
        sys.exit(4)

if mode == "sleep":
    time.sleep(5)
    sys.exit(0)

if mode == "fail" or script == fail_on:
    sys.stderr.write(script + " exploded\nmore detail\n")
    sys.exit(3)

if mode == "stale":
    sys.exit(0)

portfolio = json.load(open(os.environ["PORTFOLIO_FILE"], encoding="utf-8"))
source = os.environ["PORTFOLIO_FILE"]
portfolio_run_ts = portfolio.get("run_ts")
if mode == "fallback":
    source = "hardcoded_fallback"
    portfolio_run_ts = None
elif mode == "wrong_source":
    source = "/tmp/not-the-portfolio.json"
elif mode == "wrong_run_ts":
    portfolio_run_ts = "1999-01-01T00:00:00-05:00"

if script == "portfolio_risk_score_leverage":
    data = {
        "target_leverage": 3.5,
        "risk_score": 35.0,
        "excluded": [{"ticker": "RY.TO", "reason": "no US-listed options"}],
    }
elif script == "portfolio_vix":
    data = {"vix_portfolio": 18.2, "excluded": []}
elif script == "entry_signal_tool":
    data = {
        "entries": [
            {"order": 1, "ticker": "GLD", "action": "BUY", "target_weight": 0.6}
        ],
        "excluded": [],
    }
elif script == "active_management":
    data = {
        "regime": "normal",
        "rebalances": [{"ticker": "GLD", "action": "HOLD"}],
        "excluded": [],
    }
elif script == "portfolio_gex_field":
    data = {"n_holdings": 2, "macro_y": 0.4, "excluded": []}
elif script == "fundamental_analysis":
    data = {"n_tickers": 2, "excluded": []}
else:
    data = {"excluded": []}

data["headless_env"] = os.environ.get("HEADLESS")
run_ts = datetime.now(ZoneInfo("America/Bogota")).replace(microsecond=0).isoformat()
payload = {
    "schema_version": 1,
    "script": script,
    "run_ts": run_ts,
    "portfolio_source": source,
    "portfolio_run_ts": portfolio_run_ts,
    "portfolio_optimizer": portfolio.get("optimizer"),
    "weights_used": portfolio.get("weights") or {},
    "data": data,
    "warnings": ["watch " + script],
}
out_dir = os.environ["SIGNALS_OUT_DIR"]
os.makedirs(out_dir, exist_ok=True)
path = os.path.join(out_dir, script + ".json")
with open(path, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, indent=2)
    handle.write("\n")
'''


def _portfolio(**overrides):
    payload = {
        "schema_version": 1,
        "source_repo": "AM-PM-Architecture",
        "optimizer": "black_litterman",
        "risk_profile": "agresivo",
        "run_ts": PORTFOLIO_RUN_TS,
        "horizon_days": 61,
        "horizon_end": "2026-12-05",
        "tickers": ["AAA", "BBB"],
        "weights": {"AAA": 0.6, "BBB": 0.4},
        "params": {},
        "metrics": {"expected_return": 0.1, "volatility": 0.2},
    }
    payload.update(overrides)
    return payload


class CycleTestCase(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.tmp = self._td.name
        self.fake = os.path.join(self.tmp, "fake_step.py")
        Path(self.fake).write_text(FAKE_STEP, encoding="utf-8")
        self.commands = []

    def tearDown(self):
        self._td.cleanup()

    def _build(self, script):
        self.commands.append(script)
        return [sys.executable, self.fake, script]

    def invoke(self, *args, env=None, payload=None, timeout="30", write_portfolio=True):
        portfolio_path = os.path.join(self.tmp, "portfolio.json")
        if write_portfolio:
            body = _portfolio() if payload is None else payload
            Path(portfolio_path).write_text(json.dumps(body), encoding="utf-8")
        signals = os.path.join(self.tmp, "signals")
        summary = os.path.join(self.tmp, "summary")
        state = os.path.join(self.tmp, "state", "weekly_last_run.json")
        log_path = os.path.join(self.tmp, "steps.log")
        cmd = [
            "--portfolio", portfolio_path,
            "--signals-dir", signals,
            "--summary-dir", summary,
            "--weekly-state", state,
            "--timeout", timeout,
            *args,
        ]
        overlay = {"FAKE_LOG": log_path}
        if env:
            overlay.update(env)
        stdout = io.StringIO()
        stderr = io.StringIO()
        self.commands = []
        with mock.patch.dict(os.environ, overlay, clear=False):
            with mock.patch("run_cycle.build_command", side_effect=self._build):
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    code = run_cycle.main(cmd)
        return {
            "code": code,
            "stdout": stdout.getvalue(),
            "stderr": stderr.getvalue(),
            "portfolio": os.path.abspath(portfolio_path),
            "signals": os.path.abspath(signals),
            "summary": os.path.abspath(summary),
            "state": os.path.abspath(state),
            "log": log_path,
        }

    def summary(self, result):
        path = os.path.join(result["summary"], "cycle_summary_latest.json")
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)

    def assert_summary_files(self, result):
        names = os.listdir(result["summary"])
        self.assertIn("cycle_summary_latest.json", names)
        self.assertIn("cycle_summary_latest.txt", names)
        self.assertTrue(any(
            name.startswith("cycle_summary_") and name.endswith(".json")
            and name != "cycle_summary_latest.json"
            for name in names
        ))
        self.assertTrue(any(
            name.startswith("cycle_summary_") and name.endswith(".txt")
            and name != "cycle_summary_latest.txt"
            for name in names
        ))
        self.assertFalse(any(name.endswith(".tmp") for name in names))


class SuccessPathTests(CycleTestCase):
    def test_daily_success_writes_summary_scalars_and_entries(self):
        result = self.invoke()
        self.assertEqual(result["code"], 0, result["stderr"])
        self.assertEqual(
            self.commands,
            [
                "fundamental_analysis",
                "portfolio_risk_score_leverage",
                "portfolio_gex_field",
                "portfolio_vix",
                "entry_signal_tool",
            ],
        )
        body = self.summary(result)
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["mode"], "daily")
        self.assertEqual(body["portfolio"]["path"], result["portfolio"])
        self.assertEqual(body["portfolio"]["optimizer"], "black_litterman")
        self.assertEqual(body["portfolio"]["run_ts"], PORTFOLIO_RUN_TS)
        self.assertEqual(body["portfolio"]["horizon_end"], "2026-12-05")
        self.assertIsNone(body["failing_step"])
        self.assertEqual([step["status"] for step in body["steps"]], ["success"] * 5)
        self.assertTrue(all(step["duration_seconds"] is not None for step in body["steps"]))
        self.assertTrue(all(step["output_file"] for step in body["steps"]))
        self.assertEqual(body["scalars"]["target_leverage"], 3.5)
        self.assertEqual(body["scalars"]["risk_score"], 35.0)
        self.assertEqual(body["scalars"]["vix_portfolio"], 18.2)
        self.assertEqual(body["scalars"]["n_entries"], 1)
        self.assertEqual(body["scalars"]["entries"][0]["ticker"], "GLD")
        self.assertEqual(body["scalars"]["entries"][0]["action"], "BUY")
        self.assertEqual(
            body["excluded"]["portfolio_risk_score_leverage"],
            [{"ticker": "RY.TO", "reason": "no US-listed options"}],
        )
        self.assertIn("watch portfolio_vix", body["signal_warnings"]["portfolio_vix"])
        self.assertIn("watch entry_signal_tool", body["signal_warnings"]["entry_signal_tool"])
        run_at = datetime.fromisoformat(body["run_ts"])
        self.assertEqual(run_at.utcoffset(), datetime.now(BOGOTA).utcoffset())
        self.assert_summary_files(result)
        text = Path(os.path.join(result["summary"], "cycle_summary_latest.txt")).read_text(encoding="utf-8")
        self.assertIn("status: success", text)
        self.assertIn("target_leverage: 3.5", text)
        self.assertIn("GLD", text)
        self.assertIn("RY.TO", text)
        gex = json.loads(Path(os.path.join(result["signals"], "portfolio_gex_field.json")).read_text(encoding="utf-8"))
        entry = json.loads(Path(os.path.join(result["signals"], "entry_signal_tool.json")).read_text(encoding="utf-8"))
        self.assertEqual(gex["data"]["headless_env"], "1")
        self.assertIsNone(entry["data"]["headless_env"])
        self.assertFalse(os.path.exists(result["state"]))

    def test_steps_subset_follows_canonical_order(self):
        result = self.invoke("--steps", "entry_signal_tool,portfolio_vix")
        self.assertEqual(result["code"], 0, result["stderr"])
        self.assertEqual(self.commands, ["portfolio_vix", "entry_signal_tool"])
        body = self.summary(result)
        self.assertEqual([step["script"] for step in body["steps"]], ["portfolio_vix", "entry_signal_tool"])


class FailureTests(CycleTestCase):
    def test_failing_step_stops_the_cycle_and_writes_summary(self):
        result = self.invoke(env={"FAKE_FAIL_ON": "portfolio_risk_score_leverage"})
        self.assertEqual(result["code"], 1)
        self.assertEqual(
            self.commands,
            ["fundamental_analysis", "portfolio_risk_score_leverage"],
        )
        self.assertIn("portfolio_risk_score_leverage", result["stderr"])
        self.assertIn("exit code 3", result["stderr"])
        self.assertIn("exploded", result["stderr"])
        body = self.summary(result)
        self.assertEqual(body["status"], "failed")
        self.assertEqual(body["failing_step"], "portfolio_risk_score_leverage")
        statuses = {step["script"]: step["status"] for step in body["steps"]}
        self.assertEqual(statuses["fundamental_analysis"], "success")
        self.assertEqual(statuses["portfolio_risk_score_leverage"], "failed")
        self.assertEqual(statuses["portfolio_gex_field"], "not_run")
        self.assertEqual(statuses["entry_signal_tool"], "not_run")
        self.assertFalse(os.path.exists(os.path.join(result["signals"], "portfolio_gex_field.json")))
        self.assertIn("exploded", body["error"])
        self.assert_summary_files(result)
        text = Path(os.path.join(result["summary"], "cycle_summary_latest.txt")).read_text(encoding="utf-8")
        self.assertIn("status: failed", text)
        self.assertIn("portfolio_risk_score_leverage", text)

    def test_stale_signal_file_is_rejected(self):
        result_dir = os.path.join(self.tmp, "signals")
        os.makedirs(result_dir)
        portfolio_path = os.path.abspath(os.path.join(self.tmp, "portfolio.json"))
        stale = {
            "schema_version": 1,
            "script": "fundamental_analysis",
            "run_ts": "2020-01-01T00:00:00-05:00",
            "portfolio_source": portfolio_path,
            "portfolio_run_ts": PORTFOLIO_RUN_TS,
            "data": {},
        }
        path = os.path.join(result_dir, "fundamental_analysis.json")
        Path(path).write_text(json.dumps(stale), encoding="utf-8")
        old = time.time() - 100_000
        os.utime(path, (old, old))
        result = self.invoke("--steps", "fundamental_analysis,portfolio_vix", env={"FAKE_MODE": "stale"})
        self.assertEqual(result["code"], 1)
        self.assertEqual(self.commands, ["fundamental_analysis"])
        body = self.summary(result)
        self.assertEqual(body["status"], "failed")
        self.assertEqual(body["failing_step"], "fundamental_analysis")
        self.assertIn("stale", body["error"])
        self.assertEqual(body["steps"][1]["status"], "not_run")

    def test_wrong_portfolio_source_is_rejected(self):
        result = self.invoke("--steps", "fundamental_analysis", env={"FAKE_MODE": "wrong_source"})
        self.assertEqual(result["code"], 1)
        body = self.summary(result)
        self.assertEqual(body["failing_step"], "fundamental_analysis")
        self.assertIn("portfolio_source", body["error"])
        self.assertNotIn("hardcoded_fallback", body["error"])
        self.assertIn("/tmp/not-the-portfolio.json", body["error"])

    def test_wrong_portfolio_run_ts_is_rejected(self):
        result = self.invoke("--steps", "fundamental_analysis", env={"FAKE_MODE": "wrong_run_ts"})
        self.assertEqual(result["code"], 1)
        body = self.summary(result)
        self.assertIn("portfolio_run_ts", body["error"])
        self.assertIn("1999-01-01T00:00:00-05:00", body["error"])
        self.assertIn(PORTFOLIO_RUN_TS, body["error"])

    def test_old_run_ts_is_stale_even_when_the_file_mtime_is_new(self):
        path = os.path.join(self.tmp, "fundamental_analysis.json")
        step_start = run_cycle._now_bogota()
        payload = {
            "schema_version": 1,
            "script": "fundamental_analysis",
            "run_ts": "2020-01-01T00:00:00-05:00",
            "portfolio_source": "/p.json",
            "portfolio_run_ts": PORTFOLIO_RUN_TS,
            "data": {},
        }
        Path(path).write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaises(run_cycle.SignalError) as caught:
            run_cycle.verify_signal(
                path, "fundamental_analysis", "/p.json", PORTFOLIO_RUN_TS, step_start,
            )
        message = str(caught.exception)
        self.assertIn("stale", message)
        self.assertIn("run_ts", message)

    def test_hardcoded_fallback_is_rejected(self):
        result = self.invoke("--steps", "fundamental_analysis", env={"FAKE_MODE": "fallback"})
        self.assertEqual(result["code"], 1)
        body = self.summary(result)
        self.assertIn("hardcoded_fallback", body["error"])
        self.assertEqual(body["status"], "failed")

    def test_timeout_stops_the_step(self):
        result = self.invoke(
            "--steps", "fundamental_analysis,portfolio_vix",
            env={"FAKE_MODE": "sleep"},
            timeout="1",
        )
        self.assertEqual(result["code"], 1)
        self.assertEqual(self.commands, ["fundamental_analysis"])
        body = self.summary(result)
        self.assertEqual(body["failing_step"], "fundamental_analysis")
        self.assertIn("timed out", body["error"])
        self.assertEqual(body["steps"][1]["status"], "not_run")

    def test_stdin_is_devnull(self):
        result = self.invoke("--steps", "fundamental_analysis", env={"FAKE_MODE": "stdin"})
        self.assertEqual(result["code"], 0, result["stderr"])
        self.assertNotIn("stdin was not closed", result["stderr"])


class WeeklyTests(CycleTestCase):
    def test_weekly_runs_only_active_management(self):
        result = self.invoke("--weekly", "--date", "2026-10-12")
        self.assertEqual(result["code"], 0, result["stderr"])
        self.assertEqual(self.commands, ["active_management"])
        body = self.summary(result)
        self.assertEqual(body["mode"], "weekly")
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["as_of_date"], "2026-10-12")
        self.assertEqual(body["scalars"]["regime"], "normal")
        self.assertEqual(body["scalars"]["n_rebalances"], 1)
        state = json.loads(Path(result["state"]).read_text(encoding="utf-8"))
        self.assertEqual(state["last_run_date"], "2026-10-12")
        iso = date(2026, 10, 12).isocalendar()
        self.assertEqual(state["iso_year"], iso[0])
        self.assertEqual(state["iso_week"], iso[1])
        self.assertEqual(state["portfolio_run_ts"], PORTFOLIO_RUN_TS)

    def test_weekly_skipped_after_horizon_end(self):
        payload = _portfolio(horizon_end="2026-10-01")
        result = self.invoke("--weekly", "--date", "2026-10-12", "--force", payload=payload)
        self.assertEqual(result["code"], 0, result["stderr"])
        self.assertEqual(self.commands, [])
        body = self.summary(result)
        self.assertEqual(body["status"], "skipped_after_horizon")
        self.assertIn("skipped_after_horizon", result["stdout"])
        self.assertIn("2026-10-01", result["stdout"])
        self.assertFalse(os.path.exists(result["state"]))
        self.assertEqual(body["steps"][0]["script"], "active_management")
        self.assertEqual(body["steps"][0]["status"], "not_run")

    def test_null_horizon_end_runs_with_a_warning(self):
        payload = _portfolio()
        payload["horizon_end"] = None
        result = self.invoke("--weekly", "--date", "2026-10-12", payload=payload)
        self.assertEqual(result["code"], 0, result["stderr"])
        self.assertEqual(self.commands, ["active_management"])
        body = self.summary(result)
        self.assertEqual(body["status"], "success")
        self.assertIsNone(body["portfolio"]["horizon_end"])
        self.assertTrue(any("horizon_end is null" in warning for warning in body["warnings"]))

    def test_labor_day_monday_is_not_due_and_tuesday_is(self):
        monday = self.invoke("--weekly", "--date", "2026-09-07")
        self.assertEqual(monday["code"], 0, monday["stderr"])
        self.assertEqual(self.commands, [])
        body = self.summary(monday)
        self.assertEqual(body["status"], "not_due")
        self.assertEqual(body["not_due_reason"], "non_trading_day")
        self.assertIn("not_due: non_trading_day", monday["stdout"])
        self.assertFalse(os.path.exists(monday["state"]))

        tuesday = self.invoke("--weekly", "--date", "2026-09-08")
        self.assertEqual(tuesday["code"], 0, tuesday["stderr"])
        self.assertEqual(self.commands, ["active_management"])
        self.assertEqual(self.summary(tuesday)["status"], "success")

    def test_memorial_day_is_due_on_tuesday(self):
        monday = self.invoke("--weekly", "--date", "2026-05-25")
        self.assertEqual(self.summary(monday)["not_due_reason"], "non_trading_day")
        self.assertEqual(self.commands, [])
        tuesday = self.invoke("--weekly", "--date", "2026-05-26")
        self.assertEqual(tuesday["code"], 0, tuesday["stderr"])
        self.assertEqual(self.commands, ["active_management"])

    def test_columbus_day_week_is_due_monday_not_tuesday(self):
        monday = self.invoke("--weekly", "--date", "2026-10-12")
        self.assertEqual(monday["code"], 0, monday["stderr"])
        self.assertEqual(self.commands, ["active_management"])
        tuesday = self.invoke("--weekly", "--date", "2026-10-13")
        self.assertEqual(tuesday["code"], 0, tuesday["stderr"])
        self.assertEqual(self.commands, [])
        body = self.summary(tuesday)
        self.assertEqual(body["status"], "not_due")
        self.assertEqual(body["not_due_reason"], "not_first_trading_day_of_week")

    def test_already_ran_this_week_is_not_due(self):
        first = self.invoke("--weekly", "--date", "2026-10-12")
        self.assertEqual(first["code"], 0, first["stderr"])
        second = self.invoke("--weekly", "--date", "2026-10-12")
        self.assertEqual(second["code"], 0, second["stderr"])
        self.assertEqual(self.commands, [])
        body = self.summary(second)
        self.assertEqual(body["status"], "not_due")
        self.assertEqual(body["not_due_reason"], "already_ran_this_week")

    def test_weekend_is_not_due(self):
        saturday = self.invoke("--weekly", "--date", "2026-10-10")
        self.assertEqual(self.summary(saturday)["not_due_reason"], "non_trading_day")
        sunday = self.invoke("--weekly", "--date", "2026-10-11")
        self.assertEqual(self.summary(sunday)["not_due_reason"], "non_trading_day")
        self.assertEqual(self.commands, [])

    def test_force_on_holiday_marks_the_week_and_tuesday_is_not_due(self):
        forced = self.invoke("--weekly", "--date", "2026-09-07", "--force")
        self.assertEqual(forced["code"], 0, forced["stderr"])
        self.assertEqual(self.commands, ["active_management"])
        body = self.summary(forced)
        self.assertTrue(any("bypassed" in warning for warning in body["warnings"]))
        tuesday = self.invoke("--weekly", "--date", "2026-09-08")
        self.assertEqual(self.summary(tuesday)["not_due_reason"], "already_ran_this_week")
        self.assertEqual(self.commands, [])

    def test_force_does_not_bypass_horizon(self):
        payload = _portfolio(horizon_end="2026-09-01")
        result = self.invoke("--weekly", "--date", "2026-09-08", "--force", payload=payload)
        self.assertEqual(result["code"], 0)
        self.assertEqual(self.summary(result)["status"], "skipped_after_horizon")
        self.assertEqual(self.commands, [])

    def test_failed_weekly_does_not_record_success(self):
        result = self.invoke("--weekly", "--date", "2026-10-12", env={"FAKE_MODE": "fail"})
        self.assertEqual(result["code"], 1)
        self.assertEqual(self.summary(result)["failing_step"], "active_management")
        self.assertFalse(os.path.exists(result["state"]))
        retry = self.invoke("--weekly", "--date", "2026-10-12")
        self.assertEqual(retry["code"], 0, retry["stderr"])
        self.assertEqual(self.commands, ["active_management"])

    def test_missing_calendar_is_a_clear_error(self):
        with mock.patch(
            "run_cycle.nyse_session_dates",
            side_effect=run_cycle.CalendarUnavailable(
                "NYSE calendar library is not installed. "
                "Install pandas_market_calendars or exchange_calendars "
                "(pip install -r requirements.txt)."
            ),
        ):
            result = self.invoke("--weekly", "--date", "2026-10-12")
        self.assertEqual(result["code"], 1)
        self.assertIn("NYSE calendar library is not installed", result["stderr"])
        self.assertIn("pandas_market_calendars", result["stderr"])
        body = self.summary(result)
        self.assertEqual(body["status"], "failed")
        self.assertEqual(self.commands, [])

    def test_real_calendar_is_installed(self):
        sessions = run_cycle.nyse_session_dates(date(2026, 9, 7), date(2026, 9, 11))
        self.assertEqual(sessions[0], date(2026, 9, 8))
        self.assertNotIn(date(2026, 9, 7), sessions)
        columbus = run_cycle.nyse_session_dates(date(2026, 10, 12), date(2026, 10, 12))
        self.assertEqual(columbus, [date(2026, 10, 12)])


class PortfolioAndCliTests(CycleTestCase):
    def test_invalid_portfolio_file(self):
        cases = [
            ("missing", None, False),
            ("schema", _portfolio(schema_version=2), True),
            ("weights", _portfolio(weights={"AAA": 0.6, "BBB": 0.3}, tickers=["AAA", "BBB"]), True),
            ("tickers", _portfolio(tickers=["AAA", "CCC"]), True),
            ("run_ts", _portfolio(run_ts=""), True),
            ("optimizer", _portfolio(optimizer=""), True),
            ("json", None, True),
        ]
        for name, payload, write in cases:
            with self.subTest(name=name):
                if name == "json":
                    path = os.path.join(self.tmp, "portfolio.json")
                    Path(path).write_text("{not json", encoding="utf-8")
                    result = self.invoke(write_portfolio=False)
                elif not write:
                    result = self.invoke(write_portfolio=False)
                else:
                    result = self.invoke(payload=payload)
                self.assertEqual(result["code"], 1, result["stderr"])
                self.assertEqual(self.commands, [])
                self.assertIn("invalid portfolio", result["stderr"])
                body = self.summary(result)
                self.assertEqual(body["status"], "failed")
                self.assertIsNone(body["failing_step"])
                self.assertIn("invalid portfolio", body["error"])

    def test_dry_run_prints_the_plan_and_writes_nothing(self):
        result = self.invoke("--dry-run")
        self.assertEqual(result["code"], 0, result["stderr"])
        self.assertIn("dry-run mode=daily", result["stdout"])
        for script in run_cycle.DAILY_STEPS:
            self.assertIn(script, result["stdout"])
        self.assertNotIn("active_management", result["stdout"])
        self.assertIn("HEADLESS=1", result["stdout"])
        self.assertFalse(os.path.exists(os.path.join(result["summary"], "cycle_summary_latest.json")))
        self.assertFalse(os.path.isdir(result["signals"]))

        portfolio = os.path.join(self.tmp, "dry_portfolio.json")
        Path(portfolio).write_text(json.dumps(_portfolio()), encoding="utf-8")
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = run_cycle.main([
                "--dry-run",
                "--portfolio", portfolio,
                "--summary-dir", os.path.join(self.tmp, "dry_summary"),
                "--signals-dir", os.path.join(self.tmp, "dry_signals"),
            ])
        self.assertEqual(code, 0)
        plan = stdout.getvalue()
        self.assertIn("--once", plan)
        self.assertIn("--no-show", plan)
        self.assertIn("HEADLESS=1", plan)
        self.assertFalse(os.path.isdir(os.path.join(self.tmp, "dry_signals")))

    def test_weekly_dry_run_not_due_writes_nothing(self):
        result = self.invoke("--weekly", "--dry-run", "--date", "2026-10-11")
        self.assertEqual(result["code"], 0)
        self.assertIn("not_due: non_trading_day", result["stdout"])
        self.assertEqual(self.commands, [])
        self.assertFalse(os.path.exists(os.path.join(result["summary"], "cycle_summary_latest.json")))

    def test_unknown_step_exits_2(self):
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            code = run_cycle.main(["--steps", "not_a_script", "--portfolio", os.path.join(self.tmp, "p.json")])
        self.assertEqual(code, 2)
        self.assertIn("unknown step", stderr.getvalue())

    def test_bad_date_exits_2(self):
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            try:
                code = run_cycle.main(["--date", "10/12/2026"])
            except SystemExit as exc:
                code = exc.code
        self.assertEqual(code, 2)

    def test_real_commands_are_noninteractive(self):
        for script in run_cycle.DAILY_STEPS + run_cycle.WEEKLY_STEPS:
            command = run_cycle.build_command(script)
            self.assertEqual(command[0], sys.executable)
            self.assertTrue(os.path.isfile(command[1]), command[1])
            self.assertTrue(command[1].endswith(script + ".py"))
        gex = run_cycle.build_command("portfolio_gex_field")
        self.assertIn("--once", gex)
        vix = run_cycle.build_command("portfolio_vix")
        self.assertIn("--no-show", vix)
        entry = run_cycle.build_command("entry_signal_tool")
        self.assertEqual(len(entry), 2)
        with mock.patch.dict(os.environ, {"HEADLESS": "0", "ENTRY_CYCLE_DAY": "2", "ENTRY_INVESTED_PCT": "40"}):
            gex_env = run_cycle.step_environment("/p.json", "/signals", "portfolio_gex_field")
            entry_env = run_cycle.step_environment("/p.json", "/signals", "entry_signal_tool")
        self.assertEqual(gex_env["HEADLESS"], "1")
        self.assertEqual(gex_env["PORTFOLIO_FILE"], "/p.json")
        self.assertEqual(gex_env["SIGNALS_OUT_DIR"], "/signals")
        self.assertEqual(gex_env["ENTRY_CYCLE_DAY"], "2")
        self.assertEqual(entry_env["HEADLESS"], "0")
        self.assertEqual(entry_env["ENTRY_INVESTED_PCT"], "40")
        self.assertEqual(entry_env["ENTRY_CYCLE_DAY"], "2")


if __name__ == "__main__":
    unittest.main()
