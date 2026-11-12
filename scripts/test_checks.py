"""Contract and legacy-rule coverage for the check command."""
import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import astrid_dev
import checks
import golden
from test_check_completion import PLAN
from test_check_gap_boundaries import ORIGINAL
from test_check_project_planning import DRAFT


def invoke(args, **kwargs):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = astrid_dev.main(args, **kwargs)
    return code, output.getvalue()


class ContractTests(unittest.TestCase):
    def test_check_selection_messages_and_context(self):
        calls = []
        def run(name, messages):
            def check(context):
                calls.append((name, context))
                return messages
            return check
        entries = [checks.Check("a", "always", "First check", run("a", ["old message", "second"])),
                   checks.Check("b", "pr", "PR check", run("b", ["PR message"])),
                   checks.Check("c", "always", "Last check", run("c", []))]
        root = Path("/fixture")
        code, output = invoke(["check"], root=root, registry=entries)
        self.assertEqual((code, output), (1, "ERROR a: old message\nERROR a: second\n"))
        self.assertEqual([name for name, _ in calls], ["a", "c"])
        for option in ("--body-file", "--event"):
            calls.clear()
            code, output = invoke(["check", "--base", "abc", option, "input"], root=root, registry=entries)
            self.assertEqual(code, 1)
            self.assertEqual(output, "ERROR a: old message\nERROR a: second\nERROR b: PR message\n")
            self.assertEqual([name for name, _ in calls], ["a", "b", "c"])
            self.assertEqual(calls[1][1].root, root)
            self.assertEqual(calls[1][1].base, "abc")
            self.assertEqual(getattr(calls[1][1], "body_file" if option == "--body-file" else "event"), Path("input"))

    def test_success_list_and_invalid_arguments(self):
        entries = [checks.Check("one", "always", "A check", lambda _: []),
                   checks.Check("two", "pr", "Another check", lambda _: [])]
        self.assertEqual(invoke(["list"], registry=entries), (0, "one always A check\ntwo pr Another check\n"))
        self.assertEqual(invoke(["check"], registry=entries), (0, ""))
        for args in (["check", "--base", "abc"], ["check", "--event", "e"],
                     ["check", "--base", "abc", "--event", "e", "--body-file", "b"]):
            with self.subTest(args=args), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exc:
                invoke(args, registry=entries)
            self.assertEqual(exc.exception.code, 2)

    def test_definition_validation(self):
        for args in (("", "always", "description", lambda _: []),
                     ("id", "other", "description", lambda _: []),
                     ("id", "pr", "two\nlines", lambda _: []),
                     ("id", "pr", "description", None)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                checks.Check(*args)


class RegisteredRuleTests(unittest.TestCase):
    def test_generated_views_is_a_pr_check(self):
        entry = next(entry for entry in checks.REGISTRY if entry.id == "generated-views")
        self.assertEqual(entry.trigger, "pr")

    # Inventory covered by the golden fixture comparisons: catalog parsing and
    # order, owners and paths; release/strategy; gaps, routes and backlinks;
    # project files; subjects; obsolete paths, ledger, links; public vision.
    # The PR fixture covers completion and strategy, boundary, and planning.
    # IDs and prose are intentionally editorial; reported IDs must be listed.
    def test_all_golden_fixture_errors_are_discoverable_and_unchanged(self):
        # The frozen oracle inventories documentation and public-vision rule verdicts.
        for overlay_path in sorted(golden.FIXTURES.glob("*/overlay.json")):
            with self.subTest(fixture=overlay_path.parent.name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "repo"
                golden._copy_tree(root)
                for relative, contents in json.loads(overlay_path.read_text()).items():
                    target = root / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(contents, encoding="utf-8")
                expected = golden._errors(root)
                code, output = invoke(["check"], root=root)
                messages = [line.split(": ", 1)[1] for line in output.splitlines() if line.startswith("ERROR ")]
                _, listing = invoke(["list"], root=root)
                listed = {line.split()[0] for line in listing.splitlines()}
                for line in output.splitlines():
                    if line.startswith("ERROR "):
                        self.assertIn(line[6:].split(": ", 1)[0], listed)
                self.assertEqual(sorted(messages), sorted(expected))
                self.assertEqual(code, bool(expected))

    def test_pr_rules_and_uncommitted_planning_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            golden._copy_tree(root)
            def git(*args):
                return subprocess.check_output(["git", *args], cwd=root, text=True).strip()
            git("init", "-q")
            git("config", "user.name", "Test")
            git("config", "user.email", "test@example.com")
            project = root / "plans/20-zero-to-first-image"
            project.mkdir(parents=True, exist_ok=True)
            from test_records import ProjectRecordTests as Records
            active = Records.plan(Project="First image", Status="active") + PLAN.split("\n\n", 1)[1]
            (project / "plan.md").write_text(active)
            (project / "inputs.md").write_text(DRAFT)
            (root / "plans/index.md").write_text("| Project | Goal | Status | Owner | Estimate | Waiting on | Plan |\n"
                "|---|---|---|---|---:|---|---|\n"
                "| First image | Build a flow | active | Owner | TBD | — | [Plan 20](20-zero-to-first-image/plan.md) |\n")
            gap = root / "vision/gaps/F-005-local-files-cloud-assist.md"
            gap.parent.mkdir(parents=True, exist_ok=True)
            gap_text = ORIGINAL.replace("[Local-first](../principles/local-first-cloud-capable.md)", "[Local-first](../principles/local-first-cloud-capable.md) (primary)")
            gap.write_text(gap_text)
            git("add", ".")
            git("commit", "-qm", "base")
            base = git("rev-parse", "HEAD")
            body = root / "body.txt"
            body.write_text("")
            # All three rules must inspect current content, including unstaged edits.
            (project / "plan.md").write_text(active.replace("**Status:** active", "**Status:** done"))
            gap_text = gap_text.replace("An outcome is not yet available", "A changed outcome")
            gap.write_text(gap_text)
            (project / "inputs.md").write_text(DRAFT.replace("**Approach:**", "**Missing approach:**"))
            code, output = invoke(["check", "--base", base, "--body-file", str(body)], root=root)
            for expected in ("Plan 20: missing '## Completion assessment", "F-005: missing '## Gap boundary assessment", "20-zero-to-first-image: missing 'Approach' planning evidence"):
                with self.subTest(expected=expected):
                    self.assertEqual(code, 1, output)
                    self.assertIn(expected, output)
            malformed = ORIGINAL.replace("An outcome is not yet available", "A changed outcome")
            gap.write_text(malformed)
            code, output = invoke(["check", "--base", base, "--body-file", str(body)], root=root)
            self.assertEqual(code, 1, output)
            self.assertRegex(output, r"ERROR [^:]+: gap boundary gate: invalid gap relationship or role:")


class ProjectCatalogContractTests(unittest.TestCase):
    def errors(self, root, rule):
        entry = next(entry for entry in checks.REGISTRY if entry.id == rule)
        self.assertEqual(entry.trigger, "always")
        return entry.run(checks.Context(root))

    def test_synthetic_fixture_essential_errors(self):
        expected = {
            "bad-status": ("plan-catalog", ("plans/99-fixture/plan.md: invalid status 'maybe'",)),
            "unnamed-active-owner": ("catalog-paths", ("active project needs a named accountable owner: Synthetic fixture",)),
            "missing-project-field": ("plan-catalog", ("plans/99-fixture/plan.md:", "Status", "missing")),
            "duplicate-project-field": ("plan-catalog", ("plans/99-fixture/plan.md:", "Status", "duplicat")),
            "priority-unknown-id": ("plan-catalog", ("plans/priority.md", "98-no-such-folder")),
        }
        for name, (rule, fragments) in expected.items():
            with self.subTest(fixture=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory) / "repo"
                golden._copy_tree(root)
                overlay = json.loads((golden.FIXTURES / name / "overlay.json").read_text(encoding="utf-8"))
                self.assertIn("plans/99-fixture/plan.md", overlay)
                self.assertFalse(any(path.startswith("plans/") and path.endswith("/plan.md")
                                     and path != "plans/99-fixture/plan.md" for path in overlay))
                for relative, text in overlay.items():
                    target = root / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(text, encoding="utf-8")
                errors = self.errors(root, rule)
                self.assertTrue(any(all(part in line for part in fragments) for line in errors), errors)

    def test_catalog_aggregates_bad_folder_fields_and_priority_errors(self):
        from test_records import ProjectRecordTests as Records
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            Records.write(root, "bad-folder", Records.plan())
            Records.write(root, "01-alpha", Records.plan().replace("**Goal:** Build **one** thing\n", ""))
            Records.write(root, "02-beta", Records.plan(Status="maybe"))
            (root / "plans/priority.md").write_text(
                "## Order\n- 02-beta\n- 02-beta\n- 98-unknown\n", encoding="utf-8")
            errors = self.errors(root, "plan-catalog")
            self.assertEqual(len(errors), 5, errors)
            for fragments in (("bad-folder",), ("plans/01-alpha/plan.md:", "Goal", "missing"),
                              ("plans/02-beta/plan.md: invalid status 'maybe'",),
                              ("plans/priority.md", "02-beta", "duplicat"),
                              ("plans/priority.md", "98-unknown")):
                with self.subTest(fragments=fragments):
                    self.assertTrue(any(all(part in line for part in fragments) for line in errors), errors)
            self.assertTrue(all("\n" not in line for line in errors))

    def test_catalog_reports_each_malformed_priority_line(self):
        from test_records import ProjectRecordTests as Records
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            Records.write(root, "30-update-everywhere", Records.plan())
            Records.write(root, "38-one-process-identity", Records.plan())
            (root / "plans/priority.md").write_text(
                "# Priority\n## Order\n* 30-update-everywhere\n"
                "- 38-one-process-identity  (owner: keep high)\n", encoding="utf-8")
            self.assertEqual(self.errors(root, "plan-catalog"), [
                "plans/priority.md: invalid line 3 under ## Order; fix it to - <folder-id>",
                "plans/priority.md: invalid line 4 under ## Order; fix it to - <folder-id>",
            ])

    def test_every_other_documentation_rule_skips_a_bad_record(self):
        from test_records import ProjectRecordTests as Records
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            Records.write(root, "01-alpha", Records.plan().replace("**Status:** queued\n", ""))
            context = checks.Context(root)
            self.assertTrue(self.errors(root, "plan-catalog"))
            # These are the eleven legacy documentation guards named by PM-6b.
            # Public-vision and generated-view diagnostics have separate ownership.
            documentation = {"release-documents", "strategy-consistency", "catalog-paths",
                             "gap-structure", "plan-files", "subjects", "obsolete-sources",
                             "canonical-principles", "obsolete-templates", "ledger", "markdown-links"}
            self.assertEqual({entry.id for entry in checks.REGISTRY} & documentation, documentation)
            for entry in checks.REGISTRY:
                if entry.id in documentation:
                    with self.subTest(rule=entry.id):
                        self.assertEqual(entry.run(context), [])

    def test_unique_project_numbers_reports_duplicates_and_is_registered(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plans = root / "plans"
            (plans / "40-a").mkdir(parents=True)
            (plans / "40-b").mkdir()
            entry = next(entry for entry in checks.REGISTRY if entry.id == "unique-project-numbers")
            self.assertEqual(entry.trigger, "always")
            self.assertEqual(entry.run(checks.Context(root)), [
                "duplicate project number 40: 40-a, 40-b"])
            (plans / "40-b").rmdir()
            self.assertEqual(entry.run(checks.Context(root)), [])
            _, listing = invoke(["list"])
            self.assertIn("unique-project-numbers always", listing)

if __name__ == "__main__":
    unittest.main()
