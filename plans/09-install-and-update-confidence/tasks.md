# Tasks: Install and update confidence

[Plan](plan.md) · [Inputs](inputs.md) · [Project status and owner](../../README.md)

The project is planned, not dispatched. Exact test selectors are not present in the source plan; identify them during task setup. Do not run broad or auto-discovered suites. Task progress is the single `[ ]` record in each index row/card.

## Task index

| ID / outcome | Route | Depends on | Progress |
|---|---|---|---|
| [IU-0 Freeze sources and record path × OS × evidence baseline](#iu-0-freeze-sources-and-record-path--os--evidence-baseline) | N | start | [ ] |
| [IU-1 Consolidate update transaction and delegate routes](#iu-1-consolidate-update-transaction-and-delegate-routes) | X | IU-0 | [ ] |
| [IU-2 Hosted update-while-running and rollback legs on three OSes](#iu-2-hosted-update-while-running-and-rollback-legs-on-three-oses) | X | IU-1 | [ ] |
| [IU-3 Real version update with schema migration](#iu-3-real-version-update-with-schema-migration) | X | IU-1 | [ ] |
| [IU-4 Windows locked-file handling](#iu-4-windows-locked-file-handling) | X | IU-2 | [ ] |
| [IU-5 Hosted in-app/background routes or removal](#iu-5-hosted-in-appbackground-routes-or-removal) | N | IU-1 | [ ] |
| [IU-6 Uninstall after R0→R1 upgrade](#iu-6-uninstall-after-r0r1-upgrade) | N | IU-0 | [ ] |
| [IU-7 Windows R0→R1 upgrade or permanent refusal](#iu-7-windows-r0r1-upgrade-or-permanent-refusal) | X | IU-1 | [ ] |
| [IU-8 Typed Agent↔Runtime control contract and dead-code retirement](#iu-8-typed-agentruntime-control-contract-and-dead-code-retirement) | S | IU-1 | [ ] |
| [IU-9 Platform breadth](#iu-9-platform-breadth) | N | IU-2 | [ ] |
| [IU-10 Captured real service-manager output in unit fakes](#iu-10-captured-real-service-manager-output-in-unit-fakes) | N | IU-0 | [ ] |
| [IU-11 Update-test hardening (from the R1 update-test review)](#iu-11-update-test-hardening-from-the-r1-update-test-review) | N / Luna | IU-1 | [ ] |
| [IU-12 Windows pack-host retirement premise](#iu-12-windows-pack-host-retirement-premise) | X | IU-0 | [ ] |
| [IU-13 Installer lock hand-off for schema-changing updates](#iu-13-installer-lock-hand-off-for-schema-changing-updates) | X | IU-1 | [ ] |
| [IU-14 Unblock: set aside managed copies of built-in packs (Release 13)](#iu-14-unblock-set-aside-managed-copies-of-built-in-packs-release-13) | X | start | [ ] |
| [IU-15 Lived-in update gate from every published release](#iu-15-lived-in-update-gate-from-every-published-release) | X | IU-14 | [ ] |
| [IU-16 Sign-in on clean installs without the legacy copy](#iu-16-sign-in-on-clean-installs-without-the-legacy-copy) | X | IU-14 | [ ] |
| [IU-17 One bundled-pack root, capabilities proven](#iu-17-one-bundled-pack-root-capabilities-proven) | N | start | [ ] |
| [IU-18 Nothing outside the version root is authoritative or fatal](#iu-18-nothing-outside-the-version-root-is-authoritative-or-fatal) | S | IU-15, IU-17 | [ ] |
| [IU-19 Tombstones retired with version pruning](#iu-19-tombstones-retired-with-version-pruning) | X | IU-15, IU-18 | [ ] |
| [IU-20 An update a person can follow](#iu-20-an-update-a-person-can-follow) | X | IU-14 | [ ] |
| [IU-21 Review rule for ownership moves](#iu-21-review-rule-for-ownership-moves) | N | IU-15 | [ ] |
| [IU-END Scoped review and promotion](#iu-end-scoped-review-and-promotion) | X | all | [ ] |

## Task details

### IU-0 Freeze sources and record path × OS × evidence baseline

- **Outcome:** Frozen starting identities and a baseline matrix classifying each supported path on Linux, macOS, and Windows as real, mocked, or untested.
- **Route:** N
- **Dependencies and inputs:** Start; see [inputs](inputs.md). Record exact `pre-main` heads for all three repositories, Plan 08 verified outputs and donor commits, and create-only candidate naming rule. Recover baseline evidence at task start.
- **Work:** Enumerate supported paths from this plan: newer-release update; update while Runtime runs; failed-update rollback after staging; in-app button; background job (or note proposed removal dependency); install-line repair; uninstall; real R1→candidate schema migration; Windows locked-file case; Linux without a systemd user manager; Intel macOS; Windows 11 Home, non-admin, and Defender. Mark each path/OS cell and evidence mode.
- **Baseline matrix (record at start):** Each cell is `real`, `mocked`, `none`, or a named limitation; all are TBD until evidence is collected.

  | Path | Linux | macOS | Windows |
  |---|---|---|---|
  | Fresh install | TBD | TBD | TBD |
  | Update to newer release | TBD | TBD | TBD |
  | Update while Runtime runs | TBD | TBD | TBD |
  | Rollback after post-stage failure | TBD | TBD | TBD |
  | In-app update route (if retained) | TBD | TBD | TBD |
  | Background update job (if retained) | TBD | TBD | TBD |
  | Install-line repair | TBD | TBD | TBD |
  | Uninstall | TBD | TBD | TBD |
  | Released R1→candidate schema migration | TBD | TBD | TBD |
  | Locked file during update | TBD | TBD | TBD |
  | No systemd user manager | TBD | N/A | N/A |
  | Intel Mac | N/A | TBD | N/A |
  | Windows 11 Home / non-admin / Defender | N/A | N/A | TBD |
- **Focused checks:** No product test selector specified. Record the exact existing selectors and hosted job IDs during setup; the matrix itself must distinguish real hosted evidence from mocked/unit evidence and absence.
- **Done:** Baseline matrix and exact frozen identities are recorded; source and predecessor custody is clear.

### IU-1 Consolidate update transaction and delegate routes

- **Outcome:** Install-line `--update`, in-app `astrid/installer/local_update.py`, `update_job.py`, and `app_update.py` delegate to one stage → switch `current` → restart → verify transaction, with rollback on failure; fold in or retire `custody.py`.
- **Route:** X
- **Dependencies and inputs:** IU-0; Plan 08 update step and Plan 01 I-02 file overlap. See [inputs](inputs.md).
- **Work:** Implement the single update path while preserving data and old working version on failure/refusal. Coordinate shared `cli.py` and `backend.py` changes with Plan 01; rebase whichever lands second.
- **Focused checks:** Source acceptance names existing update unit tests, expected to pass unchanged, and one shared call path. Exact selectors are TBD at setup; do not substitute broad suites.
- **Done:** Existing focused update tests pass and route inspection shows a single transaction path; evidence records `custody.py` disposition.

### IU-2 Hosted update-while-running and rollback legs on three OSes

- **Outcome:** Hosted Linux, macOS, and Windows legs update while Runtime is running and roll back after an injected failure after staging.
- **Route:** X
- **Dependencies and inputs:** IU-1; frozen candidate and matrix from IU-0.
- **Work:** Exercise both behaviors per OS. On injected failure, verify the old version remains current and healthy and user data remains intact. Include: an upgrade or update stops a busy Runtime and interrupts its in-flight task (R1 named limitation); prove the task is resumed or cleanly failed.
- **Focused checks:** Exact hosted workflow/job selectors TBD at setup; record each OS result and fault-injection point.
- **Done:** Both hosted legs pass on all three OSes, or affected matrix cells are explicitly recorded as unsupported limitations.

### IU-3 Real version update with schema migration

- **Outcome:** Previous released R1 updates to the candidate, including workspace schema migration, with data checked after restart.
- **Route:** X
- **Dependencies and inputs:** IU-1; recover the actual released R1 identity and candidate identity at setup. Plan 08 stand-in evidence alone is insufficient.
- **Work:** Run a genuine version-to-version update on Linux, macOS, and Windows; verify migrated workspace data and task state after restart.
- **Focused checks:** Exact hosted job selectors and data assertions TBD at setup.
- **Done:** Real R1→candidate hosted evidence verifies data and task intact after restart on each supported OS, or records a named limitation per matrix cell.

### IU-4 Windows locked-file handling

- **Outcome:** Windows update handles stop ordering and locked files safely.
- **Route:** X
- **Dependencies and inputs:** IU-2; Windows service behavior at `service.py` around lines 972–983 (verify current source at setup).
- **Work:** Exercise service stop ordering and a locked file during update; refuse cleanly when the file cannot be safely changed. The CI direct-windows row now uses the real user profile on hosted runners (astrid-agent #270); the old sandbox profile split the installer from the Task-Scheduler-started Runtime and hid its logs. Keep the real profile, or make the Runtime's paths profile-independent.
- **Focused checks:** Exact Windows hosted selector and lock injection mechanism TBD at setup.
- **Done:** Update succeeds or refuses in one sentence while the old version remains working and data remains intact.

### IU-5 Hosted in-app/background routes or removal

- **Outcome:** Each retained in-app update button and background-job route has hosted coverage, or redundant routes are removed under the single-entry design.
- **Route:** N
- **Dependencies and inputs:** IU-1; route inventory from IU-0.
- **Work:** Decide which of `local_update.py`, `update_job.py`, and `app_update.py` remain user-facing/necessary after consolidation; test every kept route.
- **Focused checks:** Exact hosted selectors TBD at setup; each kept route requires a pass on Linux, macOS, and Windows.
- **Done:** Every retained route has three-OS hosted evidence, or its removal is evidenced and its replacement route is covered.

### IU-6 Uninstall after R0→R1 upgrade

- **Outcome:** Uninstall after an R0→R1 upgrade follows the verified-program-path rule.
- **Route:** N
- **Dependencies and inputs:** IU-0; R0 and R1 identities from the frozen source/release records.
- **Work:** Verify R1's program label/path first, then R0's only when each path points inside its own root. Preserve refusal on ambiguity and protect user data.
- **Focused checks:** Exact hosted upgrade/uninstall selectors TBD at setup.
- **Done:** Hosted upgrade legs assert clean uninstall with the program-path rule and retained data behavior.

### IU-7 Windows R0→R1 upgrade or permanent refusal

- **Outcome:** Implement Windows R0→R1 upgrade, or record the owner's choice to keep the R1 refusal permanently.
- **Route:** X
- **Dependencies and inputs:** IU-1; Windows R0/R1 identities and current refusal behavior to be frozen at setup.
- **Work:** Owner decision is preserved: this is low priority because few R0 Windows users exist; if refusal remains, ensure it is permanent and safe.
- **Focused checks:** Exact Windows hosted selector TBD at setup; for refusal, verify it occurs before mutation and preserves old version/data.
- **Done:** Hosted Windows upgrade passes, or the permanent refusal decision and evidence are recorded.

### IU-8 Typed Agent↔Runtime control contract and dead-code retirement

- **Outcome:** Runtime CLI schema becomes the typed Agent↔Runtime control contract; retire the Runtime discovery file except as an endpoint hint and delete R0-era Agent code with no remaining callers.
- **Route:** S
- **Dependencies and inputs:** IU-1; frozen astrid-agent and astrid-runtime source identities from IU-0.
- **Work:** Define/align both sides on the typed CLI contract, preserve discovery file only as endpoint hint, and establish that deleted legacy code has no callers.
- **Focused checks:** Contract tests on both Agent and Runtime and a caller search; exact selectors TBD at setup.
- **Done:** Both contract-test evidence and no-caller evidence are recorded for removed code.

### IU-9 Platform breadth

- **Outcome:** Fresh install and update coverage addresses Linux without a systemd user manager, Intel macOS, and Windows 11 Home, non-admin users, and Defender.
- **Route:** N
- **Dependencies and inputs:** IU-2; per-OS gap matrix from IU-0. Linux fallback is identified in `service.py` around lines 110–127; verify current source at setup.
- **Work:** Exercise each named environment and classify supported versus limited behavior for fresh install and update. Add the real-Mac (self-hosted) fresh install and update smoke: it never passed during R1 (MAC-UPDATE-01..04 on astrid-agent issue #167); hosted macOS passes.
- **Focused checks:** Exact environment/hosted selectors TBD at setup.
- **Done:** Fresh install and update pass for each environment, or a named limitation is recorded for each unsupported matrix cell.

### IU-10 Captured real service-manager output in unit fakes

- **Outcome:** Unit fakes for `systemctl`, `launchctl`, and `schtasks` use captured real output.
- **Route:** N
- **Dependencies and inputs:** IU-0; capture provenance from the relevant OSes.
- **Work:** Replace synthetic output that previously missed the `=> true` versus `=> disabled` distinction, a bug hit twice in R1.
- **Focused checks:** Exact focused unit selectors TBD at setup; compare fake fixtures to captured output.
- **Done:** Captures and provenance are recorded, fakes match them, and the focused tests pass.

### IU-11 Update-test hardening (from the R1 update-test review)

- **Outcome:** The update tests share one stand-in release generator, check old-version retention by digest, and use fewer mocks.
- **Route:** N / Luna.
- **Dependencies and inputs:** IU-1. Source: the R1 update-test review.
- **Work:** Dedupe the stand-in release generator into `make_standin_release.py`; `journey_fresh_update.standin` and `windows_update_journey.py` hold copies with differing markers. Strengthen the old-version retention check: compare the old manifest digest before and after the update, not only that `version.json` exists. The gate binds `manifest_sha256` to the uploaded artifact bytes and marker. Reduce mocks in `tests/test_journey_fresh_update.py` and `tests/test_windows_fresh_update.py`.
- **Focused checks:** Exact selectors TBD at setup; the two test files above only, no broad suite.
- **Done:** One generator remains; the retention check compares digests; the gate binding is covered by a focused check; both test files use fewer mocks.

### IU-12 Windows pack-host retirement premise

- **Outcome:** The R1 fix B premise holds on Windows, and parked fix A is decided.
- **Route:** X.
- **Dependencies and inputs:** IU-0. R1 fix B (astrid-agent #283) retires an old pack-host registration when its Runtime instance has exited. It relies on Runtime services running in a Windows Job with `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` (astrid-runtime `runtime_protocol/platform.py`, around line 724).
- **Work:** Confirm that every Windows service launch is inside that Job, with no breakaway. Decide parked fix A: the Runtime writes the pack-host `job_drained` receipt before the installer's manager-stop callback (astrid-runtime `runtime_protocol/services.py`).
- **Focused checks:** Source inspection of each Windows service launch path; exact selectors TBD at setup.
- **Done:** Evidence lists each Windows launch path as inside the Job or a named breakaway, and fix A has a recorded decision.

### IU-13 Installer lock hand-off for schema-changing updates

- **Outcome:** An update that changes the workspace schema completes on both the direct and Pinokio paths.
- **Route:** X.
- **Dependencies and inputs:** IU-1. Found while proving Pinokio (Plan 07; astrid-agent #290). The installer holds `astrid-install.lock` for the whole update: the direct CLI holds it itself, and on Pinokio the stopped-path custody child holds it. The Runtime's `upgrade` takes the same lock without waiting (astrid-runtime `astrid_runtime/operator_upgrade.py` `_installer_mutex`, around lines 208-226) and refuses with "another installer owns the installation lifetime lock". #290 made same-schema updates skip `upgrade`, so no released update hits this yet. The first schema-changing release will.
- **Work:** Let the Runtime accept proof that its parent installer already holds the lock: an inherited lock descriptor on the direct path, and a custody lease on Pinokio, because a Windows byte-range lock cannot be handed to another process. Or have the Agent run the migration without the Runtime's own installer mutex. Do not weaken or bypass the lock.
- **Focused checks:** A stand-in release with a newer schema target updates through both paths on Linux, macOS and Windows, with the workspace preserved.
- **Done:** That stand-in update passes on all six direct and Pinokio rows.

### IU-14 Unblock: set aside managed copies of built-in packs (Release 13)

- **Outcome:** A user who signed in to Hivemind on Release 1, 9 or 10 updates to the current release by re-running the normal update, keeps Hivemind sign-in, and can still roll back.
- **Route:** X. Implemented on astrid-agent `claude/bold-keller-m2v22v` `4d9c8e447`, including the skills-sync stderr fix found by the journey.
- **Dependencies and inputs:** [Phase 2 evidence](inputs.md#phase-2-upgrade-safe-installed-state).
  - R1, R9 and R10 `astrid login` provisions a managed Hivemind *before* authenticating: an `active.hivemind` entry in `~/.local/state/astrid/default/pack-sources.json` and a checkout in `~/.local/share/astrid/packs/hivemind`.
  - From R11, Hivemind is built in, and `astrid/core/pack/ownership.py:39-45` makes the duplicate fatal. The pack host exits 1 and the installer rolls back.
  - An edited legacy checkout fails at verification (`source_setup.py:384`). A registration whose checkout was deleted fails in `custody_broker.py:2412`.
- **Work:**
  - Derive the product pack ids from what ships in the version.
  - In `active_sources`, set aside managed entries with those ids *before verification*. The custody broker's own parser does the same.
  - Sign-in keeps reading the legacy helper, and nothing writes the state file or the checkout.
- **Focused checks:**
  - Unit fixtures with an R1-shaped state: a clean, a dirty and a deleted checkout; the state is byte-identical afterwards; a non-product managed pack is still verified.
  - A macOS journey that provisions the managed Hivemind with R1's own code, then updates. It fails on R12, passes on the hotfix, and includes a forced rollback.
- **Done:** The journey passes in all three variants from R1, R9 and R10. Folded into Release 13 (owner, 12 Nov), together with IU-20's progress lines.

### IU-15 Lived-in update gate from every published release

- **Outcome:** The update gate starts from every published release, in a state that real use creates, and from a hostile home folder.
- **Route:** X.
- **Dependencies and inputs:** IU-14. The R12 matrix starts from three hand-picked releases with an empty, isolated HOME, so it could not see this incident.
- **Work:**
  - **Fixtures:** for each release in the App manifest history, build a fixture with that release's own code in a disposable HOME/XDG. It signs in (provisioning only), adds a pack, makes a project with a timeline, and keeps an App tab polling during the update. Save it once per release.
  - **Gate rows:** update from each fixture to the candidate, plus one forced rollback from each origin.
  - **Hostile-state test:** whatever is under XDG state and data (garbage, duplicates, dirty or missing checkouts, old formats), the host reaches ready with every product capability.
  - **Write-set:** record each release's write-set outside `versions/` and diff it at review.
- **Focused checks:** each new row fails against R12 for the incident fixture and passes on IU-14.
- **Done:** The gate's origin list is generated from the manifest history, and the release skill requires it.

### IU-16 Sign-in on clean installs without the legacy copy

- **Outcome:** `astrid login` works on a fresh install, and updating or rolling back never signs a user out.
- **Route:** X.
- **Dependencies and inputs:** IU-14. The R12 `auth.py:45-63` finds a helper only in a managed Hivemind checkout or on PATH. Core Hivemind ships none, and the default declarations are empty (`source_setup.py:508`).
- **Work:** Ship the helper from core Hivemind (its protocol lives in the Hivemind repository), using the same credential store as the legacy helper.
- **Focused checks:**
  - login, status and logout on a clean install;
  - a signed-in R10 fixture updates and is still signed in;
  - rollback keeps the login.
- **Done:** Those three pass on macOS and Linux.

### IU-17 One bundled-pack root, capabilities proven

- **Outcome:** An installed release scans its bundled packs once, and its capability set matches a source checkout.
- **Route:** N.
- **Dependencies and inputs:** On installed R12, 11 bundled packs are "quarantined" from `versions/<v>/a/astrid/packs/<id>` while their capabilities still register, which points to a second physical copy. `loader.packs_root()` is path-derived (`loader.py:98-99`), so a second copy makes path-based ownership unsound.
- **Work:** Find why the second root is scanned and remove it or exclude it. Compare installed and source capability sets.
- **Focused checks:** No quarantine lines for bundled packs on an installed host, and identical capability ids.
- **Done:** Both hold on macOS, Linux and Windows.

### IU-18 Nothing outside the version root is authoritative or fatal

- **Outcome:** Astrid's own code lives only inside `versions/<v>`. Anything outside it is user data or cache, and can never override a product pack or stop the host.
- **Route:** S.
- **Dependencies and inputs:**
  - IU-15 protects the refactor; IU-17 makes path-derived ownership sound.
  - Today ownership is reconstructed independently by name reservation (`discovery.py:437`), manifest arbitration (`ownership.py:39`), path ancestry (`loader.py:296`) and sign-in (`auth.py:45`).
  - About ten consumers read the managed inventory, including `loader.py`, `skills/__init__.py:29`, `scopes.py:57` and `remotion_runtime.py`.
- **Work:**
  - One admission decision, consulted by every discovery path, provisioning, the custody broker and sign-in.
  - Product pack ids are derived from the version.
  - Problems with optional inputs set that item aside: duplicate, dirty, malformed, unknown collision. Only loss of a required product component is fatal.
  - Take managed sources out of the host start path; they are vestigial since R12.
  - Do **not** rewrite `generic_host.py`, build a generic migration framework or loosen validation.
- **Focused checks:** IU-15's hostile-state test; the existing pack suites. Replace `tests/core/pack/test_inventory_review_fix.py:163` only with an assertion of the new rule, never a weaker one.
- **Done:** The hostile-state test passes, and a single admission function is the only place ownership is decided.

### IU-19 Tombstones retired with version pruning

- **Outcome:** Leftovers of older releases that Astrid can recreate are removed aggressively, without ever losing user data or breaking rollback.
- **Route:** X.
- **Dependencies and inputs:** IU-15 and IU-18. Owner direction (12 Nov): be aggressive about cleaning up redundant state; never lose projects, timelines, media, credentials or packs the user wrote.
- **Work:**
  - Keep one list of legacy product state outside `versions/`. Examples:
    - the managed Hivemind registration and checkout;
    - the stale chat command;
    - old pack-host registration and ready files;
    - the R0 workspace the R1 handoff retained, once every project is verified in the new workspace;
    - old version folders beyond the rollback target.
  - Each entry records its preservation rule (user edits and unknown content are kept; git cleanliness is not proof, because ignored files escape the digest) and which retained versions still need it.
  - Remove an entry, registration and files together, when the last version needing it is pruned. Log each removal in install.log, and list pending removals in the diagnostics download.
- **Focused checks:**
  - an update from an R10 fixture removes the legacy Hivemind only after the rollback target no longer needs it;
  - an edited copy is kept;
  - the space freed is reported.
- **Done:** Those checks pass, and an IU-15 fixture shows no unlisted product leftovers.

### IU-20 An update a person can follow

- **Outcome:** Someone watching an update knows what is happening, why it failed, and what state they are left in.
- **Route:** X, across Agent, Runtime and App.
- **Dependencies and inputs:** IU-14. Today:
  - The installer prints only "Installing Astrid." and "Starting Astrid." across about 15 phases, and prints a log path instead of the cause. The rollback receipt drops the cause (`installer/outcome.py:165-168`).
  - The App shows "Couldn't load this timeline" while the Runtime is fenced.
  - The R1-era App shows "Astrid needs repair before it can update" during any update.
  - "Last update result: Recovery needed" stays after a clean rollback.
- **Work:**
  - The installer prints one line per phase, and the failing service's safe cause in plain words, in both the terminal and the receipt. A clean rollback says so plainly, with the next step.
  - Long phases show a small animated indicator when the terminal is interactive: the owner's zigzag line that draws itself and then erases (12 Nov). Never in logs or piped output.
  - The bootstrap's first line stops saying "the first time takes a few minutes" on an update.
  - Internal notes such as "Previous chat command is unavailable…" go to the log only. Building on Agent and App `r13/installer-progress`, for Release 13.
  - The Runtime and App distinguish an update in progress, temporary fencing and abandoned recovery. The App shows one "Astrid is updating" state and holds edits.
  - The diagnostics download includes the service logs.
  - The `timeline_commit_error` name for fenced polls is corrected.
- **Focused checks:** A scripted failing update with an App tab open asserts the terminal lines, the receipt cause, the App states, and the final "back on Release N" state.
- **Done:** Those assertions pass on macOS, Linux and Windows.

### IU-21 Review rule for ownership moves

- **Outcome:** A change that moves who owns something names its old writers, current consumers and rollback needs before it merges.
- **Route:** N.
- **Dependencies and inputs:** IU-15's write-set diff makes the rule mechanical. The incident came from Hivemind moving into core on the R2–R8 line, which merged into the user line at R11 without reconciling R1, R9 and R10 state.
- **Work:** Add the rule to the review and release skills, triggered whenever the write-set diff or the product pack ids change, and always at a release-line merge.
- **Focused checks:** Doc check; the release skill cites the write-set diff.
- **Done:** The rule is in both skills.

### IU-END Scoped review and promotion

- **Outcome:** Review the exact candidate and promote it to `pre-main`.
- **Route:** X
- **Dependencies and inputs:** All IU tasks and their evidence; existing run review/publication authority.
- **Work:** Assess IU-0 matrix coverage and all named limitations, verify candidate identities, then apply only the existing review and promotion rules.
- **Focused checks:** Exact review target and permitted promotion operation recorded by the existing run; no additional suite implied.
- **Done:** Exact candidate review is complete and the authorized promotion to `pre-main` is recorded. Completion does not claim unsupported paths are covered; they remain named limitations.
