"""Test package. Importing it isolates the whole run from the machine's real pipeline.

Several modules read the portfolio at import time (``entry_signal_tool.TICKERS``)
and default to ``/workspace/pipeline/...`` or to whatever ``PORTFOLIO_FILE`` /
``EXECUTIONS_DIR`` / ... the shell exports. On a machine with a real pipeline
that leaks live portfolios, fills and state into the tests (e.g. a state that has
no ``GLD`` -> ``KeyError``). So, before any test module imports the scripts:

- the pipeline-related environment variables are removed, and
- the default pipeline paths of ``pipeline_io`` / ``run_cycle`` (and the legacy
  entry-state path of ``entry_signal_tool``) point into an empty temp sandbox.

A test that needs a pipeline builds its own temp dir and sets the env vars it
needs with ``mock.patch.dict(os.environ, ...)``; with nothing set, the scripts
see "no portfolio file" and use their hardcoded fallback, as on a clean checkout.
"""

import atexit
import os
import shutil
import tempfile

# Variables that select a pipeline location or alter pipeline behaviour.
_PIPELINE_ENV = (
    "PORTFOLIO_FILE", "PIPELINE_DIR", "EXECUTIONS_DIR", "SIGNALS_OUT_DIR", "SIGNALS_DIR_EXACT",
    "SIGNALS_PER_PORTFOLIO", "ENTRY_STATE_FILE", "ROTATION_STATE_FILE", "CYCLE_SUMMARY_DIR",
    "CYCLE_DATE", "CYCLE_STEP_TIMEOUT", "PORTFOLIO_HORIZON_DAYS", "RISK_FREE_RATE",
    "ENTRY_CYCLE_DAY", "ENTRY_INVESTED_PCT", "ENTRY_FORCE_NEW_TRANCHE", "ENTRY_STAGGER_PCT",
    "ROTATION_UNIVERSE", "ROTATION_CUSTOM_TICKERS", "FUNDAMENTAL_STATE_FILE",
    "FUNDAMENTAL_EXTRA_TICKERS",
)

SANDBOX_DIR = tempfile.mkdtemp(prefix="pm_tests_pipeline_")
atexit.register(shutil.rmtree, SANDBOX_DIR, ignore_errors=True)

for _name in _PIPELINE_ENV:
    os.environ.pop(_name, None)


def _isolate_pipeline_defaults():
    import pipeline_io

    root = os.path.join(SANDBOX_DIR, "pipeline")
    pipeline_io.DEFAULT_PORTFOLIO_FILE = os.path.join(root, "portfolio", "portfolio_latest.json")
    pipeline_io.DEFAULT_SIGNALS_DIR = os.path.join(root, "signals")
    pipeline_io.DEFAULT_EXECUTIONS_DIR = os.path.join(root, "executions")
    # Only now: entry_signal_tool reads the portfolio when it is imported.
    import entry_signal_tool
    import run_cycle

    run_cycle.DEFAULT_PORTFOLIO_FILE = pipeline_io.DEFAULT_PORTFOLIO_FILE
    run_cycle.DEFAULT_SIGNALS_DIR = pipeline_io.DEFAULT_SIGNALS_DIR
    run_cycle.DEFAULT_SUMMARY_DIR = root
    run_cycle.DEFAULT_WEEKLY_STATE = os.path.join(root, "state", "weekly_last_run.json")
    run_cycle.WEEKLY_STATE_DIR = os.path.dirname(run_cycle.DEFAULT_WEEKLY_STATE)
    entry_signal_tool.LEGACY_STATE_PATH = os.path.join(SANDBOX_DIR, "entry_state.json")


_isolate_pipeline_defaults()
