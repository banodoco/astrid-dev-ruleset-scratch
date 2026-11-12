# Tasks — Recorded boundaries and an offline generation harness

[Plan](plan.md) · [Inputs](inputs.md)

A draft can use a short outline with unknowns. Before dispatch, every task needs one bounded outcome, its input and deliverable, dependencies, a suitable route, and focused proof. Name source identity where one task consumes another project's output. Reuse the prior-art and source identities in [inputs.md](inputs.md); don't repeat them.

**Task ids:** `RB-1`, `RB-2`, …

**Critical path:** RB-2 → RB-3 → RB-4 → R. RB-1 runs in parallel with RB-2 and must land before RB-4.

**Test inventory:**
- Agent:
  - `tests/integrations/test_remote_machine_cpu.py`
  - `tests/providers/test_provider_contract.py` and `tests/providers/runpod/fixtures/`
  - `tests/packs/runpod/test_pack_actions.py`
  - `tests/sdk/test_project_render.py`
  - `tests/sdk/test_project_render_rrp.py`
  - `tests/sdk/test_invocation_observation.py`
  - `tests/core/execution/test_bug14_settlement_liveness.py`
  - `tests/core/execution/test_claim_head_of_line.py`
  - the `networkVolumeId` readers found by `rg -l networkVolumeId tests`
- Runtime: the tests the inline-proof branch adds for `runtime_protocol/service.py:_stage_outputs` and `runtime_protocol/store.py:_claim_task`.

**Worker command:** `bash scripts/worker-env/agent-pytest.sh -q <files>`, with the integration lane's Runtime checkout. RB-1 makes this literal for the journey.

| Task / outcome | Route | Depends on | Scope | Focused proof | Progress |
| --- | --- | --- | --- | --- | --- |
| RB-1 The CPU journey runs in the shared worker environment and in the Agent integration lane: identify the setup the lane is missing (setup lives in `tests/conftest.py` and its helpers), add it to astrid-dev's [worker environment](../../env/README.md), and coordinate the lane change with [Plan 39](../39-green-mains/plan.md) | N | the Release 13 rejected-publication fix (Runtime inline proof, or an Agent upload with a receipt) | `env/` scripts; `tests/conftest.py` setup helpers only; the Agent integration-lane workflow | `test_remote_machine_cpu.py -m integration` passes on the Release 13 candidate from the worker script and in the lane | [ ] |
| RB-2 Extend the existing RunPod recordings: repair the port-type damage in `tests/providers/runpod/fixtures/`, add the requests the journey makes that have no recording, match requests strictly (refuse unrecorded ones), state each fixture's provenance (run, date, scrubber), and add a narrow ratchet against new hand-written RunPod pod dicts and Runtime task dicts in `tests/` | X | — | `tests/providers/`; a test-only capture hook in the RunPod client; the ratchet script and its CI hook | Replay serves recorded requests and refuses an unrecorded one; the scrubber keeps JSON types; the ratchet fails on a planted hand-written dict and passes at baseline | [ ] |
| RB-3 Correct the fixtures that hid the 11–12 Nov bugs, each checked against a captured real response: the flat task spec in `tests/packs/runpod/test_pack_actions.py`, `tests/sdk/test_project_render.py` and `tests/sdk/test_project_render_rrp.py` (already converted on `r13/cli-wait-visibility`; verify against a recorded `tasks show`); the `networkVolumeId` readers; an empty-log publication case | N | RB-2 | the named tests' fixtures only | Each converted test fails on its pre-fix revision (recorded in the card at dispatch) and passes on the fix | [ ] |
| RB-4 The fault matrix in the CPU journey (rows in [plan.md](plan.md#outcome-and-scope)), extending its existing stock, killed-pod, cancellation and receipt tests. A table of expected reasons and end states (task: failed/cancelled/completed; machine: released with reason / idle / `stale_after_failure`) documents what the Release 13 reconcile and keep-warm fixes implement; it adds no new semantics. Storage-wait and held-slot rows unblock or cancel within a deadline before asserting | X | RB-1, RB-2, RB-3 | `tests/integrations/test_remote_machine_cpu.py` and its helpers | Every row passes on the integrated revisions; the rejected-publication and silent-wait rows fail on their pre-fix revisions | [ ] |
| R Review rounds (at most 1, recommended; the owner confirms) | S | all other tasks | read-only | Rounds per the [run contract](../../skills/astrid-dev-shared/run-contract.md): findings become rows `R1.<n>` added directly below this one, each with route, scope, dependencies and proof; publishing or closing waits for them | [ ] |
