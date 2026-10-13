"""No-network tests: the entry cycle day follows entry_phase.day (NYSE sessions since
entry_start_date), an empty tranche or an older fills signal_run_ts never holds it back,
and day 5 completes 100% of the ORIGINAL target from the real net holdings.

Fixtures mirror the quadratic_utility portfolio whose day 3 (2026-10-12) was an empty
tranche (state left at dia_ciclo=2, pending_cycle_day=3). Days 1-4 keep the normal
cumulative-% schedule; net holdings only stop an overbuy there.
"""

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd

import entry_signal_tool as est
import pipeline_io

META = {
    "weights": {"AVGO": 0.30, "AMZN": 0.20, "LLY": 0.20, "META": 0.10, "NTES": 0.10, "ORLY": 0.10},
    "portfolio_source": "/pipeline/portfolio/portfolio_latest.json",
    "portfolio_run_ts": "2026-10-08T12:12:53-05:00",
    "portfolio_optimizer": "quadratic_utility",
}
TARGETS = dict(META["weights"])
FOLDER = "quadratic_utility_20261008T121253"
FILLS_NAME = "fills_quadratic_utility_20261008T121253.json"
SELL_NAME = "sell_fills_quadratic_utility_20261008T121253.json"
DAY1_TS = "2026-10-08T13:00:00-05:00"
DAY2_TS = "2026-10-09T13:00:00-05:00"
DAY3_TS = "2026-10-13T09:11:30-05:00"
# pct_ya_invertido that the attached quadratic_utility state recorded after day 2.
STATE_PCT = {"AVGO": 0.692, "AMZN": 0.685, "LLY": 0.652, "META": 0.656, "NTES": 0.614, "ORLY": 0.67}
SCHEDULE_PCT = 0.5  # what the score asks for today: below every stored %, so MANTENER

_ENTRY_ENV = ("ENTRY_CYCLE_DAY", "ENTRY_INVESTED_PCT", "ENTRY_FORCE_NEW_TRANCHE",
              "ENTRY_STATE_FILE", "PIPELINE_DIR", "CYCLE_DATE", "RISK_FREE_RATE", "PORTFOLIO_CAPITAL")


def _row(ticker, pct=SCHEDULE_PCT):
    return {
        "fecha": pd.Timestamp("2026-10-13"), "ticker": ticker, "spot": 100.0,
        "score_conviccion": 60.0, "pct_entrada_sugerido": pct, "tier": "native",
        "analysis_ticker": ticker, "proxy_etf": None, "modo_entrada": "native",
    }


class EntryCalendarDayBase(unittest.TestCase):
    schedule_pct = SCHEDULE_PCT

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
            ("TICKERS", list(TARGETS)),
            ("PESOS_OBJETIVO", dict(TARGETS)),
            ("RECORTADOS_POR_ROTACION", set()),
            ("HIST_PATH", str(self.root / "history.csv")),
            ("LEGACY_STATE_PATH", str(self.root / "entry_state.json")),
            ("graficar_resumen", lambda resumen: None),
            ("calcular_fila_instrumento",
             lambda ticker, hist, warns, excluded: _row(ticker, self.schedule_pct)),
        ):
            patch = mock.patch.object(est, name, value)
            patch.start()
            self.addCleanup(patch.stop)

    def run_entry(self, day, *argv, **env):
        with mock.patch.dict(os.environ, {"CYCLE_DATE": day, **env}):
            with redirect_stdout(io.StringIO()):
                est.main(list(argv))
        return json.loads((self.signals / FOLDER / "entry_signal_tool.json").read_text(encoding="utf-8"))

    def state(self):
        return json.loads(Path(pipeline_io.entry_state_path(META)).read_text(encoding="utf-8"))

    def write_state(self, **overrides):
        state = {
            "ciclo": 1, "dia_ciclo": 2, "ciclo_cerrado": False, "ultima_actualizacion": "2026-10-09",
            "pending_signal_run_ts": None, "pending_cycle_day": None, "pending_cycle": None,
            "pending_targets": {}, "pending_cash": {}, "pending_decisions": {},
            "activos": {t: {"pct_ya_invertido": pct, "pct_cash_consolidado": 0.0, "decision_final": None}
                        for t, pct in STATE_PCT.items()},
            "portfolio": {"optimizer": META["portfolio_optimizer"], "run_ts": META["portfolio_run_ts"]},
            "entry_start_date": "2026-10-08", "pausas_entrada": {},
        }
        state.update(overrides)
        path = Path(pipeline_io.entry_state_path(META))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state), encoding="utf-8")
        return state

    def stale_empty_pending(self):
        """The state the day-3 empty tranche left behind (attached quadratic_utility state)."""
        return self.write_state(
            pending_signal_run_ts=DAY3_TS, pending_cycle_day=3, pending_cycle=1,
            last_tranche_date="2026-10-13",
            last_tranche={"entries": [], "waiting": [{"ticker": t} for t in TARGETS],
                          "cycle_day": 3, "cycle": 1, "signal_run_ts": DAY3_TS},
        )

    def write_fills(self, held=None, sold=None):
        """Cumulative buy file (days 1 and 2) so that net weight / target == ``held`` (default: state)."""
        held = held or STATE_PCT
        fills = []
        for ticker, pct in held.items():
            weight = pct * TARGETS[ticker]
            for ts, part in ((DAY1_TS, 0.5), (DAY2_TS, 0.5)):
                fills.append({"ticker": ticker, "action": "BUY", "filled_weight": weight * part,
                              "filled_qty": 10, "price": 100.0, "status": "filled",
                              "deal_id": f"{ticker}-{ts}", "fill_ts": ts, "signal_run_ts": ts})
        (self.executions / FILLS_NAME).write_text(json.dumps({
            "schema_version": 1, "signal_run_ts": DAY2_TS, "executed_ts": "2026-10-09T15:00:00-05:00",
            "fills": fills,
        }), encoding="utf-8")
        if sold:
            (self.executions / SELL_NAME).write_text(json.dumps({
                "schema_version": 1, "script": "active_management", "portfolio_optimizer": "quadratic_utility",
                "portfolio_run_ts": META["portfolio_run_ts"], "executed_ts": "2026-10-12T15:00:00-05:00",
                "fills": [{"ticker": t, "action": "SELL", "filled_weight": w, "filled_qty": 5,
                           "price": 100.0, "status": "filled", "deal_id": f"sell-{t}",
                           "fill_ts": "2026-10-12T15:00:00-05:00"} for t, w in sold.items()],
            }), encoding="utf-8")

    @staticmethod
    def entries(payload):
        return {e["ticker"]: e for e in payload["data"]["entries"]}


class EmptyTrancheTests(EntryCalendarDayBase):
    def test_empty_tranche_closes_its_day_and_the_next_day_is_day_four(self):
        self.write_state(last_tranche_date=None, last_tranche=None, entry_start_date="2026-10-08")
        self.write_fills()
        day3 = self.run_entry("2026-10-12")
        self.assertEqual(day3["data"]["cycle_day"], 3)
        self.assertEqual(day3["data"]["entries"], [])
        state = self.state()
        self.assertEqual(state["dia_ciclo"], 3)
        self.assertIsNone(state["pending_signal_run_ts"])
        self.assertEqual(state["last_tranche_date"], "2026-10-12")
        self.assertFalse(state["ciclo_cerrado"])

        day4 = self.run_entry("2026-10-13")
        self.assertEqual(day4["data"]["signal"], "new_tranche")
        self.assertEqual(day4["data"]["cycle_day"], 4)
        self.assertEqual(self.state()["dia_ciclo"], 4)

    def test_empty_tranche_same_day_is_still_locked(self):
        self.write_state()
        self.write_fills()
        self.run_entry("2026-10-12")
        again = self.run_entry("2026-10-12")
        self.assertEqual(again["data"]["signal"], "already_prepared_today")
        self.assertEqual(again["data"]["tranche_status"], "executed")
        self.assertEqual(self.state()["dia_ciclo"], 3)

    def test_helper_closes_only_a_pending_tranche_without_orders(self):
        staged = pipeline_io.stage_pending_entry(
            {"ciclo": 1, "dia_ciclo": 2, "ultima_actualizacion": "2026-10-09"}, "ts-3", 3, 1,
            prepared_date="2026-10-12", tranche={"entries": [], "waiting": [], "cycle_day": 3, "cycle": 1})
        self.assertTrue(pipeline_io.pending_is_empty_tranche(staged))
        closed = pipeline_io.close_empty_tranche(staged, 5, today="2026-10-12")
        self.assertEqual((closed["dia_ciclo"], closed["ultima_actualizacion"]), (3, "2026-10-12"))
        self.assertIsNone(closed["pending_signal_run_ts"])
        self.assertEqual(pipeline_io.tranche_lock(closed, "2026-10-12")["status"], "executed")

        with_orders = pipeline_io.stage_pending_entry(
            {}, "ts-3", 3, 1, {"AVGO": 0.3}, prepared_date="2026-10-12",
            tranche={"entries": [{"ticker": "AVGO"}], "cycle_day": 3, "cycle": 1})
        self.assertFalse(pipeline_io.pending_is_empty_tranche(with_orders))
        estado, status = pipeline_io.reconcile_pending_entry(with_orders, None, 5, "2026-10-13")
        self.assertEqual(status, "stale")
        self.assertIs(estado, with_orders)

    def test_late_confirmation_of_an_older_day_does_not_move_the_day_back(self):
        staged = pipeline_io.stage_pending_entry(
            {"ciclo": 1, "dia_ciclo": 4, "ultima_actualizacion": "2026-10-13"}, "ts-3", 3, 1, {"AVGO": 0.3})
        updated, applied = pipeline_io.apply_entry_fills(
            staged, {"signal_run_ts": "ts-3", "fills": [], "executed_ts": "2026-10-13"}, 5)
        self.assertTrue(applied)
        self.assertEqual(updated["dia_ciclo"], 4)


class StalePendingTests(EntryCalendarDayBase):
    def test_stale_pending_and_old_fills_reconcile_to_calendar_day_four(self):
        # Reproduces 2026-10-13: state dia_ciclo=2, pending day 3 (empty), fills of 10-09.
        self.stale_empty_pending()
        self.write_fills()
        payload = self.run_entry("2026-10-13")
        data = payload["data"]
        self.assertEqual(data["signal"], "new_tranche")
        self.assertEqual(data["cycle_day"], 4)
        self.assertFalse(any("fills ignored" in w or "stale fills" in w for w in payload["warnings"]))
        self.assertTrue(any("tranche of 2026-10-13 was for cycle day 3" in w for w in payload["warnings"]))
        state = self.state()
        self.assertEqual(state["dia_ciclo"], 4)
        self.assertIsNone(state["pending_signal_run_ts"])
        self.assertEqual(state["last_tranche"]["cycle_day"], 4)

    def test_unconfirmed_tranche_with_orders_does_not_pin_the_day(self):
        self.schedule_pct = 1.0
        self.write_state(ultima_actualizacion="2026-10-08", dia_ciclo=1)
        self.write_fills({t: 0.3 for t in TARGETS})
        first = self.run_entry("2026-10-12")
        self.assertEqual(first["data"]["cycle_day"], 3)
        self.assertTrue(first["data"]["entries"])
        # The executor never confirms it (only older fills exist): next session is day 4.
        second = self.run_entry("2026-10-13")
        self.assertEqual(second["data"]["cycle_day"], 4)
        self.assertTrue(any("stale fills" in w for w in second["warnings"]))

    def test_state_ahead_of_the_calendar_never_runs_an_earlier_day(self):
        state = {"ciclo": 1, "dia_ciclo": 4, "ciclo_cerrado": False, "ultima_actualizacion": "2026-10-10"}
        self.assertEqual(pipeline_io.suggest_cycle_day(state, 5, calendar_day=3, today="2026-10-12"), 5)
        day, warn = pipeline_io.resolve_cycle_day(2, state, 5, calendar_day=3, today="2026-10-12")
        self.assertEqual(day, 4)
        self.assertIn("behind", warn)

    def test_state_behind_the_calendar_catches_up(self):
        state = {"ciclo": 1, "dia_ciclo": 2, "ciclo_cerrado": False, "ultima_actualizacion": "2026-10-09"}
        self.assertEqual(pipeline_io.suggest_cycle_day(state, 5, calendar_day=4, today="2026-10-13"), 4)
        self.assertEqual(pipeline_io.suggest_cycle_day(state, 5, calendar_day=9, today="2026-10-20"), 5)
        self.assertEqual(pipeline_io.suggest_cycle_day(state, 5), 3)  # legacy call is unchanged
        later_cycle = dict(state, ciclo=2)
        self.assertEqual(pipeline_io.suggest_cycle_day(later_cycle, 5, calendar_day=9), 3)
        fresh = {"ultima_actualizacion": None, "ciclo": 1}
        self.assertEqual(pipeline_io.suggest_cycle_day(fresh, 5, calendar_day=1), 1)


class ForcedDayThenNormalDayTests(EntryCalendarDayBase):
    def test_forced_day_four_then_next_session_is_day_five(self):
        self.stale_empty_pending()
        self.write_fills()
        forced = self.run_entry("2026-10-13", ENTRY_CYCLE_DAY="4")
        self.assertEqual(forced["data"]["cycle_day"], 4)
        self.assertEqual(self.state()["dia_ciclo"], 4)

        day5 = self.run_entry("2026-10-14")
        self.assertEqual(day5["data"]["cycle_day"], 5)
        self.assertEqual(day5["data"]["cycle"], 1)
        self.assertTrue(all(e["signal"] == "cycle_close" for e in day5["data"]["entries"]))

    def test_leftover_entry_cycle_day_env_cannot_pin_day_four(self):
        self.stale_empty_pending()
        self.write_fills()
        self.run_entry("2026-10-13", ENTRY_CYCLE_DAY="4")
        day5 = self.run_entry("2026-10-14", ENTRY_CYCLE_DAY="4")
        self.assertEqual(day5["data"]["cycle_day"], 5)
        self.assertTrue(any("behind entry day 5" in w for w in day5["warnings"]))

    def test_attached_state_without_any_force_goes_straight_to_day_five(self):
        # State untouched since 10-13 (pending empty day 3, dia_ciclo=2): day 5 on 10-14.
        self.stale_empty_pending()
        self.write_fills()
        day5 = self.run_entry("2026-10-14")
        self.assertEqual(day5["data"]["cycle_day"], 5)
        self.assertEqual(day5["data"]["cycle"], 1)


class DayFiveCompletionTests(EntryCalendarDayBase):
    def assert_completes_to_target(self, payload, net_weights):
        entries = self.entries(payload)
        for ticker, target in TARGETS.items():
            bought = entries[ticker]["tranche_weight"] if ticker in entries else 0.0
            self.assertAlmostEqual(net_weights.get(ticker, 0.0) + bought, target, delta=3e-4,
                                   msg=f"{ticker} does not reach its target")

    def test_day_five_buys_the_remainder_from_net_fills_when_state_is_consistent(self):
        self.stale_empty_pending()
        self.write_fills()
        payload = self.run_entry("2026-10-14")
        net = {t: pct * TARGETS[t] for t, pct in STATE_PCT.items()}
        self.assert_completes_to_target(payload, net)
        self.assertEqual(len(payload["data"]["entries"]), len(TARGETS))

    def test_day_five_buys_back_a_sale_the_state_does_not_know_about(self):
        # active_management sold part of AVGO on day 3; state still says 69.2% invested.
        self.stale_empty_pending()
        self.write_fills(sold={"AVGO": 0.10})
        payload = self.run_entry("2026-10-14")
        net = {t: pct * TARGETS[t] for t, pct in STATE_PCT.items()}
        net["AVGO"] -= 0.10
        self.assert_completes_to_target(payload, net)
        avgo = self.entries(payload)["AVGO"]
        self.assertAlmostEqual(avgo["tranche_weight"], 0.30 - net["AVGO"], delta=3e-4)
        self.assertEqual(avgo["target_weight"], 0.30)
        self.assertTrue(any("AVGO" in w and "net holdings" in w for w in payload["warnings"]))

    def test_day_five_with_a_sale_recorded_only_in_quantity(self):
        self.stale_empty_pending()
        self.write_fills()
        (self.executions / SELL_NAME).write_text(json.dumps({
            "schema_version": 1, "portfolio_optimizer": "quadratic_utility",
            "portfolio_run_ts": META["portfolio_run_ts"],
            "fills": [{"ticker": "AVGO", "action": "SELL", "filled_qty": 5, "price": 100.0,
                       "status": "filled", "deal_id": "s1", "fill_ts": "2026-10-12T15:00:00-05:00"}],
        }), encoding="utf-8")
        payload = self.run_entry("2026-10-14")
        bought_weight = STATE_PCT["AVGO"] * TARGETS["AVGO"]
        net = bought_weight * (20 - 5) / 20  # 2 buys of 10 shares, 5 sold
        self.assertAlmostEqual(self.entries(payload)["AVGO"]["tranche_weight"], 0.30 - net, delta=3e-4)

    def test_day_five_ignores_state_drift_in_both_directions(self):
        self.stale_empty_pending()
        held = {"AVGO": 0.40, "AMZN": 0.90, "LLY": 0.05, "META": 1.0, "NTES": 0.3, "ORLY": 0.5}
        self.write_fills(held)  # state says ~65% everywhere
        payload = self.run_entry("2026-10-14")
        self.assert_completes_to_target(payload, {t: p * TARGETS[t] for t, p in held.items()})
        self.assertNotIn("META", self.entries(payload))  # already at 100% of target

    def test_day_five_after_an_all_empty_history_still_completes(self):
        # No fills for LLY at all while others have fills: LLY is bought in full.
        self.stale_empty_pending()
        held = {t: p for t, p in STATE_PCT.items() if t != "LLY"}
        self.write_fills(held)
        payload = self.run_entry("2026-10-14")
        self.assertAlmostEqual(self.entries(payload)["LLY"]["tranche_weight"], TARGETS["LLY"], delta=3e-4)

    def test_day_five_closes_the_cycle_after_fills(self):
        self.stale_empty_pending()
        self.write_fills()
        payload = self.run_entry("2026-10-14")
        (self.executions / FILLS_NAME).write_text(json.dumps({
            "schema_version": 1, "signal_run_ts": payload["run_ts"], "executed_ts": "2026-10-14T15:00:00-05:00",
            "fills": json.loads((self.executions / FILLS_NAME).read_text())["fills"] + [
                {"ticker": e["ticker"], "action": "BUY", "filled_weight": e["tranche_weight"],
                 "status": "filled", "deal_id": f"d5-{e['ticker']}", "fill_ts": "2026-10-14T15:00:00-05:00",
                 "signal_run_ts": payload["run_ts"]} for e in payload["data"]["entries"]],
        }), encoding="utf-8")
        locked = self.run_entry("2026-10-14")
        state = self.state()
        self.assertEqual(state["dia_ciclo"], 5)
        self.assertTrue(state["ciclo_cerrado"])
        for ticker in TARGETS:
            self.assertAlmostEqual(state["activos"][ticker]["pct_ya_invertido"], 1.0, places=2)
        self.assertEqual(locked["data"]["tranche_status"], "executed")


class DaysOneToFourKeepTheScheduleTests(EntryCalendarDayBase):
    def test_state_69_percent_but_less_held_does_not_rebalance_before_day_five(self):
        # Schedule asks 50% today, state says ~69%, holdings say 30%: normal logic keeps
        # MANTENER (entry is not a rebalancer); the gap is closed on day 5.
        self.stale_empty_pending()
        self.write_fills({t: 0.3 for t in TARGETS})
        day4 = self.run_entry("2026-10-13")
        self.assertEqual(day4["data"]["cycle_day"], 4)
        self.assertEqual(day4["data"]["entries"], [])

    def test_schedule_ahead_of_state_buys_the_normal_delta(self):
        self.schedule_pct = 0.8
        self.stale_empty_pending()
        self.write_fills()
        day4 = self.run_entry("2026-10-13")
        for ticker, entry in self.entries(day4).items():
            expected = (0.8 - STATE_PCT[ticker]) * TARGETS[ticker]
            self.assertAlmostEqual(entry["tranche_weight"], expected, delta=3e-4)

    def test_net_holdings_above_the_state_prevent_an_overbuy(self):
        self.schedule_pct = 0.8
        self.write_state()
        self.write_fills({t: 0.9 for t in TARGETS})  # fills the state never recorded
        day4 = self.run_entry("2026-10-13")
        self.assertEqual(day4["data"]["entries"], [])
        self.assertTrue(any("not buying more than is already held" in w for w in day4["warnings"]))

    def test_no_fills_at_all_keeps_the_state_percentages(self):
        self.schedule_pct = 0.8
        self.write_state()
        day4 = self.run_entry("2026-10-13")
        for ticker, entry in self.entries(day4).items():
            self.assertAlmostEqual(entry["tranche_weight"], (0.8 - STATE_PCT[ticker]) * TARGETS[ticker],
                                   delta=3e-4)


class InvestedFractionTests(unittest.TestCase):
    def test_fraction_cases(self):
        holdings = {
            "A": {"bought_qty": 10, "sold_qty": 0, "bought_weight": 0.2, "sold_weight": 0.0,
                  "net_qty": 10, "net_weight": 0.2},
            "B": {"bought_qty": 10, "sold_qty": 4, "bought_weight": 0.2, "sold_weight": 0.0,
                  "net_qty": 6, "net_weight": 0.2},
            "C": {"bought_qty": 10, "sold_qty": 0, "bought_weight": 0.0, "sold_weight": 0.0,
                  "net_qty": 10, "net_weight": 0.0},
            "D": {"bought_qty": 10, "sold_qty": 0, "bought_weight": 0.5, "sold_weight": 0.0,
                  "net_qty": 10, "net_weight": 0.5},
        }
        f = pipeline_io.invested_fraction_from_holdings
        self.assertAlmostEqual(f(holdings, "A", 0.4), 0.5)
        self.assertAlmostEqual(f(holdings, "B", 0.4), 0.3)
        self.assertIsNone(f(holdings, "C", 0.4))
        self.assertEqual(f(holdings, "D", 0.4), 1.0)
        self.assertEqual(f(holdings, "E", 0.4), 0.0)
        self.assertIsNone(f({}, "A", 0.4))
        self.assertIsNone(f(holdings, "A", float("nan")))
        self.assertIsNone(f(holdings, "A", 0.0))


if __name__ == "__main__":
    unittest.main()
