# Earthward Rescue Task Force — Runner Service

Built on the same foundation as `services/traceability/` — the same four
rules that govern every foundry agent apply here without exception:

1. No agent self-certifies its own output.
2. No agent hides a failure to look complete.
3. No agent invents a standard or authorization.
4. Every escalation names who it goes to.

## What this is

A pipeline runner that routes rescue incidents through the foundry agent
fleet, remapped to rescue functions. The foundry's physical workflow
(design → make → measure → accept) becomes the incident workflow
(assess → plan → deploy → extract → verify → close).

The same enforcement that prevents a CMM agent from marking a part
"accepted" prevents an operations agent from closing an incident before
objectives are verified. Same code, same pattern, different domain.

## Foundry → Rescue mapping

| Foundry house / agent       | Rescue equivalent         |
|-----------------------------|---------------------------|
| Records / Traceability      | Incident Log Agent        |
| Metrology / Quality Eng.    | Assessment Agent          |
| Engineering / Mfg. Engineer | Planning Agent            |
| Materials / Materials Eng.  | Resource Agent            |
| Forge / Fabrication Seq.    | Operations Agent          |
| Assembly / Integration Eng. | Integration Agent         |
| Validation / Test & Val.    | Verification Agent        |
| EHS / Safety                | Safety Agent              |
| Leadership / GM             | Command Agent             |

## Files

```
services/rescue/
├── models.py        data structures — Incident, IncidentAction, Hazard,
│                    Victim, Escalation, OperationalPlan, enums, errors
├── incident_log.py  append-only incident store (SQLite, zero external deps)
│                    public API: open_incident, log_action, open_hazard,
│                    clear_hazard, add_victim, raise_escalation,
│                    draft_plan, approve_plan, get_incident
├── runner.py        TaskForceRunner — 9-phase pipeline, human gates,
│                    intake() and resume() entry points
└── demo.py          narrated walkthrough — one urban SAR incident end-to-end
```

## Running the demo

```bash
cd services/rescue
python demo.py
```

The demo walks one urban SAR incident (structural collapse, 2 trapped, gas
leak) through all 9 phases and shows 2 intentional rejections:

- Agent attempts to approve its own plan → `UnauthorizedSourceError`
- Agent attempts to close incident before objectives verified → `InvalidSequenceError`

No dependencies beyond the Python standard library.

## The pipeline

```
intake()
  Phase 1  Incident Log Agent   — open incident, activate log
  Phase 2  Safety Agent         — hazard sweep, escalate to Safety Officer
  Phase 3  Assessment Agent     — situational picture, surface gaps
  Phase 4  Resource Agent       — identify requirements, escalate to Logistics
  Phase 5  Planning Agent       — draft operational plan
  *** HALT — awaiting Incident Commander plan approval ***

resume(from_phase="operations-agent", authorized_by=<human IC>)
  Phase 6  Operations Agent     — deploy teams against approved plan
  Phase 7  Integration Agent    — check team-to-objective coverage
  Phase 8  Verification Agent   — confirm objectives met (requires extraction_complete)
  Phase 9  Command Agent        — cross-team status roll-up

Human logs: INCIDENT_CLOSED → AFTER_ACTION_FILED
```

## Human-only actions

These cannot be logged by an agent source — the service rejects the
attempt with `UnauthorizedSourceError`:

- `operational_plan_approved`
- `victim_transferred`
- `hazard_mitigated`
- `hazard_cleared`
- `incident_closed`

## Sequence rules (enforced in code)

| Action                    | Requires                        |
|---------------------------|---------------------------------|
| `operational_plan_approved` | `operational_plan_drafted`    |
| `team_deployed`           | `operational_plan_approved`     |
| `extraction_started`      | `victim_located`                |
| `extraction_complete`     | `extraction_started`            |
| `victim_stabilized`       | `victim_assessed`               |
| `victim_transferred`      | `victim_stabilized`             |
| `objective_verified`      | `team_deployed`                 |
| `incident_closed`         | `objective_verified`            |
| `after_action_filed`      | `incident_closed`               |

Additionally, `team_deployed`, `extraction_started`, `victim_transferred`,
and `incident_closed` are blocked while any critical or high hazard is open.

## Escalation rules

`raise_escalation()` rejects vague targets. `escalate_to` must name a
specific role or callsign — "a human" or "someone" is rejected outright.

## What's not here yet

- HTTP API wrapper (same pattern as `services/traceability/api.py`)
- Claude tool-use wiring (same pattern as `services/traceability/agent_tools.py`)
- Personnel and resource registry (stubs in `models.py`, not yet persisted)
- UI / field interface — framework only at this stage

These are the next build phases, in that order.
