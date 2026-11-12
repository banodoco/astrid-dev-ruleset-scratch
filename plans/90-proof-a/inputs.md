# Inputs — <project name>

[Plan](plan.md) · [Tasks](tasks.md)

## Planning evidence

A compact record for a **new project's** decision. Bugs and small fixes use their issue/PR evidence instead. The [planning skill](../../skills/astrid-dev-plan/SKILL.md) describes when a deeper independent review is worthwhile. For a draft, use **Pending — why. Next: action**; do not invent a source or approval.

**Scope decision:** Pending — The owner has not selected an end state. Next: present meaningful alternatives and record the actual decision.

**Prior art:** Pending — Relevant implementations and prior plans have not been inspected. Next: trace current behavior and record source links/revisions, reuse opportunities and meaningful negative findings.

**Approach:** Pending — Reuse, an existing pack, a new pack, a core change or doing less has not been selected. Next: compare alternatives and identify the smallest complete approach.

**Challenge:** Pending — The consequence and architectural risk are not yet clear. Next: obtain an independent simplification critique if warranted, or explain why a separate review would add little.

**Proof and limits:** Pending — Acceptance evidence and supported contexts are not yet known. Next: specify observable results, meaningful failure cases and unresolved assumptions.

**Review rounds:** Pending — None for a simple, bounded project; otherwise recommend a number and say why ([guide](../../skills/astrid-dev-shared/run-contract.md#review-and-promotion-boundaries)). Next: the owner confirms.

**Run start:** Pending — No run is authorized. Next: when the owner starts a run, record the date, the phase or tasks it covers, the accountable session ([who that is](../../skills/astrid-dev-shared/run-contract.md#who-answers-for-a-run)), what it may do without asking, what still needs the owner's go, and the advisor session if there is one.

## Owner decisions

Number each decision the owner must make (`D1`, `D2`, …) with the options and your recommendation; when decided, add the date and the choice. If there are none, write `None` and keep the heading.

## Source identities

Before code work, record the actual repository/ref/SHA, retained changes, base versus donors, and intended integration destination. Never guess or confuse historical snapshots with the current source.

## References

Link supporting research, reviewer notes or the owner's decision when readers need the detail. Keep credentials, private logs and machine-specific data out of this pack.
