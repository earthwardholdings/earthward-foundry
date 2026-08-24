# Traceability Service

The first piece of the core loop — see `docs/build-order.md`, Phase 1.
Everything else in the agent fleet depends on this existing and being
trustworthy before any other agent goes live.

## Why it's built this way

`service.py` has **zero external dependencies** — pure Python stdlib
(`sqlite3`, `dataclasses`, `uuid`). This is deliberate: the spine of the
whole system shouldn't be coupled to a web framework or ORM choice. Two
public functions, matching the Traceability Agent's own stated contract:

- `append_event(...)` — the only way anything writes to a part's history
- `get_record(...)` — the only way anything reads it

Everything else (`api.py`, `agent_tools.py`) is a thin adapter on top.

## What's enforced in code, not just in the prompt

The prompt in `agents/records/traceability.md` says the agent "never"
does certain things. This service backs that up structurally so a
misbehaving or confused agent call can't actually do them:

| Rule | Enforced by |
|---|---|
| `acceptance_decision`, `ncr_closed`, `ncr_waived` require a human source | `HUMAN_ONLY_EVENT_TYPES` check in `append_event`, raises `UnauthorizedSourceError` |
| Can't log `acceptance_decision` before `inspection_result` exists | `_check_sequence()`, raises `InvalidSequenceError` |
| Can't log `inspection_result` before `inspection_program_run` exists | same |
| Can't close/waive an NCR that was never opened | same |
| Every event needs a real reference, not free text | `append_event` raises `TraceabilityError` on empty reference |
| History is append-only | there is no `update_event()` or `delete_event()` function — corrections are new events via `corrects_event_id` |
| `current_status` is derived, never asserted | `_derive_status()` computes it fresh from event history every read; there is no column an agent can set directly |
| Gaps are reported, not filled | `check_gaps()` / `gap_report` in every `get_record()` response |

## Running it

```bash
cd services/traceability

# 1. Prove the rules hold (narrated walkthrough, includes 2 intentional rejections)
python3 demo.py

# 2. Regression tests
python3 tests/test_traceability.py

# 3. HTTP API smoke test (no live server needed — uses Flask's test client)
python3 tests/test_api.py

# 4. Run the actual API
pip install flask
python3 api.py
# -> http://127.0.0.1:5000
```

### HTTP API

| Method | Path | Purpose |
|---|---|---|
| POST | `/parts` | create a part (`part_number`, `revision`) |
| GET | `/parts/<part_id>` | full record: events, derived status, gap report |
| POST | `/parts/<part_id>/events` | append an event (enforces every rule above) |
| GET | `/parts/<part_id>/gaps` | just the gap report |
| GET | `/health` | liveness check |

A rejected write returns the real HTTP status for what went wrong:
`403` unauthorized source, `409` invalid sequence, `404` unknown part,
`400` malformed/missing reference.

### Wiring the actual Traceability Agent

`agent_tools.py` exposes `TOOLS` (an Anthropic tool-use schema with
exactly `append_event` and `get_record` — nothing else, on purpose) and
`dispatch_tool_call(name, input)` to execute one. Load
`agents/records/traceability.md` as the system prompt, pass `TOOLS`, and
route any `tool_use` block through `dispatch_tool_call`. See the
docstring at the top of `agent_tools.py` for the exact call shape.

## Note on FastAPI vs Flask

The build plan called for FastAPI + SQLAlchemy. This sandbox has no
network access to `pip install` them, so this build uses Flask + stdlib
`sqlite3` instead — which turned out fine, since `service.py` has no
framework dependency at all. If you want FastAPI's async/pydantic
ergonomics later, only `api.py` needs to change; treat it as a drop-in
swap, not a rewrite.

## Next

Per `docs/build-order.md` Phase 2: wire the CMM Programming and Quality
Engineering agents to `append_event`/`get_record` the same way, pick one
real part, and run it through by hand before automating anything further.
