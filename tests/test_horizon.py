"""Portfolio horizon: pipeline_io helpers, per-script expiry selection and the
horizon run_cycle passes to each step. No network: option chains are fakes."""

import json
import math
import os
import tempfile
import unittest
import warnings
from datetime import date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pandas as pd

import entry_signal_tool as est
import pipeline_io
import portfolio_gex_field as gex
import portfolio_vix as vix
import run_cycle
from tests import test_daily_safety as tds
from tests import test_run_cycle as trc
from tests.test_international_fallback import _load_functions

RUN_TS = "2026-10-05T16:40:12-05:00"
# Contract v1 portfolios: 2 months (quadratic utility default) and 1 month.
TWO_MONTHS = {"run_ts": RUN_TS, "horizon_days": 61, "horizon_end": "2026-12-05",
              "params": {"horizon_months": 2}}
ONE_MONTH = {"run_ts": RUN_TS, "horizon_days": 31, "horizon_end": "2026-11-05",
             "params": {"horizon_months": 1}}
NO_ENV = {pipeline_io.HORIZON_ENV: ""}


def _expiries(today, offsets):
    return [(today + timedelta(days=d)).isoformat() for d in offsets]


def _contracts_endpoint(expirations, calls=None):
    """Fake /v3/reference/options/contracts: gte/lte/order/limit on expiration_date."""
    def query(params):
        if calls is not None:
            calls.append(dict(params))
        gte, lte = params.get("expiration_date.gte"), params.get("expiration_date.lte")
        dates = sorted(d for d in expirations
                       if (gte is None or d >= gte) and (lte is None or d <= lte))
        if params.get("order") == "desc":
            dates = dates[::-1]
        return {"results": [{"expiration_date": d} for d in dates[:int(params.get("limit", 1000))]]}
    return query


# ------------------------------------------------------------------------------
# pipeline_io
# ------------------------------------------------------------------------------

class PortfolioHorizonDaysTests(unittest.TestCase):
    def test_full_and_remaining_for_two_and_one_month(self):
        today = date(2026, 11, 4)
        self.assertEqual(pipeline_io.portfolio_horizon_days(TWO_MONTHS, today, "full"), 61)
        self.assertEqual(pipeline_io.portfolio_horizon_days(TWO_MONTHS, today, "remaining"), 31)
        self.assertEqual(pipeline_io.portfolio_horizon_days(ONE_MONTH, date(2026, 10, 7), "full"), 31)
        self.assertEqual(pipeline_io.portfolio_horizon_days(ONE_MONTH, date(2026, 10, 7)), 29)

    def test_end_derived_from_run_date_when_horizon_end_is_missing(self):
        only_days = {"run_ts": RUN_TS, "horizon_days": 61}
        self.assertEqual(pipeline_io.portfolio_horizon_days(only_days, date(2026, 11, 4)), 31)
        only_months = {"run_ts": RUN_TS, "params": {"horizon_months": 1}}
        self.assertEqual(pipeline_io.portfolio_horizon_days(only_months, date(2026, 10, 5), "full"), 31)
        self.assertEqual(pipeline_io.portfolio_horizon_days(only_months, date(2026, 10, 25)), 11)

    def test_no_horizon_gives_none(self):
        self.assertIsNone(pipeline_io.portfolio_horizon_days({"run_ts": RUN_TS}, date(2026, 10, 7)))
        self.assertIsNone(pipeline_io.portfolio_horizon_days(None, date(2026, 10, 7), "full"))
        fallback = pipeline_io._fallback_result({"AAA": 1.0}, "test")
        self.assertIsNone(pipeline_io.portfolio_horizon_days(fallback, date(2026, 10, 7)))

    def test_load_portfolio_surfaces_the_horizon(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "p.json")
            path.write_text(json.dumps(dict(TWO_MONTHS, schema_version=1, optimizer="quadratic_utility",
                                            weights={"AAA": 1.0})), encoding="utf-8")
            with mock.patch.dict(os.environ, {"PORTFOLIO_FILE": str(path)}):
                meta = pipeline_io.load_portfolio({"ZZZ": 1.0})
        self.assertEqual(meta["horizon_days"], 61)
        self.assertEqual(meta["horizon_end"], "2026-12-05")
        self.assertEqual(meta["horizon_months"], 2)
        self.assertEqual(pipeline_io.portfolio_horizon_days(meta, date(2026, 11, 4)), 31)

    def test_invalid_mode_raises(self):
        with self.assertRaises(ValueError):
            pipeline_io.portfolio_horizon_days(TWO_MONTHS, date(2026, 11, 4), "half")


class ResolveHorizonTests(unittest.TestCase):
    def test_default_without_portfolio(self):
        out = pipeline_io.resolve_horizon(None, 42, env=NO_ENV)
        self.assertEqual((out["days"], out["source"], out["via"]), (42, "default", None))
        self.assertFalse(out["floored"])

    def test_portfolio_file_by_mode(self):
        remaining = pipeline_io.resolve_horizon(TWO_MONTHS, 42, "remaining", date(2026, 11, 4), env=NO_ENV)
        full = pipeline_io.resolve_horizon(TWO_MONTHS, 30, "full", date(2026, 11, 4), env=NO_ENV)
        self.assertEqual((remaining["days"], remaining["source"], remaining["via"]), (31, "portfolio", "file"))
        self.assertEqual(full["days"], 61)
        self.assertEqual(full["horizon_end"], "2026-12-05")

    def test_env_from_run_cycle_wins(self):
        out = pipeline_io.resolve_horizon(TWO_MONTHS, 42, env={pipeline_io.HORIZON_ENV: "20"})
        self.assertEqual((out["days"], out["source"], out["via"]), (20, "portfolio", "env"))

    def test_invalid_env_is_ignored(self):
        with mock.patch("builtins.print"):
            out = pipeline_io.resolve_horizon(None, 29, env={pipeline_io.HORIZON_ENV: "soon"})
        self.assertEqual((out["days"], out["source"]), (29, "default"))

    def test_min_days_floor(self):
        late = pipeline_io.resolve_horizon(ONE_MONTH, 29, "remaining", date(2026, 11, 2), env=NO_ENV)
        self.assertEqual((late["raw_days"], late["days"], late["floored"]), (3, pipeline_io.MIN_OPTION_DAYS, True))
        expired = pipeline_io.resolve_horizon(ONE_MONTH, 29, "remaining", date(2026, 11, 20), env=NO_ENV)
        self.assertEqual(expired["days"], 7)
        self.assertEqual(pipeline_io.MIN_OPTION_DAYS, 7)


class PickExpirationTests(unittest.TestCase):
    TODAY = date(2026, 10, 7)

    def _offsets(self, *days):
        return [self.TODAY + timedelta(days=d) for d in days]

    def test_closest_to_target(self):
        exps = self._offsets(3, 10, 24, 31, 59, 66)
        self.assertEqual(pipeline_io.pick_expiration(exps, self.TODAY, 29), (self.TODAY + timedelta(days=31), False))
        self.assertEqual(pipeline_io.pick_expiration(exps, self.TODAY, 61)[0], self.TODAY + timedelta(days=59))

    def test_floor_skips_short_expiries(self):
        exps = self._offsets(3, 12)
        chosen, fallback = pipeline_io.pick_expiration(exps, self.TODAY, 4)
        self.assertEqual(chosen, self.TODAY + timedelta(days=12))
        self.assertFalse(fallback)

    def test_fallback_to_nearest_available(self):
        chosen, fallback = pipeline_io.pick_expiration(self._offsets(2, 5), self.TODAY, 30)
        self.assertEqual(chosen, self.TODAY + timedelta(days=5))
        self.assertTrue(fallback)
        self.assertEqual(pipeline_io.pick_expiration([], self.TODAY, 30), (None, False))

    def test_tie_goes_to_earlier_and_strings_are_accepted(self):
        exps = [d.isoformat() for d in self._offsets(26, 34)]
        self.assertEqual(pipeline_io.pick_expiration(exps, self.TODAY, 30)[0], self.TODAY + timedelta(days=26))


# ------------------------------------------------------------------------------
# Per-script expiry selection
# ------------------------------------------------------------------------------

OFFSETS = (3, 10, 17, 24, 31, 45, 59, 66, 94)


class RiskScoreExpiryTests(unittest.TestCase):
    def _fn(self, offsets):
        import datetime as dt
        self.today = dt.date.today()
        self.logs = []
        query = _contracts_endpoint(_expiries(self.today, offsets))
        ns = _load_functions("portfolio_risk_score_leverage.py", {"get_target_expiration"}, {
            "dt": dt, "to_polygon": lambda t: t, "log_warn": self.logs.append,
            "polygon_get": lambda path, params=None, api_key=None: query(params),
            "pick_expiration": pipeline_io.pick_expiration, "MIN_OPTION_DAYS": pipeline_io.MIN_OPTION_DAYS,
        })
        return ns["get_target_expiration"]

    def test_default_one_month_and_two_month_horizon(self):
        fn = self._fn(OFFSETS)
        self.assertEqual(fn("GLD", 29, "k")["days_to_expiry"], 31)
        self.assertEqual(fn("GLD", 61, "k")["days_to_expiry"], 59)
        self.assertEqual(fn("GLD", 31, "k")["days_to_expiry"], 31)

    def test_min_days_floor_and_no_chain_fallback(self):
        self.assertEqual(self._fn((3, 12))("GLD", 4, "k")["days_to_expiry"], 12)
        out = self._fn((2, 5))("GLD", 30, "k")
        self.assertEqual(out["days_to_expiry"], 5)
        self.assertTrue(any(">= 7" in msg for msg in self.logs))
        self.assertIsNone(self._fn(())("GLD", 30, "k")["expiration"])

    def test_default_horizon_is_unchanged(self):
        source = Path("portfolio_risk_score_leverage.py").read_text(encoding="utf-8")
        self.assertIn('HORIZON = resolve_horizon(_PORTFOLIO_META, _default_options_days, mode="remaining")', source)
        self.assertEqual(round(1 * 21 * 7 / 5), 29)
        self.assertIn('_senal_riesgo_data["horizon"] = dict(HORIZON, trading_days=horizon_days)', source)


class ActiveManagementExpiryTests(unittest.TestCase):
    def _fn(self, offsets):
        self.today = date.today()
        query = _contracts_endpoint(_expiries(self.today, offsets))
        client = SimpleNamespace(get=lambda url, params=None: query(params))
        ns = _load_functions("active_management.py", {"select_target_expiration"}, {
            "date": date, "datetime": datetime, "timedelta": timedelta, "warnings": warnings,
            "polygon_api_key": "k", "polygon_client": lambda api_key=None: client,
            "POLYGON_BASE_URL": "https://example", "to_polygon": lambda t: t,
            "expiration_search_window_days": 20,
            "pick_expiration": pipeline_io.pick_expiration, "MIN_OPTION_DAYS": pipeline_io.MIN_OPTION_DAYS,
        })
        return ns["select_target_expiration"]

    def days(self, value):
        return (value - self.today).days

    def test_calendar_days_target(self):
        fn = self._fn(OFFSETS)
        self.assertEqual(self.days(fn("GLD", math.ceil(30 * 7 / 5))), 45)   # default 42
        self.assertEqual(self.days(fn("GLD", 31)), 31)                       # 1 month left
        self.assertEqual(self.days(fn("GLD", 61)), 59)                       # 2 months left

    def test_floor_and_fallback(self):
        self.assertEqual(self.days(self._fn((3, 12))("GLD", 2)), 12)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            self.assertEqual(self.days(self._fn((2, 5))("GLD", 30)), 5)
            self.assertIsNone(self._fn(())("GLD", 30))
        self.assertEqual(len(caught), 2)

    def test_default_is_42_calendar_days(self):
        source = Path("active_management.py").read_text(encoding="utf-8")
        self.assertIn("DEFAULT_HORIZON_TRADING_DAYS = 30", source)
        self.assertIn('_senal_activa["horizon"] = HORIZON', source)


class EntryExpiryTests(unittest.TestCase):
    def _select(self, offsets, horizon):
        self.today = datetime.utcnow().date()
        self.calls = []
        query = _contracts_endpoint(_expiries(self.today, offsets), self.calls)
        client = SimpleNamespace(get=lambda url, params: query(params))
        with mock.patch.object(est, "polygon", lambda: client), mock.patch("builtins.print"):
            chosen = est.seleccionar_vencimiento_objetivo("GLD", horizon)
        return None if chosen is None else (chosen - self.today).days

    def test_window_centred_on_horizon(self):
        self.assertEqual(self._select(OFFSETS, 30), 31)
        self.assertEqual(self._select(OFFSETS, 61), 59)
        desc = [c for c in self.calls if c.get("order") == "desc"][0]
        self.assertEqual(desc["expiration_date.gte"], str(self.today + timedelta(days=41)))
        asc = [c for c in self.calls if c.get("order") == "asc"][0]
        self.assertEqual(asc["expiration_date.lte"], str(self.today + timedelta(days=81)))

    def test_window_never_below_min_days(self):
        self._select(OFFSETS, 20)
        desc = [c for c in self.calls if c.get("order") == "desc"][0]
        self.assertEqual(desc["expiration_date.gte"], str(self.today + timedelta(days=7)))
        self.assertEqual(self._select((3, 12), 2), 12)

    def test_no_chain_in_window_falls_back_to_nearest_available(self):
        self.assertEqual(self._select((120,), 30), 120)
        self.assertEqual(self._select((3,), 30), 3)
        self.assertIsNone(self._select((), 30))

    def test_default_without_portfolio(self):
        self.assertEqual(est.HORIZON_DIAS_DEFAULT, 30)
        out = pipeline_io.resolve_horizon(None, est.HORIZON_DIAS_DEFAULT, mode="full", env=NO_ENV)
        self.assertEqual((out["days"], out["source"]), (30, "default"))


class EntrySignalRecordsHorizonTests(unittest.TestCase):
    setUp = tds.EntryTrancheLockTests.setUp
    run_entry = tds.EntryTrancheLockTests.run_entry
    signal = tds.EntryTrancheLockTests.signal

    def test_new_and_locked_signals_carry_the_horizon(self):
        horizon = pipeline_io.resolve_horizon(TWO_MONTHS, 30, "full", env=NO_ENV)
        with mock.patch.object(est, "HORIZON", horizon):
            first = self.run_entry(tds.DAY1)["data"]
            locked = self.run_entry(tds.DAY1)["data"]
        self.assertEqual(first["horizon"]["days"], 61)
        self.assertEqual(first["horizon"]["source"], "portfolio")
        self.assertEqual(locked["signal"], "already_prepared_today")
        self.assertEqual(locked["horizon"]["days"], 61)


class GexHorizonTests(unittest.TestCase):
    def _fetch(self, **kwargs):
        calls = []

        def paginate(url, params, max_pages=None):
            calls.append(dict(params))
            return []

        client = SimpleNamespace(paginate=paginate)
        with mock.patch.object(gex, "polygon", lambda: client), mock.patch("builtins.print"):
            out = gex.get_polygon_options_data("GLD", 100.0, **kwargs)
        self.assertTrue(out.empty)
        today = datetime.utcnow().date()
        return [(date.fromisoformat(c["expiration_date.lte"]) - today).days for c in calls]

    def test_chain_capped_at_horizon_with_default_fallback(self):
        self.assertEqual(self._fetch(horizon_days=31), [31, 60])
        self.assertEqual(self._fetch(horizon_days=61), [61])
        self.assertEqual(self._fetch(horizon_months=2), [60])

    def test_defaults_and_floor(self):
        self.assertEqual(gex.DEFAULT_HORIZON_DAYS, 60)
        self.assertEqual(gex.GEX_MIN_HORIZON_DAYS, gex.NEAR_TERM_DAYS_CUTOFF + pipeline_io.MIN_OPTION_DAYS)
        self.assertEqual(gex._horizonte(), (gex.GEX_HORIZON_MONTHS, gex.GEX_HORIZON_DAYS))
        self.assertEqual(gex._horizonte(horizon_days=61)[1], 61)
        late = pipeline_io.resolve_horizon(ONE_MONTH, gex.DEFAULT_HORIZON_DAYS, "remaining",
                                           date(2026, 11, 1), env=NO_ENV, min_days=gex.GEX_MIN_HORIZON_DAYS)
        self.assertEqual(late["days"], 14)


class VixHorizonTests(unittest.TestCase):
    def test_interpolate_days_matches_30d_and_is_flat_for_flat_variance(self):
        engine = vix.CBOEVarianceEngine
        args = (24 / 365, 0.04, 31 / 365, 0.05)
        self.assertAlmostEqual(engine.interpolate_days(*args, 30.0), engine.interpolate_30d(*args))
        self.assertAlmostEqual(engine.interpolate_days(59 / 365, 0.04, 66 / 365, 0.04, 61.0), 0.04)

    def test_bracket_pair(self):
        fits = [SimpleNamespace(T=d / 365, variance=v) for d, v in ((66, 4), (24, 1), (59, 3), (31, 2))]
        near, nxt = vix.bracket_pair(fits, 30.0)
        self.assertEqual((near.variance, nxt.variance), (1, 2))
        near, nxt = vix.bracket_pair(fits, 61.0)
        self.assertEqual((near.variance, nxt.variance), (3, 4))
        near, nxt = vix.bracket_pair(fits[:1], 61.0)
        self.assertIsNone(nxt)

    def test_horizon_variance_uses_its_own_bracket(self):
        single = SimpleNamespace(engine=vix.CBOEVarianceEngine(r=0.04))
        fits = [SimpleNamespace(T=d / 365, variance=v) for d, v in ((24, 0.04), (31, 0.04), (59, 0.09), (66, 0.09))]
        self.assertAlmostEqual(vix.SingleAssetVIX.horizon_variance(single, fits, 61.0), 0.09)
        self.assertAlmostEqual(vix.SingleAssetVIX.horizon_variance(single, fits, 30.0), 0.04)

    def test_expiry_selection_adds_horizon_pair(self):
        today = pd.Timestamp.now(tz="UTC").date()
        exps = _expiries(today, OFFSETS)
        base = vix.select_cboe_expiries(exps, 7.0)
        self.assertEqual(base, _expiries(today, (24, 31)))
        self.assertEqual(vix.select_expiries_for(exps, 7.0, 30.0), base)
        self.assertEqual(vix.select_expiries_for(exps, 7.0, None), base)
        self.assertEqual(vix.select_expiries_for(exps, 7.0, 61.0), _expiries(today, (24, 31, 59, 66)))
        self.assertEqual(vix.select_expiries_for(_expiries(today, (3, 10, 40)), 7.0, 30.0),
                         _expiries(today, (10, 40)))

    def test_signal_carries_horizon_reading(self):
        results = {
            "breakdown": pd.DataFrame({"ticker": ["GLD"], "peso": [1.0], "VIX_individual": [18.0],
                                       "sigma_30d": [0.18], "MCR": [0.18], "CTR": [0.18],
                                       "CTR_VIX_pts": [18.0], "CTR_%": [100.0]}).set_index("ticker"),
            "metrics": {"sigma_portfolio_30d": 0.18}, "vix": 18.0, "source": "synthetic",
            "excluded": [],
            "horizon": {"days": 61.0, "vix_portfolio": 20.0, "sigma_portfolio_horizon": 0.0817,
                        "by_ticker": {"GLD": 20.0}},
        }
        cfg = SimpleNamespace(vol_method="svi", corr_method="ewma", r=0.045, horizon_days=61.0)
        data = vix._senal_vix(results, cfg)
        self.assertEqual(data["vix_portfolio"], 18.0)
        self.assertEqual(data["vix_portfolio_horizon"], 20.0)
        self.assertEqual(data["horizon"]["days"], 61.0)
        self.assertIn(data["horizon"]["source"], ("portfolio", "default"))
        self.assertEqual(data["holdings"][0]["vix_horizon"], 20.0)
        self.assertIsNone(vix._senal_vix(dict(results, horizon=None), cfg)["vix_portfolio_horizon"])

    def test_calculator_runs_both_readings_on_synthetic_chains(self):
        with tempfile.TemporaryDirectory() as tmp, warnings.catch_warnings():
            warnings.simplefilter("ignore")
            def run(days):
                cfg = vix.VIXConfig(tickers=["AAA", "BBB"], weights=[0.6, 0.4], source="synthetic",
                                    verbose=False, html_file=os.path.join(tmp, "r.html"),
                                    show_plot=False, horizon_days=days)
                return vix.PortfolioVIXCalculator(cfg).run()
            at_30, at_61 = run(30.0), run(61.0)
        self.assertAlmostEqual(at_30["horizon"]["vix_portfolio"], at_30["vix"])
        self.assertEqual(at_61["horizon"]["days"], 61.0)
        self.assertGreater(at_61["horizon"]["vix_portfolio"], 0)
        self.assertAlmostEqual(at_61["horizon"]["sigma_portfolio_horizon"],
                               at_61["horizon"]["vix_portfolio"] / 100 * math.sqrt(61 / 365))

    def test_default_horizon_is_30_days(self):
        out = pipeline_io.resolve_horizon(None, 30, env=NO_ENV)
        self.assertEqual(out["days"], 30)


# ------------------------------------------------------------------------------
# run_cycle
# ------------------------------------------------------------------------------

def _loaded(payload):
    return {"run_ts": payload["run_ts"], "horizon_days": payload.get("horizon_days"),
            "horizon_end": date.fromisoformat(payload["horizon_end"]) if payload.get("horizon_end") else None,
            "horizon_months": (payload.get("params") or {}).get("horizon_months")}


class StepHorizonTests(unittest.TestCase):
    def test_per_step_mode_two_months(self):
        port, as_of = _loaded(TWO_MONTHS), date(2026, 11, 4)
        days = {s: run_cycle.step_horizon_days(s, port, as_of) for s in run_cycle.ALL_STEPS}
        self.assertEqual(days, {
            "fundamental_analysis": None, "portfolio_risk_score_leverage": 31,
            "portfolio_gex_field": 31, "portfolio_vix": 31, "entry_signal_tool": 61,
            "active_management": 31,
        })

    def test_per_step_mode_one_month(self):
        port, as_of = _loaded(ONE_MONTH), date(2026, 10, 7)
        self.assertEqual(run_cycle.step_horizon_days("entry_signal_tool", port, as_of), 31)
        self.assertEqual(run_cycle.step_horizon_days("portfolio_vix", port, as_of), 29)

    def test_no_horizon_in_portfolio(self):
        port = {"run_ts": RUN_TS, "horizon_days": None, "horizon_end": None}
        self.assertIsNone(run_cycle.step_horizon_days("portfolio_vix", port, date(2026, 10, 7)))

    def test_step_environment_sets_or_clears_the_variable(self):
        with mock.patch.dict(os.environ, {pipeline_io.HORIZON_ENV: "99"}):
            env = run_cycle.step_environment("/p.json", "/s", "portfolio_vix", date(2026, 10, 7), False, 29)
            self.assertEqual(env[pipeline_io.HORIZON_ENV], "29")
            env = run_cycle.step_environment("/p.json", "/s", "portfolio_vix", date(2026, 10, 7))
            self.assertNotIn(pipeline_io.HORIZON_ENV, env)

    def test_load_portfolio_file_keeps_horizon_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "p.json")
            path.write_text(json.dumps(trc._portfolio(params={"horizon_months": 2})), encoding="utf-8")
            port = run_cycle.load_portfolio_file(str(path))
        self.assertEqual((port["horizon_days"], port["horizon_months"]), (61, 2))
        self.assertEqual(run_cycle._portfolio_view(port)["horizon_days"], 61)


class RunCyclePassesHorizonTests(trc.CycleTestCase):
    def _seen(self, result, script):
        payload = json.loads(Path(result["signals"], f"{script}.json").read_text(encoding="utf-8"))
        return payload["data"]["env_seen"]["PORTFOLIO_HORIZON_DAYS"]

    def test_daily_cycle_two_month_portfolio(self):
        result = self.invoke("--date", "2026-11-04", env={pipeline_io.HORIZON_ENV: "5"})
        self.assertEqual(result["code"], 0, result["stderr"])
        self.assertEqual(self._seen(result, "entry_signal_tool"), "61")
        for script in ("portfolio_risk_score_leverage", "portfolio_gex_field", "portfolio_vix"):
            self.assertEqual(self._seen(result, script), "31", script)
        self.assertIsNone(self._seen(result, "fundamental_analysis"))
        steps = {s["script"]: s.get("horizon_days") for s in self.summary(result)["steps"]}
        self.assertEqual(steps["entry_signal_tool"], 61)
        self.assertEqual(steps["portfolio_vix"], 31)

    def test_daily_cycle_one_month_portfolio(self):
        payload = trc._portfolio(horizon_days=31, horizon_end="2026-11-05", params={"horizon_months": 1})
        result = self.invoke("--date", "2026-10-07", payload=payload)
        self.assertEqual(result["code"], 0, result["stderr"])
        self.assertEqual(self._seen(result, "entry_signal_tool"), "31")
        self.assertEqual(self._seen(result, "portfolio_vix"), "29")

    def test_weekly_cycle_active_management(self):
        result = self.invoke("--weekly", "--force", "--date", "2026-11-04")
        self.assertEqual(result["code"], 0, result["stderr"])
        self.assertEqual(self._seen(result, "active_management"), "31")

    def test_portfolio_without_horizon_leaves_steps_on_defaults(self):
        payload = trc._portfolio(horizon_days=None, horizon_end=None)
        result = self.invoke("--date", "2026-10-07", payload=payload, env={pipeline_io.HORIZON_ENV: "5"})
        self.assertEqual(result["code"], 0, result["stderr"])
        self.assertIsNone(self._seen(result, "portfolio_vix"))
        self.assertIsNone(self._seen(result, "entry_signal_tool"))


if __name__ == "__main__":
    unittest.main()
