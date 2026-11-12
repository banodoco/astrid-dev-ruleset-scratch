"""Registry contract for repository checks."""
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal
import json
import re
import sys
import subprocess

sys.path.insert(0, str(Path(__file__).resolve().parent))




# Documentation rules retain the legacy order and skip after a bad catalog.
def _catalog(context):
    import lifecycle
    from project_contract import PLAN_FOLDER
    from records import project_fields, priority_order, section
    root = context.root
    errors = []
    folders = set()
    for path in sorted((root / "plans").glob("*/plan.md")):
        folder = path.parent.name
        if not PLAN_FOLDER.fullmatch(folder):
            errors.append(f"plans/{folder}: invalid plan folder name; rename it to the NN-short-name form, like 48-one-record-model")
            continue
        folders.add(folder)
        try:
            fields = project_fields(path.read_text(encoding="utf-8"))
            if fields["Status"] not in lifecycle.names():
                errors.append(f"plans/{folder}/plan.md: invalid status {fields['Status']!r}; use {lifecycle.phrase()}")
        except (ValueError, OSError) as exc:
            errors.append(f"plans/{folder}/plan.md: {exc}")
    priority = root / "plans/priority.md"
    priority_text = priority.read_text(encoding="utf-8") if priority.exists() else None
    order = priority_order(priority_text)
    order_section = section(priority_text or "", "Order")
    order_heading = re.search(r"^## Order\s*$", priority_text or "", re.M)
    first_order_line = (priority_text[:order_heading.start()].count("\n") + 2) if order_heading else 1
    for line_number, line in enumerate(order_section.splitlines(), first_order_line):
        if line.strip() and not re.fullmatch(r"- \d{2,}-[a-z0-9-]+", line):
            errors.append(f"plans/priority.md: invalid line {line_number} under ## Order; fix it to - <folder-id>")
    seen = set()
    for folder in order:
        if folder in seen:
            errors.append(f"plans/priority.md: duplicate {folder} under ## Order; delete one of its lines")
        if folder not in folders:
            errors.append(f"plans/priority.md: unknown {folder} under ## Order (there is no plans/{folder}/plan.md); fix the name or delete the line")
        seen.add(folder)
    return errors


def _unique_project_numbers(context):
    plans = context.root / "plans"
    by_number = {}
    for folder in plans.iterdir():
        if folder.is_dir() and (match := re.match(r"^(\d{2})-", folder.name)):
            by_number.setdefault(match.group(1), []).append(folder.name)
    return [f"duplicate project number {number}: {', '.join(sorted(folders))}"
            for number, folders in sorted(by_number.items()) if len(folders) > 1]


def _release_documents(context):
    from check_docs import read, release_errors
    root = context.root
    try:
        if _catalog(context):
            return []
        from records import projects
        rows = projects(root)
    except (OSError, ValueError, IndexError):
        return []
    errors = []
    release_folder = root / 'releases'
    if not (release_folder / 'TEMPLATE.md').is_file():
        errors.append('releases/TEMPLATE.md: missing canonical release template')
    release_docs = {p.name: read(root, p.relative_to(root))
                    for p in release_folder.glob('[0-9]*.md') if p.stem.isdigit()}
    for filename, body in release_docs.items():
        errors.extend(release_errors(filename, body))
    return errors


def _strategy_consistency(context):
    from check_docs import read, STRATEGY, strategy_errors
    root = context.root
    try:
        if _catalog(context):
            return []
        from records import projects
        rows = projects(root)
    except (OSError, ValueError, IndexError):
        return []
    errors = []
    release_folder = root / 'releases'
    release_docs = {p.name: read(root, p.relative_to(root)) for p in release_folder.glob('[0-9]*.md') if p.stem.isdigit()}
    try:
        errors.extend(strategy_errors(read(root, STRATEGY), release_docs))
    except OSError as exc:
        errors.append(f'strategy.md: {exc}')
    return errors


def _catalog_paths(context):
    from check_docs import read, PLAN_FOLDER, unnamed_active_owners
    root = context.root
    try:
        if _catalog(context):
            return []
        from records import projects
        rows = projects(root)
    except (OSError, ValueError, IndexError):
        return []
    return unnamed_active_owners(rows)


def _gap_structure(context):
    from check_docs import read, GAP_NAME, parse_gap_relationships, route_issues
    root = context.root
    try:
        if _catalog(context):
            return []
        from records import projects
        rows = projects(root)
    except (OSError, ValueError, IndexError):
        return []
    errors = []
    gaps = sorted((root / 'vision/gaps').glob('*.md'))
    gap_ids = set()
    for file in gaps:
        match = GAP_NAME.fullmatch(file.name)
        if not match:
            errors.append(f'bad gap filename: {file.name}')
            continue
        gap_id = match.group(1)
        if gap_id in gap_ids:
            errors.append(f'duplicate gap ID: {gap_id}')
        gap_ids.add(gap_id)
        text = read(root, file.relative_to(root))
        if not text.startswith(f'# {gap_id} —'):
            errors.append(f'{file.name}: title must start with gap ID')
        for field in ['**Applies to:**', '**Assessment:**', '## Desired state', '## Current state', '## Gap', '## Closure evidence', '## Sources and reassessment']:
            if field not in text:
                errors.append(f'{file.name}: missing {field}')
        applies = next((s for s in text.splitlines() if s.startswith('**Applies to:**')), '')
        try:
            parse_gap_relationships(applies)
        except ValueError as exc:
            errors.append(f'{file.name}: {exc}')
        plan_texts = {p.parent.name: read(root, p.relative_to(root)) for p in (root / 'plans').glob('*/plan.md')}
        errors.extend(route_issues(file.name, gap_id, text, plan_texts))

    return errors


def _plan_files(context):
    from check_docs import read, GAP_NAME, plan_gap_ids
    root = context.root
    try:
        if _catalog(context):
            return []
        from records import projects
        rows = projects(root)
    except (OSError, ValueError, IndexError):
        return []
    errors = []
    actual = set(Path('plans') / p.parent.name / 'plan.md' for p in (root / 'plans').glob('*/plan.md'))
    gap_ids = {m.group(1) for p in (root / 'vision/gaps').glob('*.md') if (m := GAP_NAME.fullmatch(p.name))}
    for plan in sorted(actual):
        for name in ('plan.md', 'tasks.md', 'inputs.md'):
            if not (root / plan.parent / name).is_file():
                errors.append(f'{plan.parent}: missing {name}')
        body = read(root, plan)
        try:
            refs = plan_gap_ids(body)
            for gap in refs:
                if gap not in gap_ids:
                    errors.append(f'{plan}: unknown vision gap {gap}')
        except ValueError as exc:
            errors.append(f'{plan}: {exc}')
    return errors


def _subjects(context):
    from check_docs import read, parse_subject
    root = context.root
    try:
        if _catalog(context):
            return []
        from records import projects
        rows = projects(root)
    except (OSError, ValueError, IndexError):
        return []
    errors = []
    # Do not let pillar and principle docs quietly drift into unrelated prose
    # structures. Both are edited from one authoring template and parsed by
    # the public Vision exporter.
    for folder, prefix in (('pillars', 'Pillar'), ('principles', 'Principle')):
        entries = sorted((root / 'vision' / folder).glob('*.md'))
        if len(entries) != 4:
            errors.append(f'vision/{folder}: expected exactly four canonical subjects')
        for file in entries:
            relative = file.relative_to(root)
            try:
                parse_subject(read(root, relative), relative.as_posix())
            except ValueError as exc:
                errors.append(str(exc))
    return errors


def _obsolete_sources(context):
    from check_docs import read
    root = context.root
    try:
        if _catalog(context):
            return []
        from records import projects
        rows = projects(root)
    except (OSError, ValueError, IndexError):
        return []
    errors = []
    for stale in ('AGENTS.md', 'visions', 'vision/vision.md', 'vision/principles.md', 'vision/gaps.md'):
        if (root / stale).exists():
            errors.append(f'obsolete source must be removed: {stale}')
    return errors


def _canonical_principles(context):
    from check_docs import read
    root = context.root
    try:
        if _catalog(context):
            return []
        from records import projects
        rows = projects(root)
    except (OSError, ValueError, IndexError):
        return []
    errors = []
    expected_principles = {'local-first-cloud-capable', 'open-by-design', 'in-the-creators-control', 'eliminate-needless-technical-wrangling'}
    actual_principles = {p.stem for p in (root / 'vision/principles').glob('*.md')}
    if actual_principles != expected_principles:
        errors.append(f'expected four canonical principle pages, got {sorted(actual_principles)}')
    return errors


def _obsolete_templates(context):
    from check_docs import read, obsolete_template_paths
    root = context.root
    try:
        if _catalog(context):
            return []
        from records import projects
        rows = projects(root)
    except (OSError, ValueError, IndexError):
        return []
    errors = []
    errors.extend(obsolete_template_paths(root))
    return errors


def _ledger(context):
    from check_docs import read, ledger_errors
    root = context.root
    try:
        if _catalog(context):
            return []
        from records import projects
        rows = projects(root)
    except (OSError, ValueError, IndexError):
        return []
    errors = []
    errors.extend(ledger_errors(root))
    return errors


def _markdown_links(context):
    from check_docs import read, CATALOG, README, local_links
    root = context.root
    try:
        if _catalog(context):
            return []
        from records import projects
        rows = projects(root)
    except (OSError, ValueError, IndexError):
        return []
    errors = []
    mandatory = [README, CATALOG, Path('vision/README.md'),
                 Path('vision/templates/subject.md'),
                 Path('CONTRIBUTING.md'),
                 Path('templates/project/plan.md'), Path('docs/project-format.md'),
                 Path('docs/contribution-design-principles.md'),
                 Path('docs/contribution-workflow.md'), Path('docs/contribution-automation-setup.md'),
                 Path('templates/product-pr/review.md')]
    # Every Markdown file must be current. No grandfathered dead references.
    # Product evidence and old task cards must either have valid local links
    # or be removed/replaced by their authoritative project source.
    mandatory += [p.relative_to(root) for p in root.rglob("*.md")
                  if ".git" not in p.relative_to(root).parts]
    for path in sorted(set(mandatory)):
        errors.extend(local_links(root, path))

    return errors


def _public_vision(context):
    import export_public_vision
    try:
        page = export_public_vision.build(context.root, '0000000000000000000000000000000000000000')
    except (ValueError, OSError) as exc:
        return [f'public vision content: {exc}']
    return []


def _generated_views(context):
    import views
    if not context.base:
        return []
    errors = []
    for view in views.VIEWS:
        try:
            if views.touched(view, context.root, context.base):
                errors.extend(views.check_view(view, context.root))
        except (OSError, ValueError, subprocess.CalledProcessError) as exc:
            errors.append(f'view {view.name}: cannot check {view.target}: {exc}; '
                          f'{view.target} is generated from {", ".join(view.sources)}, so fix any error there, '
                          'then run python3 scripts/astrid_dev.py sync')
    if _catalog(context):
        errors = [message for message in errors if not message.startswith(("view plan-catalog ", "view plan-catalog:"))]
    # The legacy public-vision rule owns diagnostics for these two targets.
    legacy_errors = _public_vision(context)
    if legacy_errors:
        errors = [message for message in errors
                  if not message.startswith(('view public-vision ', 'view public-vision:',
                                             'view root-vision-summary ', 'view root-vision-summary:'))]
    return errors


def _body(context):
    if context.body_file:
        return context.body_file.read_text(encoding='utf-8')
    if context.event:
        return json.loads(context.event.read_text(encoding='utf-8')).get('pull_request', {}).get('body') or ''
    return ''


def _completion_impl(context):
    import check_completion as gate
    before = gate.project_statuses(context.root, context.base)
    after = gate.project_statuses(context.root)
    changes = gate.transitions_to_done(before, after)
    if not changes:
        return []
    errors = gate.check_pr(changes, _body(context), context.root)
    errors.extend(gate.strategy_errors(gate.changed_paths(context.base, context.root)))
    return errors

def _boundary_impl(context):
    import check_gap_boundaries as gate
    from gap_relationships import parse_gap_relationships
    from records import read_text
    required = gate.affected_gaps(context.base, context.root)
    if not required:
        return []
    body = _body(context)
    expected = {}
    for gap_id in sorted(required):
        paths = list((context.root / 'vision/gaps').glob(gap_id + '-*.md'))
        if len(paths) > 1:
            raise ValueError(f'{gap_id}: duplicate gap files')
        if paths:
            meta = next((line for line in read_text(context.root, paths[0].relative_to(context.root)).splitlines() if line.startswith('**Applies to:**')), '')
            expected[gap_id] = parse_gap_relationships(meta)
        else:
            expected[gap_id] = None
    return gate.check_pr(required, body, expected)


def _planning_impl(context):
    import check_project_planning as gate
    from records import read_text
    names = gate.changed_projects(context.base, context.root)
    errors = []
    for name in sorted(names):
        errors.extend(gate.validate_pack(name, read_text(context.root, Path('plans') / name / 'inputs.md')))
    return errors


def _pack_shape_impl(context):
    import pack_shape as gate
    root = context.root
    shape = gate.template_shape(root)
    errors = []
    for name in gate.new_packs(context.base, root):
        errors.extend(gate.shape_errors(name, shape, root))
    return errors


def _completion(context):
    try:
        return _completion_impl(context)
    except (OSError, ValueError) as exc:
        return [f"completion gate: {exc}"]


def _boundary(context):
    try:
        return _boundary_impl(context)
    except (OSError, ValueError) as exc:
        return [f"gap boundary gate: {exc}"]


def _planning(context):
    try:
        return _planning_impl(context)
    except (OSError, ValueError) as exc:
        return [f"project evidence: {exc}"]


def _pack_shape(context):
    try:
        return _pack_shape_impl(context)
    except (OSError, ValueError) as exc:
        return [f"can't check new packs against the templates: {exc}; if the base revision is missing, fetch the PR base, then run the check again"]


@dataclass(frozen=True)
class Context:
    root: Path
    base: str | None = None
    event: Path | None = None
    body_file: Path | None = None


@dataclass(frozen=True)
class Check:
    id: str
    trigger: Literal["always", "pr"]
    description: str
    run: Callable[[Context], list[str]]

    def __post_init__(self):
        if not self.id or any(c.isspace() for c in self.id):
            raise ValueError("check id must be a nonempty token")
        if self.trigger not in ("always", "pr"):
            raise ValueError("check trigger must be always or pr")
        if not self.description.strip() or "\n" in self.description or "\r" in self.description:
            raise ValueError("check description must be one nonempty line")
        if not callable(self.run):
            raise ValueError("check must be callable")


REGISTRY: tuple[Check, ...] = (
    Check('plan-catalog', 'always', 'Parse the plan catalog', _catalog),
    Check('unique-project-numbers', 'always', 'Require unique project numbers', _unique_project_numbers),
    Check('release-documents', 'always', 'Validate release documents', _release_documents),
    Check('strategy-consistency', 'always', 'Validate strategy consistency', _strategy_consistency),
    Check('catalog-paths', 'always', 'Validate catalog paths', _catalog_paths),
    Check('gap-structure', 'always', 'Validate gap structure', _gap_structure),
    Check('plan-files', 'always', 'Validate plan files', _plan_files),
    Check('subjects', 'always', 'Validate subjects', _subjects),
    Check('obsolete-sources', 'always', 'Validate obsolete sources', _obsolete_sources),
    Check('canonical-principles', 'always', 'Validate canonical principles', _canonical_principles),
    Check('obsolete-templates', 'always', 'Validate obsolete templates', _obsolete_templates),
    Check('ledger', 'always', 'Validate ledger', _ledger),
    Check('markdown-links', 'always', 'Validate markdown links', _markdown_links),
    Check('public-vision-content', 'always', 'Validate public vision source content', _public_vision),
    Check('generated-views', 'pr', 'Validate generated views that a pull request changes', _generated_views),
    Check('completion-assessment', 'pr', 'Require evidence for plans newly marked done', _completion),
    Check('gap-boundary-assessment', 'pr', 'Require a first-principles assessment for redefined gaps', _boundary),
    Check('project-planning-evidence', 'pr', 'Validate planning evidence for new or opted-in projects', _planning),
    Check('pack-shape', 'pr', 'Check that new project packs follow the templates', _pack_shape),
)
