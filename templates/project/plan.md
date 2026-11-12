# <Project name>

**Project:** The project's name as the catalog and the public vision page show it.

**Goal:** One sentence on what creators get when this is done.

**Status:** `queued`, `active`, `blocked`, `paused`, `done` or `cancelled`.

**Owner:** Who is accountable now; `Unassigned` until someone claims it.

**Estimate:** Engineering days left, or `TBD`.

**Waiting on:** What the project waits for, or `—`.

**Start:** [Astrid contributor skill](../../skills/astrid-dev/SKILL.md) and [domain map](../../skills/astrid-dev/references/domains.md). The six lines above are this project's row in the [catalog](../../plans/index.md): change them here, one line each; the catalog refreshes itself on `main` after merge, so you need not commit it. Its priority is its place in [priority.md](../../plans/priority.md); a plan not listed there comes after the listed ones.

**Vision gaps:** Link the relevant [existing gap](../../vision/README.md), with its primary and truly useful supporting relationships, or state **Vision role: Foundational enabler** with a reason. A small bug or maintenance fix belongs in an issue.

**Contributes to closure:** When a gap's Route to closure names this plan, state the gap ID and the closure-evidence items this plan delivers, for example `F-008: every default slot runs live on RunPod`. Otherwise omit this line.

## Outcome and scope

What independently useful change should creators experience? State the included work, the boundaries and what is deferred.

## Existing work and decision

What do we retain or build on, and why is this the smallest sound approach? Summarize and link the actual source findings, alternatives, challenge (where warranted) and owner choice in [inputs.md](inputs.md#planning-evidence). Do not claim a draft is accepted.

## Sequence and readiness

Describe the shortest path, real dependencies, source/environment or budget constraints and unresolved decisions. Link task details to [tasks.md](tasks.md); recording a plan does not authorize implementation.

## Interfaces and handoff

What existing output or contract does this project **consume**, and how will its exact version be identified? What artifact or observable behavior will it **produce** that another agent can safely build on? Name any unresolved compatibility or provenance limits. Link relevant product PRs and the final integrated completion PR when available. That PR's concise [review evidence](../../docs/contribution-workflow.md#submit-a-completed-project) should point to the exact tested revisions and results, without duplicating the evidence here.

## Completion

What observable result, evidence and negative case would show the chosen outcome works? State the limits of that proof and the relevant integration/release boundary without presuming authority.
