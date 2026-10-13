"""Day 5 (2026-10-14) from the REAL entry states of the minimum_variance and
quadratic_utility portfolios as they were on 2026-10-13 (tests/fixtures: dia_ciclo=2,
empty day-3 signal pending, last_tranche_date 2026-10-13).

No fills file was attached, so cumulative buy fills are synthesised to match each
state's pct_ya_invertido (equal 1/6 targets). Three starting points are checked: the state
as it is, the state an old-code forced ENTRY_CYCLE_DAY=4 run leaves behind (a second empty
pending signal, dia_ciclo still 2), and that one with ENTRY_CYCLE_DAY=4 still exported.
"""

import copy
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import entry_signal_tool as est
import pipeline_io
from tests.test_entry_calendar_day import _ENTRY_ENV, _row

FIXTURES = Path(__file__).resolve().parent / "fixtures"
STATES = ("entry_state_minimum_variance_20261008T112902.json",
          "entry_state_quadratic_utility_20261008T121253.json")
FORCED_TS = "2026-10-13T11:40:00-05:00"


class _Helpers(unittest.TestCase):
    def load(self, name, weights=None):
        self.state0 = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
        tickers = list(self.state0["activos"])
        self.targets = dict(weights) if weights else {t: 1.0 / len(tickers) for t in tickers}
        optimizer, run_ts = self.state0["portfolio"]["optimizer"], self.state0["portfolio"]["run_ts"]
        self.meta = {"weights": dict(self.targets), "portfolio_source": "/p/portfolio_latest.json",
                     "portfolio_run_ts": run_ts, "portfolio_optimizer": optimizer}
        self.key = pipeline_io.portfolio_key(self.meta)

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.executions = self.root / "executions"
        self.executions.mkdir()
        env = {k: v for k, v in os.environ.items() if k not in _ENTRY_ENV}
        env.update({"SIGNALS_OUT_DIR": str(self.root / "signals"), "EXECUTIONS_DIR": str(self.executions)})
        patcher = mock.patch.dict(os.environ, env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        for attr, value in (
            ("_PORTFOLIO_META", self.meta), ("TICKERS", tickers), ("PESOS_OBJETIVO", dict(self.targets)),
            ("RECORTADOS_POR_ROTACION", set()), ("HIST_PATH", str(self.root / "h.csv")),
            ("LEGACY_STATE_PATH", str(self.root / "legacy.json")), ("graficar_resumen", lambda r: None),
            ("calcular_fila_instrumento", lambda t, h, w, x: _row(t, 0.5)),
        ):
            patch = mock.patch.object(est, attr, value)
            patch.start()
            self.addCleanup(patch.stop)

    def put_state(self, state):
        path = Path(pipeline_io.entry_state_path(self.meta))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state), encoding="utf-8")

    def put_fills(self, sold=None):
        fills = []
        for ticker, info in self.state0["activos"].items():
            weight = info["pct_ya_invertido"] * self.targets[ticker]
            for ts in ("2026-10-08T13:00:00-05:00", "2026-10-09T13:00:00-05:00"):
                fills.append({"ticker": ticker, "action": "BUY", "filled_weight": weight / 2, "filled_qty": 10,
                              "price": 100.0, "status": "filled", "deal_id": f"{ticker}{ts}", "fill_ts": ts,
                              "signal_run_ts": ts})
        (self.executions / f"fills_{self.key}.json").write_text(json.dumps({
            "schema_version": 1, "signal_run_ts": "2026-10-09T13:00:00-05:00",
            "executed_ts": "2026-10-09T15:00:00-05:00", "fills": fills}), encoding="utf-8")
        if sold:
            stamp = pipeline_io.run_ts_stamp(self.meta["portfolio_run_ts"])
            (self.executions / f"sell_fills_{self.meta['portfolio_optimizer']}_{stamp}.json").write_text(
                json.dumps({"schema_version": 1, "portfolio_optimizer": self.meta["portfolio_optimizer"],
                            "portfolio_run_ts": self.meta["portfolio_run_ts"],
                            "fills": [{"ticker": t, "action": "SELL", "filled_weight": w, "filled_qty": 4,
                                       "price": 100.0, "status": "filled", "deal_id": f"s{t}",
                                       "fill_ts": "2026-10-12T15:00:00-05:00"} for t, w in sold.items()]}),
                encoding="utf-8")

    def forced_day4_state(self):
        """What the old code left after ENTRY_CYCLE_DAY=4: another empty pending signal."""
        state = copy.deepcopy(self.state0)
        tranche = dict(state["last_tranche"], cycle_day=4, signal_run_ts=FORCED_TS)
        state.update(pending_signal_run_ts=FORCED_TS, pending_cycle_day=4, last_tranche=tranche)
        return state

    def day5(self, **env):
        with mock.patch.dict(os.environ, {"CYCLE_DATE": "2026-10-14", **env}):
            with redirect_stdout(io.StringIO()):
                est.main([])
        folder = Path(pipeline_io.resolve_signals_dir(self.meta))
        return json.loads((folder / "entry_signal_tool.json").read_text(encoding="utf-8"))

    def check_completes(self, payload, net_weights):
        self.assertEqual((payload["data"]["cycle_day"], payload["data"]["cycle"]), (5, 1))
        entries = {e["ticker"]: e for e in payload["data"]["entries"]}
        for ticker, target in self.targets.items():
            held = net_weights[ticker]
            bought = entries[ticker]["tranche_weight"] if ticker in entries else 0.0
            self.assertAlmostEqual(held + bought, target, delta=3e-4, msg=ticker)


class AttachedStateDayFiveTests(_Helpers):
    def test_both_portfolios_reach_100_percent_on_day_five_from_every_starting_state(self):
        for name in STATES:
            for label, make_state, env in (
                ("as attached", lambda: self.state0, {}),
                ("after old-code forced day 4", self.forced_day4_state, {}),
                ("forced day 4, ENTRY_CYCLE_DAY still set", self.forced_day4_state, {"ENTRY_CYCLE_DAY": "4"}),
            ):
                with self.subTest(portfolio=name[12:-5], start=label):
                    self.load(name)
                    self.put_state(make_state())
                    self.put_fills()
                    payload = self.day5(**env)
                    net = {t: i["pct_ya_invertido"] * self.targets[t] for t, i in self.state0["activos"].items()}
                    self.check_completes(payload, net)
                    state = json.loads(Path(pipeline_io.entry_state_path(self.meta)).read_text())
                    self.assertEqual(state["pending_cycle_day"], 5)
                    self.assertEqual(state["last_tranche"]["cycle_day"], 5)

    def test_quadratic_utility_avgo_sale_is_bought_back_on_day_five(self):
        self.load(STATES[1])
        self.put_state(self.forced_day4_state())
        sale = 0.05
        self.put_fills(sold={"AVGO": sale})
        payload = self.day5()
        net = {t: i["pct_ya_invertido"] * self.targets[t] for t, i in self.state0["activos"].items()}
        net["AVGO"] -= sale
        self.check_completes(payload, net)
        entries = {e["ticker"]: e for e in payload["data"]["entries"]}
        self.assertGreater(entries["AVGO"]["tranche_weight"], self.targets["AVGO"] * (1 - 0.692) + 0.04)


# weights_used of the 2026-10-13 09:16 / 09:17 entry signals, and the states they left behind.
REAL = {
    "entry_state_minimum_variance_20261008T112902_after_force.json": {
        "BRK-B": 0.260029, "PG": 0.188411, "MCD": 0.165178, "JNJ": 0.158179, "RY.TO": 0.149841, "AEP": 0.078362},
    "entry_state_quadratic_utility_20261008T121253_after_force.json": {
        "AVGO": 0.300001, "AMZN": 0.26503, "LLY": 0.200746, "META": 0.147551, "NTES": 0.057287, "ORLY": 0.029385},
}


class PostForceStateDayFiveTests(_Helpers):
    """The states the 2026-10-13 forced ENTRY_CYCLE_DAY=4 runs really left (empty day-4 signal pending)."""

    def test_post_force_states_complete_to_target_on_day_five(self):
        for name, weights in REAL.items():
            with self.subTest(portfolio=name[12:-5]):
                self.load(name, weights)
                self.assertEqual((self.state0["pending_cycle_day"], self.state0["dia_ciclo"]), (4, 2))
                self.put_state(self.state0)
                self.put_fills()
                payload = self.day5(ENTRY_CYCLE_DAY="4")
                net = {t: i["pct_ya_invertido"] * self.targets[t] for t, i in self.state0["activos"].items()}
                self.check_completes(payload, net)
                self.assertTrue(all(e["signal"] == "cycle_close" for e in payload["data"]["entries"]))

    def test_post_force_quadratic_utility_buys_avgo_toward_30_percent(self):
        name = "entry_state_quadratic_utility_20261008T121253_after_force.json"
        self.load(name, REAL[name])
        self.put_state(self.state0)
        sale = 0.05
        self.put_fills(sold={"AVGO": sale})
        payload = self.day5()
        entries = {e["ticker"]: e for e in payload["data"]["entries"]}
        held = 0.692 * 0.300001 - sale
        self.assertAlmostEqual(entries["AVGO"]["target_weight"], 0.300001, delta=1e-4)
        self.assertAlmostEqual(entries["AVGO"]["tranche_weight"], 0.300001 - held, delta=3e-4)
        self.assertAlmostEqual(held + entries["AVGO"]["tranche_weight"], 0.30, delta=3e-4)


if __name__ == "__main__":
    unittest.main()
