"""Per-portfolio signal folders: two portfolios never overwrite each other's
``*_latest`` outputs. No network; step scripts are fakes."""

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

import pipeline_io
import portfolio_gex_field as gex
import portfolio_vix as vix
import run_cycle
from tests.test_run_cycle import FAKE_STEP, PAST_ENTRY_PHASE

MV = {"optimizer": "minimum_variance", "run_ts": "2026-10-08T11:29:02-05:00"}
QU = {"optimizer": "quadratic_utility", "run_ts": "2026-10-08T12:12:53-05:00"}
MV_KEY = "minimum_variance_20261008T112902"
QU_KEY = "quadratic_utility_20261008T121253"
MONDAY = "2026-10-05"
WEDNESDAY = "2026-10-07"

_LAYOUT_ENV = ("SIGNALS_DIR_EXACT", "SIGNALS_PER_PORTFOLIO", "SIGNALS_OUT_DIR", "FIGURES_DIR",
               "PIPELINE_DIR", "PORTFOLIO_FILE", "WEEKLY_STATE_FILE", "CYCLE_SUMMARY_DIR")


def _portfolio_file(**ident):
    return {
        "schema_version": 1,
        "optimizer": ident["optimizer"],
        "run_ts": ident["run_ts"],
        "horizon_days": 61,
        "horizon_end": "2026-12-05",
        "tickers": ["AAA", "BBB"],
        "weights": {"AAA": 0.6, "BBB": 0.4},
    }


def _meta(ident):
    return {"portfolio_optimizer": ident["optimizer"], "portfolio_run_ts": ident["run_ts"]}


class CleanEnvCase(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.tmp = td.name
        patcher = mock.patch.dict(os.environ, {})
        patcher.start()
        self.addCleanup(patcher.stop)
        for name in _LAYOUT_ENV:
            os.environ.pop(name, None)


class ResolutionTests(CleanEnvCase):
    def test_portfolio_signals_dir_uses_optimizer_and_stamp(self):
        self.assertEqual(pipeline_io.portfolio_signals_dir(_meta(MV), "/base"), f"/base/{MV_KEY}")
        self.assertEqual(pipeline_io.portfolio_signals_dir(_meta(QU), "/base"), f"/base/{QU_KEY}")

    def test_validated_portfolio_file_dict_gives_the_same_folder(self):
        self.assertEqual(
            pipeline_io.portfolio_signals_dir(MV, "/base"),
            pipeline_io.portfolio_signals_dir(_meta(MV), "/base"),
        )

    def test_hardcoded_fallback_folder(self):
        fallback = {"portfolio_source": "hardcoded_fallback", "portfolio_run_ts": None,
                    "portfolio_optimizer": None}
        self.assertEqual(pipeline_io.portfolio_signals_dir(fallback, "/base"), "/base/hardcoded_fallback")
        self.assertEqual(pipeline_io.portfolio_signals_dir(None, "/base"), "/base/hardcoded_fallback")
        half = {"portfolio_optimizer": "minimum_variance", "portfolio_run_ts": None}
        self.assertEqual(pipeline_io.portfolio_signals_dir(half, "/base"), "/base/hardcoded_fallback")

    def test_base_defaults_to_signals_out_dir_then_the_built_in_default(self):
        self.assertEqual(
            pipeline_io.portfolio_signals_dir(_meta(MV)),
            os.path.join(pipeline_io.DEFAULT_SIGNALS_DIR, MV_KEY),
        )
        os.environ["SIGNALS_OUT_DIR"] = "/custom"
        self.assertEqual(pipeline_io.portfolio_signals_dir(_meta(MV)), f"/custom/{MV_KEY}")

    def test_resolution_order(self):
        os.environ["SIGNALS_OUT_DIR"] = "/base"
        self.assertEqual(pipeline_io.resolve_signals_dir(_meta(MV)), f"/base/{MV_KEY}")
        os.environ["SIGNALS_PER_PORTFOLIO"] = "0"
        self.assertEqual(pipeline_io.resolve_signals_dir(_meta(MV)), "/base")
        os.environ["SIGNALS_DIR_EXACT"] = "/exact/mv_day2"
        self.assertEqual(pipeline_io.resolve_signals_dir(_meta(MV)), "/exact/mv_day2")
        os.environ["SIGNALS_PER_PORTFOLIO"] = "1"
        self.assertEqual(pipeline_io.resolve_signals_dir(_meta(MV)), "/exact/mv_day2")

    def test_per_portfolio_switch_values(self):
        for value, expected in (("0", False), ("false", False), ("OFF", False), ("1", True),
                                ("", True), ("yes", True)):
            with self.subTest(value=value):
                self.assertEqual(
                    pipeline_io.per_portfolio_enabled({"SIGNALS_PER_PORTFOLIO": value}), expected,
                )
        self.assertTrue(pipeline_io.per_portfolio_enabled({}))

    def test_artifacts_figures_and_history_follow_the_layout(self):
        os.environ["SIGNALS_OUT_DIR"] = "/pipe/signals"
        meta = _meta(MV)
        self.assertEqual(
            pipeline_io.artifact_path(meta, "r.html", "/legacy"), f"/pipe/signals/{MV_KEY}/artifacts/r.html",
        )
        self.assertEqual(pipeline_io.default_figures_dir(meta), f"/pipe/signals/{MV_KEY}/figures")
        self.assertEqual(
            pipeline_io.optimizer_history_path(meta, "/repo/portfolio_risk_history.csv"),
            "/repo/portfolio_risk_history_minimum_variance.csv",
        )
        os.environ["SIGNALS_PER_PORTFOLIO"] = "0"
        self.assertEqual(pipeline_io.artifact_path(meta, "r.html", "/legacy"), "/legacy/r.html")
        self.assertEqual(pipeline_io.default_figures_dir(meta), "/pipe/figures")
        self.assertEqual(
            pipeline_io.optimizer_history_path(meta, "/repo/portfolio_risk_history.csv"),
            "/repo/portfolio_risk_history.csv",
        )
        # No optimizer: the shared legacy history.
        del os.environ["SIGNALS_PER_PORTFOLIO"]
        self.assertEqual(
            pipeline_io.optimizer_history_path(None, "/repo/portfolio_risk_history.csv"),
            "/repo/portfolio_risk_history.csv",
        )

    def test_announce_prints_the_resolved_dir(self):
        os.environ["SIGNALS_OUT_DIR"] = "/base"
        buf = io.StringIO()
        with redirect_stdout(buf):
            resolved = pipeline_io.announce_signals_dir("portfolio_vix", _meta(QU))
        self.assertEqual(resolved, f"/base/{QU_KEY}")
        self.assertIn(f"portfolio_vix: output dir = /base/{QU_KEY}", buf.getvalue())


class ExportTests(CleanEnvCase):
    def _meta_full(self, ident):
        return {"weights": {"AAA": 1.0}, "portfolio_source": "/p.json",
                "portfolio_run_ts": ident["run_ts"], "portfolio_optimizer": ident["optimizer"]}

    def test_two_portfolios_keep_separate_latest_files(self):
        os.environ["SIGNALS_OUT_DIR"] = self.tmp
        mv_path = pipeline_io.export_signals("portfolio_vix", {"vix_portfolio": 11.0}, self._meta_full(MV))
        mv_before = Path(mv_path).read_text(encoding="utf-8")
        qu_path = pipeline_io.export_signals("portfolio_vix", {"vix_portfolio": 22.0}, self._meta_full(QU))
        self.assertEqual(mv_path, os.path.join(self.tmp, MV_KEY, "portfolio_vix.json"))
        self.assertEqual(qu_path, os.path.join(self.tmp, QU_KEY, "portfolio_vix.json"))
        self.assertEqual(Path(mv_path).read_text(encoding="utf-8"), mv_before)
        self.assertEqual(json.loads(Path(mv_path).read_text(encoding="utf-8"))["data"]["vix_portfolio"], 11.0)
        self.assertEqual(json.loads(Path(qu_path).read_text(encoding="utf-8"))["data"]["vix_portfolio"], 22.0)
        # Nothing loose in the base, and each folder has its latest plus one stamped copy.
        self.assertEqual(sorted(os.listdir(self.tmp)), sorted([MV_KEY, QU_KEY]))
        for key in (MV_KEY, QU_KEY):
            self.assertEqual(len(os.listdir(os.path.join(self.tmp, key))), 2)

    def test_exact_dir_and_flat_layout(self):
        os.environ["SIGNALS_OUT_DIR"] = os.path.join(self.tmp, "base")
        os.environ["SIGNALS_DIR_EXACT"] = os.path.join(self.tmp, "exact")
        path = pipeline_io.export_signals("portfolio_vix", {}, self._meta_full(MV))
        self.assertEqual(path, os.path.join(self.tmp, "exact", "portfolio_vix.json"))
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "base")))
        del os.environ["SIGNALS_DIR_EXACT"]
        os.environ["SIGNALS_PER_PORTFOLIO"] = "0"
        path = pipeline_io.export_signals("portfolio_vix", {}, self._meta_full(MV))
        self.assertEqual(path, os.path.join(self.tmp, "base", "portfolio_vix.json"))

    def test_hardcoded_fallback_export(self):
        os.environ["SIGNALS_OUT_DIR"] = self.tmp
        meta = {"weights": {"AAA": 1.0}, "portfolio_source": "hardcoded_fallback",
                "portfolio_run_ts": None, "portfolio_optimizer": None}
        path = pipeline_io.export_signals("portfolio_vix", {}, meta)
        self.assertEqual(path, os.path.join(self.tmp, "hardcoded_fallback", "portfolio_vix.json"))

    def test_pipeline_dir_comes_from_the_base_not_the_portfolio_folder(self):
        os.environ["SIGNALS_OUT_DIR"] = os.path.join(self.tmp, "pipeline", "signals")
        self.assertEqual(pipeline_io.pipeline_dir(), os.path.join(self.tmp, "pipeline"))
        self.assertEqual(
            pipeline_io.entry_state_path(_meta(MV)),
            os.path.join(self.tmp, "pipeline", "state", f"entry_state_{MV_KEY}.json"),
        )


class ParentChildAgreementTests(CleanEnvCase):
    """run_cycle (reads the file) and a step (load_portfolio meta) must pick one folder."""

    def test_step_export_lands_where_run_cycle_validates(self):
        portfolio_path = os.path.join(self.tmp, "portfolio.json")
        Path(portfolio_path).write_text(json.dumps(_portfolio_file(**MV)), encoding="utf-8")
        base = os.path.join(self.tmp, "signals")
        parent_dir = run_cycle.resolve_cycle_signals(run_cycle.load_portfolio_file(portfolio_path), base)

        step_start = run_cycle._now_bogota()
        env = {"PORTFOLIO_FILE": portfolio_path, "SIGNALS_OUT_DIR": base}
        with mock.patch.dict(os.environ, env):
            meta = pipeline_io.load_portfolio({"AAA": 1.0})
            written = pipeline_io.export_signals("portfolio_vix", {"vix_portfolio": 1.0}, meta)
        self.assertEqual(written, os.path.join(parent_dir, "portfolio_vix.json"))
        payload = run_cycle.verify_signal(
            os.path.join(parent_dir, "portfolio_vix.json"), "portfolio_vix",
            portfolio_path, MV["run_ts"], step_start,
        )
        self.assertEqual(payload["portfolio_optimizer"], "minimum_variance")

    def test_entry_reads_back_the_signal_it_exported_in_the_portfolio_folder(self):
        # entry_signal_tool.main reads run_ts back from export_signals' returned path.
        import entry_signal_tool as est
        from tests.test_daily_safety import META

        base = os.path.join(self.tmp, "signals")
        with mock.patch.dict(os.environ, {"SIGNALS_OUT_DIR": base, "CYCLE_DATE": "2026-10-07",
                                          "EXECUTIONS_DIR": os.path.join(self.tmp, "ex")}):
            with mock.patch.multiple(
                est, _PORTFOLIO_META=META, TICKERS=["GLD"], PESOS_OBJETIVO={"GLD": 0.1},
                HIST_PATH=os.path.join(self.tmp, "h.csv"),
                LEGACY_STATE_PATH=os.path.join(self.tmp, "legacy.json"),
                graficar_resumen=lambda resumen: None,
            ), redirect_stdout(io.StringIO()):
                est.main([])
            folder = Path(base, "black_litterman_20261005T164012")
            signal = json.loads((folder / "entry_signal_tool.json").read_text(encoding="utf-8"))
            state = json.loads(Path(pipeline_io.entry_state_path(META)).read_text(encoding="utf-8"))
        self.assertEqual(state["pending_signal_run_ts"], signal["run_ts"])
        self.assertEqual(os.listdir(base), ["black_litterman_20261005T164012"])


class SideOutputTests(CleanEnvCase):
    def test_gex_report_goes_to_the_portfolio_artifacts_folder(self):
        os.environ["SIGNALS_OUT_DIR"] = self.tmp
        with mock.patch.object(gex, "_PORTFOLIO_META", _meta(MV)):
            folder, name = gex._resolve_output(gex.OUTPUT_HTML_PATH)
            self.assertEqual(folder, os.path.join(self.tmp, MV_KEY, "artifacts"))
            self.assertEqual(name, "portfolio_gex_field.html")
            self.assertTrue(os.path.isdir(folder))
            self.assertEqual(gex.DATA_JSON_FILENAME, "portfolio_gex_field_data.json")
            # An explicit path is respected.
            explicit = os.path.join(self.tmp, "mine", "g.html")
            self.assertEqual(gex._resolve_output(explicit), (os.path.dirname(explicit), "g.html"))
            # Flat layout: where it always was (the working directory).
            os.environ["SIGNALS_PER_PORTFOLIO"] = "0"
            self.assertEqual(gex._resolve_output(gex.OUTPUT_HTML_PATH), (os.getcwd(), "portfolio_gex_field.html"))

    def test_two_portfolios_get_separate_gex_reports(self):
        os.environ["SIGNALS_OUT_DIR"] = self.tmp
        dirs = []
        for ident in (MV, QU):
            with mock.patch.object(gex, "_PORTFOLIO_META", _meta(ident)):
                dirs.append(gex._resolve_output(gex.OUTPUT_HTML_PATH)[0])
        self.assertNotEqual(*dirs)

    def test_vix_report_default_name_goes_to_artifacts(self):
        os.environ["SIGNALS_OUT_DIR"] = self.tmp
        fig = mock.MagicMock()
        with mock.patch.object(vix, "_PORTFOLIO_META", _meta(QU)):
            out = vix.ReportPlotter.plot({}, None, {}, None, show=False, fig=fig)
            explicit = os.path.join(self.tmp, "elsewhere", "v.html")
            out_explicit = vix.ReportPlotter.plot({}, None, {}, None, html_file=explicit, fig=fig)
        self.assertEqual(out, os.path.join(self.tmp, QU_KEY, "artifacts", "portfolio_vix_report.html"))
        self.assertEqual(out_explicit, explicit)
        self.assertEqual(fig.write_html.call_count, 2)

    def test_unwritable_artifacts_folder_falls_back_without_raising(self):
        blocker = os.path.join(self.tmp, "file")
        Path(blocker).write_text("x", encoding="utf-8")
        with redirect_stdout(io.StringIO()):
            path = pipeline_io.prepare_artifact_path(os.path.join(blocker, "a", "r.html"), self.tmp)
        self.assertEqual(path, os.path.join(self.tmp, "r.html"))


class CycleCase(CleanEnvCase):
    """run_cycle.main with fake steps and the default (per-portfolio) layout."""

    def setUp(self):
        super().setUp()
        self.fake = os.path.join(self.tmp, "fake_step.py")
        Path(self.fake).write_text(FAKE_STEP, encoding="utf-8")
        self.base = os.path.join(self.tmp, "pipeline", "signals")
        self.summary_dir = os.path.join(self.tmp, "pipeline", "summary")
        self.state_dir = os.path.join(self.tmp, "pipeline", "state")
        for patch in (
            mock.patch.object(run_cycle, "WEEKLY_STATE_DIR", self.state_dir),
            mock.patch.object(run_cycle, "DEFAULT_WEEKLY_STATE", os.path.join(self.state_dir, "weekly_last_run.json")),
            mock.patch.object(run_cycle, "build_command", side_effect=lambda s: [sys.executable, self.fake, s]),
            mock.patch.object(run_cycle, "entry_phase", return_value=PAST_ENTRY_PHASE),
        ):
            patch.start()
            self.addCleanup(patch.stop)

    def cycle(self, ident, *args, env=None, date=WEDNESDAY):
        path = os.path.join(self.tmp, f"portfolio_{ident['optimizer']}.json")
        Path(path).write_text(json.dumps(_portfolio_file(**ident)), encoding="utf-8")
        argv = ["--portfolio", path, "--signals-dir", self.base, "--summary-dir", self.summary_dir,
                "--timeout", "30", "--date", date, *args]
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, env or {}), redirect_stdout(out), redirect_stderr(err):
            code = run_cycle.main(argv)
        return code, out.getvalue(), err.getvalue(), path

    def read(self, *parts):
        return json.loads(Path(*parts).read_text(encoding="utf-8"))


class TwoPortfolioCycleTests(CycleCase):
    def test_daily_cycles_of_two_portfolios_do_not_overwrite_each_other(self):
        code, out, err, mv_file = self.cycle(MV)
        self.assertEqual(code, 0, err)
        mv_dir = os.path.join(self.base, MV_KEY)
        before = {name: Path(mv_dir, name).read_text(encoding="utf-8") for name in os.listdir(mv_dir)}
        mv_summary = Path(self.summary_dir, MV_KEY, "cycle_summary_latest.json").read_text(encoding="utf-8")

        code, out, err, qu_file = self.cycle(QU)
        self.assertEqual(code, 0, err)
        qu_dir = os.path.join(self.base, QU_KEY)

        self.assertEqual(sorted(os.listdir(self.base)), sorted([MV_KEY, QU_KEY]))
        for script in run_cycle.DAILY_STEPS:
            mv_signal = self.read(mv_dir, f"{script}.json")
            qu_signal = self.read(qu_dir, f"{script}.json")
            self.assertEqual((mv_signal["portfolio_source"], mv_signal["portfolio_run_ts"]), (mv_file, MV["run_ts"]))
            self.assertEqual((qu_signal["portfolio_source"], qu_signal["portfolio_run_ts"]), (qu_file, QU["run_ts"]))
        # MV's files are byte for byte what its own run left.
        self.assertEqual({name: Path(mv_dir, name).read_text(encoding="utf-8") for name in before}, before)

        # Summaries: one folder each, MV's untouched; names the folder the steps wrote to.
        mv_body = self.read(self.summary_dir, MV_KEY, "cycle_summary_latest.json")
        qu_body = self.read(self.summary_dir, QU_KEY, "cycle_summary_latest.json")
        self.assertEqual(Path(self.summary_dir, MV_KEY, "cycle_summary_latest.json").read_text(encoding="utf-8"), mv_summary)
        self.assertEqual((mv_body["portfolio"]["optimizer"], mv_body["signals_dir"]), ("minimum_variance", mv_dir))
        self.assertEqual((qu_body["portfolio"]["optimizer"], qu_body["signals_dir"]), ("quadratic_utility", qu_dir))
        self.assertTrue(all(step["output_file"].startswith(qu_dir) for step in qu_body["steps"]))
        for key in (MV_KEY, QU_KEY):
            names = os.listdir(os.path.join(self.summary_dir, key))
            self.assertIn("cycle_summary_latest.txt", names)
            self.assertEqual(len([n for n in names if n.endswith(".json")]), 2)
        self.assertIn(f"signals_dir: {qu_dir}", Path(self.summary_dir, QU_KEY, "cycle_summary_latest.txt").read_text(encoding="utf-8"))
        # Top-level pointer: the last cycle of any portfolio, self-describing.
        top = self.read(self.summary_dir, "cycle_summary_latest.json")
        self.assertEqual(top["portfolio"]["optimizer"], "quadratic_utility")
        self.assertIn(f"signals_dir={qu_dir}", out)
        self.assertIn(os.path.join(self.summary_dir, QU_KEY, "cycle_summary_latest.json"), out)

    def test_steps_get_the_resolved_dir_and_the_base(self):
        env = run_cycle.step_environment(
            "/p.json", f"/b/{MV_KEY}", "portfolio_vix", signals_base="/b",
        )
        self.assertEqual(env["SIGNALS_DIR_EXACT"], f"/b/{MV_KEY}")
        self.assertEqual(env["SIGNALS_OUT_DIR"], "/b")

    def test_weekly_cycle_is_due_per_portfolio_on_the_same_monday(self):
        code, _, err, _ = self.cycle(MV, "--weekly", date=MONDAY)
        self.assertEqual(code, 0, err)
        code, out, err, _ = self.cycle(QU, "--weekly", date=MONDAY)
        self.assertEqual(code, 0, err)
        self.assertNotIn("not_due", out)

        self.assertEqual(
            sorted(os.listdir(self.state_dir)),
            sorted([f"weekly_last_run_{MV_KEY}.json", f"weekly_last_run_{QU_KEY}.json"]),
        )
        self.assertEqual(self.read(self.state_dir, f"weekly_last_run_{MV_KEY}.json")["portfolio_run_ts"], MV["run_ts"])
        self.assertEqual(self.read(self.state_dir, f"weekly_last_run_{QU_KEY}.json")["portfolio_run_ts"], QU["run_ts"])
        for key in (MV_KEY, QU_KEY):
            self.assertEqual(self.read(self.base, key, "active_management.json")["script"], "active_management")
            self.assertEqual(self.read(self.summary_dir, key, "cycle_summary_latest.json")["status"], "success")

        # A second run for the same portfolio the same week is still blocked.
        code, out, _, _ = self.cycle(MV, "--weekly", date=MONDAY)
        self.assertEqual(code, 0)
        self.assertIn("already_ran_this_week", out)

    def test_explicit_weekly_state_file_is_shared_as_before(self):
        shared = os.path.join(self.tmp, "shared_weekly.json")
        code, _, err, _ = self.cycle(MV, "--weekly", "--weekly-state", shared, date=MONDAY)
        self.assertEqual(code, 0, err)
        code, out, _, _ = self.cycle(QU, "--weekly", "--weekly-state", shared, date=MONDAY)
        self.assertIn("already_ran_this_week", out)
        self.assertFalse(os.path.exists(self.state_dir))

    def test_unreadable_portfolio_summary_goes_to_the_top_level(self):
        path = os.path.join(self.tmp, "broken.json")
        Path(path).write_text("{not json", encoding="utf-8")
        err = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(err):
            code = run_cycle.main(["--portfolio", path, "--signals-dir", self.base,
                                   "--summary-dir", self.summary_dir, "--date", WEDNESDAY])
        self.assertEqual(code, 1)
        self.assertEqual(self.read(self.summary_dir, "cycle_summary_latest.json")["status"], "failed")
        self.assertEqual([n for n in os.listdir(self.summary_dir) if os.path.isdir(os.path.join(self.summary_dir, n))], [])

    def test_dry_run_prints_the_resolved_dirs(self):
        code, out, err, _ = self.cycle(MV, "--dry-run")
        self.assertEqual(code, 0, err)
        self.assertIn(f"signals_dir={os.path.join(self.base, MV_KEY)}", out)
        self.assertIn(f"SIGNALS_DIR_EXACT={os.path.join(self.base, MV_KEY)}", out)
        self.assertIn(f"SIGNALS_OUT_DIR={self.base}", out)
        self.assertFalse(os.path.exists(self.base))


class OverrideCycleTests(CycleCase):
    def test_signals_dir_exact_is_used_as_is_and_validated(self):
        exact = os.path.join(self.tmp, "signals", "cycle2_mv_day2")
        code, out, err, _ = self.cycle(MV, env={"SIGNALS_DIR_EXACT": exact})
        self.assertEqual(code, 0, err)
        self.assertEqual(
            sorted(n for n in os.listdir(exact) if not any(c.isdigit() for c in n)),
            sorted(f"{s}.json" for s in run_cycle.DAILY_STEPS),
        )
        self.assertFalse(os.path.exists(self.base))
        self.assertEqual(self.read(self.summary_dir, MV_KEY, "cycle_summary_latest.json")["signals_dir"], exact)
        self.assertIn(f"signals_dir={exact}", out)

    def test_per_portfolio_off_restores_the_flat_layout(self):
        code, out, err, _ = self.cycle(MV, env={"SIGNALS_PER_PORTFOLIO": "0"})
        self.assertEqual(code, 0, err)
        for script in run_cycle.DAILY_STEPS:
            self.assertTrue(os.path.isfile(os.path.join(self.base, f"{script}.json")), script)
        self.assertFalse(os.path.exists(os.path.join(self.base, MV_KEY)))
        # Flat summary, no per-portfolio folder, and the single legacy weekly state.
        self.assertEqual(self.read(self.summary_dir, "cycle_summary_latest.json")["signals_dir"], self.base)
        self.assertFalse(os.path.exists(os.path.join(self.summary_dir, MV_KEY)))
        code, _, err, _ = self.cycle(MV, "--weekly", env={"SIGNALS_PER_PORTFOLIO": "0"}, date=MONDAY)
        self.assertEqual(code, 0, err)
        self.assertEqual(os.listdir(self.state_dir), ["weekly_last_run.json"])


if __name__ == "__main__":
    unittest.main()
