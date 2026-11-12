# 09 — Install and update confidence

**Project:** Install and update confidence

**Goal:** Make installing and updating dependable on all three OSes: one update path, and a real hosted test for every install, update, rollback and removal route.

**Status:** queued

**Owner:** Unassigned

**Estimate:** TBD

**Waiting on:** —

**Vision gaps:** [Platform reliability](../../vision/gaps/F-001-platform-reliability.md) (primary).

**Contributing:** [Astrid development skill](../../skills/astrid-dev/SKILL.md).

Make supported install, update, rollback, repair, and uninstall routes dependable on Linux, macOS, and Windows. Qualify them with real hosted evidence and a single update transaction while preserving the previous working version and user data on failure or refusal.

## Goal and scope

- **Included:** one transaction shared by supported update routes; hosted real-path coverage across the three operating systems; real released-R1-to-candidate update with schema migration; Windows locked-file handling; post-R0→R1 uninstall; platform breadth; typed Agent↔Runtime control contract and dead R0-code retirement; captured real service-manager output for unit fakes. See [tasks.md](tasks.md) for the preserved boundaries and task cards.
- **Included, phase 2 (from the 12 Nov Release 1 → 12 incident):** updates stay safe whatever older releases left on the machine.
  - An unblock hotfix (IU-14).
  - An update gate from every published release, lived-in and hostile (IU-15).
  - Sign-in without the legacy copy (IU-16) and one bundled-pack root (IU-17).
  - The invariant that nothing outside the version root is authoritative or fatal (IU-18).
  - Aggressive, rollback-aware cleanup of old leftovers (IU-19).
  - An update a person can follow (IU-20), and a review rule for ownership moves (IU-21).
  - See [Phase 2](#phase-2-upgrade-safe-installed-state).
- **Deferred:** Pinokio install/update routes ([Plan 07](../07-pinokio/plan.md)); pack transactions ([Plan 06, PK-9](../06-packs/tasks.md#pk-9-transactions)); unused Release-2 browser machinery unless reused by a task; broad Agent unit-suite debt.
- **Owner decision:** Windows R0→R1 upgrade may be implemented or refused permanently; its existing low-priority rationale is preserved in IU-7.

## What we build on

Start from Plan 08's verified Release 1 output, including its five-row hosted gate and update step. Freeze current `pre-main` heads for astrid-agent, astrid-runtime, and astrid-app when work starts; the exact heads and donor commits are not recorded here. Plan 01 shares installer files (`cli.py`, `backend.py`) and must be sequenced with IU-1. Historical source observations and the R1 stand-in do not prove current identities or real schema migration; see [inputs.md](inputs.md).

## Sequence

IU-0 freezes source identities and records the path × OS × evidence-mode baseline. IU-1 consolidates the update transaction; IU-2 and IU-3 then cover hosted runtime/rollback legs and real version migration, with IU-4 and IU-9 extending platform evidence. IU-5, IU-6, IU-7, IU-8, and IU-10 follow their indexed dependencies and can proceed independently where the graph permits. IU-END reviews and promotes the exact candidate. Full routes and acceptance are in [tasks.md](tasks.md).

## Phase 2: upgrade-safe installed state

On 12 Nov a Release 1 user's update to Release 12 failed and rolled back. Release 1 had downloaded Hivemind into the user's home folder at sign-in. Release 11 made Hivemind built in, and the duplicate stopped the pack host. Every user who signed in on Release 1, 9 or 10 is affected. The 11-row matrix missed it because it starts from three hand-picked releases with an empty home folder.

Reviews by Astra (with 14 Luna probes) and Fable agreed: this is structural, not a one-off. The category is **incomplete installation-state transitions**: a release moves who owns something without reconciling what older releases left behind, the code that still reads it, and what rollback needs. Two design flaws make it likely:
- ownership is reconstructed separately by each consumer instead of being decided once;
- updates check only the workspace schema, while the product also reads state outside the workspace.

The design keeps the concepts few:
- **One invariant:** Astrid's own code lives only inside the versioned root; anything outside is user data or cache, and never authoritative or fatal.
- **One derived set** of product pack ids.
- **One tombstone list** for legacy product state, retired with version pruning.
- **One gate** that updates from every published release, lived-in and hostile.

IU-14 ships first, in Release 13 (owner, 12 Nov); then the gate (IU-15), before the refactor it protects (IU-18). [Phase 2 evidence](inputs.md#phase-2-upgrade-safe-installed-state).

## Completion

The IU-0 matrix must show a real hosted test for every supported path on every OS, or a named limitation for that cell; IU-END then reviews the exact candidate and promotes it to `pre-main`. Evidence must preserve the old working version and data on failure/refusal. Any unsupported path is recorded as a named limitation. Existing run authority and review limits apply; this plan does not start work or expand publication authority.

## Read next

- [tasks.md](tasks.md): task index, routes, dependencies, acceptance, and progress.
- [inputs.md](inputs.md): repositories, starting identities, predecessor/donor inputs, and evidence limits.
