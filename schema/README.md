# Schema notes

`part-record.schema.json` is the single shared spine every house agent
writes to, via the Traceability Agent only.

**Key design choices baked into the schema:**

- **Append-only** — `events` is a list, never mutated in place. Corrections
  reference the original `event_id` rather than overwriting it.
- **Every event traces to a source** — either a named agent or a named
  human employee ID, never anonymous.
- **`current_status` is derived, not asserted** — computed from event
  history, not set arbitrarily, so it can be recomputed/audited at any
  time.
- **No agent may write an `acceptance_decision` event.** This must be
  enforced at the application layer (a role check on the write path), not
  left to convention — acceptance is always a named human's action.
