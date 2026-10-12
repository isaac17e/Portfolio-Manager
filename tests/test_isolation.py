"""The test run must not see the machine's real pipeline (see tests/__init__.py)."""

import os
import unittest

import entry_signal_tool
import pipeline_io
import run_cycle
from tests import _PIPELINE_ENV, SANDBOX_DIR


class PipelineIsolationTests(unittest.TestCase):
    def test_pipeline_env_is_scrubbed(self):
        # Tests that set one of these restore it on exit, so at rest none is set.
        for name in _PIPELINE_ENV:
            self.assertNotIn(name, os.environ, name)

    def test_default_paths_live_in_the_sandbox(self):
        paths = [
            pipeline_io.DEFAULT_PORTFOLIO_FILE, pipeline_io.DEFAULT_SIGNALS_DIR,
            pipeline_io.DEFAULT_EXECUTIONS_DIR, run_cycle.DEFAULT_PORTFOLIO_FILE,
            run_cycle.DEFAULT_SIGNALS_DIR, run_cycle.DEFAULT_SUMMARY_DIR,
            run_cycle.DEFAULT_WEEKLY_STATE, run_cycle.WEEKLY_STATE_DIR,
            entry_signal_tool.LEGACY_STATE_PATH,
        ]
        for path in paths:
            self.assertTrue(os.path.abspath(path).startswith(SANDBOX_DIR), path)

    def test_helpers_resolve_inside_the_sandbox(self):
        self.assertTrue(pipeline_io.executions_dir().startswith(SANDBOX_DIR))
        self.assertTrue(pipeline_io.signals_base_dir().startswith(SANDBOX_DIR))
        self.assertTrue(pipeline_io.pipeline_dir().startswith(SANDBOX_DIR))
        self.assertTrue(pipeline_io.entry_state_path(None).startswith(SANDBOX_DIR))
        self.assertTrue(pipeline_io.rotation_state_path(None).startswith(SANDBOX_DIR))

    def test_no_portfolio_file_means_hardcoded_fallback(self):
        self.assertFalse(os.path.exists(pipeline_io.DEFAULT_PORTFOLIO_FILE))
        loaded = pipeline_io.load_portfolio({"AAA": 1.0})
        self.assertEqual(loaded["weights"], {"AAA": 1.0})
        self.assertIsNone(loaded.get("portfolio_optimizer"))


if __name__ == "__main__":
    unittest.main()
