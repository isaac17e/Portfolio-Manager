"""Show a figure, or write it to HTML when nobody can look at it.

Without a browser ``plotly``'s ``fig.show()`` starts a localhost server and
waits forever for a request (it hung a pipeline run with BROWSER=/bin/true).
Every script hands its figures to ``show_or_save`` so the decision lives here:

- ``HEADLESS`` set to a true value (1/true/yes/y/on): never show, write HTML.
  Set to anything else (e.g. 0): show. run_cycle sets HEADLESS=1 for every step.
- ``HEADLESS`` unset: headless when there is no display (Linux without
  DISPLAY / WAYLAND_DISPLAY) or the run is not interactive (stdin or stdout
  not a terminal, outside IPython / Jupyter).

The HTML goes to ``FIGURES_DIR``, else ``<pipeline dir>/figures`` (see
``pipeline_io.pipeline_dir``), as ``<script>_<name>_<YYYYMMDDTHHMMSS>.html``.
``fig.write_html`` needs no kaleido.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime

from pipeline_io import _file_token, pipeline_dir

HEADLESS_ENV = "HEADLESS"
FIGURES_DIR_ENV = "FIGURES_DIR"
_TRUTHY = {"1", "true", "yes", "y", "on"}


def _in_ipython() -> bool:
    try:
        from IPython import get_ipython
    except ImportError:
        return False
    return get_ipython() is not None


def _interactive() -> bool:
    if _in_ipython():
        return True
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except (AttributeError, ValueError):
        return False


def headless(env=None, interactive=None) -> bool:
    """True when figures must be written to a file instead of shown."""
    env = os.environ if env is None else env
    explicit = str(env.get(HEADLESS_ENV, "")).strip().lower()
    if explicit:
        return explicit in _TRUTHY
    if sys.platform.startswith("linux") and not (env.get("DISPLAY") or env.get("WAYLAND_DISPLAY")):
        return True
    return not (_interactive() if interactive is None else interactive)


def figures_dir(env=None) -> str:
    env = os.environ if env is None else env
    return env.get(FIGURES_DIR_ENV) or os.path.join(pipeline_dir(), "figures")


def figure_path(script: str, name: str = "", env=None, now=None) -> str:
    stamp = (now or datetime.now()).strftime("%Y%m%dT%H%M%S")
    parts = [_file_token(script)] + ([_file_token(name)] if name else []) + [stamp]
    return os.path.join(figures_dir(env), "_".join(parts) + ".html")


def show_or_save(fig, script: str, name: str = "", env=None) -> str | None:
    """``fig.show()``, or in headless mode write ``fig`` to HTML and return the path.

    A figure that cannot be written is reported and skipped: a chart must not
    fail the step whose signal is already exported.
    """
    if fig is None:
        return None
    if not headless(env):
        fig.show()
        return None
    path = figure_path(script, name, env)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fig.write_html(path, include_plotlyjs="cdn", full_html=True)
    except OSError as exc:
        print(f"[figures] could not write {path}: {exc}")
        return None
    print(f"[figures] headless: figure written to {path}")
    return path
