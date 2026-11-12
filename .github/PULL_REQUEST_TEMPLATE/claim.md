## Claim an existing project

- **Project:** Link the exact [queued, unassigned project](https://github.com/banodoco/astrid-dev/blob/main/plans/index.md).
- **Owner:** Your own authenticated GitHub `@username`.

Change **only the Owner line** in that project's `plans/<id>/plan.md`, from `**Owner:** Unassigned` to `**Owner:** @username` with your own username. Do not change status, priority, waiting-on, estimate, scope or any other file; the catalog refreshes itself on `main` after merge. Once CI passes, the claim bot merges this PR where it is turned on; otherwise a maintainer does.

Claiming records accountability. It does not authorize code execution, costs, merging other PRs or publication. After claiming, check the plan's scope and waiting-on field; request a start decision when needed. To return non-active work, request a reviewed PR back to `Unassigned`. For active work, first arrange a reviewed pause or handoff; an active project must retain an owner.

[Claiming and next steps](https://github.com/banodoco/astrid-dev/blob/main/docs/contribution-workflow.md#claim-a-project)
