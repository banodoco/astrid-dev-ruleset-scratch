"""Contract for the lifecycle declaration and its consumers."""
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import check_completion
import check_docs
import checks
import lifecycle
import records
import views


ROOT = Path(__file__).resolve().parent.parent
NAMES = ("queued", "active", "blocked", "paused", "done", "cancelled")
PHRASE = "queued, active, blocked, paused, done or cancelled"
SENTENCE = ("`queued` = planned, not started; `active` = explicitly started; "
            "`blocked` = known impediment; `paused` = deliberately stopped; "
            "`done` = accepted completion evidence; `cancelled` = intentionally abandoned, "
            "with reason in the plan.")
EXTRA = lifecycle.Status("reviewing", True, "under review", ("named-owner", "completion-assessment"))


def write_plan(root, folder, status, owner="Ada"):
    path = root / "plans" / folder / "plan.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"**Project:** {folder}\n**Goal:** goal\n**Status:** {status}\n"
                    f"**Owner:** {owner}\n**Estimate:** TBD\n**Waiting on:** —\n", encoding="utf-8")


def route(word):
    return ("## Closure approach\nApproach.\n## Route to closure\n"
            "| Step | Detail |\n| --- | --- |\n" f"| Work | {word} |\n")


def status_view(test):
    matches = [view for view in views.VIEWS if view.name == "status-definitions"]
    test.assertEqual(len(matches), 1, "status-definitions must be registered once")
    return matches[0]


class DeclarationTests(unittest.TestCase):
    def test_declaration_records(self):
        self.assertEqual([(s.name, s.terminal, s.meaning, s.needs) for s in lifecycle.STATUSES], [
            ("queued", False, "planned, not started", ()),
            ("active", False, "explicitly started", ("named-owner",)),
            ("blocked", False, "known impediment", ()),
            ("paused", False, "deliberately stopped", ()),
            ("done", True, "accepted completion evidence", ("completion-assessment",)),
            ("cancelled", True, "intentionally abandoned, with reason in the plan", ()),
        ])

    def test_names(self):
        self.assertEqual(list(lifecycle.names()), list(NAMES))

    def test_terminal(self):
        self.assertEqual(set(lifecycle.terminal()), {"done", "cancelled"})

    def test_phrase(self):
        self.assertEqual(lifecycle.phrase(), PHRASE)

    def test_route_pattern(self):
        pattern = lifecycle.route_pattern()
        for name in NAMES:
            with self.subTest(name=name):
                match = re.search(pattern, name.upper())
                self.assertIsNotNone(match)
                self.assertEqual(match.group(1), name.upper())
                self.assertIsNone(re.search(pattern, "x" + name + "x"))

    def test_requiring(self):
        self.assertEqual(set(lifecycle.requiring("named-owner")), {"active"})
        self.assertEqual(set(lifecycle.requiring("completion-assessment")), {"done"})
        with self.assertRaises(ValueError):
            lifecycle.requiring("unknown")

    def test_requiring_rejects_unknown_needs(self):
        for need in ("named-owner", "completion-assessment"):
            with self.subTest(need=need):
                self.assertIsInstance(lifecycle.requiring(need), tuple)
        with self.assertRaisesRegex(ValueError, r"known needs: named-owner, completion-assessment"):
            lifecycle.requiring("completion-assesment")

    def test_definitions(self):
        self.assertEqual(lifecycle.definitions(), SENTENCE)

    def test_template_lists_every_declared_status(self):
        text = (ROOT / "templates/project/plan.md").read_text(encoding="utf-8")
        line = next(line for line in text.splitlines() if line.startswith("**Status:**"))
        for status in lifecycle.STATUSES:
            with self.subTest(status=status.name):
                self.assertIn(f"`{status.name}`", line)


class ExistingReaderTests(unittest.TestCase):
    def test_catalog_and_projects_current_statuses_and_invalid_message(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for i, name in enumerate(NAMES, 1):
                write_plan(root, f"{i:02}-item", name)
            self.assertEqual(checks._catalog(checks.Context(root)), [])
            self.assertEqual([row[2] for row in records.projects(root)], list(NAMES))
            write_plan(root, "07-invalid", "maybe")
            message = f"plans/07-invalid/plan.md: invalid status 'maybe'; use {PHRASE}"
            self.assertEqual(checks._catalog(checks.Context(root)), [message])
            with self.assertRaises(ValueError) as error:
                records.projects(root)
            self.assertEqual(str(error.exception), message)

    def test_route_words_current_message(self):
        for name in NAMES:
            with self.subTest(name=name):
                self.assertEqual(check_docs.route_issues("gap.md", "F-001", route(name), {}),
                                 [f"gap.md: route row carries status/ownership word '{name}'; the catalog owns it"])
        self.assertEqual(check_docs.route_issues("gap.md", "F-001", route("work"), {}), [])

    def test_owner_current_message(self):
        rows = [[name, "goal", name, "Unassigned"] for name in NAMES]
        self.assertEqual(check_docs.unnamed_active_owners(rows),
                         ["active project needs a named accountable owner: active"])

    def test_completion_current_transitions(self):
        before = {"same": "done", "reopened": "done", "moving": "active"}
        after = {"same": "done", "reopened": "active", "moving": "done", "new": "done"}
        self.assertEqual(check_completion.transitions_to_done(before, after),
                         ["moving/plan.md", "new/plan.md"])


class PatchedDeclarationTests(unittest.TestCase):
    def setUp(self):
        patcher = patch.object(lifecycle, "STATUSES", lifecycle.STATUSES + (EXTRA,))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_accessors_follow_new_record(self):
        cases = (
            ("names", lambda: list(lifecycle.names()), list(NAMES) + ["reviewing"]),
            ("terminal", lambda: set(lifecycle.terminal()), {"done", "cancelled", "reviewing"}),
            ("phrase", lifecycle.phrase, "queued, active, blocked, paused, done, cancelled or reviewing"),
            ("named-owner", lambda: set(lifecycle.requiring("named-owner")), {"active", "reviewing"}),
            ("completion-assessment", lambda: set(lifecycle.requiring("completion-assessment")), {"done", "reviewing"}),
            ("route", lambda: bool(re.search(lifecycle.route_pattern(), "REVIEWING")), True),
            ("definitions", lifecycle.definitions, SENTENCE[:-1] + "; `reviewing` = under review."),
        )
        for label, read, expected in cases:
            with self.subTest(accessor=label):
                self.assertEqual(read(), expected)

    def test_catalog_accepts_new_status(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_plan(root, "01-item", "reviewing")
            self.assertEqual(checks._catalog(checks.Context(root)), [])

    def test_catalog_names_new_status_in_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_plan(root, "01-item", "maybe")
            self.assertEqual(checks._catalog(checks.Context(root)), [
                "plans/01-item/plan.md: invalid status 'maybe'; use queued, active, blocked, paused, done, cancelled or reviewing"])

    def test_projects_accepts_and_orders_new_terminal_status(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_plan(root, "01-terminal", "reviewing")
            write_plan(root, "02-open", "queued")
            self.assertEqual([row[2] for row in records.projects(root)], ["queued", "reviewing"])

    def test_projects_orders_new_open_status_before_terminal(self):
        open_status = lifecycle.Status("reviewing", False, "under review")
        with patch.object(lifecycle, "STATUSES", lifecycle.STATUSES[:-1] + (open_status,)):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                write_plan(root, "01-terminal", "done")
                write_plan(root, "02-open", "reviewing")
                self.assertEqual([row[2] for row in records.projects(root)], ["reviewing", "done"])

    def test_projects_names_new_status_in_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_plan(root, "01-item", "maybe")
            with self.assertRaises(ValueError) as error:
                records.projects(root)
            self.assertEqual(str(error.exception), "plans/01-item/plan.md: invalid status 'maybe'; use "
                             "queued, active, blocked, paused, done, cancelled or reviewing")

    def test_route_finds_new_status(self):
        self.assertEqual(check_docs.route_issues("gap.md", "F-001", route("reviewing"), {}),
                         ["gap.md: route row carries status/ownership word 'reviewing'; the catalog owns it"])

    def test_owner_requirement_applies_to_new_status(self):
        self.assertEqual(check_docs.unnamed_active_owners([["item", "goal", "reviewing", "Unassigned"]]),
                         ["active project needs a named accountable owner: item"])

    def test_completion_requirement_applies_to_new_status(self):
        self.assertEqual(check_completion.transitions_to_done(
            {"same": "reviewing", "moving": "active"}, {"same": "reviewing", "moving": "reviewing"}),
            ["moving/plan.md"])


class StatusViewTests(unittest.TestCase):
    def test_registration(self):
        view = status_view(self)
        self.assertEqual(view.sources, ("scripts/lifecycle.py",))
        self.assertEqual(view.target, "plans/index.md")
        self.assertEqual(view.region, "status-definitions")

    def test_region_render_and_hand_edit(self):
        view = status_view(self)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / view.target
            path.parent.mkdir(parents=True)
            path.write_text("Before\n<!-- status-definitions:start -->\nold\n"
                            "<!-- status-definitions:end -->\nAfter\n", encoding="utf-8")
            rendered = views.expected(view, root)
            region = rendered.split("<!-- status-definitions:start -->", 1)[1].split("<!-- status-definitions:end -->", 1)[0]
            self.assertIn(lifecycle.definitions(), region)
            path.write_text(rendered.replace("Before", "Edited outside"), encoding="utf-8")
            self.assertEqual(views.check_view(view, root), [])
            path.write_text(path.read_text(encoding="utf-8").replace(lifecycle.definitions(), "hand edit"), encoding="utf-8")
            self.assertEqual(views.check_view(view, root), [
                "view status-definitions: the generated part of plans/index.md does not match its sources; "
                "edit scripts/lifecycle.py instead and undo your change to that part; it refreshes itself on main after merge"])

    def test_missing_markers_uses_existing_error(self):
        view = status_view(self)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / view.target
            path.parent.mkdir(parents=True)
            path.write_text("No markers\n", encoding="utf-8")
            self.assertEqual(views.check_view(view, root), [
                "view status-definitions: cannot check plans/index.md: target must contain exactly one <!-- status-definitions:start --> line and one <!-- status-definitions:end --> line; "
                "restore them in plans/index.md; then run python3 scripts/astrid_dev.py sync"])


if __name__ == "__main__":
    unittest.main()
