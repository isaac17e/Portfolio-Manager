"""Sell fills (sell_fills_<optimizer>_<stamp>.json) and the net held quantity,
plus entry_signal_tool / active_management reading them. No network."""

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import pandas as pd

import entry_signal_tool as est
import pipeline_io
from tests.test_review_fixes import _load_active_management

OPT, RUN_TS, STAMP = "minimum_variance", "2026-10-08T11:05:16-05:00", "20261008T110516"
META = {"weights": {}, "portfolio_source": "mv.json", "portfolio_run_ts": RUN_TS,
        "portfolio_optimizer": OPT}


def buy(ticker, qty, weight=0.05, **extra):
    return {"ticker": ticker, "action": "BUY", "filled_qty": qty, "filled_weight": weight,
            "price": 10.0, "status": "filled", **extra}


def sell(ticker, qty, weight=0.05, **extra):
    return {"ticker": ticker, "action": "SELL", "filled_qty": qty, "filled_weight": weight,
            "price": 11.0, "status": "filled", "reason": "ROTACION_SALIDA", **extra}


def buy_doc(*fills):
    return {"schema_version": 1, "signal_run_ts": "sig-1", "executed_ts": "2026-10-08T15:00:00-05:00",
            "fills": list(fills)}


def sell_doc(*fills, **top):
    doc = {"schema_version": 1, "script": "drawdown_rotation", "portfolio_optimizer": OPT,
           "portfolio_run_ts": RUN_TS, "account": "demo", "account_id": "1",
           "executed_ts": "2026-10-09T15:00:00-05:00", "written_ts": "2026-10-09T15:01:00-05:00",
           "fills": list(fills)}
    doc.update(top)
    return doc


class ExecutionsDirCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.executions = self.root / "executions"
        self.executions.mkdir()
        patcher = mock.patch.dict(os.environ, {"EXECUTIONS_DIR": str(self.executions)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def write(self, name, doc):
        (self.executions / name).write_text(json.dumps(doc), encoding="utf-8")

    def write_buys(self, *fills):
        self.write(f"fills_{OPT}_{STAMP}.json", buy_doc(*fills))

    def write_sells(self, *fills, name=None, **top):
        self.write(name or f"sell_fills_{OPT}_{STAMP}.json", sell_doc(*fills, **top))


class SummarizeHoldingsTests(unittest.TestCase):
    def test_net_is_buys_minus_sells(self):
        h = pipeline_io.summarize_holdings(
            buy_doc(buy("GLD", 10, 0.06), buy("KO", 5, 0.02)), [sell_doc(sell("GLD", 4, 0.024))])
        self.assertEqual(h["GLD"]["bought_qty"], 10)
        self.assertEqual(h["GLD"]["sold_qty"], 4)
        self.assertEqual(h["GLD"]["net_qty"], 6)
        self.assertAlmostEqual(h["GLD"]["net_weight"], 0.036)
        self.assertEqual(h["KO"]["net_qty"], 5)
        self.assertEqual(h["KO"]["sold_qty"], 0)

    def test_net_is_floored_at_zero(self):
        h = pipeline_io.summarize_holdings(buy_doc(buy("GLD", 3)), [sell_doc(sell("GLD", 10))])
        self.assertEqual(h["GLD"]["net_qty"], 0)
        self.assertEqual(h["GLD"]["net_weight"], 0)

    def test_sell_without_any_buy_is_zero_not_negative(self):
        h = pipeline_io.summarize_holdings(None, [sell_doc(sell("GLD", 10))])
        self.assertEqual(h["GLD"]["net_qty"], 0)

    def test_tolerates_negative_qty_and_side_field(self):
        negative = {"ticker": "GLD", "action": "SELL", "filled_qty": -4, "status": "filled"}
        by_sign = {"ticker": "GLD", "filled_qty": -2, "status": "filled"}
        by_side = {"ticker": "GLD", "side": "SELL", "filled_qty": 1, "status": "filled"}
        h = pipeline_io.summarize_holdings(buy_doc(buy("GLD", 10)), [sell_doc(negative, by_sign, by_side)])
        self.assertEqual(h["GLD"]["sold_qty"], 7)
        self.assertEqual(h["GLD"]["net_qty"], 3)

    def test_sell_file_fill_without_action_counts_as_a_sale(self):
        bare = {"ticker": "GLD", "filled_qty": 4, "status": "filled"}
        h = pipeline_io.summarize_holdings(buy_doc(buy("GLD", 10)), [sell_doc(bare)])
        self.assertEqual(h["GLD"]["net_qty"], 6)

    def test_sell_in_the_buy_file_also_reduces(self):
        h = pipeline_io.summarize_holdings(buy_doc(buy("GLD", 10), sell("GLD", 3)), [])
        self.assertEqual(h["GLD"]["net_qty"], 7)

    def test_only_applied_statuses_count(self):
        fills = [sell("GLD", 2, status="rejected"), sell("GLD", 3, status="partial"),
                 sell("GLD", 1, status="partially_filled"), sell("GLD", 9, status="pending")]
        h = pipeline_io.summarize_holdings(buy_doc(buy("GLD", 10)), [sell_doc(*fills)])
        self.assertEqual(h["GLD"]["sold_qty"], 4)

    def test_repeated_deal_counts_once(self):
        one = sell("GLD", 4, deal_id="d1", fill_ts="t1")
        h = pipeline_io.summarize_holdings(buy_doc(buy("GLD", 10)), [sell_doc(one), sell_doc(dict(one))])
        self.assertEqual(h["GLD"]["sold_qty"], 4)
        other = sell("GLD", 4, deal_id="d2", fill_ts="t2")
        h = pipeline_io.summarize_holdings(buy_doc(buy("GLD", 10)), [sell_doc(one), sell_doc(other)])
        self.assertEqual(h["GLD"]["sold_qty"], 8)

    def test_junk_is_skipped(self):
        junk = [None, "x", {"ticker": "", "status": "filled"}, {"status": "filled"},
                {"ticker": "GLD", "status": "filled", "filled_qty": "ten"}]
        self.assertEqual(pipeline_io.summarize_holdings(buy_doc(*junk), [sell_doc(*junk)]),
                         {"GLD": {"bought_qty": 0.0, "sold_qty": 0.0, "bought_weight": 0.0,
                                  "sold_weight": 0.0, "net_qty": 0.0, "net_weight": 0.0}})
        self.assertEqual(pipeline_io.summarize_holdings(None, []), {})


class LoadSellFillsTests(ExecutionsDirCase):
    def test_reads_every_sell_file_of_the_portfolio(self):
        self.write_sells(sell("GLD", 1), name=f"sell_fills_{OPT}_20261009T150000.json")
        self.write_sells(sell("GLD", 2), name=f"sell_fills_{OPT}_20261010T150000.json")
        docs = pipeline_io.load_portfolio_sell_fills(META)
        self.assertEqual(len(docs), 2)

    def test_stamp_in_the_name_may_be_the_portfolio_stamp(self):
        self.write_sells(sell("GLD", 1))
        self.assertEqual(len(pipeline_io.load_portfolio_sell_fills(META)), 1)

    def test_other_optimizer_or_portfolio_is_ignored(self):
        self.write_sells(sell("GLD", 1), name="sell_fills_quadratic_utility_20261008T112003.json",
                         portfolio_optimizer="quadratic_utility", portfolio_run_ts="2026-10-08T11:20:03-05:00")
        # Same name prefix, longer optimizer name.
        self.write_sells(sell("GLD", 1), name=f"sell_fills_{OPT}_x_20261009T150000.json",
                         portfolio_optimizer=OPT + "_x")
        # Same optimizer, a newer portfolio (different run_ts).
        self.write_sells(sell("GLD", 1), name=f"sell_fills_{OPT}_20261009T150000.json",
                         portfolio_run_ts="2026-10-09T08:00:00-05:00")
        self.assertEqual(pipeline_io.load_portfolio_sell_fills(META), [])

    def test_without_run_ts_in_the_file_the_name_stamp_decides(self):
        doc = sell_doc(sell("GLD", 1))
        del doc["portfolio_run_ts"]
        self.write(f"sell_fills_{OPT}_{STAMP}.json", doc)
        self.write(f"sell_fills_{OPT}_20261009T150000.json", doc)
        self.assertEqual(len(pipeline_io.load_portfolio_sell_fills(META)), 1)

    def test_invalid_files_are_skipped_without_raising(self):
        (self.executions / f"sell_fills_{OPT}_20261009T150000.json").write_text("{not json", encoding="utf-8")
        self.write_sells(sell("GLD", 1), name=f"sell_fills_{OPT}_20261010T150000.json", schema_version=2)
        self.write_sells(name=f"sell_fills_{OPT}_20261011T150000.json", fills="oops")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(pipeline_io.load_portfolio_sell_fills(META), [])

    def test_no_portfolio_key_or_directory(self):
        self.assertEqual(pipeline_io.load_portfolio_sell_fills(None), [])
        self.assertEqual(pipeline_io.load_portfolio_sell_fills(META, str(self.root / "missing")), [])

    def test_holdings_combine_both_files(self):
        self.write_buys(buy("GLD", 10), buy("KO", 5))
        self.write_sells(sell("GLD", 10))
        h = pipeline_io.load_portfolio_holdings(META)
        self.assertEqual(h["GLD"]["net_qty"], 0)
        self.assertEqual(h["KO"]["net_qty"], 5)

    def test_holdings_of_another_portfolio_are_not_mixed(self):
        self.write_buys(buy("GLD", 10))
        self.write(f"fills_quadratic_utility_20261008T112003.json", buy_doc(buy("GLD", 99)))
        self.assertEqual(pipeline_io.load_portfolio_holdings(META)["GLD"]["bought_qty"], 10)

    def test_holdings_without_files(self):
        self.assertEqual(pipeline_io.load_portfolio_holdings(META), {})


class FullySoldTests(unittest.TestCase):
    HOLD = pipeline_io.summarize_holdings(
        buy_doc(buy("A", 10), buy("B", 10), buy("C", 10)),
        [sell_doc(sell("A", 10), sell("B", 4), sell("Z", 5))])

    def test_only_bought_then_fully_sold(self):
        self.assertEqual(pipeline_io.fully_sold_tickers(self.HOLD), ["A"])  # B partial, Z never bought

    def test_a_name_the_rotation_picked_again_is_not_fully_sold(self):
        state = {"triggers": {"A": {"date": "2026-10-09"}},
                 "history": [{"date": "2026-10-09", "bought": ["B"]}, {"date": "2026-10-12", "bought": ["A"]}]}
        self.assertEqual(pipeline_io.fully_sold_tickers(self.HOLD, state), [])
        self.assertTrue(pipeline_io.rotation_reentered(state, "A"))
        self.assertFalse(pipeline_io.rotation_reentered(state, "C"))
        old = {"triggers": {"A": {"date": "2026-10-09"}}, "history": [{"date": "2026-10-01", "bought": ["A"]}]}
        self.assertFalse(pipeline_io.rotation_reentered(old, "A"))
        self.assertEqual(pipeline_io.fully_sold_tickers(self.HOLD, old), ["A"])
        self.assertFalse(pipeline_io.rotation_reentered(None, "A"))


class ActiveManagementHoldingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.am = _load_active_management()

    def _signal(self, holdings=None):
        table = pd.DataFrame([
            {"Ticker": "GLD", "Peso_Inicial": 0.5, "Nuevo_Peso": 0.4, "Racional": "r", "Accion": "RECORTAR"},
            {"Ticker": "KO", "Peso_Inicial": 0.5, "Nuevo_Peso": 0.6, "Racional": "r", "Accion": "AUMENTAR"},
        ])
        return self.am["_senal_gestion_activa"]({"tabla_rebalanceo": table, "regimen_riesgo": {}}, holdings)

    def test_without_holdings_the_signal_is_unchanged(self):
        signal = self._signal()
        self.assertNotIn("net_holdings", signal)
        self.assertTrue(all("net_held_qty" not in r for r in signal["rebalances"]))

    def test_net_held_qty_per_rebalance(self):
        holdings = pipeline_io.summarize_holdings(buy_doc(buy("GLD", 10)), [sell_doc(sell("GLD", 10))])
        signal = self._signal(holdings)
        by_ticker = {r["ticker"]: r for r in signal["rebalances"]}
        self.assertEqual(by_ticker["GLD"]["net_held_qty"], 0)
        self.assertIsNone(by_ticker["KO"]["net_held_qty"])
        self.assertEqual(signal["net_holdings"], {"GLD": 0})

    def test_warns_about_trading_a_fully_sold_name(self):
        holdings = pipeline_io.summarize_holdings(buy_doc(buy("GLD", 10)), [sell_doc(sell("GLD", 10))])
        rebalances = [{"ticker": "GLD", "action": "SELL"}, {"ticker": "KO", "action": "BUY"}]
        warns = self.am["_advertencias_tenencias"](rebalances, holdings)
        self.assertEqual(len(warns), 1)
        self.assertIn("GLD: SELL proposed", warns[0])
        self.assertEqual(self.am["_advertencias_tenencias"](rebalances, {}), [])


if __name__ == "__main__":
    unittest.main()
