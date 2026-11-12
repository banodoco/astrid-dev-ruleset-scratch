# Release 13: making the generation placement path correct by construction

Written 2026-11-12, about 01:45 UTC. Read-only study of Agent rehearsal `8cf3ada9` (`/home/user/wt/c-release`), runpod-lifecycle `f294881` (the canonical pin), Runtime `4f5477c` (`/home/user/astrid-runtime`), tonight's decision log from 00:20 onwards, `briefs/release-diag.log`, the reconciled plan `briefs/struct-design.md` (01:35), and the four recordings in `briefs/evidence/runpod-recorded/`. Nothing was run against RunPod, and no repository file was edited.

**How this relates to the reconciled plan.** `struct-design.md` already fixes the direction: Move 1 (`MachineRecord`/`MachineProvider`), Move 2 (`PlacementRefused` with a required gate), and Move 3 (`host_failure` plus an engine-keyed fact allowlist). Slices s1–s3 have been dispatched. This document is the detailed A–D design under that plan. It keeps the plan's names. It adds the parts the plan does not cover: the full raw-read inventory, the capture rule and its enforcement, the reason channel up to the receipt and CLI, the rate gate, and the offline harness. Where it disagrees with an in-flight slice, it says so in §8, "Amendments". The most important amendment is to s1: as briefed, it would encode tonight's failure 1 as correct behaviour.

---

## 0. The decision in ten lines

1. **One root cause.** Every provider, check and engine boundary passes an untyped value (a `dict`, a bare `bool` or a free `str`), and each consumer re-guesses what it means. Tonight cost four rentals because each guess failed at a different place, and each failure said nothing.
2. **A.** One provider boundary in the Agent. Neutral records live in `astrid/core/generation/machine_provider.py`, and RunPod's parse functions in `astrid/packs/runpod/provider.py`. Lifecycle stays the transport. Records carry **which fields the shape actually observed**, so "no volume" can never again be confused with "not reported".
3. **A also gets one account-scoped provider gate.** It is a file-locked cooldown shared by the daemon, `machines release` and the release polling, and it fixes the 429 storm.
4. **B.** Provider-shaped test data comes only from recordings. Recordings are captured passively during paid runs we already make, at zero extra rental, and scrubbed by a fixed, type-preserving allowlist. A replaying fake refuses any request that was never recorded, and a ratchet stops new hand-written provider dicts.
5. **C.** One stdlib-only reason vocabulary (`stage`, `gate`, `step`, `code`, plus bounded numbers), carried by every refusal from the pod frame to the receipt and the CLI. No free text crosses the boundary. A lint makes `from None` without a reason a CI failure.
6. **C and G3.** Every one of tonight's six failures is fully diagnosable from structured reasons. **Make the free-text bundle opt-in, not default** (owner's call: H10).
7. **D.** Upgrade the existing CPU journey (`tests/integrations/test_remote_machine_cpu.py`): its provider half replays recordings, and a fault matrix asserts a named reason for every injected failure. This first slice would have caught all four failures offline, and it catches two gaps still live at `8cf3ada9`.
8. **The shape is multi-provider and multi-engine.** Each provider implements `MachineProvider` plus a parse module and a recordings folder, and each engine implements a recipe plus an engine-keyed fact table. Shared code names neither. §3 lists today's RunPod and ComfyUI leaks with file:line.
9. **Release 13:** s1–s3 (with amendments), the reason slice C1, the provider gate, recording plus replay, and harness slice D1. That is about 7.5 worker-days, and it fits in parallel across three workers.
10. **Later:** migrating the remaining readers, lifecycle typed errors (a pin bump), a real pod agent in the harness, a no-op CPU engine, and a container CI job. That is about 11 worker-days.

---

## 1. What went wrong, as one mechanism

| # | Seam (paid run) | What actually happened (file:line at `8cf3ada9`, or the fixing commit) | Detectable offline? | Why it was blind |
|---|---|---|---|---|
| 1 | Pod record fields read raw, with stale names (TTS 1, 00:23) | Lifecycle `list_pods` returns the SDK GraphQL record, which has no `networkVolumeId`. The enrichment adds only a REST `networkVolume` object (lifecycle `api.py:136-178`). The Agent read `networkVolumeId`, saw None, and reported "volume mismatch". Fixed by `e6d85766` with the `pod_fields.py` alias accessor. | Yes: the shape is visible in `sdk-graphql-myself-pods.json` | `target_selection.py:878-886` re-raised as `AcquisitionUnresolvedError ... failed gate: provider` `from None`. The receipt said `no_machine`/`unknown` although a pod existed (`failure_receipt.py:58-61`, because no `claim_context` was set). |
| 2 | REST `GET /v1/pods/{id}` without `includeNetworkVolume` | **This never failed.** The recordings show that a default GET returns `networkVolumeId` and `imageName` (`rest-get-pod-default.json`). The OpenAPI file omits both. The `e6d85766` parameter change was harmless and unnecessary (decision log 01:35). | Yes: and a replay would have *disproved* the hypothesis at zero cost | The tests faked `read_exact_pod` itself, so nobody could check the claim either way. |
| 3 | The capacity wait treated unclear observations as final (TTS 2, 00:55) | After real stock-out, one all-HTTP-200 observation became `provider_observation_unavailable` and ended the run. Lifecycle emits about 17 distinct reason strings (`availability.py:159-376`). The Agent maps 4 of them and collapses the rest into one at `adapter.py:37-48`. The most likely trigger is `"Provider stock snapshots disagree; retry"` (`availability.py:262`), but the receipt cannot say which. Fixed by `f1a487c9` (bounded retry). | Yes: it is a value-only variation of recorded stock and price responses | Retry was decided by a string allowlist (`target_selection.py:625-650`), and the specific reason was discarded at `adapter.py:48`. |
| 4 | Post-install verification returned False without a reason (TTS 3, 01:06) | `_canonical_installed` returned a bare False on four conditions. `61eafd53` labels most of them, but **the receipt still never copies the label**: `failure_receipt.py:126-133` copies `reason` only when `stage == no_machine`. Bare False returns remain at `remote_placement.py:613`, `617`, `619`, `699`, `704`, `708` and `710`. | Yes: a fault-inject on the `engines status` answer | The label lives only in the exception text, which the receipt deliberately never reads. **This is still live.** |
| 5 | Release 429 storm (00:27, `release-diag.log`) | Owner recovery retries every failure after 1 s (`worker_owner.py:705`). Each attempt makes up to two inventory reads (`worker_preparation.py:1102`, `1129`). **Each `list_pods` costs two HTTP requests for any non-empty account**, because lifecycle's own `QUERY_PODS` (`graphql.py:19-61`) never selects `networkVolumeId`, so the "GraphQL is enough" test at `api.py:140` is never true. Lifecycle drops `Retry-After` (`api.py:155-158`). | Yes: replay a 429 with `Retry-After` | `_release_inventory` raises `from None` at `worker_preparation.py:693-696` and `706-709`, and only the exception type name is kept (`worker_owner.py:705-712`). |
| 6 | Terminal-evidence readback (`generic_host.py:5859`) | The host submits `result.error`. Runtime overwrites it with the failure payload (`store.py:6804` in `_fail_task_in_transaction`, from 6798). The host's readback (`generic_host.py:5830`) then fails, and the spool is kept as pending. | Yes: the CPU journey already runs a real Runtime | Two owners write one key, and nothing tests a failure whose host error differs from the payload. |

**Pattern.** All six were detectable offline. Five were blind because a typed fact was flattened into text, None or False at one boundary. Tests faked exactly those boundaries, with shapes RunPod never returns.

---

## 2. Ground truth, and what the four recordings do not yet cover

The recordings are right, and the OpenAPI file is wrong in at least five places. Real REST responses include `networkVolumeId`, `imageName` and `gpuCount`. They do not include `image`, `gpu`, `adjustedCostPerHr` or `portMappings` (the last may have been removed by scrubbing; this is unknown). Neither real shape has `actualStatus`, `machineType`, a top-level `dataCenterId` or `computeType`, yet the code reads all four: `worker_preparation.py:322`, `pod_fields.py:14`, `worker_preparation.py:385`, `h3_release.py:97`, `110` and `396`, and lifecycle `api.py:659`.

Gaps that matter before recordings become the test contract:

- **G-a. The GraphQL recording is the SDK's query, not the one production sends.** `sdk-graphql-myself-pods.json` has `machine {gpuDisplayName}` only. Production `list_pods` sends lifecycle's `QUERY_PODS`, which also selects `machine.dataCenterId` (`graphql.py:47-50`). A strict key set derived from this file would reject production output. Recordings must therefore be keyed by the **exact request**: method, path template, query parameters, and the GraphQL query text hash.
- **G-b. The scrubbing changed types.** `runtime.ports` held objects `{ip, privatePort, publicPort, type}` and now holds the string `"<redacted>"`. REST `ports` held `"8000/http"` strings, which lifecycle parses with a regex (`api.py:645-656`). `publicIp` is no longer an IPv4 address. Replaying these files through `_normalize_pod_status` or `get_pod_ssh_details` would silently produce no routes. The files are good for identity fields only, until they are re-scrubbed under §5.2.
- **G-c. Unrecorded request states.** The lifecycle single-pod GraphQL query (used by `confirm_acquired_machine`, `read_acquired_gpu_count` and `get_pod_status`); a pod while `PROVISIONING`; REST with `includeMachine=true`; `GET` 404; the REST and GraphQL `networkVolumes` forms; the `gpuTypes` catalogue; `dataCenters` stock and prices (seam 3); 429 with headers; DELETE; and the post-terminate list.
- **G-d. A hypothesis to settle by recording, not assume.** The code asserts "REST reports `machine: {}` on a correct fresh pod" (`worker_preparation.py:291-293`, `target_selection.py:898-900`). The OpenAPI file has `includeMachine` defaulting to false, and both REST recordings were made without it. If `includeMachine=true` returns `machine.dataCenterId` and `gpuDisplayName`, the 3-second GraphQL polling loop of up to 900 s (`worker_preparation.py:484-501`) becomes one REST read.

---

## 3. Shared abstractions to extend, and today's leaks

**What already exists, and what this design extends:**

- `generation.machine` point. The `Machine` protocol (`packs/generation/extensions/points/machine_protocol.py`) defines claim/start/poll/cancel/fetch/release, and `core/execution/machine_run.py:69-148` drives it with an `on_failure(facts)` hook. **This is the provider interface.** `MachineProvider` (A) is the observation half beneath it.
- `generation.engine` point. The `Engine` protocol (`engine_protocol.py`), recipes (`engine_recipe.py`) and the runner (`engine_runner.py`) already have a fixed error vocabulary: `EngineError.code` plus `step_id` (`engine_contracts.py:16-28`), and `_STATUS_ERROR_CODES` (`engine_runner.py:63-68`) with `failed_step_id` (`engine_runner.py:1026-1088`). **This is the engine interface.** C reuses its codes and step ids, and adds none.
- `failure_diagnostics.CODES`/`FACTS` (`packs/runpod/failure_diagnostics.py:22-55`) is a fixed code-to-category table. It is already shipped as stdlib-only source to the pod (`machine.py:410`). **This is the seed of the C vocabulary.**
- `target_provider.resolve_target_provider` (`core/execution/target_provider.py:15-58`) resolves an admitted pack's `adapter.py`. A second provider pack plugs in here without editing core.

**RunPod-specific code in shared paths** (each needs a neutral hook before a second provider lands; the s3 ratchet freezes the count):

| Site | What |
|---|---|
| `core/execution/generic_host.py:7185`, `7200-7202` | `is_runpod` gate; imports `packs.runpod.failure_receipt.recorder`, so only RunPod machine jobs get receipts |
| `core/generation/cli.py:728-735`, `743`, `776` | `generate failure` reads `packs.runpod.failure_receipt`; leases come from `packs.runpod.machine.journal_leases` |
| `core/generation/placement.py:26`, `98-104`, `223-229` | `_PROVIDER_FALLBACK=("runpod",)`, `is_runpod_placement`, `_runpod_leases` |
| `core/generation/engine_contracts.py:10`, `493`; `engine_runner.py:221-224` | `Placement = Literal["local","runpod"]` (s2 makes it a registered-kind string) |
| `core/machines_cli.py:23`, `95`, `133`, `211`, `243`, `328`, `347-348` | the whole `machines` CLI imports RunPod preference, consent and selection types |
| `sdk/generation.py:275`, `289`, `313`, `377`, `389`, `1140` | the SDK facade imports `RunPodPreferences`, `PaidRunConsent` and `policy_consent_digest` |
| `core/generation/interfaces.py:94`, `122` | `RunPodPreparationRequest`, `RunPodGenerationPreparation` |
| `core/generation/preflight.py:23`; `engine_readiness.py:711-712` | import RunPod pack internals |
| `core/execution/target_adapter.py:35-37`, `292-322`; `core/execution/__init__.py:23-25` | `pod_id` and `volume_id` fields on the neutral observation; `RunPodTargetAdapter` in the shared module |
| `packs/runpod/failure_receipt.py:130-131`, `failure_diagnostics.py` | provider-neutral content, but in the RunPod pack, with RunPod gate names |
| `packs/vibecomfy/extensions/generation.engine/comfyui.yaml:8`; `engine_release.py:198`; `engine_bootstrap.py:37` | the ComfyUI Linux recipe lives at `packs/runpod/recipe.linux-cu130.json` (engine and provider coupled by path) |
| `packs/runpod/remote_placement.py:43-44` | `ENGINE_ID="comfyui"`, `DATACENTER="EUR-NO-1"` hard-coded |

**ComfyUI-specific code in shared paths:**

| Site | What |
|---|---|
| `core/generation/engine_recipe.py:50` | `_PLACEHOLDERS` contains `comfy_root` |
| `core/generation/engine_recipe.py:396-397` | **at most one engine per platform**, which blocks a second Linux engine and the harness's no-op engine |
| `core/generation/engine_contracts.py:208-213` | `HealthSpec.object_info_path`, `required_nodes` (ComfyUI `/object_info`) |
| `core/generation/engine_runner.py:122-131`, `441`, `481`, `638`, `734-739` | `_object_info_sha256`, the `comfy_root` binding, a `comfyui`+cu130 special case |
| `core/generation/engine_runner.py:1060` | status refuses an install without a `cuda_visible_devices` start fact (a GPU-only assumption; blocks a CPU engine) |
| `core/generation/engine_readiness.py:43`, `715`, `888`; `targets.py:38`, `312`; `engine_local_endpoint.py:214`, `260`, `341`, `391`; `engine_local_server.py:17`; `engine_custody.py:1079`; `engine_facts.py:34-38`; `canonical_pins.py:23` | `"comfyui"` default engine id |
| `packs/runpod/failure_diagnostics.py:37-55`, `160-178` | `FACT_ALLOW` ComfyUI node classes (s3 keys it by engine); `_graph_nodes` parses ComfyUI API and editor graphs |
| `core/generation/placement.py:157` | `comfy_selector` |

---

## 4. Piece A: one typed provider boundary

### 4.1 Where it lives, and why

- **Neutral types: `astrid/core/generation/machine_provider.py`** (s1, in flight). Its consumers are the generation-machine point and core's receipt path, both in the Agent. Lifecycle cannot hold them, because a second provider will never import a RunPod library and lifecycle must not import the Agent.
- **RunPod decoding: `astrid/packs/runpod/provider.py`** (s1). There is one pure function per real response shape, keyed by request, which owns that shape's key set. Three reasons it belongs in the Agent pack rather than lifecycle:
  1. The Agent already issues its own REST calls that lifecycle does not own (`worker_preparation.read_exact_pod:569-588`, `h3_release.RunPodREST:318-345`), so a lifecycle-only boundary would leave holes.
  2. Lifecycle already has two normalisers that disagree with the Agent's (`discovery.py:116-230` `PodSummary`/`_network_volume_id`, and `api.py:627-667` `_normalize_pod_status`). Adding a third in lifecycle repeats the pattern.
  3. A lifecycle change needs a pin bump. Under G4 that means the canonical `pins.json`, the identity check, the byte-identical lock and a reinstall: too costly for Release 13 tonight.
- **Lifecycle stays the transport and query builder.** It needs two changes at the next pin bump (Release 14), listed in §4.6.

### 4.2 Records (amending s1's `MachineRecord`)

```python
# astrid/core/generation/machine_provider.py  (stdlib + typing only)
@dataclass(frozen=True)
class MachineRecord:            # RunPod "pod" (instance)
    provider: str; machine_id: str
    state: Literal["starting", "running", "stopped", "gone"]
    observed: frozenset[str]    # NEW: field names this response shape carries
    name: str | None = None; image: str | None = None
    storage_id: str | None = None; storage_mount: str | None = None
    gpu_count: int | None = None; gpu_label: str | None = None
    region: str | None = None; hourly_usd: float | None = None
    def require(self, field: str) -> Any:  # raises PlacementRefused(gate=..., code="field_not_observed")

@dataclass(frozen=True)
class StorageRecord:            # RunPod network volume (slice A2)
    provider: str; storage_id: str; name: str | None; size_gb: int | None; region: str | None
    observed: frozenset[str]
```

- **Why `observed` matters.** On a record parsed from the SDK GraphQL shape, `storage_id=None` must mean "this shape does not report attachments", not "no volume". The contract check calls `record.require("storage_id")`. On a GraphQL-shaped record that refuses with `gate=storage`, `code=field_not_observed`, naming the field. Without `observed`, the check reports "expected vol-x, observed None", which is exactly tonight's failure 1. For a no-volume contract the check also needs proof that storage is absent, so it must read a shape that observes storage.
- **Names.** "Pod", "Offer", "Volume" and "Machine" in the brief map to `MachineRecord`, `RunPodOffer` (kept), `StorageRecord`, and host fields folded into `MachineRecord` (`gpu_label`, `region`). "Machine" already means the generation-machine contribution, so a separate `Machine` host record would collide.
- **Offers.** The plan explicitly does not build a neutral offers interface, and the records were not the problem: `RunPodOffer` (`target_selection.py:270-293`) and lifecycle `GpuAvailability` (`availability.py:23-51`) are already typed. The offer defect is the reason channel, which C fixes.

### 4.3 Account-scoped provider gate (seam 5)

New `ProviderGate` class in `machine_provider.py`, about 70 lines. The provider decides the account key; the cooldown logic is neutral.

- **State:** `<runtime data root>/providers/<provider>/<sha256(account_ref)[:16]>/gate.json`, holding `{not_before_utc, consecutive, last_code}`, under `fcntl.flock`. The daemon, `astrid machines release` and every other process for that account share it. There is no in-memory-only state.
- **`gate.before(op, *, deadline)`:** sleeps until `not_before`, or raises `PlacementRefused(gate="provider", code="provider_cooldown", retryable=True, retry_after=...)` when the wait would pass the caller's deadline. The paid-deadline release path **starts** at once and records `cleanup_pending`, but never sends a request inside a provider-mandated `Retry-After`.
- **`gate.after(outcome)`:** on 429 or a transport failure, sets `not_before = now + next_delay(consecutive, retry_after)` (s2's function: 5 s doubling to 60, honouring `Retry-After`, with jitter). On success it resets.
- **Coalescing:** one release attempt takes one inventory snapshot. That replaces `reconcile_pod_cleanup(verify_timeout_seconds=0)` (`worker_preparation.py:1102-1108`) plus `_release_inventory` (`1129`).
- **Lifecycle absence polling:** the Agent calls `terminate_pod(..., verify_timeout_seconds=0)` (`api.py:922-928`) and polls absence itself, through the gate.
- **Callers to change:** `worker_owner.py:242`, `455`, `671`, `698` and `714` (`timer(1, ...)` → `timer(gate.delay())`; the catch-all is at 705); `machines_cli` release (§3 lines); `worker_preparation.py:653`, `684`, `1102`, `1129` and `1561`.
- **Until lifecycle is typed (§4.6):** `provider.py` classifies lifecycle's exact `RuntimeError` prefix `"RunPod pod listing failed: HTTP <n>"` (`api.py:156`) in one function, with a test pinned to the text at `f294881`. This is the same accepted stop-gap pattern as `adapter.py:37-48`. It is deleted at the pin bump.

### 4.4 Inventory of raw provider reads, and how each migrates

Phases: **A1** = s1 (in flight), **A1+** = the §8 amendment, **A2** = first follow-on slice (Release 13 if time allows, otherwise Release 14), **A3** = Release 14, **L** = lifecycle at the next pin bump. Agent `.get("...")` calls on non-provider records (journals, receipts, preferences) are excluded. Of 1213 `.get("` calls in the pack, about 50 touch provider records.

| Site (Agent unless noted) | Record | Fields read raw | Migration |
|---|---|---|---|
| `worker_preparation.py:569-588` `read_exact_pod` | pod (REST GET) | `id` | A1 → `provider.read()`; the return contract is kept |
| `target_selection.py:40-44` `_exact_volume_id` | pod (REST) | via `pod_field("volume")` | A1 → `MachineRecord.storage_id`; A1+ → `require()` |
| `target_selection.py:893-897` | pod (REST) | `volumeMountPath`, volume | A2 → `require("storage_mount")`, `require("storage_id")`, with separate codes for status/absent/mount/id (today one message covers four cases) |
| `worker_preparation.py:306-322` | pod (list) | `id`, `name`, `desiredStatus`, `actualStatus` (in no shape) | A2 → `MachineRecord.state`, `name`; delete `actualStatus` |
| `worker_preparation.py:337-358` | pod.machine | `pod_field("gpu_name")` (aliases `machineType` and `gpu`, neither ever returned), `machine.gpuDisplayName`, `gpuTypeId` | A2 → `gpu_label` (observed only for the GraphQL shape) |
| `worker_preparation.py:360-378` | pod | `pod_field("image")`, `pod_field("volume")` | A2 → `require("image")`, `require("storage_id")` |
| `worker_preparation.py:380-388` | pod and volume | `dataCenterId` (top-level, in no shape), `machine.dataCenterId` | A2 → `region` (GraphQL lifecycle query only) |
| `worker_preparation.py:484-509` `confirm_acquired_machine` | pod (GraphQL single) | `machine.gpuDisplayName`, `dataCenterId`; `except Exception: machine = {}` at 492 | A2 → `provider.read_host()`; typed error instead of an empty dict; settle G-d first |
| `worker_preparation.py:511-526`, `1700-1712` | gpuTypes catalogue | `id`, `displayName` | A3 (catalogue record) |
| `worker_preparation.py:529-541` `read_acquired_gpu_count` | pod (GraphQL) | `gpuCount`; `except Exception: record=None` | A2 → `require("gpu_count")` |
| `worker_preparation.py:684-712` `_release_inventory` | pod list, volumes | `id` | A2 → `provider.list()` and `volumes()` through the gate |
| `worker_preparation.py:1561-1606` `reconcile_target` find-by-name | pod list | `name`, `id` | A1 already has `provider.find()`; A2 switches the caller |
| `worker_preparation.py:219-246`, `412-450`, `593-608`, `1176`, `1239-1240` | volume | `id`, `name`, `size`, `dataCenterId` | A2 → `StorageRecord` |
| `adapter.py:61-91` `setup_datacenters`/`setup_gpu_types` | lifecycle `probe()` dicts | `gpu_type`, `display_name`, `displayName`, `datacenters_available` | A3 (also setup bug B) |
| `adapter.py:106-118` | volume | `dataCenterId` | A2 → `StorageRecord.region` |
| `adapter.py:127-160` | `GpuAvailability` (typed) | `retry_after` through `getattr`, **never set by lifecycle** (dead code) | C1 (reason codes); L (real `retry_after`) |
| `adapter.py:191-193` `actual_rate` | lifecycle `get_pod_status` snake_case dict | `cost_per_hr` | A2 → `MachineRecord.hourly_usd` from the same REST read |
| `h3_release.py:74-84` | volume (REST) | `id`, `size`, `dataCenterId` | A2 → `StorageRecord` |
| `h3_release.py:89-112` `check_attachment` | pod (REST) | `pod_field` volume/image, `networkVolume.dataCenterId`, `machine.dataCenterId`, top-level `dataCenterId`, `volumeMountPath`, `computeType` (not a response field) | A2. Latent bug: on a default GET the datacenter is never observed, so `AttachmentPending` can spin until the claim deadline. `require()` turns that into an immediate named refusal. |
| `h3_release.py:247`, `393-410`, `419`, `436-437` | pod (REST and SDK `get_pod`) | `costPerHr`, merges SDK `machine`, `name`, `portMappings`, `publicIp` | A2 → `provider.read()`; the SDK single-pod query shape is unrecorded (G-c) |
| `shared/common.py:826`, `966-975`, `1288-1290`, `1429-1432`, `1660` | lifecycle `get_pod`/`get_pod_status` | `desired_status`, ports | A3 (legacy action path) |
| lifecycle `api.py:74-122` `get_network_volumes` | volume, 3 transports | SDK, REST and GraphQL shapes; **every failure returns `[]`**, so "transport down" reads as "volume does not exist" | A2: the Agent calls REST `/v1/networkvolumes` through `provider.volumes()` with typed errors. L: raise instead of returning `[]`. |
| lifecycle `api.py:125-178` `list_pods` | pod list | GraphQL then REST merge; non-200 becomes a free-text `RuntimeError` | A2: the Agent decodes the merged shape as its own recorded shape. L: typed error, and one request when REST is needed anyway. |
| lifecycle `api.py:627-667`, `740-771` | pod status | `actualStatus`, `runtime.ports` vs REST port strings and `portMappings`, `uptimeInSeconds` | A3 (Agent stops calling `get_pod_status`) |
| lifecycle `api.py:203-219`, `525-536` | gpu catalogue, volumes by name | `displayName`, `id`, `name` | A3 |
| lifecycle `graphql.py:114-118`, `252-256`, `274` | GraphQL envelopes | `["data"]["pod"]` etc., so a GraphQL `errors` body becomes `KeyError` (it is then swallowed at `worker_preparation.py:492`) | L: check envelopes and raise typed errors |
| lifecycle `availability.py:54-80`, `141-283`, `285-376` | offers | `stockStatus`, `available`, prices; free-text `reason` | L: add a `code` field next to `reason`. C1 maps all 17 strings in the meantime. |
| lifecycle `discovery.py:35-230` | pod mounts, `PodSummary` | duplicate attachment normaliser | stays lifecycle-CLI-only; the Agent never imports it |
| `pod_fields.py` (all) | pod | the alias accessor | deleted when A2 completes |

### 4.5 First slice (A1+, on top of s1)

- **Files:** `machine_provider.py` (+15 lines: `observed`, `require`); `provider.py` (each parse function sets `observed` from its shape's key set); `test_provider_contract.py`. Amend the s1 test: the SDK fixture yields `storage_id=None` **and** `"storage_id" not in observed`, and `require("storage_id")` refuses with `code=field_not_observed`.
- **Size:** about 60 lines of code and 40 of tests. **0.25 worker-day.**
- **Replaces:** the "missing key reads as None" rule from `e6d85766` (change 3).
- **Risk:** a caller that today accepts None on purpose (the no-volume path). Mitigation: `require` is opt-in per call site, and A1 changes only `_exact_volume_id`.

**A2** (1.5 worker-days) migrates the rows marked A2 and deletes `pod_fields.py`. **Provider gate** (1.0 worker-day) touches `worker_owner.py`, which is owned by the bundle round, so it lands after that round.

### 4.6 Lifecycle, at the next pin bump (Release 14)

- **L1:** `ProviderHTTPError(status, retry_after)` from `api.py:155-158` and `availability.py:66-72`; GraphQL envelope checks in `graphql.py`; `get_network_volumes` raises instead of returning `[]`.
- **L2:** a stable `code` on `DataCenterAvailability` and `GpuAvailability` next to the human `reason`.
- **L3:** `list_pods` makes one request: REST alone when attachment evidence is needed, which is always today.

Cost: 1.0 worker-day, plus 0.5 for the pin cycle.

---

## 5. Piece B: recorded contract fixtures

### 5.1 Capture without an extra rental

Tonight's four files were captured from a live diagnostic pod at no extra cost. Make that the standing method.

- **Recorder:** `scripts/providers/record_runpod.py`, run by the manager only. Workers never hold the credential (standing rule). It is read-only: GET requests and GraphQL queries only, no mutations. It runs against the **already rented** diagnostic pod at fixed moments: right after create (`PROVISIONING`); once readiness is green; after the claim; and after release (404 and list absence). It also does one pod-less pass for the catalogue, stock and prices (for the Release 13 GPUs in EUR-NO-1 and "any"), `networkVolumes` (REST and GraphQL), empty lists, and a 404.
- **Each pass records exactly what production sends:** lifecycle's `QUERY_PODS`, `generate_pod_query`, availability queries and gpuTypes query (imported from the pinned lifecycle, so their text hashes match production), and REST with each of `{}`, `includeNetworkVolume`, `includeMachine` and both. That fills G-a, G-c and G-d.
- **429:** never provoked on the shared account, because it would endanger releases. It is recorded when it happens naturally: the recorder keeps the next 429 it sees (status, `Retry-After`, body shape).
- **401:** probably impossible to capture through the credential-injecting proxy. Synthesise it as a status-only variation and mark it `synthetic`.
- **Cost:** about $0 extra, plus about 0.25 manager-hour per paid run. If a state is still missing after two paid runs, one dedicated supervised session (an RTX 5090 with the `storage` volume, about 10 minutes, about $0.25) covers it.

### 5.2 Scrubbing by a fixed allowlist (type- and format-preserving)

- **Values kept verbatim** (allowlisted key paths per shape): enums (`desiredStatus`, `podType`, `stockStatus`), numbers (`costPerHr`, `gpuCount`, `size`, `memoryInGb`, `vcpuCount`, `containerDiskInGb`, `volumeInGb`), `volumeMountPath`, `imageName` (a public digest), `gpuDisplayName`, `gpuTypeId`, `dataCenterId`, `displayName`, and port **formats** (`"8000/http"`).
- **Everything else becomes a placeholder of the same JSON type and format.** Ids become `[A-Za-z0-9]` strings of the same length. IPs become `192.0.2.x`. Integers become the same integer class. Timestamps become a fixed ISO value. `runtime.ports[*]` stays an object with placeholder values.
- **Always masked:** `env` values (key names kept), `dockerArgs`, `ASTRID_POD_*`, `PUBLIC_KEY`.
- **Unknown keys are kept as key names with a placeholder value.** Key presence is the contract; values are not.
- **Headers:** only `Content-Type`, `Retry-After` and `X-RateLimit-*`.
- **Requests:** method; path template (`/v1/pods/{pod}`); query parameters (names and allowlisted values); GraphQL operation plus SHA-256 of the query text (full text kept for queries, which lifecycle builds without secrets; mutations are never recorded).
- **Post-scrub verifier (fails closed, deletes the capture):** no value at a non-allowlisted path differs from its placeholder; no string matches credential patterns (long base64 or hex runs, the RunPod key prefix, `Bearer`); the policy's SHA-256 is written into the manifest.
- **Format:** `tests/providers/runpod/recordings/<YYYYMMDD>/<scenario>/<nn>-<op>.json` (schema `astrid.provider-recording.v1`: `{provider, request, response:{status, headers, body}, state, lifecycle_revision, scrub_policy_sha256, synthetic}`), plus `manifest.json` with each file's SHA-256. Other providers get `tests/providers/<kind>/recordings/` and their own `scrub.<kind>.json`. The recorder core (walk, allowlist, verifier) is shared.
- **Tonight's four files** stay valid for identity fields. They should be re-scrubbed or replaced on the next pass (G-b).

### 5.3 The rule, and how it is enforced

1. **Controller logic tests construct typed records** (`MachineRecord`, `StorageRecord`, `RunPodOffer`) and never build provider dicts. After A2, the gate checks take records, so these tests need no provider shape at all.
2. **Decoder and harness tests load recordings** through `tests/providers/recorded.py::load(provider, name)`. They may `vary(path, value)`, which keeps the key and the JSON type. They may `omit(path)` only in a test named `test_*drift*`, which documents a provider change.
3. **The replay fake refuses unrecorded requests.** It matches on method, host, path template, query parameter set and GraphQL query hash, and raises `UnrecordedProviderRequest`. A new query, or a dropped or added parameter, fails CI until it is recorded.
4. **A ratchet** (`tests/test_provider_fakes_recorded.py`): an AST scan of `tests/` outside `tests/providers/` for dict literals with two or more keys from the recorded provider key vocabulary (the union of recorded key sets: `desiredStatus`, `imageName`, `networkVolumeId`, `networkVolume`, `gpuCount`, `machine`, `costPerHr`, `volumeMountPath`, `stockStatus`, and so on). The per-file counts are committed and may only fall. This works like Ruff's 2128 and s3's neutrality ratchet.

**Existing fakes that violate the rule.** The common pattern serves as the **`list_pods` inventory**, but production's list record is the GraphQL shape plus a `networkVolume` object. So these fakes contain `networkVolumeId`, which hid failure 1, and they add `actualStatus` and `machineType`, which exist in no real shape:

| File:line | Problem |
|---|---|
| `tests/packs/runpod/test_target_selection.py:44-48`, `289-291`, `500-502`, `772-774` | list-inventory fakes with `networkVolumeId`, `actualStatus`, `machineType`, and no `machine` |
| `tests/packs/runpod/test_target_selection.py:84` | REST exact fake: `networkVolumeId` only, with no `imageName`, `desiredStatus` or `name` (a partial shape) |
| `tests/packs/runpod/test_worker_preparation.py:48-58` (`_pod`), `472-473`, `963`, `976-978`, `983`, `995` | an invented union shape; `machineType` |
| `tests/packs/runpod/test_generation_preparation.py:120-124` | union: top-level `dataCenterId` plus `machine.gpuTypeId`/`dataCenterId` plus `networkVolumeId` |
| `tests/packs/runpod/test_generation_preparation.py:235-236` | replaces `_HttpsOps._bounded_call` with `_call_direct`, so the spawned-child path is never exercised |
| `tests/packs/runpod/test_acquisition_gates_provider_fields.py:73` | REST fake (s1 migrates it) |
| `tests/packs/runpod/test_acquisition_graphql_confirmation.py:49-52` | "REST" fake with `actualStatus` |
| `tests/packs/runpod/test_acquisition_catalog_id.py:54` | partial REST |
| `tests/packs/runpod/test_release_after_acquisition_failure.py:178`, `199` | union and partial shapes |
| `tests/packs/runpod/test_release_unreported_machine.py:37-40`, `87-88` | labelled "shape observed live", but it lacks `networkVolumeId`, `volumeMountPath`, `gpuCount` and `costPerHr` from the real shape |
| `tests/packs/runpod/test_warm_session.py:766-768` | list-inventory union with `machineType` |
| `tests/packs/runpod/test_h3_release.py:48-49`, `91-93`, `690` | `computeType` and top-level `dataCenterId` (not REST response fields) |
| `tests/packs/runpod/test_pod_fields.py:28-42` | alias combinations no endpoint produces (the module is deleted at A2) |
| `tests/scripts/test_claim_runpod_5090_backup.py:504-505` | union shape |
| `tests/integrations/test_remote_machine_cpu.py:166-172` | one record for every endpoint: `imageName`, `networkVolumeId`, `actualStatus`, top-level `dataCenterId`, `machineType`, and a full `machine` |
| `tests/integrations/test_remote_machine_cpu.py:139-145`, `439-443` | stock is always self-consistent; REST GET ignores query parameters |
| `tests/packs/runpod/test_failure_diagnostics.py:177`; `test_machine.py:400`, `465`, `509` | `_bounded_call` replaced |
| `tests/packs/runpod/test_install_verify_reason.py` | fakes the verification seam directly |

### 5.4 First slice (B1)

- **Files:** `scripts/providers/record_runpod.py` (about 150 lines: request list, scrub walk, verifier); `scripts/providers/scrub.runpod.json`; `tests/providers/recorded.py` (loader, `vary`, `omit`, and a replay matcher of about 120 lines); `tests/providers/test_scrub_policy.py` (the verifier rejects a planted token, and the type preservation round-trips); `tests/test_provider_fakes_recorded.py` (the ratchet, with today's counts).
- **Size:** about 1.25 worker-days, plus 0.25 manager-hour for each paid run that records.
- **Replaces:** hand-built provider dicts, over time, through the ratchet. Validating shapes against OpenAPI is never done.
- **Risk:**
  - Leaking a secret into the repository. Mitigations: allowlist rather than denylist, the fail-closed verifier, a manager review of the first commit of recordings, and never recording mutations.
  - Recordings going stale when RunPod changes. That is the point: a drift test and a re-record make the change explicit. Each recording stores the lifecycle revision.

---

## 6. Piece C: one typed failure-reason channel

### 6.1 The vocabulary

`astrid/core/generation/failure_vocabulary.py` is stdlib-only and shipped to the pod as source, as `failure_diagnostics.py` already is (`machine.py:410`). `packs/runpod/failure_diagnostics.py` keeps its pod-side frame and graph-fact code and imports the tables from it.

```python
STAGES = ("no_machine", "boot", "install", "model_download", "workflow_validation",
          "execution", "output_collection", "release")          # = failure_receipt.STAGES
STEPS  = ("stock_wait", "create", "provider_contract", "readiness", "bootstrap",
          "engine_install", "verify", "job", "fetch", "reset", "release")  # controller steps
GATES  = s2's Gate literal + ("offer", "provider")               # one list, not three
CODES  = failure_diagnostics.CODES ∪ engine _STATUS_ERROR_CODES ∪ provider codes:
         {"provider_rate_limited", "provider_transport", "provider_auth", "provider_malformed",
          "provider_cooldown", "field_not_observed", "mismatch", "stock_unavailable",
          "stock_snapshots_disagree", "price_unconfirmed", "status_exit", "status_no_receipt",
          "status_deadline_exhausted", "receipt_read_failed", "readback_mismatch", ...}

@dataclass(frozen=True)
class Reason:
    stage: str; step: str; code: str
    gate: str | None = None
    engine_step: str | None = None   # validated against the engine plan's step ids (engine_runner._status_step_ids)
    field: str | None = None         # a MachineRecord/StorageRecord field name, from a fixed list
    exit_code: int | None = None     # -255..255
    retry_after: float | None = None
    facts: Mapping[str, str] = {}    # FACTS, engine-keyed allowlist (s3)
    def validated(self) -> "Reason"  # every field in its vocabulary, or replaced by "unclassified"
```

- **No free text.** Every string field is drawn from a closed set. `engine_step` and the graph facts are checked against the job's own plan or graph, as `_safe_fact` already does. The human sentence is rendered from the vocabulary, as `failure_receipt._MESSAGES` does today.
- **Multi-engine:** an engine contributes `engine_step` (its recipe step ids) and a fact table. It never adds codes to core.
- **Multi-provider:** a provider maps its errors onto the same codes in its own pack, for example `provider.py` for RunPod.

### 6.2 How a reason flows

1. **Raise.** Every refusal is `PlacementRefused` (s2) or `EngineError` and carries a `Reason` (`exc.reason`). A check that used to return `bool` returns `Reason | None`, where None means pass.
2. **Pod.** The pod frame (`failure_diagnostics.parse_frame`) gains `step` and `engine_step`. `engine status` already emits `status`, `error_code` and `failed_step_id`, and these map one-to-one.
3. **Controller.** `machine_run._report_failure` (`machine_run.py:141-148`) passes `failure.reason` through as is. `machine.py:610-619` sets `claim_context` whenever a pod id is journaled, not only after `on_acquired`. That fixes failure 1's `no_machine` label.
4. **Receipt.** `failure_receipt.build_receipt` writes `cause.reason = reason.validated()` for **every** stage (today it does so only for `no_machine`, at `failure_receipt.py:126-133`). It derives `stage` from `reason.stage` when present, before the heuristics in `decide_stage`.
5. **Host to Runtime.** The canonical failure payload is built once from the Reason. The host writes its evidence under `result["host_failure"]` (s3) and compares that key on readback. `result.error` is Runtime's and is never asserted. Seam 6 then becomes a code-and-identity contract: `readback_mismatch` names the key that differed.
6. **CLI.** `generate failure` renders `Cause: stage=install step=verify code=status_exit exit_code=124 engine_step=start`. `--json` prints the Reason object.
7. **Neutral home.** The receipt moves from the RunPod pack to `core/generation/failure_receipt.py`, re-exported from the pack. `generic_host.py:7200` drops `is_runpod`, so local and attached failures get receipts too (Release 14).

### 6.3 Where reasons are dropped today (at `8cf3ada9`)

| # | File:line | How the reason is lost |
|---|---|---|
| 1 | `packs/runpod/worker_preparation.py:43-51` | any unknown gate becomes `"provider"` (tonight's "gate said provider") |
| 2 | `packs/runpod/target_selection.py:878-886` | `AcquisitionUnresolvedError(... failed gate)` `from None`; the cause is dropped, and the receipt's stage becomes `no_machine` |
| 3 | `packs/runpod/target_selection.py:874-877` | `NotReadyTimeout` becomes a generic text, `from None` |
| 4 | `packs/runpod/target_selection.py:893-897` | four conditions (status ≠ 200, empty body, mount mismatch, id mismatch) share one message |
| 5 | `packs/runpod/target_selection.py:912-917` | rate read: `from None`, or "could not be read" for any exception |
| 6 | `packs/runpod/target_selection.py:929-935` | non-gate exceptions become `unexpected <Type>`, with gate `unclassified` |
| 7 | `packs/runpod/target_selection.py:474-478`, `555-561`, `563-573` | any exception becomes `observation_failed` `from None` |
| 8 | `packs/runpod/adapter.py:37-48` | 17 lifecycle reasons collapse to 4; everything else becomes `provider_observation_unavailable` (seam 3) |
| 9 | `packs/runpod/adapter.py:127-128`, `140-142` | `retry_after` is read but never set by lifecycle |
| 10 | `packs/runpod/worker_preparation.py:490-493` | a GraphQL error becomes `machine = {}`, then "not reported before timeout" |
| 11 | `packs/runpod/worker_preparation.py:513-519` | catalogue failure, `from None` |
| 12 | `packs/runpod/worker_preparation.py:533-541` | an exception becomes `record = None`, then "gpuCount not reported" |
| 13 | `packs/runpod/worker_preparation.py:581-588` | 401, 429 and 500 all become "exact pod GET did not succeed"; then `from None` |
| 14 | `packs/runpod/worker_preparation.py:691-696`, `704-709` | release inventory `from None`; 429 becomes generic (seam 5) |
| 15 | `packs/runpod/worker_preparation.py:338-341`, `361-364`, `370-373` | `InvalidPodField` `from None` (it does not say which alias or source) |
| 16 | `packs/runpod/target_selection.py:40-44` | the same, for volume |
| 17 | `packs/runpod/remote_placement.py:613`, `617`, `619` | bare False (the legacy-status branch: JSON decode, `status ≠ installed`, health) |
| 18 | `packs/runpod/remote_placement.py:699`, `704`, `708`, `710` | bare False with no label (verification-branch deadline, base64, size) |
| 19 | `packs/runpod/remote_placement.py:638-641` with `failure_receipt.py:126-133` | the install label exists only in exception text; the receipt never copies it (seam 4, **live**) |
| 20 | `packs/runpod/remote_placement.py:595-597` | "bootstrap finished without marker" with no code |
| 21 | `packs/runpod/remote_placement.py:875-891` | `_bounded_call` reduces every failure to "bounded pod operation failed" `from None` |
| 22 | `packs/runpod/machine.py:822-826`, `844-846` | "remote failure diagnostic unavailable", "result is not JSON" `from None` |
| 23 | `packs/runpod/failure_receipt.py:58-61` and `machine.py:610-619` | no `claim_context` until `on_acquired`, so a pod that exists is labelled `no_machine` |
| 24 | `packs/runpod/failure_diagnostics.py:96-97`, `103-104` | `fallback()` gives `unknown`; non-listed exception classes become `UnknownError` |
| 25 | `packs/runpod/worker_owner.py:705-712` | only `type(exc).__name__` is kept; every failure is retried after 1 s |
| 26 | `packs/runpod/h3_release.py:367`, `387`, `390`, `452` | `BuildError(str(exc))` `from None`: provider free text re-raised as text |
| 27 | `packs/runpod/h3_release.py:428-433` | `"HTTP 401" in str(exc)` string matching |
| 28 | lifecycle `api.py:83-84`, `93-94`, `118-122` | volume lookup failures return `[]`, so "transport down" reads as "no such volume" |
| 29 | lifecycle `api.py:155-158` | `RuntimeError` with status and body text; `Retry-After` lost |
| 30 | lifecycle `availability.py:66-72`, `262`, `376` | free-text reasons; `reason=str(exc)` |
| 31 | `core/execution/generic_host.py:5830` with Runtime `store.py:6804` | `result.error` is written by two owners, so the readback fails (seam 6) |

### 6.4 First slice (C1)

- **Files:**
  - `core/generation/failure_vocabulary.py`: about 120 lines (tables plus `Reason`).
  - `failure_receipt.py`: copy `cause.reason` for every stage; derive the stage from the Reason.
  - `machine.py:610-619`: `claim_context` from the journaled pod id.
  - `remote_placement.py`: `_canonical_installed` and `_engine_installed_healthy` return `Reason | None`, which removes all 7 bare False returns (sites 17–19).
  - `adapter.py:37-48`: one table covering all 17 lifecycle strings, with a test that reads the installed lifecycle's `availability.py` and fails on any unmapped literal.
  - `generate failure` renders the Reason.
  - `tests/test_no_reasonless_refusals.py`: an AST lint over `astrid/packs/*` and `astrid/core/generation`. A `raise X(...) from None` must construct an exception with `reason=` or a required `gate=`. The committed per-file count of offenders may only fall, starting from about 23 `from None` sites in lifecycle and about 58 in the pack.
- **Tests:** one receipt test per controller step (for example, an `engines status` exit gives `stage=install`, `step=verify`, `code=status_exit`, `exit_code`); the offer table; `claim_context`; the CLI render.
- **Size:** about 1.5 worker-days.
- **Replaces:** the three gate sets (`worker_preparation.py:48-50`, `failure_receipt.py:130-131`, the `PaidSelectionError` docstring), `_OFFER_FAILURES` as the retry decider (it stays as message text), the `install_unverified` string join (`remote_placement.py:670-671`), and stage guessing from exception class.
- **Ownership:** `failure_receipt.py`, `remote_placement.py` and `machine.py` are held by the bundle round, so C1 lands right after it.
- **Risk:**
  - The vocabulary grows into free text. Mitigation: closed sets, `validated()` at every crossing, and a fixed message table.
  - Receipt schema churn. Mitigation: `cause.reason` is additive, under the same `astrid.generation.failure-receipt.v1` schema.

### 6.5 The G3 bundle

**Could structured facts make the free-text bundle unnecessary by default? Yes.**

The evidence is tonight's six failures. Each is fully diagnosable from a Reason plus timing, with no log:

1. `gate=storage code=field_not_observed field=storage_id step=provider_contract`;
2. disproved offline by replay;
3. `step=stock_wait code=stock_snapshots_disagree`;
4. `stage=install step=verify code=status_exit exit_code=<n>` or `engine_step=start code=deadline_exceeded`;
5. `step=release code=provider_rate_limited retry_after=<s>`;
6. `code=readback_mismatch field=result.error`.

None needed a pod log.

The bundle's review history (BLOCK in rounds 1 and 2) has one root cause, the decode-and-match denylist (decision log 00:58). That is the same anti-pattern this design removes: free text treated as data.

**Recommendation (owner's call, H10):**

- Structured reasons are the default for every run.
- The bundle becomes opt-in per run, with explicit consent (`--collect-failure-logs`), and is offered only when the Reason is `stage=execution` with `code ∈ {command_failed, generation_failed}`. That is the one class where step, code and exit status cannot say why, for example a Python traceback inside a node pack.
- The redactor work continues, but it is off the paid critical path.
- "The bundle gates every later run" (decision log 23:00) is replaced by "the Reason gates every later run": a run whose receipt says `unknown` is a defect to fix before the next rental.

---

## 7. Piece D: an offline end-to-end harness

### 7.1 What exists

- **`tests/integrations/test_remote_machine_cpu.py` (1251 lines).** It runs a real Runtime (`real_runtime`), a real host, `GenericPackHost`, the lease owner, the HTTPS client and receipts. Provider HTTP and the pod agent are faked by intercepting `httpx.Client.send`/`requests.Session.send` (`:530-554`) into `MachineProviderHTTP` (`:64-460`). Commands are answered by string matching (`:197-245`). It covers cold and warm runs, custody change, cancel, a bad mount, a killed pod, CLI release, keep, receipts and no stock.
  - Its gaps: one invented pod record for every endpoint (`:166-172`); REST ignores parameters (`:439-443`); stock is always consistent (`:139-145`); `engines status` returns a receipt at once (`:237-240`); there are no 429s; and it never asserts the host readback.
  - It does not patch `_bounded_call` itself. Its siblings do (§5.3), so the spawned-child path used by bounded verification is never tested against any fake.
- **`tests/helpers/pod_jobs_runtime.py:237-293`.** It runs the **real lifecycle `AgentServer`** on `127.0.0.1` with a real `HttpsPodTransport(base_url=...)`, with real detached jobs, uploads and downloads. It is used by `tests/scripts/test_pod_jobs.py`, but not by the machine journey.
- **`tests/integrations/test_remote_machine_job_seam_cpu.py`.** The shipped job runs through the real pod-side local runner.
- **`tests/core/generation/test_closure_install_cpu.py`.** It runs real install subprocesses locally, up to a sentinel.
- **`_HttpsOps(base_url=...)`** (`remote_placement.py:788-801`) already accepts a base URL. Production never sets it.

### 7.2 What is missing

1. **A replaying provider.** Its provider half should be built from §5 recordings: it honours parameters, matches GraphQL by query hash, refuses unrecorded requests, and allows value variations only.
2. **A fault matrix.** One injected failure per step should assert one expected Reason, so a blind failure is a test failure.
3. **The real pod agent in the journey.** The pod half should be the real `AgentServer`, reachable from spawned children, so the `_bounded_call` fakes can go.
4. **A no-op CPU engine.** It needs a real `engines install`/`status` that is not ComfyUI. Today three rules block it: one engine per platform (`engine_recipe.py:396`), no CPU platform key (`engine_recipe.py:49`), and the required `cuda_visible_devices` (`engine_runner.py:1060`). Its health probe has to fit `HealthSpec`'s ComfyUI fields (`engine_contracts.py:208-213`).
5. **The real pod layout.** Bootstrap writes `/opt/astrid` and `/root/astrid/...` (`remote_placement.py:50-57`, `pod_bootstrap.py:90-91`). The full chain therefore needs a container CI job.

### 7.3 First slice (D1): catches all four of tonight's failures and the two later ones

**Scope:** change `MachineProviderHTTP`'s provider half only. The pod half and the engine stay faked for now.

- **D1-a. Replay.** `graphql()` and the REST branch answer from `tests/providers/recorded.py`. Pod records are recorded shapes with `vary()` for the journey's ids, image and volume. REST honours `includeNetworkVolume` and `includeMachine` exactly as recorded. Stock and price come from recorded availability responses.
- **D1-b. Fault matrix** (`tests/integrations/test_remote_machine_faults_cpu.py`, parametrised). Each case gives: injection, then expected `Reason` in `failure-receipt.json` and in `generate failure --json`.

| Case | Injection | Expected Reason (and other assertions) |
|---|---|---|
| contract | the list record in the GraphQL-plus-`networkVolume` shape | the claim succeeds today. With the pre-`e6d85766` reader it fails with `gate=storage`, `code=field_not_observed` (**seam 1**) |
| exact GET | a default REST GET (no `networkVolume` object) | the claim succeeds. This proves offline that **seam 2** was not a failure |
| stock | one cycle where the stock snapshot ≠ the price snapshot (a value `vary`) | the wait continues; the progress row says `stock_snapshots_disagree`. Pre-`f1a487c9` code refuses (**seam 3**) |
| verify | `engines status`: exit 124 / empty / `status=failed, error_code=X, failed_step_id=start` | `stage=install`, `step=verify`, with `code=status_exit` and `exit_code=124`, or `status_no_receipt`, or `code=X engine_step=start`. **This fails at `8cf3ada9`** (seam 4: `failure_receipt.py:126-133`) |
| release 429 | `GET /v1/pods` replays a 429 with `Retry-After: 30` three times | `step=release`, `code=provider_rate_limited`, `retry_after=30`; at most N requests per window across daemon and CLI; never an absence receipt (**seam 5**) |
| execution | the job exits 1 with a frame | `stage=execution`; the host readback succeeds; the attempt spool is not kept as pending; no "claim failed" log line. **This fails at `8cf3ada9`** (seam 6) |
| boot | the agent's `/health` answers only after the readiness window | `stage=boot`, `step=readiness`; the pod id is in the receipt (never `no_machine`) |
| create rejected | recorded capacity rejection | `stage=no_machine`, `step=create`, `code=stock_unavailable` |

- **D1-c. Invariant over every journey:** `receipt.cause.reason.code != "unknown"`, and every provider request seen was recorded.
- **Files:** `test_remote_machine_cpu.py` (provider half, about −150 and +80 lines); a new fault test of about 250 lines; `tests/providers/recorded.py` (from B1).
- **Size:** about 1.5 worker-days.
- **Depends on:** B1 (recordings and replay), C1 (Reason in the receipt) for the assertions, and s3 (`host_failure`) for the execution row.
- **Replaces:** the hand-written provider half and its invented records.
- **Risk:**
  - The journey is slow (a real Runtime). Mitigation: the fault matrix shares one Runtime per module, and stays under 120 s.
  - Rows 4 and 6 fail before C1 and s3 merge. They land `xfail(strict=True)` with the fixing slice named, and the xfail is removed in that slice.

### 7.4 Later slices

- **D2 (1.0 worker-day). Real pod agent.** `MachineProviderHTTP`'s pod half becomes the `pod_jobs_runtime` `AgentServer`. A test-only `_HttpsOps` factory supplies `base_url`; a production environment hook is never added. Spawned `_bounded_call` children get it through their arguments, which already carry `base_url` (`remote_placement.py:822`, `938-942`). The `_bounded_call` replacements in `test_generation_preparation.py:236`, `test_failure_diagnostics.py:177` and `test_machine.py:400`, `465` and `509` are then removed. Commands run for real in a temporary root, with `ASTRID_BOOTSTRAP_ROOT`/`ASTRID_ENGINE_ROOT` overrides (`pod_bootstrap.py:90-91`); `remote_placement` constants move behind one pod-layout object.
- **D3 (2.0 worker-days). No-op CPU engine.** Add a `linux-x86_64-cpu` platform key. Index rows become unique per (engine, platform), not per platform (`engine_recipe.py:396`). `HealthSpec` gains `kind: "http_json" | "comfy_object_info"`, which takes ComfyUI out of the shared contract. The GPU-visibility fact becomes required only for GPU platforms (`engine_runner.py:1060`). The recipe `noop` (in `tests/engines/noop/` or a test catalogue through `load_recipe(registry=...)`, `engine_recipe.py:424`) starts a 20-line stdlib HTTP server. This is also the first proof that a second engine needs no core edit.
- **D4 (1.5 worker-days). Container CI job.** The full chain runs in `python:3.12-slim`, with the agent started as the pod starts it and the real `pod_bootstrap.sh` and `pod_reset` in the real paths: stock wait → create → provider contract → readiness → bootstrap → engine install → verify → job → fetch → reset → release. Runs on `r13/*` only (the 19:42 incident rule).

---

## 8. Amendments to the in-flight slices (decide before merging them)

| Slice | Amendment | Why |
|---|---|---|
| s1 | Add `MachineRecord.observed` and `require()` (§4.2). Change the s1 test "SDK GraphQL fixture yields `storage_id=None`, because that shape has no attachment" to also assert `"storage_id" not in observed` and that `require` refuses. | As briefed, the test enshrines tonight's failure-1 semantics (None meaning "no volume"). |
| s1 | Key strict key sets by request (query hash and parameters), not by file. Mark the SDK GraphQL fixture `sdk_query_pod` and do **not** use it as the key set for lifecycle's `QUERY_PODS`. | G-a: production sends a different query (it adds `machine.dataCenterId`). |
| s1 | Do not derive port and route parsing from tonight's fixtures. | G-b: the scrubbing changed types. |
| s1 | "In production, missing known keys are None" applies only to fields outside `observed`. A known key that is missing from a shape that should observe it gives `code=provider_malformed`. | This keeps it fail-closed without strict mode. |
| s2 | Add `"offer"` and `"provider"` to `Gate`, and give `PlacementRefused` an instance `reason: Reason` (C1), or at least `step` and a reason `code`. | Without them, seam 3 still collapses into one label, and the receipt can name a gate but not what failed. |
| s2 | The `OfferObservationError` "ONE table" must cover lifecycle's 17 reason strings, not the Agent's 7 labels. | `adapter.py:37-48` is where specificity is lost. |
| s3 | Also record which host-owned keys the readback compared, as `readback_mismatch` with `field`. | Seam 6 becomes self-describing. |
| none yet | The provider gate (§4.3), C1 (§6.4), B1 (§5.4) and D1 (§7.3) | They are not covered by s1–s3. Of the files they touch, `worker_owner.py`, `failure_receipt.py`, `remote_placement.py` and `machine.py` are held by the bundle round. |

---

## 9. Order

1. **Now, before s1 merges:** the s1 amendments (0.25 worker-day, folded into s1's review).
2. **s1, s2 and s3 merge.** s2 then provides `next_delay`, and s3 provides `host_failure`.
3. **B1 recorder: the manager runs it on the next paid diagnostic run.** It needs no product change, so it does not conflict with "patch only what blocks a paid cell". The replay loader and ratchet are built in parallel by a worker.
4. **C1, as soon as the bundle round releases its files.** After C1, every paid run produces a named reason.
5. **D1, after B1 and C1.** Rows 4 and 6 start as `xfail(strict)` if they land first.
6. **The provider gate, after s2 and the bundle round** (it touches `worker_owner.py`).
7. **Release 14:** A2, then lifecycle L1–L3 with a pin bump, then D2 → D3 → D4. The move of the receipt into core and the neutral-hook work on the §3 leaks run alongside.

Dependencies: A1+ → (B1, C1) → D1. s2 → gate. D3 needs the engine-index rule change. D4 needs D2 and D3.

---

## 10. Recommendation (one page)

**Do in Release 13.** This is what makes the next paid run diagnosable from its receipt:

| Item | Worker-days | Status |
|---|---|---|
| s1 + s2 + s3 (Moves 1–3) | 1.75 | in flight |
| s1 amendments: `observed`/`require`, request-keyed key sets | 0.25 | new; before s1 merges |
| C1: one vocabulary, `cause.reason` for every stage, `claim_context` fix, no bare False, 17-string offer table, no-reasonless-refusal ratchet, CLI render | 1.5 | new |
| Provider gate: account-scoped cooldown, coalesced release snapshot, `timer(1)` removed | 1.0 | new |
| B1: recorder, scrub policy and verifier, replay loader, fake ratchet; passive capture on paid runs | 1.25 | new (+0.25 manager-hour per run) |
| D1: replaying provider in the CPU journey, plus the fault matrix | 1.5 | new |
| **Total** | **≈ 7.25** | about 2.5 calendar days across three workers, plus about 1 manager day of review |

**Defer to Release 14:**

| Item | Worker-days |
|---|---|
| A2: migrate the remaining readers to records, `StorageRecord`, delete `pod_fields.py`, fix h3's latent attachment spin | 1.5 |
| Lifecycle L1–L3 (typed HTTP errors, reason codes, one-request `list_pods`) plus the pin cycle | 1.5 |
| B2: migrate the 17 violating test files under the ratchet | 2.0 |
| D2: real `AgentServer` in the journey; remove the `_bounded_call` fakes | 1.0 |
| D3: no-op CPU engine (engine index per (engine, platform), `HealthSpec.kind`, GPU fact only on GPU platforms) | 2.0 |
| D4: container CI job for the full chain | 1.5 |
| Receipt into core and neutral hooks for the §3 RunPod leaks (`generic_host`, `placement`, `machines_cli`, `sdk/generation`) | 1.5 |
| **Total** | **≈ 11.0** |

**Decisions needed from the owner or orchestrator:**

1. **Accept the s1 amendment** (`observed`/`require`). Without it, the new boundary re-creates failure 1.
2. **H10:** make the G3 bundle opt-in (consented, offered only for `execution`/`command_failed`/`generation_failed`), and replace "the bundle gates every run" with "a named Reason gates every run". **REVIEW.**
3. **Recording method:** passive capture by the manager during paid runs already planned. A dedicated session (about $0.25) only if two runs miss a state.
4. **Rule from C1 onward:** a receipt whose cause is `unknown` is a defect to fix before the next rental, not a diagnosis to buy with one.

**Expected effect.** Of tonight's six failures, five would have been caught in CI with no rental, and the sixth (seam 2) would have been ruled out at no cost. Each paid run after Release 13 either succeeds or names its stage, step and code in its receipt. A second provider adds a parse module and a recordings folder; a second engine adds a recipe and a fact table. Neither touches core.
