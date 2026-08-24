# Metrology Service (Phase 2)

CMM Programming + Quality Engineering, wired directly to the
Traceability spine (`services/traceability/service.py`) via its two
public functions only.

- `cmm.py` — `run_inspection()` writes `inspection_program_run` +
  `inspection_result`, evaluates PASS/FAIL/MARGINAL per feature (10%
  margin band), never adjusts a tolerance to force a pass.
- `quality.py` — `open_ncr()`, `acceptance_status()` (BLOCKED/CLEAR,
  defaults to BLOCKED on doubt), `correlate_root_cause()` (flags 3+
  same-cause NCRs as systemic).
- `demo_phase2.py` — run it: `python3 demo_phase2.py`. Proves one real
  part through FAIL -> NCR -> human resolves -> re-inspect -> PASS ->
  human accepts, plus a rejected agent-acceptance attempt and a
  cross-part systemic-pattern flag.

Next per docs/build-order.md Phase 3: wire Manufacturing Engineer +
Mechanical Design Engineer, get one real drawing moving through this
same loop.
