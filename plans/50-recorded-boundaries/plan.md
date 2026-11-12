# Recorded boundaries and an offline generation harness

**Project:** Recorded boundaries and an offline generation harness

**Goal:** The generation failures we know of at the RunPod and Runtime boundaries are found and named on a CPU without renting a GPU: tests use recorded real RunPod responses, and the CPU journey with the real Runtime injects each failure and checks the product's answer.

**Status:** queued

**Owner:** Unassigned

**Estimate:** about 4–5

**Waiting on:** the owner's scope decision (D1); Release 13's in-flight terminal-reconcile and Runtime inline-proof fixes, which RB-1 needs

**Start:** [Astrid contributor skill](../../skills/astrid-dev/SKILL.md) and [domain map](../../skills/astrid-dev/references/domains.md). The six lines above are this project's row in the [catalog](../../plans/index.md): change them here, one line each, then run `python3 scripts/astrid_dev.py sync`. Its priority is its place in [priority.md](../../plans/priority.md).

**Vision gaps:** [Portable generation](../../vision/gaps/F-008-portable-generation.md) (primary): generation on a rented GPU must fail with a named cause, not a silent hang, before it can be relied on. [Platform reliability](../../vision/gaps/F-001-platform-reliability.md) (supporting): failures that leave a task stuck or a machine billing are operational-lifecycle failures.

## Outcome and scope

A contributor changing the generation path can run one CPU command and see, for each enumerated boundary failure below, whether the product still says why and ends in a defined state. Concretely:

1. **The CPU journey runs.** `tests/integrations/test_remote_machine_cpu.py`, which already runs the real Runtime, passes in the shared worker environment and in the Agent integration lane. It fails 24 of 25 tests locally today.
2. **RunPod test data comes from recordings.**
   - Extend the existing recordings in `tests/providers/runpod/fixtures/` and their loader in `tests/providers/test_provider_contract.py`; repair their known port-type damage.
   - Add the RunPod requests the journey makes but that have no recording yet.
   - A narrow ratchet stops new hand-written RunPod pod dicts and Runtime task dicts in tests.
3. **The fixtures that hid the 11–12 Nov live bugs are corrected:**
   - the flat Runtime task spec (`spec.inputs` vs the real `spec.spec.inputs`; the cli-wait branch already converts three files);
   - `networkVolumeId`;
   - the empty-log output that the Runtime refused.
   Each conversion is checked against a captured real response.
4. **An offline fault matrix inside the CPU journey** extends its existing stock, killed-pod, cancellation and receipt tests. For each row it asserts a named reason in the receipt or CLI, and the task's and machine's end state as implemented by the Release 13 fixes. Rows:
   - out of stock;
   - 429 with `Retry-After`;
   - a killed pod;
   - an engine install or doctor failure;
   - a rejected success or failure publication;
   - an expired lease;
   - a host stopped mid-publication;
   - a storage wait that is then unblocked;
   - a held slot that is then released or cancelled.
   A kept machine's end state is `idle` or `stale_after_failure`, not necessarily terminated (Plan 40 D12/D13).

**Candidate follow-ups, not part of this plan's commitment:**
- engine CLI recordings;
- a replaying Runtime fake (only if the real Runtime in the journey proves insufficient);
- a lint against silent wait loops;
- a real pod agent and a no-op CPU engine in the harness;
- lifecycle typed errors (a pin bump);
- a container CI job.

**Not included:**
- keeping machines across a host restart (Plan 40 D12 keeps host shutdown as a release; it needs the deferred pod-side cap);
- GPU validation and paid capture beyond passive capture in already-authorized runs ([Plan 34](../34-real-gpu-proof/plan.md));
- greening other CI lanes ([Plan 39](../39-green-mains/plan.md)).

## Existing work and decision

This finishes the structural design written for Release 13 on 12 Nov ([structural-runpod-design.md](../../releases/13/structural-runpod-design.md)), whose pieces A (one provider boundary, slices s1–s3), C1 (a reason vocabulary) and the provider gate are already in the Release 13 rehearsal. Pieces B (recordings and replay) and D1 (the offline harness) were planned for Release 13 and not built.

The 12 Nov live batch added a second boundary the design did not cover, the Agent–Runtime protocol:
- **A stuck failure publication:** a rejected `fail` retried forever, so the task stayed `running` and every later task waited.
- **A silent CLI:** it read `spec.inputs` where the Runtime returns `spec.spec.inputs`.

Both were invisible to tests because the unit fakes agreed with the code, not with the Runtime, and the CPU journey that uses the real Runtime has never run on CI. Evidence, alternatives and the challenge are in [inputs.md](inputs.md#planning-evidence).

## Sequence and readiness

Order is in [tasks.md](tasks.md):
1. RB-1 (the journey runs) and RB-2 (recordings extended) in parallel;
2. then RB-3 (correct the known-bad fixtures);
3. then RB-4 (the fault matrix);
4. one review round at the end.

RB-1 needs the Release 13 fix for the rejected empty-log publication (the Runtime inline-proof branch, or an Agent-side upload with a receipt). Terminal reconciliation alone cannot make a rejected successful publication succeed.

Recordings are captured passively during paid runs already authorized for Release 13; this plan authorizes no spend. Recording this plan authorizes no implementation; D1 decides placement.

## Interfaces and handoff

**Consumes:**
- Agent Release 13 rehearsal `scratch/r13-rehearsal` (`dd5bc822` at writing) plus the in-flight branches `r13/terminal-reconcile`, `r13/cli-wait-visibility` and `r13/keep-warm`;
- Runtime `42ae24af` plus `r13/inline-output-proof`;
- runpod-lifecycle `f294881`;
- the recordings in `briefs/evidence/runpod-recorded/` (manager scratch; RB-2 moves them into the Agent repository).

**Produces:**
- `tests/providers/recorded.py` and per-provider recording folders;
- recorded Runtime and engine shapes;
- a runnable CPU journey with a fault matrix;
- the fault matrix's expected-outcome table, which documents the end states the Release 13 fixes implement;
- a ratchet against hand-written RunPod and Runtime task dicts.

Later engine or provider work builds on the recording folders and the matrix.

## Completion

- One documented CPU command runs the journey and fault matrix green on the integrated revisions.
- Each enumerated 11–12 Nov live failure has a row or converted fixture that fails on its pre-fix revision and passes after: `networkVolumeId`, the 429 storm, the rejected publication, the flat task spec, the hidden wait reason.
- **Negative case:** a new hand-written RunPod pod dict or Runtime task dict in a test fails the ratchet.
- **Limits:** this proves behaviour against recorded shapes, not against shapes RunPod or the Runtime have not yet returned; live GPU proof stays with Plan 34 and the release gate.
