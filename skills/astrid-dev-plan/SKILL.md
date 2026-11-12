---
name: astrid-dev-plan
description: Define independently useful new Astrid project scope by reusing prior art, challenging consequential choices, and recording a verifiable end state.
---

# Plan a new Astrid project

Enter through [astrid-dev](../astrid-dev/SKILL.md) and its [domain map](../astrid-dev/references/domains.md).

## Terms

- **Owner:** the person who chooses a project's outcome and makes its decisions.
- **Planner:** you, an administrator: gather evidence, write the task cards, and send consequential judgment to the advisor. **The advisor** is a standing advisor session if you have one ([Orchestrate](../astrid-dev-orchestrate/SKILL.md), advise path); otherwise spin up a fresh subagent on the high-judgment role, with no stake in your draft. An orchestrator may also plan a project itself before farming it out.
- **Route:** N, X, S or T; the [run contract](../astrid-dev-shared/run-contract.md) alone owns routing, execution state and review policy.
- **Scope** (of a task): the paths, and any shared surface or contract, it may change; a path includes its own tests, wherever they live. Name the functions or classes too (`path:symbol`) when the task changes only part of a file.

## The answer

You produce an agreed, testable end state and tasks another agent can run.

1. **Projects are for new, separately useful outcomes** with their own priority, owner and completion proof. Bugs, small fixes and maintenance normally go in issues; existing project tasks use their accepted plan.
2. **Planning authorizes no execution or release.** Run no product tests and start no work unless asked.
3. **Agree the outcome once.** Record the owner's actual choice with a traceable source; a draft project or PR, or no objection, is not approval. Keep earlier accepted scope; avoid repeated sign-offs.

## Steps

1. **Start from [`strategy.md`](../../strategy.md),** so the project fits the current sequence, then **find prior art** in affected source, issues, [plans](../../plans/index.md), [gaps](../../vision/README.md) and, where relevant, outside approaches. Trace input → actual implementation → user-visible result, noting useful source revisions, reuse, negative findings and uncertainties. Delegate bounded research when helpful, but no broad audit without a decision it could change.
2. **Pick the smallest complete result.** Compare reusing or extending a pack, adding one, changing core and, when relevant, doing less or nothing. Prefer an existing plan or gap to a new entry. Justify placement and tradeoffs from evidence, not architectural preference. When the gap has a route to closure, place the plan in it with the [Gap](../astrid-dev-gap/SKILL.md) skill, and add the plan's `Contributes to closure:` line.
3. **Challenge in proportion to consequence.** For material architecture, an expensive or hard-to-reverse decision, or a table case below, an independent critique is **required before you seek greenlight**: have the advisor critique the written plan and tasks for real removals, consolidation and reuse, checking your claims against the code, not against your summary. Record its findings and what you accepted, rejected or left to the owner. A simple bounded project needs only a concise alternatives review and a reason to skip the critique.
4. **Agree the outcome.** Present the real options (as many as the owner needs; ten is a useful technique, not a quota), their user-facing tradeoffs and a testable end state. When the change is complex, or the owner has to picture it to decide, [offer ten vivid statements](#ten-vivid-statements).
5. **Write a compact handoff,** one home per fact: [`inputs.md`](../../templates/project/inputs.md) for source evidence, alternatives, challenge decision, approval and uncertainty; [`plan.md`](../../templates/project/plan.md) for outcome, scope, sequence and completion; [`tasks.md`](../../templates/project/tasks.md) for assignments and focused proof ([rules below](#write-the-task-list)). **The three templates are the one definition of each file's sections and fields:** copy their headings exactly, and do not take the shape from another plan, this skill or any other document. A PR that adds a new pack is checked against them; an existing pack, renamed or not, is never checked. Link detailed work only for a distinct use.
6. **Seek greenlight.** A contributor may [open a proposal issue](../../docs/contribution-workflow.md#propose-and-greenlight-new-work) without permission. A maintainer-reviewed **scope PR** greenlights new scope by recording the owner's actual decision in `inputs.md` and adding the plan with `**Status:** queued`. Leave a new plan out of [`plans/priority.md`](../../plans/priority.md): an unlisted plan comes after the listed ones, and the catalog refreshes itself on `main` after merge. A line there only moves a plan above others; the owner or the orchestrator adds it, and you may recommend it in `inputs.md`.

## Ten vivid statements

A long plan hides its biggest decisions. When the work is meaningfully complex (a hard fix, a change to how people work, several decisions the owner must make), ask the owner whether they want about ten statements before they read the plan, and write them if they do. Skip the offer for a simple, bounded project.

- **What they are for:** the owner scans them in a minute, sees the anchor decisions and the edges of the change, and can say "no, not that" before any task is written.
- **Each statement is one sentence about what changes,** phrased boldly enough to disagree with. Contrast works well: "Now, the list defines the plans. After, the plans define the list."
- **Cover the edges, not only the benefits:** what stops being possible, who has to change a habit, what is deliberately left out, and the choice most likely to be controversial.
- **Every statement must be true of the plan as written.** If one overstates it, change the statement or change the plan. Do not write a slogan the tasks don't deliver.
- **Record the owner's reaction** to each contested statement as a decision in `inputs.md`, and revise the plan before seeking greenlight.

Ten is a guide: use fewer when there are fewer real anchors.

## Scale the method

Each step below earns its cost only under its condition; skip it otherwise. Each produces a file the next step reads.

| Step | Do it when |
|---|---|
| Map current behaviour with parallel N helpers, one read-only area each | the behaviour spans several repositories or areas, or no one planning knows it |
| List each problem with its root cause and where it is fixed | the request starts from symptoms (bugs, confusing UI) rather than a new capability |
| Consult the advisor as the critic (required in these cases), briefed to build as little as possible and to verify claims in code | the plan touches a cross-repository contract, a user-visible flow, release, security or data, changes astrid-dev's own checks, bots or workflows, or exceeds about five days |
| Phase it: a first phase with most of the value, later phases committed, estimates per phase | the estimate exceeds about ten days or value is uneven across tasks |
| Ambiguity pass by N helpers per task group, resolving from code and listing only real owner decisions | other agents will execute the tasks, or any task is X, S or T |
| Record owner decisions in `inputs.md` and enforce them with a test | a later merge could silently undo the decision |

## Write the task list

In the [tasks template](../../templates/project/tasks.md), every task has a scope and:

- **A route:** N by default, X for coupled or non-obvious changes, S where correctness needs the deepest reasoning (a protocol never run end to end, security, data safety, migration), and T for taste: small, editorial refinement that needs a high level of polish, such as user-facing copy, refusal and error messages, naming, a screen's layout or a skill's voice. A T task refines something that exists against a stated intent; it is not creative and adds no scope. Split taste out of larger tasks, so the functional change is N, X or S and the wording or polish is its own small T task ([run contract](../astrid-dev-shared/run-contract.md#routing-and-bindings)).
- **Dependencies,** only where one task needs another's result, or both change the same function, class or contract. Sharing a file is not a dependency: tasks that change different functions in one file run in parallel, with a merge order. The same applies across other active projects. If a shared surface needs one model first, consult the advisor.
- **The critical path:** state it in `tasks.md`, and keep it as short as the work allows. Chain tasks only where the rule above requires it.
- **Before implementation:** its actual base and donor revisions, exact focused checks and authority.
- **Tests only at load-bearing moments,** per the [run contract's table](../astrid-dev-shared/run-contract.md#when-a-test-run-is-load-bearing): before the first task, after each task (its own proof only), before others build on a shared part, and once before review.
- **A test inventory and focused proofs.** `tasks.md` names the existing tests the plan affects (its test inventory) and, for each task, the exact test files that prove it. The manager's local baseline runs only these. The full suite runs on CI once per review, not per task.
- **A contract card lists what it makes untrue.** A card that changes a contract, a check's trigger or a message names every existing pinned test, fixture and oracle line the change invalidates, and says how each may change. A card whose proof is a `grep` or a list of pinned tests says "re-check against the code at dispatch", because an earlier card may have moved what it names.
- **Checks a cloud worker can run.** Setup and checks use astrid-dev's [shared worker environment](../../env/README.md), called by literal path. They must work in a session with only the task's repository attached:
  - other repositories come from public git at pinned commits;
  - no GitHub archive downloads;
  - no private repositories;
  - small fixtures go inline in the task card.

  Add a missing script there, not in the plan folder.

**Suggest reviews only where they earn their cost.** State your recommendation in every plan, including when it is none; don't wait to be asked.

- **A simple, bounded project needs no review rounds:** ordinary PR review is enough, so leave the review row out. For meaningful complexity, recommend one round at the end, before any publishing task, which depends on it. Recommend more only as the [run contract](../astrid-dev-shared/run-contract.md#review-and-promotion-boundaries)'s guide says, say why, and record the recommendation and the owner's agreed number on the `Review rounds` line in `inputs.md`.
- **Add a review stop after a load-bearing part** of a significant project: a contract, data model, protocol, security boundary or shared interface that later tasks build on, where a mistake found only at the end would mean redoing those tasks or would reach users. Put it right after that part, as its own row (`RS<n>`, named for what it reviews), with the later tasks that build on it depending on it. It uses the same protocol as the final review: rounds at most _n_, findings as task cards, done before the stop clears. Use it sparingly, typically only on larger projects (above about five days, or cross-repository) and at most one or two per plan. Each stop needs a stated reason: which later tasks it protects and what a late finding would cost. Record each stop and its agreed rounds in `inputs.md`, alongside the final review.

## Readiness

- A draft can mark what is **Pending**, with the next action.
- A defined project needs real prior-art findings, an explained reuse decision, a traceable owner choice and meaningful completion evidence; a consequential design also needs critique or an explicit unresolved blocker.
- Don't make the agent fabricate evidence, or add heavy ritual to a simple decision.
