"""
Phase 2 proof: CMM Programming + Quality Engineering wired to the
Traceability spine, running one real part through fail -> NCR -> human
resolution -> re-inspect -> pass -> human acceptance.

Run: python3 demo_phase2.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "traceability"))
import service as trace  # noqa: E402
import cmm
import quality


def section(t):
    print(f"\n{'=' * 70}\n{t}\n{'=' * 70}")


def main():
    trace.init_db(reset=True)

    section("1. Create part + first CMM run (one feature fails)")
    part_id = trace.create_part("EW-BRACKET-014", "B")
    result = cmm.run_inspection(
        part_id, "CMM-PROG-v3",
        features=[
            {"name": "bore_dia_A", "nominal": 12.50, "tolerance": 0.02, "measured": 12.47},
            {"name": "face_flatness", "nominal": 0.00, "tolerance": 0.05, "measured": 0.01},
        ],
    )
    print(f"Overall: {result['overall']}")
    for f in result["features"]:
        print(f"  {f['name']}: measured={f['measured']} -> {f['result']}")

    section("2. Quality Engineering checks acceptance status")
    status = quality.acceptance_status(part_id)
    print(status)
    assert status["status"] == "CLEAR", "no NCR opened yet — this is expected, CMM only measures"

    section("3. Quality Engineering opens an NCR against the failed feature")
    quality.open_ncr(part_id, "NCR-2291", "bore_dia_A", root_cause_hypothesis="tool wear")
    status = quality.acceptance_status(part_id)
    print(status)
    assert status["status"] == "BLOCKED"

    section("4. Try to accept anyway (agent attempt — should be REJECTED)")
    try:
        trace.append_event(part_id, "acceptance_decision",
                            source=trace.Source("agent", "quality-engineering-agent"),
                            reference="ACPT-001", data={"decision": "accept"})
        print("!! SHOULD NOT PRINT")
    except trace.UnauthorizedSourceError as e:
        print("Correctly rejected:", e)

    section("5. Named human resolves the NCR (rework) and closes it")
    trace.append_event(part_id, "ncr_closed",
                        source=trace.Source("human", "m.chen-quality-director"),
                        reference="NCR-2291", data={"resolution": "reworked bore to spec"})
    status = quality.acceptance_status(part_id)
    print(status)
    assert status["status"] == "CLEAR"

    section("6. Re-inspect after rework — now passes")
    result = cmm.run_inspection(
        part_id, "CMM-PROG-v3",
        features=[
            {"name": "bore_dia_A", "nominal": 12.50, "tolerance": 0.02, "measured": 12.50},
            {"name": "face_flatness", "nominal": 0.00, "tolerance": 0.05, "measured": 0.01},
        ],
    )
    print(f"Overall: {result['overall']}")

    section("7. Named human accepts the part")
    trace.append_event(part_id, "acceptance_decision",
                        source=trace.Source("human", "j.rivera"),
                        reference="ACPT-001", data={"decision": "accept"})

    section("8. Final record")
    rec = trace.get_record(part_id)
    print(f"current_status: {rec['current_status']}")
    print(f"gap_report: {rec['gap_report']}")
    for e in rec["events"]:
        print(f"  - {e['event_type']:<22} by {e['source']['type']}:{e['source']['id']}")

    section("9. Systemic pattern check across a hypothetical multi-part run")
    trace.init_db(reset=False)
    ids = [part_id]
    for i in range(2):
        pid = trace.create_part(f"EW-BRACKET-01{i+5}", "B")
        quality.open_ncr(pid, f"NCR-330{i}", "bore_dia_A", root_cause_hypothesis="tool wear")
        ids.append(pid)
    pattern = quality.correlate_root_cause(ids)
    print("systemic_patterns:", pattern["systemic_patterns"])
    assert "tool wear" in pattern["systemic_patterns"], "3rd tool-wear NCR should trigger systemic flag"
    print("Correctly flagged as systemic (3+ NCRs, same root cause) -> escalate to Process Engineer")

    section("Phase 2 proven: CMM + Quality + Traceability working as one loop.")


if __name__ == "__main__":
    main()
