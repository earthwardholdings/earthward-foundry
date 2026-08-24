"""
Regression tests for the Traceability service's hard rules.
Run: python3 -m pytest tests/  (or python3 tests/test_traceability.py if
pytest isn't available — see the __main__ fallback runner at the bottom).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import service as svc


def setup_part():
    svc.init_db(reset=True)
    return svc.create_part(part_number="TEST-PART", revision="A")


def test_cannot_accept_before_inspection():
    part_id = setup_part()
    try:
        svc.append_event(
            part_id, "acceptance_decision",
            source=svc.Source("human", "h1"), reference="R1",
        )
        assert False, "should have raised InvalidSequenceError"
    except svc.InvalidSequenceError:
        pass


def test_agent_cannot_write_acceptance_decision():
    part_id = setup_part()
    svc.append_event(part_id, "inspection_program_run",
                      source=svc.Source("agent", "a1"), reference="R1")
    svc.append_event(part_id, "inspection_result",
                      source=svc.Source("agent", "a1"), reference="R2")
    try:
        svc.append_event(
            part_id, "acceptance_decision",
            source=svc.Source("agent", "sneaky-agent"), reference="R3",
        )
        assert False, "should have raised UnauthorizedSourceError"
    except svc.UnauthorizedSourceError:
        pass


def test_agent_cannot_close_or_waive_ncr():
    part_id = setup_part()
    svc.append_event(part_id, "ncr_opened", source=svc.Source("agent", "a1"), reference="NCR-1")
    for etype in ("ncr_closed", "ncr_waived"):
        try:
            svc.append_event(part_id, etype, source=svc.Source("agent", "a1"), reference="NCR-1")
            assert False, f"should have raised UnauthorizedSourceError for {etype}"
        except svc.UnauthorizedSourceError:
            pass


def test_human_can_close_ncr():
    part_id = setup_part()
    svc.append_event(part_id, "ncr_opened", source=svc.Source("agent", "a1"), reference="NCR-1")
    result = svc.append_event(part_id, "ncr_closed", source=svc.Source("human", "h1"), reference="NCR-1")
    assert result["event_type"] == "ncr_closed"


def test_reference_required():
    part_id = setup_part()
    try:
        svc.append_event(part_id, "material_receipt", source=svc.Source("agent", "a1"), reference="")
        assert False, "should have raised TraceabilityError for empty reference"
    except svc.TraceabilityError:
        pass


def test_unknown_part_rejected():
    svc.init_db(reset=True)
    try:
        svc.append_event("does-not-exist", "material_receipt",
                          source=svc.Source("agent", "a1"), reference="R1")
        assert False, "should have raised UnknownPartError"
    except svc.UnknownPartError:
        pass


def test_correction_never_overwrites():
    part_id = setup_part()
    original = svc.append_event(part_id, "material_receipt",
                                 source=svc.Source("agent", "a1"), reference="CERT-1")
    svc.append_event(part_id, "correction", source=svc.Source("human", "h1"),
                      reference="CERT-1-FIXED", corrects_event_id=original["event_id"])
    rec = svc.get_record(part_id)
    event_types = [e["event_type"] for e in rec["events"]]
    # both the original and the correction are present — nothing was deleted
    assert event_types.count("material_receipt") == 1
    assert event_types.count("correction") == 1
    assert rec["events"][0]["reference"] == "CERT-1"  # original untouched


def test_correction_requires_valid_target():
    part_id = setup_part()
    try:
        svc.append_event(part_id, "correction", source=svc.Source("human", "h1"),
                          reference="R1", corrects_event_id="fake-id-does-not-exist")
        assert False, "should have raised TraceabilityError"
    except svc.TraceabilityError:
        pass


def test_status_derived_not_asserted():
    """There is no way to directly set current_status — it must always
    come from _derive_status() over the real event history."""
    part_id = setup_part()
    rec = svc.get_record(part_id)
    assert rec["current_status"] == "material_received"

    svc.append_event(part_id, "inspection_program_run", source=svc.Source("agent", "a1"), reference="R1")
    rec = svc.get_record(part_id)
    assert rec["current_status"] == "inspection_pending"

    svc.append_event(part_id, "ncr_opened", source=svc.Source("agent", "a1"), reference="NCR-1")
    rec = svc.get_record(part_id)
    assert rec["current_status"] == "ncr_open"


def test_gap_report_flags_open_ncr_after_acceptance_attempt_blocked():
    part_id = setup_part()
    svc.append_event(part_id, "inspection_program_run", source=svc.Source("agent", "a1"), reference="R1")
    svc.append_event(part_id, "inspection_result", source=svc.Source("agent", "a1"), reference="R2")
    svc.append_event(part_id, "ncr_opened", source=svc.Source("agent", "a1"), reference="NCR-1")
    rec = svc.get_record(part_id)
    assert rec["current_status"] == "acceptance_blocked"


ALL_TESTS = [
    test_cannot_accept_before_inspection,
    test_agent_cannot_write_acceptance_decision,
    test_agent_cannot_close_or_waive_ncr,
    test_human_can_close_ncr,
    test_reference_required,
    test_unknown_part_rejected,
    test_correction_never_overwrites,
    test_correction_requires_valid_target,
    test_status_derived_not_asserted,
    test_gap_report_flags_open_ncr_after_acceptance_attempt_blocked,
]


if __name__ == "__main__":
    passed, failed = 0, 0
    for t in ALL_TESTS:
        try:
            t()
            print(f"PASS  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL  {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR {t.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
