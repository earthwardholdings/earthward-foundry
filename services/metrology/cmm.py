"""
CMM Programming Agent logic (Phase 2). Depends on the traceability
service's two public functions only — append_event / get_record — never
touches the traceability database directly.

Mirrors agents/metrology/cmm-programming.md exactly:
  - reports PASS / FAIL / MARGINAL (within 10% of a limit) per feature
  - never adjusts a tolerance/measurement to force a PASS
  - never marks a part "accepted" — writes inspection_result only
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "traceability"))
import service as trace  # noqa: E402

CMM_AGENT_ID = "cmm-programming-agent"


def evaluate_feature(measured: float, nominal: float, tolerance: float) -> str:
    """PASS / FAIL / MARGINAL — MARGINAL means within 10% of the tolerance
    band's limit. Never invents or bends a tolerance."""
    lower, upper = nominal - tolerance, nominal + tolerance
    band = upper - lower
    margin_zone = band * 0.10

    if lower <= measured <= upper:
        if measured <= lower + margin_zone or measured >= upper - margin_zone:
            return "MARGINAL"
        return "PASS"
    return "FAIL"


def run_inspection(part_id: str, program_ref: str, features: list[dict]) -> dict:
    """
    features: list of {name, nominal, tolerance, measured}
    Writes inspection_program_run, then one inspection_result event
    (data carries the full feature-by-feature report — the schema's
    event.data is intentionally free-form per event type).
    Returns the structured report; never softens a FAIL into a PASS.
    """
    trace.append_event(
        part_id, "inspection_program_run",
        source=trace.Source("agent", CMM_AGENT_ID),
        reference=program_ref,
    )

    report = []
    for f in features:
        result = evaluate_feature(f["measured"], f["nominal"], f["tolerance"])
        report.append({**f, "result": result})

    overall = "FAIL" if any(r["result"] == "FAIL" for r in report) else (
        "MARGINAL" if any(r["result"] == "MARGINAL" for r in report) else "PASS"
    )

    event = trace.append_event(
        part_id, "inspection_result",
        source=trace.Source("agent", CMM_AGENT_ID),
        reference=program_ref,
        data={"overall": overall, "features": report},
    )

    return {"event_id": event["event_id"], "overall": overall, "features": report}
