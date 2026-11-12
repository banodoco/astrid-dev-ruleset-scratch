import tempfile
import unittest
import contextlib
import io
import shutil
import subprocess
from pathlib import Path

from views import View, _with_marker, check, check_view, sync


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def commit_base(root):
    """Make a base only in a disposable test repository."""
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.name", "Test")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "add", ".")
    git(root, "commit", "-qm", "base")
    return git(root, "rev-parse", "HEAD")


class ViewTests(unittest.TestCase):
    def test_hand_edited_vision_title_fails_check(self):
        import astrid_dev
        source = Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            shutil.copytree(source, root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            base = commit_base(root)
            target = root / "vision/README.md"
            content = target.read_text(encoding="utf-8")
            target.write_text(content.replace("# Astrid — ", "# Astrid — Hand edited ", 1), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                body = Path(temporary) / "body.txt"
                body.write_text("", encoding="utf-8")
                code = astrid_dev.main(["check", "--base", base, "--body-file", str(body)], root=root)
            self.assertEqual(code, 1)
            self.assertIn("ERROR generated-views: view public-vision", output.getvalue())
            self.assertNotIn("ERROR public-vision-content:", output.getvalue())

    def test_list_failure_is_reported_as_generated_views_error(self):
        import astrid_dev
        import checks
        import subprocess
        from unittest.mock import patch

        registry = [entry for entry in checks.REGISTRY if entry.id == "generated-views"]
        output = io.StringIO()
        # Without a base, this PR-only check never renders the check catalog.
        with patch("views.subprocess.run", side_effect=subprocess.CalledProcessError(1, ["astrid_dev.py", "list"])) as run:
            with contextlib.redirect_stdout(output):
                code = astrid_dev.main(["check"], registry=registry)
        self.assertEqual(code, 0)
        self.assertEqual(output.getvalue(), "")
        run.assert_not_called()

    def test_legacy_source_error_hides_both_owned_view_errors(self):
        import checks
        import golden
        import json
        import views

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            golden._copy_tree(root)
            overlay = json.loads((golden.FIXTURES / "bad-status/overlay.json").read_text(encoding="utf-8"))
            for relative, contents in overlay.items():
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(contents, encoding="utf-8")
            context = checks.Context(root)
            source_errors = checks._public_vision(context)
            self.assertTrue(any("invalid status 'maybe'" in line for line in source_errors), source_errors)
            raw_errors = views.check(root)
            self.assertTrue(any(line.startswith("view public-vision:") for line in raw_errors))
            self.assertTrue(any(line.startswith("view root-vision-summary:") for line in raw_errors))
            # Source errors remain owned by public-vision-content. With no base,
            # generated-views does not report either owned target or render it.
            self.assertEqual(checks._generated_views(context), [])

    def test_view_check_is_registered(self):
        import checks
        registered = [entry for entry in checks.REGISTRY if entry.id == "generated-views"]
        self.assertEqual(len(registered), 1)
        self.assertEqual(registered[0].trigger, "pr")
        self.assertTrue(registered[0].description)
        self.assertTrue(callable(registered[0].run))

    def test_legacy_vision_failure_is_the_only_error_line(self):
        import astrid_dev
        source = Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            shutil.copytree(source, root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            base = commit_base(root)
            target = root / "README.md"
            content = target.read_text(encoding="utf-8")
            target.write_text(content.replace("<!-- vision-summary:end -->", "hand edit\n<!-- vision-summary:end -->"), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                body = Path(temporary) / "body.txt"
                body.write_text("", encoding="utf-8")
                code = astrid_dev.main(["check", "--base", base, "--body-file", str(body)], root=root)
            error_lines = [line for line in output.getvalue().splitlines() if line.startswith("ERROR ")]
            self.assertEqual(code, 1)
            self.assertEqual(len(error_lines), 1)
            self.assertIn("generated-views: view root-vision-summary", error_lines[0])

    def test_file_view_adds_standard_marker(self):
        view = View("sample", ("source.md",), "target.md", lambda root: "# Generated\n")
        self.assertEqual(
            _with_marker(view, "# Generated\n"),
            "<!-- Generated by Astrid Dev view: sample; sources: source.md. Do not edit. -->\n# Generated\n",
        )

    def test_region_view_preserves_surrounding_text_and_checks_hand_edits(self):
        view = View("summary", ("source.md",), "README.md", lambda root: "before\n<!-- vision-summary:start -->\nvalue\n<!-- vision-summary:end -->\nafter\n", True)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "README.md").write_text("before\n<!-- vision-summary:start -->\nvalue\n<!-- vision-summary:end -->\nafter\n", encoding="utf-8")
            import views
            previous = views.VIEWS
            try:
                views.VIEWS = (view,)
                self.assertEqual(sync(root), ["README.md"])
            finally:
                views.VIEWS = previous
            self.assertEqual(check_view(view, root), [])
            text = (root / "README.md").read_text(encoding="utf-8")
            self.assertIn("view: summary", text)
            (root / "README.md").write_text(text.replace("value", "hand edit"), encoding="utf-8")
            errors = check_view(view, root)
            self.assertEqual(len(errors), 1)
            self.assertIn("view summary", errors[0])

    def test_sync_is_idempotent(self):
        view = View("sample", ("source.md",), "target.md", lambda root: "content\n")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = (view,)
            import views
            previous = views.VIEWS
            try:
                views.VIEWS = original
                self.assertEqual(sync(root), ["target.md"])
                self.assertEqual(sync(root), [])
                self.assertEqual(check(root), [])
            finally:
                views.VIEWS = previous


class PlanCatalogViewTests(unittest.TestCase):
    def view(self):
        import views
        matches = [view for view in views.VIEWS if view.name == "plan-catalog"]
        self.assertEqual(len(matches), 1, "PM-6b must register the plan-catalog view")
        view = matches[0]
        self.assertEqual(view.sources, ("plans/*/plan.md", "plans/priority.md"))
        self.assertEqual(view.target, "plans/index.md")
        self.assertEqual(view.region, "plan-catalog")
        return view

    def sources(self, root):
        from test_records import ProjectRecordTests as Records
        Records.write(root, "01-alpha", Records.plan(Project="Catalog alpha", Status="active",
                      Goal="Read [release](../../releases/12.md)", **{"Waiting on": "[work](../02-beta/plan.md)"}))
        Records.write(root, "02-beta", Records.plan(Project="Catalog beta", Status="done"))
        (root / "plans/priority.md").write_text("## Order\n- 02-beta\n- 01-alpha\n", encoding="utf-8")
        # Everything outside the table is owned by the author, including the
        # title, priority explanation, six definitions, edit guidance and notes.
        (root / "plans/index.md").write_text(
            self.before() + "<!-- plan-catalog:start -->\nold table\n"
            "<!-- plan-catalog:end -->" + self.after(), encoding="utf-8")

    @staticmethod
    def before():
        return ("# Our hand-written catalog title\n\n"
                "Priority follows plans/priority.md; edit facts in each plan.md and run sync.\n\n"
                "**Definitions:** `active` = explicitly started; `queued` = planned, not started; "
                "`blocked` = known impediment; `paused` = deliberately stopped; "
                "`done` = accepted completion evidence; `cancelled` = intentionally abandoned, "
                "with reason in the plan. Owner is accountability, not permission. "
                "Estimates are remaining human engineering days or `TBD`.\n\n")

    @staticmethod
    def after():
        return "\n\n## Delivery context\n\nHand-written notes stay intact.\n"

    def test_catalog_region_preserves_prose_and_generates_only_marker_and_table(self):
        import views
        from records import split_table_row
        view = self.view()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.sources(root)
            text = views.expected(view, root)
            before, rest = text.split("<!-- plan-catalog:start -->")
            generated, after = rest.split("<!-- plan-catalog:end -->")
            self.assertEqual(before, self.before())
            self.assertEqual(after, self.after())
            self.assertEqual(text.count("<!-- plan-catalog:start -->"), 1)
            self.assertEqual(text.count("<!-- plan-catalog:end -->"), 1)
            self.assertEqual(generated.splitlines()[1], view.marker)
            self.assertTrue(all(line.startswith("|") for line in generated.splitlines()[2:] if line))
            self.assertFalse((root / "plans/catalog-notes.md").exists())
            lines = [line for line in text.splitlines() if line.startswith("|")]
            self.assertEqual(split_table_row(lines[0]), ["Plan", "Project", "Goal", "Status", "Owner", "Estimate", "Waiting on"])
            rows = [split_table_row(line) for line in lines[2:]]
            self.assertEqual(rows, [
                ["[Plan 01](01-alpha/plan.md)", "Catalog alpha", "Read [release](../releases/12.md)",
                 "active", "Ada", "TBD", "[work](02-beta/plan.md)"],
                ["[Plan 02](02-beta/plan.md)", "Catalog beta", "Build **one** thing", "done", "Ada", "TBD", "—"],
            ])

    def test_catalog_has_no_generated_preamble_helper(self):
        import views
        self.assertFalse(hasattr(views, "_catalog_preamble"))

    def test_edits_outside_catalog_region_are_free_and_survive_regeneration(self):
        import views
        from test_records import ProjectRecordTests as Records
        from unittest.mock import patch
        view = self.view()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.sources(root)
            with patch.object(views, "VIEWS", (view,)):
                views.sync(root)
                target = root / "plans/index.md"
                text = target.read_text(encoding="utf-8")
                text = text.replace(self.before(), "# A new author title\n\nFree prose above.\n")
                text = text.replace(self.after(), "\nFree prose below.\n")
                target.write_text(text, encoding="utf-8")
                self.assertEqual(views.check(root), [])
                self.assertEqual(views.sync(root), [])
                self.assertEqual(target.read_text(encoding="utf-8"), text)
                Records.write(root, "01-alpha", Records.plan(Project="Changed source", Status="active"))
                self.assertEqual(views.sync(root), ["plans/index.md"])
                rewritten = target.read_text(encoding="utf-8")
                self.assertEqual(rewritten.split("<!-- plan-catalog:start -->")[0],
                                 text.split("<!-- plan-catalog:start -->")[0])
                self.assertEqual(rewritten.split("<!-- plan-catalog:end -->")[1],
                                 text.split("<!-- plan-catalog:end -->")[1])
                self.assertIn("Changed source", rewritten)
                self.assertEqual(views.check(root), [])

    def test_region_markers_take_a_generic_region_name(self):
        # Neither a view's name nor a hard-coded vision-summary region wins
        # over its declared region name.
        view = View("sample", ("source.md",), "target.md", lambda root: "", region="other-region")
        text = "before\n<!-- other-region:start -->\nvalue\n<!-- other-region:end -->\nafter\n"
        wanted = text.replace("\nvalue\n", "\n" + view.marker + "\nvalue\n")
        self.assertEqual(_with_marker(view, text), wanted)
        self.assertEqual(_with_marker(view, wanted), wanted)
        for malformed in (text.replace("<!-- other-region:start -->", ""),
                          text.replace("<!-- other-region:end -->", ""),
                          text + "<!-- other-region:start -->\n<!-- other-region:end -->\n"):
            with self.subTest(malformed=malformed), self.assertRaisesRegex(ValueError, "view sample"):
                _with_marker(view, malformed)

    def test_vision_summary_declares_its_region_name(self):
        import views
        view = next(view for view in views.VIEWS if view.name == "root-vision-summary")
        self.assertEqual(view.region, "vision-summary")

    def test_rebase_relative_links_preserves_external_and_fragment_targets(self):
        import views
        value = ("[release](../../releases/12.md) [peer](../02-beta/plan.md#scope) "
                 "[local](#design) [web](https://example.invalid/a) [mail](mailto:a@example.invalid) "
                 "[custom](custom+app:resource) [root](/assets/icon.svg) plain text")
        wanted = ("[release](../releases/12.md) [peer](02-beta/plan.md#scope) "
                  "[local](#design) [web](https://example.invalid/a) [mail](mailto:a@example.invalid) "
                  "[custom](custom+app:resource) [root](/assets/icon.svg) plain text")
        self.assertEqual(views.rebase_links(value, Path("plans/01-alpha"), Path("plans")), wanted)
        self.assertEqual(views.rebase_links("No links **here**", Path("plans/01-alpha"), Path("plans")),
                         "No links **here**")

    def test_catalog_sync_is_idempotent_and_hand_edit_names_the_view(self):
        import checks
        import views
        from unittest.mock import patch
        view = self.view()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.sources(root)
            with patch.object(views, "VIEWS", (view,)):
                self.assertEqual(views.sync(root), ["plans/index.md"])
                first = (root / "plans/index.md").read_bytes()
                self.assertEqual(views.sync(root), [])
                self.assertEqual((root / "plans/index.md").read_bytes(), first)
                self.assertEqual(views.check(root), [])
                base = commit_base(root)
                target = root / "plans/index.md"
                target.write_text(target.read_text().replace("Catalog alpha", "Hand-edited alpha"), encoding="utf-8")
                errors = checks._generated_views(checks.Context(root, base=base))
                self.assertTrue(any("view plan-catalog" in line and "plans/index.md" in line for line in errors), errors)

    def test_new_valid_folder_appears_last_among_open_rows_without_a_catalog_edit(self):
        import views
        from records import split_table_row
        from test_records import ProjectRecordTests as Records
        view = self.view()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.sources(root)
            # It sorts before 01-alpha by folder, but explicit priority wins.
            Records.write(root, "00-new", Records.plan(Project="New open"))
            lines = [line for line in views.expected(view, root).splitlines() if line.startswith("|")][2:]
            self.assertEqual([split_table_row(line)[1] for line in lines],
                             ["Catalog alpha", "New open", "Catalog beta"])


class TouchedViewTests(unittest.TestCase):
    def repo(self, *, region=False):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        view = View("sample", ("source.md",), "target.md", lambda root: "unused", region)
        text = ("before\n<!-- custom:start -->\ngenerated\n<!-- custom:end -->\nafter\n"
                if region else "generated\n")
        (root / view.target).write_text(text, encoding="utf-8")
        (root / "source.md").write_text("source\n", encoding="utf-8")
        return root, view, commit_base(root)

    def test_unchanged_file_and_source_only_edit_are_untouched(self):
        import views
        root, view, base = self.repo()
        self.assertFalse(views.touched(view, root, base))
        (root / "source.md").write_text("new source\n", encoding="utf-8")
        self.assertFalse(views.touched(view, root, base))

    def test_unstaged_and_staged_file_edits_are_touched(self):
        import views
        root, view, base = self.repo()
        (root / view.target).write_text("hand edit\n", encoding="utf-8")
        self.assertTrue(views.touched(view, root, base))
        git(root, "add", view.target)
        self.assertTrue(views.touched(view, root, base))

    def test_committed_file_edit_is_touched(self):
        import views
        root, view, base = self.repo()
        (root / view.target).write_text("committed edit\n", encoding="utf-8")
        git(root, "add", view.target)
        git(root, "commit", "-qm", "edit target")
        self.assertTrue(views.touched(view, root, base))

    def test_new_untracked_file_is_touched(self):
        import views
        root, view, _ = self.repo()
        git(root, "rm", "-q", view.target)
        git(root, "commit", "-qm", "base without target")
        base = git(root, "rev-parse", "HEAD")
        (root / view.target).write_text("new file\n", encoding="utf-8")
        self.assertTrue(views.touched(view, root, base))

    def test_deleted_file_is_touched(self):
        import views
        root, view, base = self.repo()
        (root / view.target).unlink()
        self.assertTrue(views.touched(view, root, base))

    def test_comparison_uses_merge_base_instead_of_base_tip(self):
        import views
        root, view, _ = self.repo()
        git(root, "switch", "-qc", "other")
        (root / view.target).write_text("other branch\n", encoding="utf-8")
        git(root, "add", view.target)
        git(root, "commit", "-qm", "other target")
        base = git(root, "rev-parse", "HEAD")
        git(root, "switch", "-q", "main")
        self.assertFalse(views.touched(view, root, base))
        # Equal to the base tip, but changed relative to the common ancestor.
        (root / view.target).write_text("other branch\n", encoding="utf-8")
        self.assertTrue(views.touched(view, root, base))

    def test_generic_region_ignores_prose_before_and_after_markers(self):
        import views
        root, view, base = self.repo(region="custom")
        target = root / view.target
        target.write_text(target.read_text().replace("before", "new title").replace("after", "new notes"),
                          encoding="utf-8")
        self.assertFalse(views.touched(view, root, base))

    def test_generic_region_content_edit_is_touched(self):
        import views
        root, view, base = self.repo(region="custom")
        target = root / view.target
        target.write_text(target.read_text().replace("generated", "hand edit"), encoding="utf-8")
        self.assertTrue(views.touched(view, root, base))

    def test_missing_working_tree_region_marker_raises(self):
        import views
        root, view, base = self.repo(region="custom")
        target = root / view.target
        target.write_text(target.read_text().replace("<!-- custom:end -->", ""), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "sample|region"):
            views.touched(view, root, base)

    def test_region_marker_missing_in_both_versions_is_not_untouched(self):
        import views
        root, view, _ = self.repo(region="custom")
        target = root / view.target
        target.write_text(target.read_text().replace("<!-- custom:start -->", ""), encoding="utf-8")
        git(root, "add", view.target)
        git(root, "commit", "-qm", "missing marker")
        with self.assertRaisesRegex(ValueError, "sample|region"):
            views.touched(view, root, git(root, "rev-parse", "HEAD"))


class GeneratedViewsRefreshTests(unittest.TestCase):
    def repo(self, *, region=False):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / "source.md").write_text("source\n", encoding="utf-8")

        def render(root):
            content = (root / "source.md").read_text(encoding="utf-8")
            if not region:
                return content
            before, rest = (root / "target.md").read_text(encoding="utf-8").split("<!-- custom:start -->")
            _, after = rest.split("<!-- custom:end -->")
            return before + "<!-- custom:start -->\n" + content + "<!-- custom:end -->" + after

        view = View("sample", ("source.md",), "target.md", render, "custom" if region else False)
        target = root / view.target
        target.write_text("before\n<!-- custom:start -->\nold\n<!-- custom:end -->\nafter\n", encoding="utf-8")
        import views
        target.write_text(views.expected(view, root), encoding="utf-8")
        return root, view, commit_base(root)

    def errors(self, root, view, base=None):
        import checks
        import views
        from unittest.mock import patch
        # Isolate the refresh rule from unrelated source validators.
        with patch.object(views, "VIEWS", (view,)), \
             patch.object(checks, "_catalog", return_value=[]), \
             patch.object(checks, "_public_vision", return_value=[]):
            return checks._generated_views(checks.Context(root, base=base))

    def test_no_base_skips_a_stale_target(self):
        root, view, _ = self.repo()
        (root / "source.md").write_text("changed source\n", encoding="utf-8")
        self.assertEqual(self.errors(root, view), [])

    def test_source_only_change_leaves_stale_untouched_target_allowed(self):
        root, view, base = self.repo()
        (root / "source.md").write_text("changed source\n", encoding="utf-8")
        self.assertEqual(self.errors(root, view, base), [])

    def test_correctly_regenerated_touched_target_is_allowed(self):
        import views
        root, view, base = self.repo()
        (root / "source.md").write_text("changed source\n", encoding="utf-8")
        (root / view.target).write_text(views.expected(view, root), encoding="utf-8")
        self.assertEqual(self.errors(root, view, base), [])

    def test_hand_edit_names_view_target_and_source_to_edit(self):
        root, view, base = self.repo()
        (root / view.target).write_text("hand edit\n", encoding="utf-8")
        errors = self.errors(root, view, base)
        self.assertEqual(len(errors), 1, errors)
        for text in ("view sample", "target.md", "edit source.md"):
            self.assertIn(text, errors[0])

    def test_prose_only_edit_does_not_expose_a_stale_region(self):
        root, view, base = self.repo(region=True)
        (root / "source.md").write_text("changed source\n", encoding="utf-8")
        target = root / view.target
        target.write_text(target.read_text().replace("before", "free prose").replace("after", "free notes"),
                          encoding="utf-8")
        self.assertEqual(self.errors(root, view, base), [])

    def test_missing_region_marker_is_reported_even_when_unchanged(self):
        root, view, _ = self.repo(region=True)
        target = root / view.target
        target.write_text(target.read_text().replace("<!-- custom:start -->", ""), encoding="utf-8")
        git(root, "add", view.target)
        git(root, "commit", "-qm", "missing marker")
        errors = self.errors(root, view, git(root, "rev-parse", "HEAD"))
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("view sample", errors[0])
        self.assertIn("target.md", errors[0])

    def test_touched_check_catalog_renderer_failure_is_reported(self):
        import views
        from unittest.mock import patch
        root, _, base = self.repo()
        view = View("check-catalog", ("scripts/checks.py",), "target.md", views._checks)
        (root / view.target).write_text("hand edit\n", encoding="utf-8")
        # Keep git calls real: only the declared renderer fails.
        with patch.object(views, "_checks", side_effect=subprocess.CalledProcessError(1, ["astrid_dev.py", "list"])):
            view = View(view.name, view.sources, view.target, views._checks)
            errors = self.errors(root, view, base)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("view check-catalog:", errors[0])
        self.assertIn("target.md", errors[0])
        self.assertIn("scripts/checks.py", errors[0])


class PublicVisionRefreshTests(unittest.TestCase):
    def repo(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / "repo"
        import golden
        golden._copy_tree(root)
        return root

    def stale_targets(self, root):
        for name in ("vision/README.md", "README.md"):
            target = root / name
            target.write_text(target.read_text() + "\nStale generated content.\n", encoding="utf-8")
        # The root view owns only its region; stale content must go inside it.
        target = root / "README.md"
        target.write_text(target.read_text().replace("<!-- vision-summary:end -->",
                          "stale\n<!-- vision-summary:end -->"), encoding="utf-8")

    def test_public_vision_source_check_ignores_stale_targets(self):
        import checks
        root = self.repo()
        self.stale_targets(root)
        self.assertEqual(checks._public_vision(checks.Context(root)), [])

    def test_exporter_accepts_stale_targets_and_does_not_write_them(self):
        import export_public_vision as exporter
        import json
        from unittest.mock import patch
        root = self.repo()
        self.stale_targets(root)
        before = {name: (root / name).read_bytes() for name in ("vision/README.md", "README.md")}
        output = root.parent / "vision.json"
        revision = "0000000000000000000000000000000000000000"
        wanted = exporter.build(root, revision)
        with patch.object(exporter, "ROOT", root), \
             patch("sys.argv", ["export_public_vision.py", "--revision", revision, "--output", str(output)]), \
             contextlib.redirect_stdout(io.StringIO()):
            code = exporter.main()
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.read_text()), wanted)
        self.assertEqual({name: (root / name).read_bytes() for name in before}, before)

    def test_exporter_removes_sync_readme_option(self):
        import export_public_vision as exporter
        from unittest.mock import patch
        root = self.repo()
        with patch.object(exporter, "ROOT", root), \
             patch("sys.argv", ["export_public_vision.py", "--sync-readme", "--revision",
                                "0000000000000000000000000000000000000000"]), \
             contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                exporter.main()
        self.assertEqual(error.exception.code, 2)


class SyncTargetSafetyTests(unittest.TestCase):
    def assert_refused_before_writing(self, root, unsafe):
        import views
        from unittest.mock import patch
        safe = root / "safe.md"
        safe.write_text("unchanged\n", encoding="utf-8")
        safe_view = View("safe", ("source.md",), "safe.md", lambda root: "new safe content\n")
        unsafe_view = View("unsafe", ("source.md",), unsafe, lambda root: "unsafe content\n")
        # The invalid target comes second: a per-write check is too late.
        with patch.object(views, "VIEWS", (safe_view, unsafe_view)):
            with self.assertRaisesRegex(ValueError, "unsafe|target|repository|symlink"):
                views.sync(root)
        self.assertEqual(safe.read_text(), "unchanged\n")

    def test_target_symlink_inside_repository_is_refused_before_any_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            real = root / "real.md"
            real.write_text("real content\n", encoding="utf-8")
            (root / "link.md").symlink_to("real.md")
            self.assert_refused_before_writing(root, "link.md")
            self.assertEqual(real.read_text(), "real content\n")

    def test_parent_symlink_leaving_repository_is_refused_before_any_write(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            root = parent / "repo"
            root.mkdir()
            outside = parent / "outside"
            outside.mkdir()
            (root / "escape").symlink_to(outside, target_is_directory=True)
            self.assert_refused_before_writing(root, "escape/target.md")
            self.assertFalse((outside / "target.md").exists())

    def test_parent_traversal_leaving_repository_is_refused_before_any_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            root.mkdir()
            self.assert_refused_before_writing(root, "../outside.md")
            self.assertFalse((root.parent / "outside.md").exists())

    def test_absolute_target_outside_repository_is_refused_before_any_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            root.mkdir()
            outside = Path(directory) / "outside.md"
            self.assert_refused_before_writing(root, str(outside))
            self.assertFalse(outside.exists())


class PullRequestBaseTests(unittest.TestCase):
    def test_workflow_uses_main_as_of_merge_first_parent_or_event_base(self):
        import os
        import subprocess
        import textwrap
        source = (Path(__file__).resolve().parents[1] / ".github/workflows/docs.yml").read_text(encoding="utf-8")
        pr_step = source.split("      - name: Run repository checks\n", 1)[1].split("      - name:", 1)[0]
        self.assertIn("PR_HEAD_SHA: ${{ github.event.pull_request.head.sha }}", pr_step)
        script = textwrap.dedent(pr_step.split("        run: |\n", 1)[1])
        # The first parent is main as of that merge, not the event's base.
        for second_parent, first_parent, status, wanted_base in (
            ("pr-head", "merge-main", 0, "merge-main"),
            ("", "", 0, "event-base"),
            ("wrong-head", "merge-main", 1, None),
        ):
            with self.subTest(second_parent=second_parent), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                bin_dir = root / "bin"
                bin_dir.mkdir()
                git = bin_dir / "git"
                git.write_text("#!/bin/sh\ncase \"$*\" in\n"
                               "  'rev-parse --verify HEAD^2') [ -n \"$SECOND_PARENT\" ] || exit 1; printf '%s\\n' \"$SECOND_PARENT\" ;;\n"
                               "  'rev-parse HEAD^1') printf '%s\\n' \"$FIRST_PARENT\" ;;\n"
                               "  *) exit 2 ;;\nesac\n", encoding="utf-8")
                python = bin_dir / "python3"
                python.write_text("#!/bin/sh\nprintf '%s\\n' \"$@\" > \"$CAPTURE\"\n", encoding="utf-8")
                git.chmod(0o755)
                python.chmod(0o755)
                capture = root / "args.txt"
                env = dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ["PATH"],
                           SECOND_PARENT=second_parent, FIRST_PARENT=first_parent,
                           PR_BASE_SHA="event-base", PR_HEAD_SHA="pr-head",
                           GITHUB_EVENT_PATH="event.json", CAPTURE=str(capture))
                result = subprocess.run(["bash", "-c", script], cwd=root, env=env,
                                        text=True, capture_output=True)
                self.assertEqual(result.returncode, status, result.stderr)
                if wanted_base is None:
                    self.assertFalse(capture.exists())
                else:
                    self.assertEqual(capture.read_text().splitlines(),
                                     ["scripts/astrid_dev.py", "check", "--base", wanted_base, "--event", "event.json"])


if __name__ == "__main__":
    unittest.main()
