# Contribute to Astrid: claim, propose, review, complete

**Start at [the Astrid development skill](../skills/astrid-dev/SKILL.md).** It gives agents one contributor process. The [domain map](../skills/astrid-dev/references/domains.md) locates source and specialists; this page explains GitHub actions. [Our contribution principles](contribution-design-principles.md) explain what must stay simple.

## Choose a route

| You want to… | Action | Approval boundary |
| --- | --- | --- |
| Fix a bug or small issue | Search/open an [Astrid-dev issue](https://github.com/banodoco/astrid-dev/issues) and submit a focused product PR | Reproduction, actual proof and appropriate product PR review; no project pack |
| Take on an existing project | Claim one `queued` and `Unassigned` project through a PR that changes only the `**Owner:**` line in its `plan.md` | **The claim bot or a maintainer merges the claim.** It gives ownership, not execution authority |
| Propose new substantial work | Open a [project proposal issue](https://github.com/banodoco/astrid-dev/issues/new?template=project-proposal.md), then a reviewed scope PR | Maintainer accepts the new scope and project pack |
| Submit project work | Open product PRs; optionally open an Astrid-dev implementation review PR | An owner’s PR is **queued for review**, not auto-approved |
| Finish a project | Open an Astrid-dev completion PR linking integrated evidence | Independent completion review and authorized merge |

No mandatory project-conversation issue. Questions belong in an issue or PR; update the authoritative project documents only when a decision actually changes.

**Templates have two destinations.** GitHub issue and Astrid-dev PR forms live in [`.github/`](../.github/), where GitHub discovers them. The portable [project scaffolds](../templates/project/) and [product-repository PR examples](../templates/product-pr/) live in `templates/` because GitHub does not automatically use them in another repository. An incident starts with the [Astrid-dev bug issue template](../.github/ISSUE_TEMPLATE/bug.md); its product fix can use the [portable bug PR example](../templates/product-pr/bug.md). No second bug-issue template is kept.

## Write or improve documentation

**Writing uses the same reviewed issue/PR pipeline as code; no new project or evidence form for small edits.** Find the owner of the information before making a second document:

| Writing work | Canonical source and route |
| --- | --- |
| Vision, artistic pillars, creator principles, public copy | [Vision](../vision/README.md). Edit the source files in `vision/`; after merge, CI refreshes their derived overview on `main` and publishes the public JSON feed. Don't copy editorial content into Astrid App |
| Gap statements or gap evidence | Follow [the gap-writing procedure](#define-or-reassess-a-vision-gap). Material changes need a boundary review; evidence-only updates use normal PRs |
| New project scope, plan decisions or task briefs | [Project catalog and pack](project-format.md); new scope uses reviewed project proposals, existing project changes inherit the owner and accepted scope |
| Agent instructions, workflows or contributor docs | [Main skill](../skills/astrid-dev/SKILL.md), stage-specific skills, [run contract](../skills/astrid-dev-shared/run-contract.md), or this guide—each owns its own concern. For adding checks, generated views, or project fields, see [Extending Astrid-dev](extending.md). Documentation CI checks these paths |
| Product API, UI, installer or extension technical docs | The owning [product repository](../skills/astrid-dev/references/domains.md). Submit the documentation PR there and link it to the relevant issue/project |
| Typo, small wording or README improvement | Normal, focused PR. No project, new skill, evidence-pack file or planning ceremony |

Describe the intended correction and relevant source; give a real reviewer a way to verify technical claims. For consequential vision/architecture changes, review the *meaning*, not just Markdown validity. Don't invent a documentation-only state machine or keep copies of old drafts for posterity.

## Define or reassess a vision gap

The [vision overview](../vision/README.md#gaps--16-assessed-outcomes) lists current gaps. Each linked record in [`vision/gaps/`](../vision/gaps/) holds the detailed desired state, observed current state, missing outcome, closure evidence, and sources for reassessment. **A gap names a result that would still matter if today's proposed project were replaced.** Before creating one, compare existing gaps and the [plan catalog](../plans/index.md): reuse or refine an outcome where possible. Do not create a gap for a task, technology choice, or project milestone.

Every gap has **one primary pillar or principle**, with supporting connections only when they explain a distinct relationship. IDs identify records, not ownership. Plans link to the outcomes they address; gaps do not duplicate the project queue, status, or ownership. Assessments are **Open**, **Partially evidenced**, **Closed**, or **Needs recheck**, with dated evidence and limits. Completing a plan does not close a gap automatically.

**Changes to evidence** (current state, assessment, or sources) use a normal reviewed PR. **Creating, retiring, renaming, or materially redefining an outcome** requires one short first-principles record in the PR description—not another document:

```md
## Gap boundary assessment — F-005

Decision: Refine — why this boundary should change
Outcome: missing creator-facing result
Existing alternatives: nearby gaps/projects and why they do not suffice
Why this level: why the result survives a different implementation
Independent closure: real positive and negative proof
Primary connection: principle:local-first-cloud-capable — reason
Supporting connections: principle:in-the-creators-control — reason
Evidence: source URL or exact source SHA
```

Use `Supporting connections: None — reason` when appropriate. [CI checks structure and linkage](../scripts/astrid_dev.py), not philosophical merit or actual proof. A reviewer judges overlap, source claims, chosen relationships, and meaningful independent closure. When evidence changes, reassess honestly; don't fabricate a new approval process.

**Each gap file must include** `Applies to` (one primary and only justified supporting relationships), `Assessment` (with dated evidence), **Desired state**, **Current state**, **Gap**, **Closure evidence**, and **Sources and reassessment**. Project status and ownership live only in each plan's `plan.md`.

**Once plans serve a gap,** add a **Closure approach** and a **Route to closure**. The approach is short prose that lets a new agent understand the strategy. The route is an ordered table mapping every closure-evidence item to the plan that delivers it, or to `unplanned`, with milestones and the critical path. Each routed plan points back with a `Contributes to closure:` line. Start from [the gap template](../templates/gap.md) and follow [the gap skill](../skills/astrid-dev-gap/SKILL.md). CI checks the route's structure and back-links, not its merit; routes carry no statuses.

## Review the strategy

[**Strategy**](../strategy.md) is the short, ordered **release roadmap**. Each [release brief](../releases/TEMPLATE.md) owns the reasoning: a one-line highlight, longer intent, approach/trade-offs and the included plans with one-line reasons. Start a future release from the template and revise it as work evolves; it is not a publication request. On finalization, the **same file** becomes the immutable release ledger entry. Each plan's `plan.md` alone owns its status, owner and estimate, and [priority.md](../plans/priority.md) its priority; vision gaps still own outcomes and closure evidence.

**The strategy has four parts.** Documentation CI checks its shape and that the `Sequence` rows match their release files:
- **Focus now:** short context on the currently qualifying release and concurrent work.
- **Sequence:** one ordered row per release document with columns `Release` (link), `Highlight`, `Plans` (links) and `Why this order`. Its highlight and complete set of linked plans must match the source release document.
- **Not now:** work not yet assigned to a release, without invented commitments.
- **Decisions:** dated owner decisions affecting the release sequence, plus `**Last reviewed:**`.

**When it changes:** creating a release draft or changing its highlight/plans updates the strategy summary in the same PR. A project start/completion may change a release's scope or timing, so review the strategy and release files; the completion PR must touch `strategy.md` (`python3 scripts/astrid_dev.py check`). If the catalog's project information differs, fix the plan's six lines (or [priority.md](../plans/priority.md)); the catalog refreshes itself on `main` after merge. Don't copy status to the release brief. New priorities and scope require the owner's decision; listing work is not authorization to run or publish it.

**Safe publishing boundary:** drafts (including future numbered releases) can land on `main` with no complete pins; documentation CI validates their structure. Plan 31 implements a separate fail-closed owner-approved Draft→Final transition with pinned commits, manifest checks and immutable history. A strategy edit must never publish a release. Keep the overview short; the reasoning is in the release file and linked plan/gap documents.

## Claim a project

1. Find an existing `queued`, `Unassigned` [catalog project](../plans/index.md), read its `plan.md`/`inputs.md`/`tasks.md`, and check blockers.
2. In a clone (fork if needed), open that project's `plans/<id>/plan.md` and change **only its Owner line** from `**Owner:** Unassigned` to `**Owner:** @GitHubUsername`, with your own username. Change nothing else; the catalog refreshes itself on `main` after merge. Open a PR using [the claim template](../.github/PULL_REQUEST_TEMPLATE/claim.md).
3. The claim bot merges the PR once CI passes, where a maintainer has turned it on; otherwise a maintainer merges it. If two people compete, the second claim conflicts on the same Owner line and is not merged.
4. **This is ownership only.** It neither changes status to `active` nor accepts unresolved scope, grants code execution, incurs cost, or permits release. Honor the project’s accepted scope and existing authority/STOP controls.

No extra registration service, OAuth application for contributors or duplicate owner record.

### After claiming: start, pause or hand back

1. Check the project's `Waiting on` field, `inputs.md` planning decision and existing run controls. If the scope is already accepted **and** a specific authorized start is recorded, follow it; do not request the same approval again.
2. If scope is unresolved, open a [scope-review PR](../.github/PULL_REQUEST_TEMPLATE/project-scope.md) against the *existing* project. If the scope is settled but execution authority is missing, ask the maintainer in a [project question](https://github.com/banodoco/astrid-dev/issues/new?template=project-question.md) for an explicit go specifying the task, permitted environment/cost and destination. Record that decision in the existing project/run context and, when authorized, use an ordinary reviewed PR that changes the `**Status:**` line in its `plan.md` to `active`. **Claiming alone never activates work.**
3. If you cannot continue, preserve your work, open PRs and blockers. For a **non-active** project, submit a small reviewed PR changing your own `@handle` to `Unassigned`. For an **active** project, first arrange a reviewed handoff to another owner or a reviewed transition to `paused` alongside release; CI doesn't permit an active project without an owner. None of these are auto-claims. Don't rewrite project history.

No lease timer or separate ownership system. The `**Owner:**` line in each plan's `plan.md` is authoritative, and normal GitHub history records claims and handoffs.

## Propose and greenlight new work

A proposal issue captures the desired independent outcome, relevant existing work and gaps, alternative issue/project placements, and likely proof. Anyone can propose—without claiming the work.

To accept a new independent project, open a **scope PR** with the existing three-file pack: `plan.md` (outcome, scope, interfaces, completion, with `**Status:** queued`), `inputs.md` (prior art, reuse choice, actual owner decision, uncertainty), and `tasks.md` (work and focused proof). Use [the scope template](../.github/PULL_REQUEST_TEMPLATE/project-scope.md) (choose it from the GitHub PR template chooser, or copy its opening lines):

```text
Project: plans/NN-project-name/plan.md
Review request: scope
```

A maintainer compares the plan with existing issues, projects, gaps and source evidence. Their review/merge greenlights **the scope**, not implementation or publishing. Leave unaccepted proposals as an issue/draft PR with a specific next decision; don't manufacture accepted decisions just to satisfy CI.

## Submit work for review

A project can have **multiple PRs across Runtime, Agent, App and other repositories**. Each product PR links the project/task, states exact source/dependency revisions, describes the claim and actual checks, and names what remains unproven. Use the small [review submission](../templates/product-pr/review.md) in a target product repo; the product repo’s own CI, reviewers, branch and release rules remain authoritative.

If the contributor needs an Astrid-dev PR to review a project handoff or implementation evidence, use [the implementation-review template](../.github/PULL_REQUEST_TEMPLATE/implementation-review.md) (select it when creating the PR) and identify the canonical plan:

```text
Project: plans/NN-project-name/plan.md
Review request: implementation
```

**PR intake requires those two exact opening lines** (`Project:` and `Review request:`). The generic GitHub PR template doesn't infer a project or review lane from checkboxes; add those lines explicitly or choose the matching template. Small bug PRs don't need them.

The low-permission [review-intake workflow](../.github/workflows/review-intake.yml) checks the GitHub PR author against the **Owner line in the project's `plan.md` on live `main`**. A matching, non-draft request receives `needs-review` and an acknowledgement. Scope PRs are also queued when they add a new project's three files or change an existing project's `plan.md`. This means **accepted into the review queue**, **not approved**. Reviewers watch the [open queue](https://github.com/banodoco/astrid-dev/pulls?q=is%3Apr+is%3Aopen+label%3Aneeds-review). A label is not a reviewer assignment: a maintainer must take responsibility or request a reviewer through GitHub's normal review UI. This workflow does not run fork code, approve, merge or deploy.

**Independent review:** A fresh qualified reviewer examines actual diff and retained implementation, claims versus tests, first failures, negative cases, route provenance, dependencies and risks. They return concrete blocking findings or a justified acceptance with limitations. The contributor repairs the same failing cases on the new candidate. Human approval remains necessary for consequential changes, security, user data, migrations, costs and deployment under the product repositories’ policies. A CI pass or an agent’s advice alone does not override these authorities.

**Integration:** Freeze the intended target/donor revisions and reuse unchanged proof only where justified. Separate green product PRs do not qualify a combined Runtime/Agent/App installation. The [release skill](../skills/astrid-dev-release/SKILL.md) governs cross-repository integration and separately authorized promotion.

## Record routes as work happens

Name the **route** (`N`, `X` or `S`, see the [run contract](../skills/astrid-dev-shared/run-contract.md)) that ran each piece of work, at the relevant invocation rather than from memory at the end. Name a specific model only where the run used one other than its route's. Model identifiers stay out of repository artifacts.

In an **Astrid-dev checkout**, the [route-use helper](../scripts/model_usage.py) is available:

```sh
python3 scripts/model_usage.py --run-dir plans/<project>/.otto/runs/<id> record \
  --route N --role implementation --task <task-id> [--override <name>]
python3 scripts/model_usage.py --run-dir plans/<project>/.otto/runs/<id> summary
```

The local JSONL stays gitignored under `.otto/`; copy the helper's **Routes used:** line into the review PR. If the route is unknown, use **Unknown — reason**. A manual record is not proof of what actually executed.

## Submit a completed project

Once the required product changes are integrated into their intended destinations and the **combined result** has been qualified, the owner submits one Astrid-dev completion PR using the [completion template](../.github/PULL_REQUEST_TEMPLATE/project-completion.md):

```text
Project: plans/NN-project-name/plan.md
Review request: completion
```

It changes the `**Status:**` line in that project’s `plan.md` to `done` and includes the existing `## Completion assessment — Plan NN`: actual evidence, implementation PRs in every repo, the exact integrated candidate, **Routes used**, what remains unproven and a justified disposition for each linked vision gap (or the enabler exception). This concise PR summary is the **review evidence pack**: link real receipts, do not create another required file.

CI enforces the mechanical completion contract and current references. A reviewer judges actual integrated behavior against the project’s agreed acceptance criteria. A maintainer merges only after required independent review and authorization. Completing the project does **not** automatically close a vision gap or deploy the result.

## Get help and keep decisions discoverable

Ask a project question using the [optional issue template](https://github.com/banodoco/astrid-dev/issues/new?template=project-question.md) (or comment on a relevant PR). Reference the plan ID and tag the owner/maintainer when appropriate. Record durable scope decisions in the project pack, not a new standing conversation hub.

The README and main skill point here, templates link back, and the automated claim/review response gives the next action. **Maintainers:** [safe automation setup and adversarial smoke tests](contribution-automation-setup.md).
