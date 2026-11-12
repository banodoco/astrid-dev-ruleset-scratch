#!/usr/bin/env python3
"""Label new and edited issues; post, edit, close and remove nothing.

Trusted code from main. The issue's title and body are data: the type label comes from the
title's first word, and each real plan or gap ID under "### About" becomes a label. An ID is
real when main (the checkout this runs from) has its plan folder or gap file: no API call.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
from pathlib import Path

import contribution_api as api

ROOT = Path(__file__).resolve().parents[1]
TYPES = ("observation", "bug", "question", "idea")
TYPE_TITLE = re.compile(r"^\s*(?:(" + "|".join(TYPES) + r")\s*:|\[(bug)\])", re.I)
# The section ends at the next heading, a line that is only "---" (the footer a session's
# GitHub access appends), or the end of the body.
ABOUT = re.compile(r"^###[ \t]+About[ \t]*\n(.*?)(?=^#{1,6}[ \t]|^---[ \t]*$|\Z)", re.I | re.M | re.S)
PLAN_ID = re.compile(r"\bPlan\s+(\d{2,})\b", re.I)
GAP_ID = re.compile(r"\b([A-Z]{1,3}-\d{3})\b")
MAX_ABOUT_LABELS = 5


def type_label(title: str) -> str | None:
    match = TYPE_TITLE.match(title.strip())
    return (match.group(1) or match.group(2)).lower() if match else None


def about_labels(body: str, root: Path = ROOT) -> list[str]:
    labels = []
    for section in ABOUT.findall(body.replace("\r\n", "\n")):
        found = [("plan", f"plans/{n}-*/plan.md", n) for n in PLAN_ID.findall(section)]
        found += [("gap", f"vision/gaps/{g}-*.md", g) for g in GAP_ID.findall(section)]
        for kind, pattern, ident in found:
            if any(root.glob(pattern)) and f"{kind}:{ident}" not in labels:
                labels.append(f"{kind}:{ident}")
    return labels


def skipped(issue: dict) -> bool:
    return bool(issue.get("pull_request")) or (issue.get("user") or {}).get("type") == "Bot"


def label_event(event: dict, repo: str, root: Path = ROOT) -> str:
    stub = event.get("issue") or {}
    number = stub.get("number")
    if not isinstance(number, int):
        raise ValueError("no issue number")
    issue = {} if skipped(stub) else api.request("GET", f"/repos/{repo}/issues/{number}")
    if skipped(stub) or skipped(issue):
        return "Ignored: a pull request or a bot's issue"
    have = {label.get("name") for label in issue.get("labels", [])}
    room = MAX_ABOUT_LABELS - sum(1 for name in have if name.startswith(("plan:", "gap:")))
    kind = type_label(issue.get("title") or "")
    about = [name for name in about_labels(issue.get("body") or "", root) if name not in have]
    new = ([kind] if kind and kind not in have else []) + about[:max(room, 0)]
    for name in new:
        api.ensure_label(repo, name, "ededed" if ":" in name else "c5def5",
                         f"About {name.replace(':', ' ')}" if ":" in name else f"Issue type: {name}")
    if new:
        api.request("POST", f"/repos/{repo}/issues/{number}/labels", {"labels": new})
    return f"Issue #{number}: added {', '.join(new) or 'no labels'}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True, type=Path)
    args = parser.parse_args()
    try:
        event = json.loads(args.event.read_text(encoding="utf-8"))
        repo = os.environ["GITHUB_REPOSITORY"]
        if (event.get("repository") or {}).get("full_name") != repo:
            raise ValueError("event repository does not match trusted workflow")
        print(label_event(event, repo))
    except (ValueError, OSError, KeyError) as exc:
        print(f"Issue intake failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
