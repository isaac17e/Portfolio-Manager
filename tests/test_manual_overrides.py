"""manual_overrides.json (ARES): schema validation, precedence over the rotation / entry
state, the BUY gate, and its use by entry_signal_tool, drawdown_rotation and
active_management. No network: the entry tool runs on ``.LS`` tickers (tier "none").

The incident: Isaac replaced FTNT with MRK in portfolio quadratic_utility_20261008T121253,
yet entry_signal_tool later emitted a BUY for FTNT from the rotation / entry state targets.
The pipeline_io tests use those very tickers; the entry-tool tests use the ``.LS`` analogues
(GALP.LS replaced by NOS.LS) because FTNT / MRK need Polygon.
"""

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


import active_management as am
import drawdown_rotation as dr
import entry_signal_tool as est
import pipeline_io as pio
from tests.test_drawdown_rotation import _ohlc
from tests.test_rotation_entry import DAYS, META, OPT, STAMP, RotationEntryCase

QU = {"portfolio_optimizer": "quadratic_utility", "portfolio_run_ts": "2026-10-08T12:12:53-05:00",
      "weights": {"AVGO": 0.5, "GLD": 0.5}}
QU_KEY = "quadratic_utility_20261008T121253"
META_KEY = f"{OPT}_{STAMP}"


def entry(**kw):
    base = {"id": "ovr-1", "ts": "2026-10-09T10:01:40-05:00", "action": "replace",
            "replaced_ticker": "FTNT", "chosen_ticker": "MRK", "target_weight": 0.0462,
            "source_script": "drawdown_rotation", "approved_by": "isaac", "fills": ["deal-1"],
            "note": "Isaac prefers MRK"}
    base.update(kw)
    return base


def doc(entries, key=QU_KEY, **kw):
    out = {"schema_version": 1, "updated_ts": "2026-10-09T10:02:11-05:00",
           "portfolios": {key: {"account_id": "ACC-123", "overrides": entries}}}
    out.update(kw)
    return out


def write(path, payload):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    text = payload if isinstance(payload, str) else json.dumps(payload)
    Path(path).write_text(text, encoding="utf-8")
    return str(path)


class TempDirCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.path = str(self.dir / "state" / "manual_overrides.json")
        patcher = mock.patch.dict(os.environ, {"MANUAL_OVERRIDES_FILE": self.path})
        patcher.start()
        self.addCleanup(patcher.stop)

    def load(self, payload, meta=QU):
        write(self.path, payload)
        with redirect_stdout(io.StringIO()):
            return pio.load_manual_overrides(meta)


class ValidatorTests(unittest.TestCase):
    def test_valid_document_has_no_problems(self):
        self.assertEqual(pio.validate_manual_overrides(doc([entry()])), [])
        self.assertEqual(pio.validate_manual_overrides(doc([
            entry(id="a", action="reject", replaced_ticker="X", chosen_ticker=None, target_weight=None),
            entry(id="b", action="remove", replaced_ticker="Y", chosen_ticker=None, target_weight=0),
            entry(id="c", action="add", replaced_ticker=None, chosen_ticker="Z", target_weight=0.05),
        ])), [])

    def test_errors_name_the_portfolio_position_and_field(self):
        problems = pio.validate_manual_overrides(doc([
            entry(id="ok"),
            entry(id="bad-ts", ts="2026-10-09T10:01:40"),
            entry(id="bad-action", action="swap"),
            entry(id="bad-weight", target_weight=1.5),
            entry(id="same", chosen_ticker="ftnt"),
            entry(id="no-chosen", chosen_ticker=None),
            entry(id="reject-chosen", action="reject", chosen_ticker="MRK", target_weight=None),
            entry(id="add-replaced", action="add"),
            entry(id="ok", ticker="dup"),
            entry(id="bad-fills", fills="deal-1"),
            entry(id="no-approver", approved_by=""),
            "not an object",
        ]))
        text = "\n".join(problems)
        for fragment in (
            f"portfolios['{QU_KEY}'].overrides[1] (id 'bad-ts'): 'ts' must be an ISO-8601 timestamp with a UTC offset",
            "overrides[2] (id 'bad-action'): 'action' must be one of replace, reject, add, remove",
            "overrides[3] (id 'bad-weight'): 'target_weight' must be a number in (0, 1]",
            "overrides[4] (id 'same'): 'chosen_ticker' must differ",
            "overrides[5] (id 'no-chosen'): 'chosen_ticker' must be a ticker",
            "overrides[6] (id 'reject-chosen'): 'chosen_ticker' must be null",
            "overrides[7] (id 'add-replaced'): 'replaced_ticker' must be null",
            "overrides[8] (id 'ok'): duplicate id",
            "overrides[9] (id 'bad-fills'): 'fills' must be a list",
            "overrides[10] (id 'no-approver'): 'approved_by'",
            "overrides[11]: must be an object",
        ):
            self.assertIn(fragment, text)
        self.assertNotIn("overrides[0]", text)

    def test_document_level_problems(self):
        self.assertIn("top level", pio.validate_manual_overrides([])[0])
        self.assertIn("'schema_version' must be 1", pio.validate_manual_overrides({"schema_version": 2})[0])
        self.assertIn("'portfolios' must be an object",
                      pio.validate_manual_overrides({"schema_version": 1, "portfolios": []})[0])
        problems = pio.validate_manual_overrides({"schema_version": 1, "portfolios": {"k": {"overrides": {}}}})
        self.assertIn("'overrides' must be a list", problems[0])


class LoaderTests(TempDirCase):
    def test_no_file_changes_nothing(self):
        with redirect_stdout(io.StringIO()):
            result = pio.load_manual_overrides(QU)
        self.assertEqual(result["status"], "absent")
        self.assertEqual((result["blocked"], result["chosen"], result["unverified"]), ({}, {}, {}))
        weights = {"AVGO": 0.5, "GLD": 0.5}
        base, notes = pio.apply_rotation_overrides(weights, None)
        effective = pio.effective_targets(weights, None, None, result)
        self.assertEqual((effective["targets"], effective["notes"]), (base, notes))
        self.assertEqual(effective["override_notes"], [])

    def test_default_path_follows_the_pipeline_state_dir(self):
        env = {"SIGNALS_OUT_DIR": "/data/pipeline/signals"}
        self.assertEqual(pio.manual_overrides_path(env), "/data/pipeline/state/manual_overrides.json")
        self.assertEqual(pio.manual_overrides_path({"PIPELINE_DIR": "/p"}), "/p/state/manual_overrides.json")
        self.assertEqual(pio.manual_overrides_path({"MANUAL_OVERRIDES_FILE": "/x.json"}), "/x.json")

    def test_replace_blocks_replaced_and_sets_chosen(self):
        result = self.load(doc([entry()]))
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["account_id"], "ACC-123")
        self.assertEqual(sorted(result["blocked"]), ["FTNT"])
        self.assertEqual(result["chosen"]["MRK"]["target_weight"], 0.0462)
        self.assertIn("isaac", result["blocked"]["FTNT"]["reason"])

    def test_other_portfolio_is_ignored(self):
        result = self.load(doc([entry()], key="minimum_variance_20261008T112902"))
        self.assertEqual(result["status"], "absent")
        self.assertEqual(result["blocked"], {})

    def test_entries_replay_by_timestamp_last_word_wins(self):
        result = self.load(doc([
            entry(id="later-add", ts="2026-10-10T09:00:00-05:00", action="add", replaced_ticker=None,
                  chosen_ticker="FTNT", target_weight=0.03),
            entry(id="first"),
        ]))
        self.assertNotIn("FTNT", result["blocked"])
        self.assertEqual(result["chosen"]["FTNT"]["target_weight"], 0.03)
        self.assertEqual(result["chosen"]["MRK"]["target_weight"], 0.0462)

    def test_invalid_json_never_raises_and_flags_state_tickers(self):
        result = self.load("{ not json")
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(result["unverified_all_state"])
        self.assertIn("not valid JSON", result["errors"][0])
        state = pio.empty_rotation_state(QU)
        state["target_overrides"] = {"FTNT": 0.05, "GLD": 0.4}
        effective = pio.effective_targets(QU["weights"], state, {"pending_targets": {"NVDA": 0.02}}, result)
        self.assertEqual(sorted(effective["unverified"]), ["FTNT", "GLD", "NVDA"])
        self.assertEqual(pio.buy_gate("FTNT", effective, QU["weights"])[0], pio.REQUIRES_VERIFICATION)
        self.assertEqual(pio.buy_gate("AVGO", effective, QU["weights"])[0], "BUY")

    def test_invalid_entry_marks_only_its_tickers_and_valid_entries_still_apply(self):
        result = self.load(doc([
            entry(id="good", replaced_ticker="AAA", chosen_ticker="BBB"),
            entry(id="bad", ts="yesterday"),
        ]))
        self.assertEqual(result["status"], "invalid")
        self.assertEqual(sorted(result["unverified"]), ["FTNT", "MRK"])
        self.assertFalse(result["unverified_all_state"])
        self.assertIn("AAA", result["blocked"])
        self.assertIn("BBB", result["chosen"])
        effective = pio.effective_targets(QU["weights"], None, None, result)
        self.assertEqual(pio.buy_gate("MRK", effective, QU["weights"])[0], pio.REQUIRES_VERIFICATION)
        self.assertEqual(pio.buy_gate("BBB", effective, QU["weights"])[0], "BUY")

    def test_wrong_schema_version_and_malformed_section_are_invalid(self):
        self.assertEqual(self.load({"schema_version": 7, "portfolios": {}})["status"], "invalid")
        result = self.load({"schema_version": 1, "portfolios": {QU_KEY: {"overrides": "x"}}})
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(result["unverified_all_state"])

    def test_error_in_another_portfolio_does_not_affect_this_one(self):
        payload = doc([entry()])
        payload["portfolios"]["other_20260101T000000"] = {"overrides": [{"id": "x"}]}
        result = self.load(payload)
        self.assertEqual(result["status"], "ok")
        self.assertIn("FTNT", result["blocked"])


class EffectiveTargetsTests(unittest.TestCase):
    def setUp(self):
        self.weights = {"AVGO": 0.5, "GLD": 0.4538}
        self.rotation = pio.empty_rotation_state(QU)
        self.rotation["target_overrides"] = {"FTNT": 0.0462}
        self.entry_state = {"pending_targets": {"FTNT": 0.0462, "AVGO": 0.5}}

    def overrides(self, *entries):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(
                os.environ, {"MANUAL_OVERRIDES_FILE": str(Path(tmp) / "m.json")}):
            write(os.environ["MANUAL_OVERRIDES_FILE"], doc(list(entries)))
            with redirect_stdout(io.StringIO()):
                return pio.load_manual_overrides(QU)

    def test_ftnt_to_mrk_beats_rotation_targets_and_entry_pending(self):
        base = pio.effective_targets(self.weights, self.rotation, self.entry_state, None)
        self.assertEqual(base["targets"]["FTNT"], 0.0462)  # without the override FTNT is bought
        effective = pio.effective_targets(self.weights, self.rotation, self.entry_state,
                                          self.overrides(entry()))
        self.assertNotIn("FTNT", effective["targets"])
        self.assertEqual(effective["targets"]["MRK"], 0.0462)
        self.assertEqual(effective["targets"]["AVGO"], 0.5)
        self.assertEqual(effective["pending_targets"], {"AVGO": 0.5})
        self.assertTrue(any("FTNT" in n and "removed" in n for n in effective["override_notes"]))

    def test_chosen_target_replaces_a_rotation_target(self):
        self.rotation["target_overrides"]["MRK"] = 0.01
        self.entry_state["pending_targets"]["MRK"] = 0.01
        effective = pio.effective_targets(self.weights, self.rotation, self.entry_state,
                                          self.overrides(entry(target_weight=0.0462)))
        self.assertEqual(effective["targets"]["MRK"], 0.0462)
        self.assertEqual(effective["pending_targets"]["MRK"], 0.0462)

    def test_reject_and_remove_never_leave_a_target(self):
        effective = pio.effective_targets(
            self.weights, self.rotation, self.entry_state,
            self.overrides(
                entry(id="r", action="reject", replaced_ticker="FTNT", chosen_ticker=None, target_weight=None),
                entry(id="m", action="remove", replaced_ticker="GLD", chosen_ticker=None, target_weight=None)))
        self.assertEqual(effective["targets"], {"AVGO": 0.5})
        self.assertEqual(sorted(effective["blocked"]), ["FTNT", "GLD"])
        self.assertEqual(effective["chosen"], {})

    def test_sanitize_entry_pending_follows_the_overrides(self):
        effective = pio.effective_targets(self.weights, self.rotation, self.entry_state,
                                          self.overrides(entry()))
        estado = {"pending_targets": {"FTNT": 0.0462, "AVGO": 0.5}, "ciclo": 1}
        cleaned = pio.sanitize_entry_pending(estado, effective)
        self.assertEqual(cleaned["pending_targets"], {"AVGO": 0.5})
        self.assertEqual(estado["pending_targets"], {"FTNT": 0.0462, "AVGO": 0.5})
        same = {"pending_targets": {"AVGO": 0.5}}
        self.assertIs(pio.sanitize_entry_pending(same, effective), same)


class GateTests(unittest.TestCase):
    def setUp(self):
        self.effective = pio.effective_targets({"AVGO": 1.0}, None, None, {
            "blocked": {"FTNT": {"id": "o1", "action": "replace", "reason": "replace by isaac (override o1)"}},
            "chosen": {"MRK": {"id": "o1", "action": "replace", "target_weight": 0.05,
                               "replaced_ticker": "FTNT"}},
            "unverified": {}, "unverified_all_state": False,
        })

    def gate(self, ticker, **kw):
        kw.setdefault("portfolio_weights", {"AVGO": 1.0})
        return pio.buy_gate(ticker, self.effective, **kw)

    def test_blocked_chosen_portfolio_and_held_pass_or_stop(self):
        self.assertEqual(self.gate("FTNT")[0], "BLOCKED")
        self.assertEqual(self.gate("mrk")[0], "BUY")
        self.assertEqual(self.gate("AVGO")[0], "BUY")
        self.assertEqual(self.gate("NVDA", holdings={"NVDA": {"bought_qty": 3.0}})[0], "BUY")
        self.assertEqual(self.gate("NVDA", holdings={"holdings": {"NVDA": {"qty": 3.0}}})[0], "BUY")

    def test_unknown_ticker_requires_verification(self):
        status, reason = self.gate("NVDA", holdings={"AAPL": {}})
        self.assertEqual(status, pio.REQUIRES_VERIFICATION)
        self.assertIn("not in the portfolio file", reason)
        self.assertEqual(self.gate("NVDA")[0], pio.REQUIRES_VERIFICATION)

    def test_rotation_names_pass_unless_strict(self):
        rotation = pio.empty_rotation_state(QU)
        rotation["target_overrides"] = {"NVDA": 0.04}
        effective = pio.effective_targets({"AVGO": 1.0}, rotation, None, None)
        self.assertEqual(pio.buy_gate("NVDA", effective, {"AVGO": 1.0}, strict=False)[0], "BUY")
        self.assertEqual(pio.buy_gate("NVDA", effective, {"AVGO": 1.0}, strict=True)[0],
                         pio.REQUIRES_VERIFICATION)
        with mock.patch.dict(os.environ, {pio.STRICT_GATE_ENV: "1"}):
            self.assertEqual(pio.buy_gate("NVDA", effective, {"AVGO": 1.0})[0], pio.REQUIRES_VERIFICATION)
            # a name the override chose is verified by definition, strict or not
            self.assertEqual(self.gate("MRK")[0], "BUY")
        self.assertEqual(pio.buy_gate("TSLA", effective, {"AVGO": 1.0}, own_picks=["TSLA"], strict=False)[0], "BUY")
        self.assertEqual(pio.buy_gate("TSLA", effective, {"AVGO": 1.0}, own_picks=["TSLA"], strict=True)[0],
                         pio.REQUIRES_VERIFICATION)

    def test_apply_buy_gate_rewrites_rows(self):
        rows = [
            {"ticker": "FTNT", "action": "BUY", "current_weight": 0.0, "target_weight": 0.05},
            {"ticker": "NVDA", "action": "BUY", "current_weight": 0.0, "target_weight": 0.02},
            {"ticker": "MRK", "action": "BUY", "target_weight": 0.05},
            {"ticker": "FTNT", "action": "SELL", "target_weight": 0.0},
        ]
        out, flagged = pio.apply_buy_gate(rows, self.effective, {"AVGO": 1.0})
        self.assertEqual([(r["ticker"], r["action"]) for r in out],
                         [("NVDA", "REQUIRES_VERIFICATION"), ("MRK", "BUY"), ("FTNT", "SELL")])
        self.assertEqual(out[0]["status"], "REQUIRES_VERIFICATION")
        self.assertEqual(out[0]["original_action"], "BUY")
        self.assertIn("verification_reason", out[0])
        self.assertEqual([(f["ticker"], f["status"]) for f in flagged],
                         [("FTNT", "BLOCKED"), ("NVDA", "REQUIRES_VERIFICATION")])
        self.assertEqual(rows[1]["action"], "BUY")  # input untouched
        held, _ = pio.apply_buy_gate(rows[:1], self.effective, {"AVGO": 1.0}, blocked_as="hold")
        self.assertEqual((held[0]["action"], held[0]["target_weight"], held[0]["delta_weight"]),
                         ("HOLD", 0.0, 0.0))


class EntryToolOverridesTests(RotationEntryCase):
    """The same scenario as the incident, through entry_signal_tool.main."""

    SOLD, PROPOSED, CHOSEN = "JMT.LS", "GALP.LS", "NOS.LS"

    def setUp(self):
        super().setUp()
        self.file = str(self.root / "state" / "manual_overrides.json")
        patcher = mock.patch.dict(os.environ, {"MANUAL_OVERRIDES_FILE": self.file})
        patcher.start()
        self.addCleanup(patcher.stop)

    def set_overrides(self, payload):
        """What entry_signal_tool computes at import from the overrides file."""
        write(self.file, payload)
        with redirect_stdout(io.StringIO()):
            manual = pio.load_manual_overrides(META)
        effective = pio.effective_targets(META["weights"], self.rotation, None, manual)
        recortados = sorted(t for t, w in effective["targets"].items()
                            if t in META["weights"] and w < META["weights"][t] - 1e-9)
        for name, value in (("OVERRIDES_MANUALES", manual), ("PESOS_OBJETIVO", effective["targets"]),
                            ("TICKERS", list(effective["targets"])), ("NOTAS_ROTACION", effective["notes"]),
                            ("NOTAS_OVERRIDES", effective["override_notes"]),
                            ("RECORTADOS_POR_ROTACION", recortados)):
            patch = mock.patch.object(est, name, value)
            patch.start()
            self.addCleanup(patch.stop)
        return manual

    def doc(self, *entries):
        return doc(list(entries), key=META_KEY)

    def replace_entry(self, **kw):
        return entry(replaced_ticker=self.PROPOSED, chosen_ticker=self.CHOSEN, target_weight=0.25,
                     source_script="drawdown_rotation", **kw)

    def rotate_into_proposed(self, day):
        self.rotate(day, sold=self.SOLD, bought=[self.PROPOSED], weight_each=0.5)

    def entries(self, signal):
        return {e["ticker"]: e for e in signal["data"]["entries"]}

    def test_without_overrides_the_rotation_target_is_bought(self):
        self.rotate_into_proposed(DAYS[0])
        signal = self.run_entry(DAYS[0])
        self.assertEqual(self.entries(signal)[self.PROPOSED]["action"], "BUY")
        self.assertNotIn("manual_overrides", signal["data"])
        self.assertNotIn("flagged_by_override", signal["data"])

    def test_replace_ftnt_with_mrk_equivalent(self):
        self.rotate_into_proposed(DAYS[0])
        self.set_overrides(self.doc(self.replace_entry()))
        signal = self.run_entry(DAYS[0])
        found = self.entries(signal)
        self.assertNotIn(self.PROPOSED, found)
        self.assertEqual(found[self.CHOSEN]["action"], "BUY")
        self.assertAlmostEqual(found[self.CHOSEN]["target_weight"], est.no_options_weight_cap(0.25))
        self.assertEqual(signal["data"]["manual_overrides"]["chosen"], {self.CHOSEN: 0.25})
        self.assertIn(self.PROPOSED, signal["data"]["manual_overrides"]["blocked"])
        self.assertTrue(any("manual override" in w and self.PROPOSED in w for w in signal["warnings"]))
        self.assertNotIn(self.PROPOSED, self.state()["pending_targets"])
        self.assertIn(self.CHOSEN, self.state()["pending_targets"])

    def test_replaced_name_stays_out_in_every_later_signal_and_the_locked_replay(self):
        self.rotate_into_proposed(DAYS[0])
        self.set_overrides(self.doc(self.replace_entry()))
        first = self.run_entry(DAYS[0])
        self.write_buys(first)
        second = self.run_entry(DAYS[1])
        self.assertNotIn(self.PROPOSED, self.entries(second))
        self.assertIn(self.CHOSEN, self.entries(second))
        locked = self.run_entry(DAYS[1])  # same day again: tranche lock replays the tranche
        self.assertEqual(locked["data"]["signal"], "already_prepared_today")
        replay = [e["ticker"] for e in locked["data"]["existing_tranche"]["entries"]]
        self.assertNotIn(self.PROPOSED, replay)
        self.assertIn(self.CHOSEN, replay)

    def test_override_written_after_the_tranche_was_staged_cleans_the_replay(self):
        self.rotate_into_proposed(DAYS[0])
        staged = self.run_entry(DAYS[0])  # BUY GALP.LS is staged in the entry state
        self.assertIn(self.PROPOSED, self.state()["pending_targets"])
        self.assertEqual(self.entries(staged)[self.PROPOSED]["action"], "BUY")
        self.set_overrides(self.doc(self.replace_entry()))
        locked = self.run_entry(DAYS[0])
        self.assertEqual(locked["data"]["signal"], "already_prepared_today")
        replay = {e["ticker"]: e for e in locked["data"]["existing_tranche"]["entries"]}
        self.assertNotIn(self.PROPOSED, replay)
        self.assertEqual([f["status"] for f in locked["data"]["flagged_by_override"]], ["BLOCKED"])
        self.assertEqual([e["order"] for e in locked["data"]["existing_tranche"]["entries"]],
                         list(range(1, len(replay) + 1)))
        forced = self.run_entry(DAYS[0], "--force-new-tranche")
        self.assertNotIn(self.PROPOSED, self.entries(forced))
        self.assertNotIn(self.PROPOSED, self.state()["pending_targets"])

    def test_reject_drops_the_proposed_name(self):
        self.rotate_into_proposed(DAYS[0])
        self.set_overrides(self.doc(entry(action="reject", replaced_ticker=self.PROPOSED,
                                          chosen_ticker=None, target_weight=None)))
        signal = self.run_entry(DAYS[0])
        found = self.entries(signal)
        self.assertNotIn(self.PROPOSED, found)
        self.assertIn("EDP.LS", found)
        self.assertNotIn(self.PROPOSED, [w["ticker"] for w in signal["data"]["waiting"]])

    def test_remove_takes_a_portfolio_name_out(self):
        self.set_overrides(self.doc(entry(action="remove", replaced_ticker="JMT.LS",
                                          chosen_ticker=None, target_weight=None)))
        signal = self.run_entry(DAYS[0])
        self.assertEqual(sorted(self.entries(signal)), ["EDP.LS"])
        self.assertNotIn("JMT.LS", est.TICKERS)

    def test_override_target_beats_active_management_retarget(self):
        self.set_overrides(self.doc(entry(action="add", replaced_ticker=None, chosen_ticker="JMT.LS",
                                          target_weight=0.7)))
        with mock.patch.object(est, "load_active_management_targets",
                               return_value=({"JMT.LS": 0.45}, {"status": "used", "run_ts": "x",
                                                                "entry_day": 7})), \
                mock.patch.object(est, "entry_phase_info", wraps=est.entry_phase_info):
            signal = self.run_entry(DAYS[0])
        self.assertAlmostEqual(self.entries(signal)["JMT.LS"]["target_weight"], est.no_options_weight_cap(0.7))

    def test_invalid_file_requires_verification_instead_of_buy(self):
        self.rotate_into_proposed(DAYS[0])
        self.set_overrides("{ this is not json")
        signal = self.run_entry(DAYS[0])
        found = self.entries(signal)
        self.assertEqual(found[self.PROPOSED]["action"], "REQUIRES_VERIFICATION")
        self.assertEqual(found[self.PROPOSED]["status"], "REQUIRES_VERIFICATION")
        self.assertEqual(found[self.PROPOSED]["original_action"], "BUY")
        self.assertIn("verification_reason", found[self.PROPOSED])
        self.assertEqual(found["EDP.LS"]["action"], "BUY")
        self.assertTrue(any("manual overrides invalid" in w for w in signal["warnings"]))
        self.assertNotIn(self.PROPOSED, self.state()["pending_targets"])
        self.assertEqual(signal["data"]["manual_overrides"]["status"], "invalid")

    def test_invalid_entry_names_its_tickers_only(self):
        self.rotate_into_proposed(DAYS[0])
        self.set_overrides(self.doc(self.replace_entry(ts="not a timestamp")))
        signal = self.run_entry(DAYS[0])
        found = self.entries(signal)
        self.assertEqual(found[self.PROPOSED]["action"], "REQUIRES_VERIFICATION")
        self.assertEqual(found["EDP.LS"]["action"], "BUY")

    def test_only_unverified_entries_close_the_day_without_waiting_for_fills(self):
        self.rotate(DAYS[0], sold="JMT.LS", bought=[self.PROPOSED], weight_each=0.5)
        self.set_overrides("{ this is not json")
        for name, value in (("TICKERS", [self.PROPOSED]), ("PESOS_OBJETIVO", {self.PROPOSED: 0.5})):
            patch = mock.patch.object(est, name, value)
            patch.start()
            self.addCleanup(patch.stop)
        signal = self.run_entry(DAYS[0])
        self.assertEqual([e["action"] for e in signal["data"]["entries"]], ["REQUIRES_VERIFICATION"])
        state = self.state()
        self.assertIsNone(state["pending_signal_run_ts"])
        self.assertEqual(state["pending_targets"], {})

    def test_unknown_ticker_in_the_staged_tranche_requires_verification(self):
        self.run_entry(DAYS[0])
        path = Path(pio.entry_state_path(META))
        state = json.loads(path.read_text(encoding="utf-8"))
        state["last_tranche"]["entries"].append(
            {"order": 3, "ticker": "ZZZ.LS", "action": "BUY", "target_weight": 0.1, "tranche_weight": 0.02})
        path.write_text(json.dumps(state), encoding="utf-8")
        locked = self.run_entry(DAYS[0])
        replay = {e["ticker"]: e for e in locked["data"]["existing_tranche"]["entries"]}
        self.assertEqual(replay["ZZZ.LS"]["action"], "REQUIRES_VERIFICATION")
        self.assertEqual(replay["EDP.LS"]["action"], "BUY")

    def test_strict_gate_flags_rotation_only_names(self):
        self.rotate_into_proposed(DAYS[0])
        with mock.patch.dict(os.environ, {pio.STRICT_GATE_ENV: "1"}):
            signal = self.run_entry(DAYS[0])
        self.assertEqual(self.entries(signal)[self.PROPOSED]["action"], "REQUIRES_VERIFICATION")
        self.assertEqual(self.entries(signal)["EDP.LS"]["action"], "BUY")

    def test_chosen_name_passes_the_strict_gate(self):
        self.rotate_into_proposed(DAYS[0])
        self.set_overrides(self.doc(self.replace_entry()))
        with mock.patch.dict(os.environ, {pio.STRICT_GATE_ENV: "1"}):
            signal = self.run_entry(DAYS[0])
        self.assertEqual(self.entries(signal)[self.CHOSEN]["action"], "BUY")
        self.assertNotIn(self.PROPOSED, self.entries(signal))


class EntryImportTests(TempDirCase):
    def test_module_targets_use_the_overrides_at_import(self):
        import subprocess
        import sys

        state = pio.empty_rotation_state()
        state["target_overrides"] = {"FTNT": 0.0462}
        state_file = write(self.dir / "rotation.json", state)
        write(self.path, doc([entry()], key="hardcoded_fallback"))
        env = dict(os.environ, ROTATION_STATE_FILE=state_file, MANUAL_OVERRIDES_FILE=self.path,
                   PORTFOLIO_FILE=str(self.dir / "missing.json"))
        code = ("import entry_signal_tool as e, json; "
                "print(json.dumps({'t': e.TICKERS, 'w': e.PESOS_OBJETIVO}))")
        out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                             env=env, cwd=os.getcwd(), timeout=120)
        self.assertEqual(out.returncode, 0, out.stderr)
        payload = json.loads(out.stdout.strip().splitlines()[-1])
        self.assertNotIn("FTNT", payload["t"])
        self.assertAlmostEqual(payload["w"]["MRK"], 0.0462)


class DrawdownRotationOverridesTests(TempDirCase):
    def setUp(self):
        super().setUp()
        holdings = {"KO": 0.4, "GLD": 0.3, "MRK": 0.3}
        cands = [f"C{i}" for i in range(12)]
        self.series = {"KO": _ohlc(seed=1, last5=-0.09), "GLD": _ohlc(seed=2), "MRK": _ohlc(seed=3),
                       "NEW": _ohlc(seed=4)}
        for i, c in enumerate(cands):
            self.series[c] = _ohlc(seed=10 + i, drift=0.0002 * i)
        tactical = {"KO": -70.0, **{c: (i * 8.0 - 40) for i, c in enumerate(cands)}}
        info = {"tickers": cands, "rows": [{"ticker": c, "origin": "sp500"} for c in cands],
                "sources": {"sp500": "fake"}, "shortfall": {}}
        self.state_file = str(self.dir / "rotation_state.json")
        self.patches = [
            mock.patch.dict(os.environ, {"ROTATION_STATE_FILE": self.state_file, "HEADLESS": "1",
                                         "FIGURES_DIR": str(self.dir)}),
            mock.patch.object(dr, "_PORTFOLIO_META", {"weights": holdings,
                                                      "portfolio_source": "hardcoded_fallback"}),
            mock.patch.object(dr, "fetch_ohlc", side_effect=lambda t, days=0: self.series[t]),
            mock.patch.object(dr, "options_view", side_effect=lambda t, h: {
                "tactical_score": tactical.get(t, 0.0), "iv_atm": 0.25, "expected_move_pct": 0.05,
                "rationale": "fake", "status": "OK"}),
            mock.patch.object(dr, "build_universe", return_value=info),
        ]
        for patch in self.patches:
            patch.start()
            self.addCleanup(patch.stop)
        self.key = "hardcoded_fallback"

    def run_rotation(self, **kw):
        with redirect_stdout(io.StringIO()):
            return dr.run(mode="full", dry_run=True, **kw)

    def test_a_rejected_candidate_is_never_proposed(self):
        baseline, _ = self.run_rotation()
        picked = baseline["selection"]["tickers"]
        self.assertTrue(picked)
        target = picked[0]
        write(self.path, doc([entry(action="reject", replaced_ticker=target, chosen_ticker=None,
                                    target_weight=None)], key=self.key))
        data, _ = self.run_rotation()
        self.assertNotIn(target, data["selection"]["tickers"])
        self.assertNotIn(target, [r["ticker"] for r in data["rebalances"]])
        self.assertNotIn(target, [row["ticker"] for row in data["top"]])
        self.assertEqual(data["manual_overrides"]["status"], "ok")

    def test_replaced_portfolio_name_is_not_watched_and_chosen_one_is(self):
        write(self.path, doc([entry(replaced_ticker="MRK", chosen_ticker="NEW", target_weight=0.3)],
                             key=self.key))
        data, warns = self.run_rotation()
        watched = {row["ticker"]: row["weight"] for row in data["detector"]}
        self.assertNotIn("MRK", watched)
        self.assertEqual(watched["NEW"], 0.3)
        self.assertTrue(any("manual override" in w for w in warns))

    def test_unverified_state_name_is_not_a_buy_when_the_file_is_broken(self):
        state = pio.empty_rotation_state()
        state["target_overrides"] = {"KO": 0.0, "FTNT": 0.05}
        write(self.state_file, state)
        write(self.path, "{ broken")
        self.series["FTNT"] = _ohlc(seed=5)
        data, warns = self.run_rotation()
        self.assertEqual(data["manual_overrides"]["status"], "invalid")
        self.assertTrue(any("manual overrides invalid" in w for w in warns))
        self.assertIn("FTNT", data["manual_overrides"]["unverified"])


class ActiveManagementOverridesTests(TempDirCase):
    def senal(self):
        return {"rebalances": [
            {"ticker": "FTNT", "action": "BUY", "current_weight": 0.02, "target_weight": 0.05,
             "delta_weight": 0.03, "reason": "", "tactical_action": "AUMENTAR"},
            {"ticker": "GLD", "action": "BUY", "current_weight": 0.1, "target_weight": 0.2,
             "delta_weight": 0.1, "reason": "", "tactical_action": "AUMENTAR"},
            {"ticker": "KO", "action": "SELL", "current_weight": 0.1, "target_weight": 0.0,
             "delta_weight": -0.1, "reason": "", "tactical_action": "LIQUIDAR"},
        ]}

    def test_blocked_buy_becomes_hold_and_other_rows_are_untouched(self):
        manual = self.load(doc([entry(replaced_ticker="FTNT", chosen_ticker="MRK")], key="x"),
                           meta={"portfolio_optimizer": "x", "portfolio_run_ts": None})
        self.assertEqual(manual["status"], "absent")  # no run_ts -> hardcoded key, nothing for it
        manual = self.load(doc([entry(replaced_ticker="FTNT", chosen_ticker="MRK")], key=QU_KEY))
        weights = {"FTNT": 0.05, "GLD": 0.2, "KO": 0.1}
        senal, avisos = am._aplicar_overrides_manuales(self.senal(), weights, None, None, manual)
        rows = {r["ticker"]: r for r in senal["rebalances"]}
        self.assertEqual(rows["FTNT"]["action"], "HOLD")
        self.assertEqual(rows["FTNT"]["target_weight"], 0.02)
        self.assertEqual(rows["FTNT"]["original_action"], "BUY")
        self.assertEqual(rows["GLD"]["action"], "BUY")
        self.assertEqual(rows["KO"]["action"], "SELL")
        self.assertEqual([f["status"] for f in senal["flagged_by_override"]], ["BLOCKED"])
        self.assertTrue(avisos)

    def test_no_overrides_leaves_the_signal_alone(self):
        absent = {"status": "absent"}
        senal, avisos = am._aplicar_overrides_manuales(self.senal(), {"FTNT": 0.05}, None, None, absent)
        self.assertEqual(senal, self.senal())
        self.assertEqual(avisos, [])

    def test_broken_file_flags_nothing_in_the_portfolio_file(self):
        manual = self.load("{ broken")
        weights = {"FTNT": 0.05, "GLD": 0.2, "KO": 0.1}
        senal, _ = am._aplicar_overrides_manuales(self.senal(), weights, None, None, manual)
        self.assertEqual([r["action"] for r in senal["rebalances"]], ["BUY", "BUY", "SELL"])


class RunCycleExtrasTests(TempDirCase):
    def test_held_extras_follow_the_overrides(self):
        import run_cycle

        portfolio = {"optimizer": "quadratic_utility", "run_ts": "2026-10-08T12:12:53-05:00",
                     "tickers": ["AVGO"], "weights": {"AVGO": 1.0}}
        state_file = str(self.dir / "rotation.json")
        state = pio.empty_rotation_state({"portfolio_optimizer": "quadratic_utility",
                                          "portfolio_run_ts": portfolio["run_ts"]})
        state["target_overrides"] = {"FTNT": 0.05}
        write(state_file, state)
        write(self.path, doc([entry()]))
        with mock.patch.dict(os.environ, {"ROTATION_STATE_FILE": state_file}):
            self.assertEqual(run_cycle.rotation_held_extras(portfolio), ["MRK"])
        os.remove(self.path)
        with mock.patch.dict(os.environ, {"ROTATION_STATE_FILE": state_file}):
            self.assertEqual(run_cycle.rotation_held_extras(portfolio), ["FTNT"])


if __name__ == "__main__":
    unittest.main()
