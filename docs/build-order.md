# Build Order

Same discipline that governs the physical foundry applies to the agent
fleet: **prove one vertical before expanding surface area.** Don't stand up
all agents at once.

## Phase 1 — The spine
**`agents/records/traceability.md`** — prompt
**`services/traceability/`** — running implementation ✅
Every other agent's output is worthless without a real record trail. This
goes live first, alone, against the shared schema in
`schema/part-record.schema.json`. The implementation in `services/traceability/`
enforces the hard rules (human-only acceptance/NCR-closure events, valid
event sequencing, append-only history) in code, with a passing test suite
and a runnable demo — not just as prompt instructions.

## Phase 2 — Pass/fail backbone
**`agents/metrology/cmm-programming.md`**
**`agents/metrology/quality-engineering.md`**
Establishes the acceptance-decision workflow: measure against tolerance,
track non-conformances, block acceptance until resolved. Both write events
to the Traceability Agent.

## Phase 3 — One real part
**`agents/engineering/manufacturing-engineer.md`**
**`agents/engineering/mechanical-design-engineer.md`**
Gets a single real part moving through Engineering → Materials → Forge.
This is the proof loop: one drawing, one process plan, one measured
result, one acceptance decision, fully traced.

## Phase 4 — Once one part-family is proven
**`agents/materials/metallurgist.md`**
**`agents/materials/foundry-process-engineer.md`**
Material selection and process-parameter tuning layer in once the basic
design → make → measure → accept loop is trusted.

## Phase 5 — Expand outward
Remaining agents in Forge, Assembly, Validation, and the rest of
Stewardship (Procurement, EHS, Program Management, Applications
Engineering, Maintenance) come online as volume and complexity justify it
— not simultaneously, and not speculatively.

## What "not done yet" means

As of this scaffold:
- None of these agents are wired to real tools or live data sources.
- None should go live simultaneously.
- The five Phase 1–3 agents have complete, detailed system prompts
  (JOB / NEVER / ESCALATE / OUTPUT) ready to wire into a framework.
- The remaining ~26 agents have complete system prompts as well, but are
  intentionally sequenced behind the first five per this document.

## Cross-cutting rules (apply to every agent, no exceptions)

1. No agent self-certifies its own output. Every irreversible or
   safety/quality/spend-relevant action requires a named human sign-off.
2. No agent hides a failure to look complete — blocked, failed, or
   uncertain results are reported as such, never smoothed over or
   silently retried into a passing-looking state.
3. No agent invents a standard, spec, or certification. If no real
   standard backs a recommendation, the agent says so and routes to a
   human for real testing/verification.
4. Every escalation names who it goes to — never just "a human."
