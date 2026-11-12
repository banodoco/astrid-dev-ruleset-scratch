# Tasks — <project name>

[Plan](plan.md) · [Inputs](inputs.md)

A draft can use a short outline with unknowns. Before dispatch, every task needs one bounded outcome, its input and deliverable, dependencies, a suitable route, and focused proof. Name source identity where one task consumes another project's output. Reuse the prior-art and source identities in [inputs.md](inputs.md); don't repeat them.

**Task ids:** one short prefix for the project and a number (`AB-1`, `AB-2`, …). **Critical path:** the ordered ids that bound the finish. **Test inventory:** the existing test files this plan affects.

| Task / outcome | Route | Depends on | Scope | Focused proof | Progress |
| --- | --- | --- | --- | --- | --- |
| | | | | | |
| RS1 Review stop after _load-bearing part_ (optional: only where a late finding would redo later tasks or reach users; remove if unused; rounds at most _n_) | S | the load-bearing tasks | read-only | Same protocol as R, on that part's integrated result; findings become rows `RS1.<n>`; the tasks built on it depend on this row | [ ] |
| R Review rounds (at most _n_, agreed with the owner; remove this row if _n_ is 0, as for a simple, bounded project) | S | all other tasks | read-only | Rounds per the [run contract](../../skills/astrid-dev-shared/run-contract.md): findings become rows `R<round>.<n>` added directly below this one, each with route, scope, dependencies and proof; publishing or closing waits for them | [ ] |

Add task details beneath the index only when useful. Scope names the paths, and any shared surface or contract, the task may change (a path includes its own tests, wherever they live); tasks with overlapping scopes need a dependency. X and S tasks delegate research, reading, mechanical edits and checks to N helpers. Use N by default and X/S only where warranted by [the run contract](../../skills/astrid-dev-shared/run-contract.md). A check must name the actual behavior it demonstrates and its inputs; do not invent broad suites, duplicate task ledgers or extra approvals.
