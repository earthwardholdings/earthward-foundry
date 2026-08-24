"""
Wires the Traceability Agent's system prompt (see
agents/records/traceability.md) to the real service in service.py, via
Anthropic tool-use function calling.

The agent gets exactly two tools, matching its two-function contract:
  - append_event
  - get_record

It deliberately has NO other tools — no update, no delete, no direct DB
access. If the agent's prompt is ever compromised or confused, the worst
it can do through these tools is what service.py already enforces:
no human-only event types, no invalid sequences, no editing history.

Usage:
    from anthropic import Anthropic
    from agent_tools import TOOLS, dispatch_tool_call

    client = Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=open("../../agents/records/traceability.md").read(),
        tools=TOOLS,
        messages=[{"role": "user", "content": "Log that lot L-2291 was received for part <id>, cert CERT-4471, alloy 6061-T6."}],
    )
    # then for any tool_use block in response.content:
    #   result = dispatch_tool_call(block.name, block.input)
    #   ... send result back as a tool_result message
"""

from typing import Any

import service as svc

TOOLS = [
    {
        "name": "append_event",
        "description": (
            "Append a new event to a part's permanent chain-of-custody record. "
            "This is append-only: it can never edit or delete a past event. "
            "If correcting a prior event, use event_type='correction' and set "
            "corrects_event_id — the original event remains visible. "
            "NOTE: acceptance_decision, ncr_closed, and ncr_waived require a "
            "human source; calling with source.type='agent' for these will be "
            "rejected by the service, not silently accepted."
        ),
        "input_schema": {
            "type": "object",
            "required": ["part_id", "event_type", "source", "reference"],
            "properties": {
                "part_id": {"type": "string"},
                "event_type": {
                    "type": "string",
                    "enum": sorted(svc.VALID_EVENT_TYPES),
                },
                "source": {
                    "type": "object",
                    "required": ["type", "id"],
                    "properties": {
                        "type": {"type": "string", "enum": ["agent", "human"]},
                        "id": {
                            "type": "string",
                            "description": "Agent name (e.g. 'cmm-programming-agent') or named human employee ID.",
                        },
                    },
                },
                "reference": {
                    "type": "string",
                    "description": "Pointer to supporting data — cert number, inspection report ID, NCR ID, sign-off record ID. Never free text standing alone.",
                },
                "data": {
                    "type": "object",
                    "description": "Event-type-specific payload (measured values, deviation details, NCR summary, etc.)",
                },
                "corrects_event_id": {
                    "type": "string",
                    "description": "Set only when event_type='correction' — the event_id being corrected.",
                },
            },
        },
    },
    {
        "name": "get_record",
        "description": (
            "Read the full, faithful event history for a part, plus its "
            "derived current_status and a gap_report. Read-only."
        ),
        "input_schema": {
            "type": "object",
            "required": ["part_id"],
            "properties": {
                "part_id": {"type": "string"},
            },
        },
    },
]


def dispatch_tool_call(name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    """Call this with the tool_use block's name/input from a Claude
    response. Returns a JSON-serializable dict — either the result or a
    structured error, never raises past this boundary so the calling
    agent loop can feed the rejection back to the model as a tool_result
    and let it explain the rejection to whoever asked for it."""

    try:
        if name == "append_event":
            source = svc.Source(type=tool_input["source"]["type"], id=tool_input["source"]["id"])
            return svc.append_event(
                part_id=tool_input["part_id"],
                event_type=tool_input["event_type"],
                source=source,
                reference=tool_input["reference"],
                data=tool_input.get("data"),
                corrects_event_id=tool_input.get("corrects_event_id"),
            )

        if name == "get_record":
            return svc.get_record(part_id=tool_input["part_id"])

        return {"error": "UnknownTool", "message": f"No such tool: {name!r}"}

    except svc.TraceabilityError as e:
        # This is the important path: a rejection is returned as data,
        # not swallowed — the agent sees exactly why the write failed
        # and must report that faithfully, per its NEVER-hide-a-failure rule.
        return {"error": type(e).__name__, "message": str(e)}
