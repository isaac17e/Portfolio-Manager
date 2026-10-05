"""Unit tests for pipeline_io. No network."""

import io
import json
import os
import stat
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path
from unittest import mock
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

import pipeline_io


FALLBACK = {"GLD": 0.6, "SLV": 0.4}
BOGOTA = ZoneInfo("America/Bogota")


def _portfolio(**weights):
    return {
        "schema_version": 1,
        "source_repo": "AM-PM-Architecture",
        "optimizer": "black_litterman",
        "run_ts": "2026-10-05T16:40:12-05:00",
        "weights": weights,
    }


class LoadPortfolioTests(unittest.TestCase):
    def test_load_renormalizes_and_returns_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "portfolio_latest.json")
            payload = _portfolio(BBB=2, AAA=2, DUST=1e-8, ZERO=0)
            Path(path).write_text(json.dumps(payload), encoding="utf-8")
            with mock.patch.dict(os.environ, {"PORTFOLIO_FILE": path}):
                loaded = pipeline_io.load_portfolio(dict(FALLBACK))

        self.assertEqual(loaded["portfolio_source"], path)
        self.assertEqual(loaded["portfolio_run_ts"], "2026-10-05T16:40:12-05:00")
        self.assertEqual(loaded["portfolio_optimizer"], "black_litterman")
        self.assertEqual(list(loaded["weights"]), ["AAA", "BBB"])
        self.assertEqual(loaded["weights"]["AAA"], 0.5)
        self.assertEqual(loaded["weights"]["BBB"], 0.5)
        self.assertEqual(sum(round(v * 1_000_000) for v in loaded["weights"].values()), 1_000_000)

    def test_three_equal_weights_sum_to_one_at_six_decimals(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "portfolio_latest.json")
            Path(path).write_text(json.dumps(_portfolio(C=1, A=1, B=1)), encoding="utf-8")
            with mock.patch.dict(os.environ, {"PORTFOLIO_FILE": path}):
                loaded = pipeline_io.load_portfolio(FALLBACK)

        weights = loaded["weights"]
        self.assertEqual(list(weights), ["A", "B", "C"])
        self.assertEqual(sum(round(v * 1_000_000) for v in weights.values()), 1_000_000)
        self.assertEqual(weights["A"], 0.333334)
        self.assertEqual(weights["B"], 0.333333)
        self.assertEqual(weights["C"], 0.333333)

    def test_missing_file_uses_fallback_without_renormalizing(self):
        uneven = {"AAA": 0.2, "BBB": 0.2}
        with tempfile.TemporaryDirectory() as tmp:
            missing = os.path.join(tmp, "nope.json")
            buf = io.StringIO()
            with mock.patch.dict(os.environ, {"PORTFOLIO_FILE": missing}):
                with redirect_stdout(buf):
                    loaded = pipeline_io.load_portfolio(uneven)
        self.assertIn("not found", buf.getvalue())
        self.assertIn("hardcoded", buf.getvalue())
        self.assertEqual(loaded["portfolio_source"], "hardcoded_fallback")
        self.assertIsNone(loaded["portfolio_run_ts"])
        self.assertIsNone(loaded["portfolio_optimizer"])
        self.assertEqual(loaded["weights"], uneven)
        self.assertIsNot(loaded["weights"], uneven)

    def test_invalid_json_negative_and_bad_schema_fall_back(self):
        cases = [
            "{",
            json.dumps({"schema_version": 1, "weights": {"AAA": -0.2, "BBB": 1.2}}),
            json.dumps({"schema_version": 2, "weights": {"AAA": 1}}),
            json.dumps(["AAA", "BBB"]),
            json.dumps({"schema_version": 1, "weights": {}}),
        ]
        for text in cases:
            with self.subTest(text=text):
                with tempfile.TemporaryDirectory() as tmp:
                    path = os.path.join(tmp, "portfolio_latest.json")
                    Path(path).write_text(text, encoding="utf-8")
                    buf = io.StringIO()
                    with mock.patch.dict(os.environ, {"PORTFOLIO_FILE": path}):
                        with redirect_stdout(buf):
                            loaded = pipeline_io.load_portfolio(FALLBACK)
                self.assertEqual(loaded["weights"], FALLBACK)
                self.assertEqual(loaded["portfolio_source"], "hardcoded_fallback")
                self.assertIn("fallback", buf.getvalue())


class ExportSignalsTests(unittest.TestCase):
    def test_export_writes_latest_and_timestamped_copy(self):
        frozen = datetime(2026, 10, 5, 16, 40, 12, tzinfo=BOGOTA)
        meta = {
            "weights": {"AAA": 0.5, "BBB": 0.5},
            "portfolio_source": "/tmp/portfolio_latest.json",
            "portfolio_run_ts": "2026-10-05T16:40:12-05:00",
            "portfolio_optimizer": "minimum_variance",
        }
        data = {
            "entries": [{"order": 1, "score": np.float64(1.5), "gap": float("nan")}],
            "frame": pd.DataFrame({"ticker": ["AAA"], "value": [np.nan]}),
            "vector": np.array([1, np.nan]),
            "nat": pd.NaT,
        }
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {"SIGNALS_OUT_DIR": tmp}):
                with mock.patch.object(pipeline_io, "_now_bogota", return_value=frozen):
                    latest = pipeline_io.export_signals("entry_signal_tool", data, meta)
            latest_path = Path(tmp) / "entry_signal_tool.json"
            stamped_path = Path(tmp) / "entry_signal_tool_20261005T164012.json"
            self.assertEqual(latest, str(latest_path))
            self.assertEqual(latest_path.read_text(encoding="utf-8"), stamped_path.read_text(encoding="utf-8"))
            self.assertFalse(list(Path(tmp).glob("*.tmp")))
            raw = latest_path.read_text(encoding="utf-8")
            payload = json.loads(raw)

        self.assertNotIn("NaN", raw)
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["script"], "entry_signal_tool")
        self.assertEqual(payload["run_ts"], "2026-10-05T16:40:12-05:00")
        self.assertEqual(payload["portfolio_source"], "/tmp/portfolio_latest.json")
        self.assertEqual(payload["portfolio_run_ts"], "2026-10-05T16:40:12-05:00")
        self.assertEqual(payload["portfolio_optimizer"], "minimum_variance")
        self.assertEqual(payload["weights_used"], {"AAA": 0.5, "BBB": 0.5})
        self.assertIsNone(payload["data"]["entries"][0]["gap"])
        self.assertEqual(payload["data"]["entries"][0]["score"], 1.5)
        self.assertIsNone(payload["data"]["frame"][0]["value"])
        self.assertEqual(payload["data"]["vector"], [1, None])
        self.assertIsNone(payload["data"]["nat"])

    def test_unwritable_directory_does_not_raise(self):
        with tempfile.TemporaryDirectory() as tmp:
            blocker = os.path.join(tmp, "not-a-directory")
            Path(blocker).write_text("x", encoding="utf-8")
            dest = os.path.join(blocker, "signals")
            buf = io.StringIO()
            with mock.patch.dict(os.environ, {"SIGNALS_OUT_DIR": dest}):
                with redirect_stdout(buf):
                    result = pipeline_io.export_signals("portfolio_vix", {"vix_portfolio": 1}, {
                        "weights": FALLBACK,
                        "portfolio_source": "hardcoded_fallback",
                        "portfolio_run_ts": None,
                        "portfolio_optimizer": None,
                    })
        self.assertIsNone(result)
        self.assertIn("Could not write", buf.getvalue())

    def test_read_only_directory_does_not_raise(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.chmod(tmp, stat.S_IRUSR | stat.S_IXUSR)
            try:
                buf = io.StringIO()
                with mock.patch.dict(os.environ, {"SIGNALS_OUT_DIR": os.path.join(tmp, "nested")}):
                    with redirect_stdout(buf):
                        result = pipeline_io.export_signals(
                            "fundamental_analysis",
                            {},
                            {"weights": {}, "portfolio_source": "hardcoded_fallback",
                             "portfolio_run_ts": None, "portfolio_optimizer": None},
                        )
                if os.geteuid() == 0:
                    self.skipTest("root ignores directory write bits")
                self.assertIsNone(result)
                self.assertIn("Could not write", buf.getvalue())
            finally:
                os.chmod(tmp, stat.S_IRWXU)


if __name__ == "__main__":
    unittest.main()
