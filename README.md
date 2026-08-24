# Earthward Foundry & Works — Agent Fleet Repository

> Understand the work before making it. Use appropriate materials. Build with care.
> Measure the result. Keep a useful record. Maintain what is worth keeping.

This repository holds the operating scaffold for Earthward's agent fleet: the
role-trained AI agents that support (never replace) the human disciplines of
the foundry, plus the shared data schema they all read and write.

## What's here

```
earthward-foundry/
├── docs/                       institutional framework, roles, build order
├── schema/                     shared traceability record schema (JSON Schema)
├── services/
│   └── traceability/           RUNNABLE Phase-1 core-loop service (see below)
└── agents/                     one house per folder, one file per agent
    ├── leadership/
    ├── engineering/            Design what should exist
    ├── materials/              Understand what it is made from
    ├── forge/                  Transform material into physical form
    ├── assembly/                Turn components into systems
    ├── metrology/              Measure what was actually produced
    ├── validation/             Prove that it performs
    ├── records/                Preserve exactly what happened
    └── stewardship/            Maintain, improve, responsibly retire
```

## The Traceability service is real and runs today

`services/traceability/` is not a stub — it's a working implementation of
Phase 1 from the build order: an append-only part record store that
enforces the fleet's hard rules in code (human-only sign-off events,
valid event sequencing, no editing history) rather than trusting every
agent's prompt to self-police. It has a passing test suite and a narrated
demo. Start here:

```bash
cd services/traceability
python3 demo.py                    # narrated walkthrough, 2 intentional rejections
python3 tests/test_traceability.py # regression suite
```

See `services/traceability/README.md` for the full breakdown of what's
enforced where, the HTTP API, and how to wire the actual Traceability
Agent prompt to it via Claude tool use.

## The eight houses

| House | Question it answers |
|---|---|
| Engineering | Design what should exist |
| Materials | Understand what it is made from |
| Forge | Transform material into physical form |
| Assembly | Turn components into systems |
| Metrology | Measure what was actually produced |
| Validation | Prove that it performs |
| Records | Preserve exactly what happened |
| Stewardship | Maintain, improve, and responsibly retire what was built |

## The non-negotiable rules (every agent, no exceptions)

1. **No agent self-certifies its own output.** Every irreversible or
   safety/quality/spend-relevant action requires a named human sign-off.
2. **No agent hides a failure to look complete.** Blocked, failed, or
   uncertain results are reported as such — never smoothed over.
3. **No agent invents a standard, spec, or certification.** If no real
   standard backs a recommendation, the agent says so and routes to a human.
4. **Every escalation names who it goes to** — never just "a human."

## Build order

This fleet is not meant to go live all at once. The proven order is:

1. **Traceability Agent** (`agents/records/traceability.md`) — every other
   agent's output is worthless without a real record trail.
2. **CMM Programming + Quality Engineering Agents** (`agents/metrology/`) —
   establishes the pass/fail backbone.
3. **Manufacturing Engineer + Mechanical Design Engineer Agents**
   (`agents/engineering/`) — gets one real part moving through the shop.
4. **Metallurgist + Foundry Process Engineer Agents** (`agents/materials/`)
   — once one part-family is proven.
5. Expand outward to Forge, Assembly, Validation, and the rest of
   Stewardship as volume justifies it.

See `docs/build-order.md` for the full rationale.

## Agent prompt format

Every agent file follows the same four-part structure so they drop directly
into a system prompt:

```
JOB:      what the agent does, precisely
NEVER:    the hard boundaries it does not cross
ESCALATE: the named-human handoff trigger(s)
OUTPUT:   the structured format it always responds in
```

## Shared spine

All house agents write events into one append-only part record, maintained
by the Traceability Agent. See `schema/part-record.schema.json`.

## Getting this into git

```bash
cd earthward-foundry
git init
git remote add origin https://github.com/earthwardholdings/earthward-foundry.git
git add .
git commit -m "Initial agent fleet scaffold: 8 houses, 31 agents, shared traceability schema"
git branch -M main
git push -u origin main
```
