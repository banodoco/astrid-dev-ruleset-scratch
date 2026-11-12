# Inputs — Recorded boundaries and an offline generation harness

[Plan](plan.md) · [Tasks](tasks.md)

## Planning evidence

**Scope decision:** Pending — The owner asked on 12 Nov that "the updated plan is on main" after asking whether this structural work was set for the next release and captured as a project. That records the plan; it is not a choice of end state or of release placement. Next: the owner decides D1.

**Prior art:**
- [structural-runpod-design.md](../../releases/13/structural-runpod-design.md) (12 Nov, 01:45 UTC) is the design this plan completes.
  - Its §1 traces six paid-run failures to one mechanism: a typed fact flattened at a boundary that tests faked with shapes RunPod never returns.
  - Its §5 (piece B) defines the recording, scrubbing and replay rules.
  - Its §7 (piece D1) defines the harness.
- Already built in the Release 13 rehearsal: s1–s3 (`ad7723a8`, `ae0f284d`, `c474563d`, `4696668d`), the reason slice C1, the provider gate `f0535fef`. `tests/providers/test_provider_contract.py` exists, but there is no `tests/providers/recorded.py` loader.
- 12 Nov live evidence (Release 13 decision log on branch [`r13-progress/decision-log`](https://github.com/banodoco/astrid-dev/blob/r13-progress/decision-log/releases/13/decisions.md), entries 12:41 to 13:00 UTC; it reaches `main` with the Release 13 record):
  - **Rejected failure publication:** a project task's failure with an empty log was refused. Runtime `runtime_protocol/service.py:9294-9321` treats an existing ownerless object as unproven even when its inline bytes are hash-verified. The Agent's `generic_host.py` reconcile loop (about 11590) then replayed the rejected `fail` forever, holding the GPU reservation and the executor's slot.
  - **Silent CLI:** `astrid/sdk/invocation.py:_runpod_generation_policy` read `task["spec"]["inputs"]`; the Runtime returns `spec.spec.inputs`. The fixture at `tests/packs/runpod/test_pack_actions.py:336` used the flat shape.
  - **Hidden wait reason:** the Runtime `_claim_task` reports only the first blocker (`store.py` about 4392-4419), so `insufficient_storage` hid the held slot.
- `tests/integrations/test_remote_machine_cpu.py -m integration` fails 24 of 25 tests on the unchanged base `b306b2be` with `ASTRID_RUNTIME_CHECKOUT` set ("target status task failed"); without it, 24 setup errors. Diagnosed 12 Nov: it is not environmental. Every failure is the same rejected publication: `runpod.setup` runs with no project and settles empty logs, then `runpod.status` under a project publishes the same empty-log digest inline and the Runtime refuses it (`service.py:9297-9321`). Agent `83eaa2402` (declared logs as task outputs, 12 Nov) introduced the trigger; stubbing `_log_outputs` makes the first test pass. CI has never run this file: Agent `main` lacks it, and the int/32 lanes run (42806140544) died in setup. So this journey, one of the integration tests that run the real Runtime, would have caught the 12 Nov stuck-task bug offline had it run anywhere. Evidence is manager execution, not code inspection: the 24/25 result on `b306b2be` with `ASTRID_RUNTIME_CHECKOUT` at `42ae24af`, the `_log_outputs` stub rerun, and the CI runs cited; the commands are in the decision log.
- Related plans:
  - [Plan 39](../39-green-mains/plan.md) (paused) owns CI greenness in general;
  - [Plan 34](../34-real-gpu-proof/plan.md) owns live GPU proof;
  - [Plan 40](../40-machine-lifetime-controls/plan.md) owns machine retention, and its deferred item "a provider-side or pod-side cap that holds when no host runs" is the prerequisite for retaining machines across a host restart.

**Approach:** Build on what exists:
- the CPU journey, which already runs the real Runtime;
- the four RunPod recordings and their loader in `tests/providers/`;
- the journey's existing stock, killed-pod, cancellation and receipt tests.

Alternatives considered:
- **(a)** Keep fixing each boundary bug as found. Cheapest now, but every 11–12 Nov boundary bug was found only on a paid pod.
- **(b)** A full simulator of RunPod and the Runtime. Larger, and it drifts like hand-written fakes do.
- **(c)** Contract tests against live services in CI. Needs credentials and paid pods.
- **(d)** A replaying Runtime fake. Not needed while the real Runtime runs in the journey.

Recorded RunPod shapes, plus the real Runtime in a runnable journey, is the smallest approach that ties tests to real shapes.

**Challenge:** Required (a cross-repository contract). An independent critic (Codex Astra, 12 Nov; read-only, checked claims against the Agent, Runtime and in-flight diffs) returned ACCEPT WITH CHANGES.
- **Accepted:**
  - fold the terminal-state contract into the matrix's expected-outcome table; it adds no semantics;
  - drop the silent-loop lint (a separate enforcement project);
  - extend the existing recordings and loader instead of new ones;
  - use the real Runtime, with no replaying Runtime fake;
  - assign the fixture ratchet to RB-2; drop engine recordings to follow-ups;
  - enumerate the coverage instead of "every boundary";
  - storage and slot rows unblock before asserting; kept machines end idle or stale;
  - fix the conftest path; coordinate with Plan 39;
  - RB-1 needs the inline-proof fix, not reconciliation alone;
  - list exact fixtures; RB-4 depends on RB-3;
  - D2 is inherited from Plan 40, not pending;
  - "committed phase 2" becomes "candidate follow-ups";
  - correct the "only test" claim and the decision-log link;
  - name the in-flight donors as uncommitted.
- **Not taken:** status stays `queued`, which is the catalog's state for a recorded, not-started plan; it grants no authority.

**Proof and limits:** See [plan.md](plan.md#completion). The matrix proves behaviour only against recorded shapes. Shapes the services have never returned are not covered, so recordings must be refreshed when a provider or Runtime changes, and the ratchet makes a missing recording a test failure, not a silent pass.

**Review rounds:** Recommend one round at the end (S route): the matrix pins user-visible end states across two repositories. No review stop: no new contract is designed here.

**Run start:** Pending — No run is authorized. Next: the owner decides D1.

## Owner decisions

- **D1. Placement.**
  - Options:
    - **(a)** The whole plan inside Release 13, before its gate. About 4–5 worker-days; the candidate slips.
    - **(b)** Inside Release 13: RB-1 (the journey runs) plus minimal regressions on the existing fixtures for the 12 Nov bugs, the converted spec fixtures already on the cli-wait branch, and an empty-log publication case, about a day. Strict replay, the ratchet and the full matrix (RB-2 to RB-4) follow after Release 13.
    - **(c)** All after Release 13.
  - **Recommendation: (b).** The 12 Nov bugs would have been caught by the journey alone.
  - Pending.
- **Inherited, not pending:** machines are released on host shutdown or restart (Plan 40 D12; D13 keeps it). Keeping them needs Plan 40's deferred pod-side cap.

## Source identities

- **Agent:** Release 13 rehearsal `scratch/r13-rehearsal` at `dd5bc82236b59e8bcbd1662e8886552d45cda731`.
  - Committed donor: `r13/keep-warm` `d072cf5da8ad271cfa281e52e78c2dfb7346829a`.
  - In-flight donors that are still uncommitted working-tree diffs at writing: `r13/terminal-reconcile`, `r13/cli-wait-visibility`.
- **Runtime:** `42ae24aff8d2cb854f874ce134161077a3ba3641`, plus the in-flight, uncommitted `r13/inline-output-proof`.
- **runpod-lifecycle:** `f2948817eeb94af8dee76be21f6d673724f1606e`.
- **VibeComfy:** `c7a47e36d6fe27518c438ddaf911ae261dbc5693`.
- **Destination:** Agent and Runtime `main` through the Release 13 or a later candidate, per D1.
- **Each task card records its exact base and donor SHAs at dispatch.**

## References

- [Release 13 structural design](../../releases/13/structural-runpod-design.md)
- Release 13 decision log: branch `r13-progress/decision-log`
- Critique: manager scratch `briefs/wave3/critique-plan50.log` (12 Nov)
