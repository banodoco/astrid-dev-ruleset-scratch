"""Small REST transport shared by trusted GitHub contribution workflows."""
from __future__ import annotations
import base64
import json
import os
import urllib.parse
import urllib.request
import urllib.error


def plan_text(repository: str, ref: str, folder: str) -> str | None:
    """Read a plain project plan at ref, returning None only for a 404."""
    owner, name = repository.split("/", 1)
    query = urllib.parse.quote(ref, safe="")
    path = f"/repos/{owner}/{name}/contents/plans/{folder}/plan.md?ref={query}"
    try:
        result = request("GET", path)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    if (not isinstance(result, dict) or result.get("type") != "file"
            or result.get("encoding") != "base64" or not isinstance(result.get("content"), str)
            or "target" in result):
        raise ValueError("expected a plain project plan file")
    try:
        return base64.b64decode(result["content"], validate=True).decode("utf-8")
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("project plan is not valid base64 UTF-8 text") from exc


def request(method: str, path: str, payload=None):
    api_root = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        api_root + path, data=data, method=method,
        headers={
            "Authorization": "Bearer " + os.environ["GH_TOKEN"],
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "astrid-dev-contributions",
            **({"Content-Type": "application/json"} if data is not None else {}),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        # Name the call: "HTTP Error 403: Forbidden" alone cannot be traced.
        raise urllib.error.HTTPError(exc.url, exc.code, f"{method} {path}: {exc.msg}", exc.hdrs, exc.fp) from exc


def changed_files(repo: str, number: int) -> list[dict]:
    files = []
    for page in range(1, 4):
        page_files = request("GET", f"/repos/{repo}/pulls/{number}/files?per_page=100&page={page}")
        files.extend(page_files)
        if len(page_files) < 100:
            return files
    raise ValueError("too many modified files to classify")


def ensure_label(repo: str, label: str, color: str, description: str) -> None:
    """Create one label if missing (a read, then at most a create). Never edits an existing label."""
    path = f"/repos/{repo}/labels/{urllib.parse.quote(label, safe='')}"
    try:
        request("GET", path)
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise
        try:
            request("POST", f"/repos/{repo}/labels",
                    {"name": label, "color": color, "description": description})
        except urllib.error.HTTPError as conflict:
            if conflict.code != 422:
                raise
            request("GET", path)


def ensure_review_label(repo: str, label: str) -> None:
    """Create one neutral review-queue label if missing. Never grant approval."""
    ensure_label(repo, label, "d4c5f9", "Submission in review queue; not approved or merged")
