"""
Runnable proof that the Traceability service's hard rules actually hold.
Run: python3 demo.py

This is not a unit test suite (see tests/ for that) — it's a narrated
walkthrough of one real part moving through the core loop, deliberately
including a few illegal moves to show they get rejected rather than
silently accepted.
"""

import service as svc


def section(title: str) -> None:
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")


def main() -> None:
    svc.init_db(reset=True)

    section("1. Create a part")
    part_id = svc.create_part(part_number="EW-BRACKET-014", revision="B")
    print(f"Created part_id: {part_id}")

    section("2. Log material receipt (agent-sourced — fine, non-authority event)")
    r = svc.append_event(
        part_id, "material_receipt",
        source=svc.Source("agent", "materials-engineer-agent"),
        reference="CERT-4471",
        data={"lot": "L-2291", "alloy": "6061-T6"},
    )
    print("Logged:", r)

    section("3. Try to log acceptance_decision way too early (should be REJECTED)")
    try:
        svc.append_event(
            part_id, "acceptance_decision",
            source=svc.Source("human", "j.rivera"),
            reference="ACPT-001",
            data={"decision": "accept"},
        )
        print("!! THIS SHOULD NOT PRINT — rejection failed to fire")
    except svc.InvalidSequenceError as e:
        print("Correctly rejected:", e)

    section("4. Process steps")
    svc.append_event(
        part_id, "process_step_start",
        source=svc.Source("agent", "manufacturing-engineer-agent"),
        reference="OP-10-START",
        data={"operation": "OP10 mill face"},
    )
    svc.append_event(
        part_id, "process_step_complete",
        source=svc.Source("agent", "manufacturing-engineer-agent"),
        reference="OP-10-COMPLETE",
        data={"operation": "OP10 mill face", "cycle_time_min": 4.2},
    )
    print("Process steps logged.")

    section("5. CMM inspection — program run, then result (FAIL)")
    svc.append_event(
        part_id, "inspection_program_run",
        source=svc.Source("agent", "cmm-programming-agent"),
        reference="CMM-PROG-v3",
    )
    svc.append_event(
        part_id, "inspection_result",
        source=svc.Source("agent", "cmm-programming-agent"),
        reference="CMM-RUN-0091",
        data={"feature": "bore_dia_A", "measured": 12.47, "tolerance": "12.50 +/-0.02", "result": "FAIL"},
    )
    print("Inspection logged as FAIL — exactly as measured, not softened.")

    section("6. Quality Engineering opens an NCR (agent-sourced — fine)")
    svc.append_event(
        part_id, "ncr_opened",
        source=svc.Source("agent", "quality-engineering-agent"),
        reference="NCR-2291",
        data={"feature": "bore_dia_A", "root_cause_hypothesis": "tool wear"},
    )
    print("NCR opened. Checking status...")
    rec = svc.get_record(part_id)
    print("current_status:", rec["current_status"])

    section("7. Try to close the NCR as an AGENT (should be REJECTED)")
    try:
        svc.append_event(
            part_id, "ncr_closed",
            source=svc.Source("agent", "quality-engineering-agent"),
            reference="NCR-2291-CLOSE",
            data={"resolution": "rework"},
        )
        print("!! THIS SHOULD NOT PRINT — rejection failed to fire")
    except svc.UnauthorizedSourceError as e:
        print("Correctly rejected:", e)

    section("8. A named human closes the NCR (allowed)")
    svc.append_event(
        part_id, "ncr_closed",
        source=svc.Source("human", "m.chen-quality-director"),
        reference="NCR-2291-CLOSE",
        data={"resolution": "rework, re-inspected"},
    )
    print("NCR closed by named human.")

    section("9. Re-inspect and pass")
    svc.append_event(
        part_id, "inspection_program_run",
        source=svc.Source("agent", "cmm-programming-agent"),
        reference="CMM-PROG-v3",
    )
    svc.append_event(
        part_id, "inspection_result",
        source=svc.Source("agent", "cmm-programming-agent"),
        reference="CMM-RUN-0092",
        data={"feature": "bore_dia_A", "measured": 12.50, "tolerance": "12.50 +/-0.02", "result": "PASS"},
    )
    print("Re-inspection logged as PASS.")

    section("10. A named human accepts the part (allowed — precondition now met)")
    svc.append_event(
        part_id, "acceptance_decision",
        source=svc.Source("human", "j.rivera"),
        reference="ACPT-001",
        data={"decision": "accept"},
    )
    print("Accepted.")

    section("11. Try to edit history directly (the API doesn't even expose this —")
    print("    there is no update_event() or delete_event() function in service.py.")
    print("    The only way to fix a past event is to append a 'correction' event")
    print("    that references the original. Demonstrating that instead:")

    rec = svc.get_record(part_id)
    first_event_id = rec["events"][0]["event_id"]
    svc.append_event(
        part_id, "correction",
        source=svc.Source("human", "j.rivera"),
        reference="CERT-4471-CORRECTED",
        corrects_event_id=first_event_id,
        data={"note": "cert number had a typo, corrected lot cert on file"},
    )
    print(f"Correction appended, referencing original event {first_event_id}")
    print("(original event is still in the record, untouched — see below)")

    section("12. Final record — full chain of custody for this part")
    rec = svc.get_record(part_id)
    print(f"part_number: {rec['part_number']}  revision: {rec['revision']}")
    print(f"current_status: {rec['current_status']}")
    print(f"gap_report: {rec['gap_report']}")
    print(f"total events: {len(rec['events'])}")
    for e in rec["events"]:
        corr = f" (corrects {e['corrects_event_id']})" if e["corrects_event_id"] else ""
        print(f"  - {e['event_type']:<22} by {e['source']['type']}:{e['source']['id']:<28} ref={e['reference']}{corr}")

    section("Done. This part's record is complete, gap-free, and every")
    print("authority-bearing event was written by a named human, not an agent.")


if __name__ == "__main__":
    main()
