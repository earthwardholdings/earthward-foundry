"""
Quality Engineering Agent logic (Phase 2). Mirrors
agents/metrology/quality-engineering.md exactly:
  - never closes/waives an NCR itself (service.py rejects that at the
    HUMAN_ONLY_EVENT_TYPES layer regardless — this module doesn't even try)
  - defaults to BLOCKED on any doubt
  - correlates 3+ same-root-cause NCRs as a systemic pattern
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "traceability"))
import service as trace  # noqa: E402

QUALITY_AGENT_ID = "quality-engineering-agent"


def open_ncr(part_id: str, ncr_id: str, feature: str, root_cause_hypothesis: str) -> dict:
    return trace.append_event(
        part_id, "ncr_opened",
        source=trace.Source("agent", QUALITY_AGENT_ID),
        reference=ncr_id,
        data={"feature": feature, "root_cause_hypothesis": root_cause_hypothesis},
    )


def acceptance_status(part_id: str) -> dict:
    """BLOCKED if any NCR open and unresolved/unwaived, CLEAR otherwise.
    Defaults to BLOCKED on any doubt (empty record, no CMM data, etc.)."""
    record = trace.get_record(part_id)
    events = record["events"]

    opened = [e for e in events if e["event_type"] == "ncr_opened"]
    closed_refs = {e["reference"] for e in events if e["event_type"] in ("ncr_closed", "ncr_waived")}
    open_ncrs = [e for e in opened if e["reference"] not in closed_refs]

    status = "BLOCKED" if open_ncrs else "CLEAR"
    return {
        "part_id": part_id,
        "status": status,
        "open_ncrs": [{"reference": e["reference"], "data": e["data"]} for e in open_ncrs],
        "waiting_on": (
            f"named human to resolve/waive: {[e['reference'] for e in open_ncrs]}"
            if open_ncrs else None
        ),
    }


def correlate_root_cause(part_ids: list[str]) -> dict:
    """Surfaces a systemic pattern (3+ NCRs, same root_cause_hypothesis)
    across a set of parts — does not just log NCRs in isolation."""
    causes: dict[str, list[str]] = {}
    for pid in part_ids:
        record = trace.get_record(pid)
        for e in record["events"]:
            if e["event_type"] == "ncr_opened":
                cause = e["data"].get("root_cause_hypothesis", "unspecified")
                causes.setdefault(cause, []).append(pid)

    systemic = {c: parts for c, parts in causes.items() if len(parts) >= 3}
    return {"all_causes": causes, "systemic_patterns": systemic}
