# Inputs — One update path and release

[Plan](plan.md) · [Tasks](tasks.md)

## Planning evidence

**Scope decision:** Accepted — the owner asked for this project and made the decisions below on 7 Nov 2026, then told the advisor to start it on 8 Nov 2026, with advisor check-ins every two hours ([planning session](https://claude.ai/code/session_011EzfVzreGCJJQnTuXpbib9); recorded under [owner decisions](./inputs.md#owner-decisions)).

**Prior art:** seven read-only maps of the current state and six task ambiguity reviews, from astrid-dev `dd87b927676ba263707051be7926f245820d12e6`, summarised here; each [task card](./tasks.md) names the code it changes:
- Seven read-only maps of the current state, at App `915bfa84`, Agent `709492fa`, Runtime `61e2c301`, launcher `d15c58b5` and astrid-dev `dd87b92`. The maps covered:
  - the App surfaces;
  - Settings and the decision logic;
  - the Plan 01 consent model;
  - the Runtime identity and update API;
  - installer install types;
  - Pinokio, fully local and source;
  - recorded decisions and docs.
- Key findings:
  - **Update now has never worked on a published install.** The Runtime and Agent disagree on the helper's first action (`reconcile`). No gate pressed the button, because hosted rows update through the CLI.
  - **The App works out install type from about 17 signals,** and has no unknown value.
  - **About 15 Runtime refusals return no reason.**
  - **`pin.mjs` and `release-check.mjs` make the release number count manifest edits.** The check runs only on push, and App `main` is unprotected. Release went from 1 to 9 in one merge, and the tuple changed several times under "Release 1".
  - **Plan 01's SetupBlock is shown on update and repair surfaces,** although its own ruling says existing installs get no choice flags.
  - **Fully-local pages can't use the in-app update,** because update routes are browser-door only.
  - **Docs describe three or four fully-local update paths,** and two of them are unused.

**Approach:** reuse and correct the existing pieces (`identity`, `resolveUpdate`, the status `reason`, `release-check.mjs`, the canary). Don't add new fields, a new resolver, a publish script or new CI rows.

**Challenge:** Reviewed — an independent high-judgment review of the first draft ([planning session](https://claude.ai/code/session_011EzfVzreGCJJQnTuXpbib9)) was accepted almost entirely. It contributed these items:
- **Cuts:** the new status fields, the new resolver, the publish script and new check, and the "main only moves by release" rule.
- **Corrections:**
  - releases 0–9 can never update in-app;
  - the `reconcile` handler exists unmerged;
  - repair is the plain install line, not Update now;
  - fully local needs its own path.
- **Gaps added:** systemd below 254 on Ubuntu 22.04 and Debian 12; the 501 status in Pinokio fully-local preview; bootstrap files as release bytes; downgrade via `--update`.
- **Rejected:** the review's deferrals and its release-number constant. The owner asked for a proper fix with no stopgaps, so the systemd floor, the Pinokio preview status and typed contracts are in scope, and a Runtime capability replaces the "release 9 or earlier" constant.

**Phasing review:** a second independent review checked a 90/10 cut against the code and moved the phase 1 estimate from 6–8 to about 11–13 days. It contributed four findings:
- a hosted button test needs a test-only Runtime seam;
- the capability belongs on update status, not health identity;
- the App can hide the never-working button now without a release-number check;
- three cheap items belong in phase 1: Pinokio fully local status, the Pinokio memory, and fully local Update now.

**Proof and limits:** see [plan.md](plan.md#completion). Existing installs on releases 9 and earlier keep the command path once; the button works only for installs from release 10.

## Owner decisions

From the owner, 7 Nov 2026 (session chat):
- **One path, no duplicates.** Updates follow the same path everywhere.
- **"Astrid on this computer" is status only.** Updates is the one place to act.
- **Pinokio users get only Update in Pinokio.**
- **Each install type sees only its own path.**
- **The primary action is Update now or Update in Pinokio,** with no middle ground. A manual command or agent instructions may remain as a secondary option.
- **Fix issues at their root,** and keep it as simple as possible.
- **The release process is part of this project.** Release 9, currently live, is kept; the next release is 10.

## Decisions recorded 7 Nov 2026

1. **Fully local:** Update now through the existing in-page updater (owner: yes).
2. **Pinokio fresh install:** asks Plan 01's setup questions, as it does today in Pinokio's terminal (owner: should ask). The hosted Pinokio row accepts the recommended choices because it has no terminal.
3. **Review rounds:** at most three before publishing (owner, 7 Nov 2026). Recommended for cross-repository release work, including a protocol never run end to end.
4. **Branch protection on App `main`:** the owner will turn it on later. UR-6's required check is ready before then.
5. **Start and check-ins:** start now, run by a manager under the Manage skill, with advisor check-ins every two hours until this plan's completion PR merges (owner, 8 Nov 2026).
6. **Which checks count:** only checks relevant to this project's scope, narrowly defined, that weren't already failing on the base. A check already red on `main` doesn't block a merge and isn't this project's to fix; full CI health is a separate project. Task work lands on each repository's `int/29-update-and-release` branch; moving the reviewed candidate to `main` follows the Release skill (owner, 8 Nov 2026). App `main` was red on Tests, E2E and Lanes, and Agent `main` on the Windows task-host journey, when this run started.
7. **Release versions:** a release is named `major.minor.patch`, worked out from the release number: patch by default, minor or major only when the owner declares it. Release 10 is `0.0.10`. astrid-dev keeps a log of every release, with its versions, kind, projects and owner go (owner, 8 Nov 2026).
8. **Required is its own decision:** a required update is set per release with a reason, never implied by kind. Kind changes no behaviour for now (owner, 8 Nov 2026).
9. **Source and history:** the log starts at a legacy Release 9 = 0.0.9 (owner, 8 Nov 2026). Superseded the same day: releases are defined and published from astrid-dev, and the App keeps one generated copy. That work moved to [Plan 31](../31-releases-from-astrid-dev/plan.md), with UR-8b–UR-8d, to start after this plan.
10. **Reviews start early:** review round 1 starts while UR-13 is still finishing, on everything already integrated, and is told what's already known so it doesn't re-report it. Round 2 covers the full integrated candidate, including UR-13 (owner, 8 Nov 2026).
11. **Round 1 non-blocking findings run now:** UR-R1.3 to UR-R1.7 run as tasks before round 2, each with a focused test that fails before and passes after: busy shows Update now disabled with no command; a fully local source refusal shows its line; needs-repair shows the plain install line, not `--update`; `pin.mjs --require` floors to the release being published; a later push to `main` never cancels the release guard for an earlier one (Hannah, 8 Nov 2026, via the advisor).
12. **UR-13j in Release 10, cut down:** keep only one shared, attempt-bound check for a finished worker with a non-zero exit. It derives failed or recovery-needed, the status GET reports it read-only, and only the locked POST reconciler and the install-line sweep persist it. It goes into Release 10 only if it is ready when #304, Runtime #36 and #37 merge; otherwise it moves to Plan 30 with the limit recorded (owner, 8 Nov 2026).
13. **Completion amended:** the fully local and Pinokio hosted rows and removing the systemd floor belong to Plan 30, which already owns them. Plan 29 adds two proofs on the release candidate: the release0-to-release1 legs are re-aimed to installed Release 9, then the install command, then the release candidate, with no new CI row; and one fresh row drives Update now with a real browser click in the candidate's hosted App, not a direct POST (owner, 8 Nov 2026).
14. **Release candidate, protection and rollback:** the final run is the release candidate itself, composed exactly as it will be published, and review round 2 runs on the same SHAs. The owner turns on branch protection later; until then Release 10 still goes to `main` through a PR that `release-guard` checks. Rollback is roll-forward only: a Release 11 may re-pin the Release 9 tuple, which has the same schema digest (owner, 8 Nov 2026).
15. **Go for Release 10:** publish to `main` once the release candidate's three fresh rows, UR-13m and UR-13n pass with their receipts and review round 2 leaves no blocking finding. The release is the frozen candidate in `run.yaml`, patch and not required, and goes through a PR that `release-guard` checks. Any blocking finding or failing proof stops it, and it comes back to the owner (owner, 8 Nov 2026).
16. **Fix R2.4 before Release 10, defer R2.2, R2.3 and R2.5** (owner, 8 Nov 2026: "YES PLEASE FIX IT"). R2.4 is status polls starting the update helper on every poll on macOS and Windows. R2.6 merges back into `int` at publish, as before.
17. **Patch lane:** a small fix ships as a *patch release* on top of the served tuple: the next integer, shown as a patch version, with change-directed evidence and carried-over evidence for unchanged components, as defined in the [Release skill](../../skills/astrid-dev-release/SKILL.md) (Patch release). Release numbers stay integers; `0.0.N` is how users see them (Plan 31 RL-3). The Release 1 → 12 update fix (Plan 09 IU-14) is folded into Release 13 rather than shipped as a patch, because no one depends on it sooner (owner, 12 Nov 2026).

## Source identities

Record exact base and donor SHAs at task start. Known donor: Agent `b97c43db8` (`reconcile` handler, unmerged).

## References

The maps and the review are working notes from the planning session. Their findings are summarised above, and each task card names the code it changes.

## Reopened decisions 8 Nov 2026 (field failure)

- **Withdrawn:** the completion claim in astrid-dev #137 is withdrawn. The owner's field report showed that `install --update` on a machine that completed the Release 1 storage handoff exits 0 and installs nothing (verified in the review on `advisor/plan29-field-failure-review`).
- **Release 11 (0.0.11, patch) gate:** CI passes with the field state as a fixture and as the re-aimed journey leg; the owner publishes with her go; then she runs the standard App command and uses Update now. If that doesn't end "Astrid updated", the fix goes out forward at once.
- **Pending owner decision:** rollback stays available only until the first successful update after a handoff. Pruning of retained R0 data waits for it.

## Owner decision 17 (9 Nov 2026, Hannah): UX pass before Release 11

One independent UX pass over every install, update, update-failure and repair path, in the App (page and Settings), the installer terminal and the diagnostics file, on mac, Linux and Windows. Rules:
1. Every path offers both "Copy instructions for your agent" and manual steps a person can follow themselves.
2. Every failure is descriptive, says plainly what happened, and points to where the full story is (Download diagnostics, and the install log path), clear to both a human and an agent.
3. Minimal and elegant. Never dump detail on the user; point to it.
4. Never lie. Exit 0 and success copy only when it is true.
5. Fix small things directly, as commits on int via PR. Propose anything big as a task card instead of doing it.

Its fixes ride in the Release 11 candidate. The pass is UR-15j, run after UR-15, UR-15a, UR-15b, UR-15c, UR-15f and the Runtime and App PRs are on int, and before Release 11 is composed.

