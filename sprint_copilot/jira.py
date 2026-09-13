"""
jira.py — Phase 3: read the sprint's tickets (and, later, act on them).

Pulls issues for a project into the shared work_items shape:
    "tickets": [{key, title, status, assignee, updated, url}]

Config from .env: JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT.
Auth is HTTP basic (email + API token).

Jira Cloud is migrating its search API, so fetch_tickets tries the newer
/rest/api/3/search/jql endpoint and falls back to the classic
/rest/api/3/search if that isn't available.
"""

import os
import requests

_FIELDS = ["summary", "status", "assignee", "updated", "created"]


def _cfg() -> tuple[str, str, str]:
    return (
        os.environ["JIRA_BASE_URL"].rstrip("/"),
        os.environ["JIRA_EMAIL"],
        os.environ["JIRA_API_TOKEN"],
    )


def _project() -> str:
    return os.environ.get("JIRA_PROJECT", "SCRUM")


def _normalise(issue: dict, base: str) -> dict:
    f = issue.get("fields", {}) or {}
    assignee = f.get("assignee") or {}
    status = f.get("status") or {}
    return {
        "key": issue.get("key", ""),
        "title": f.get("summary", ""),
        "status": status.get("name", ""),
        "assignee": assignee.get("displayName", "Unassigned"),
        "updated": f.get("updated", ""),
        "url": f"{base}/browse/{issue.get('key', '')}",
    }


def fetch_tickets(project: str | None = None, jql: str | None = None, max_results: int = 50) -> list[dict]:
    base, email, token = _cfg()
    project = project or _project()
    jql = jql or f"project = {project} ORDER BY updated DESC"
    auth = (email, token)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    # Newer enhanced-search endpoint first.
    r = requests.post(
        f"{base}/rest/api/3/search/jql",
        auth=auth, headers=headers,
        json={"jql": jql, "fields": _FIELDS, "maxResults": max_results},
        timeout=15,
    )
    # Fall back to the classic endpoint if the new one isn't there.
    if r.status_code in (404, 410):
        r = requests.get(
            f"{base}/rest/api/3/search",
            auth=auth, headers=headers,
            params={"jql": jql, "fields": ",".join(_FIELDS), "maxResults": max_results},
            timeout=15,
        )
    r.raise_for_status()

    return [_normalise(it, base) for it in r.json().get("issues", [])]


# ── Write-back: move a ticket ─────────────────────────────────────────────────

def get_transitions(key: str) -> list[dict]:
    """The workflow transitions currently available for an issue."""
    base, email, token = _cfg()
    r = requests.get(
        f"{base}/rest/api/3/issue/{key}/transitions",
        auth=(email, token), headers={"Accept": "application/json"}, timeout=15,
    )
    r.raise_for_status()
    return r.json().get("transitions", [])


def move_issue(key: str, target: str = "Done", dry_run: bool = True) -> tuple[bool, str]:
    """Move an issue to a status matching `target` (e.g. "Done").

    dry_run=True (default) only reports what it would do — nothing changes on
    the board. Pass dry_run=False to actually perform the transition.
    """
    transitions = get_transitions(key)
    chosen = None
    for tr in transitions:
        to_name = (tr.get("to") or {}).get("name", "")
        if target.lower() in to_name.lower() or target.lower() in tr.get("name", "").lower():
            chosen = tr
            break

    if not chosen:
        available = ", ".join((t.get("to") or {}).get("name", "?") for t in transitions)
        return False, f"{key}: no transition to '{target}' (available: {available or 'none'})"

    to_name = chosen["to"]["name"]
    if dry_run:
        return True, f"{key}: WOULD move → {to_name} (transition '{chosen['name']}')"

    base, email, token = _cfg()
    r = requests.post(
        f"{base}/rest/api/3/issue/{key}/transitions",
        auth=(email, token),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        json={"transition": {"id": chosen["id"]}},
        timeout=15,
    )
    r.raise_for_status()
    return True, f"{key}: moved → {to_name}"


def add_comment(key: str, text: str, dry_run: bool = True) -> tuple[bool, str]:
    """Post a comment on an issue. Jira Cloud v3 needs Atlassian Document
    Format (ADF), so we wrap the plain text in a minimal doc."""
    if dry_run:
        return True, f"{key}: WOULD comment \"{text[:60]}...\""

    base, email, token = _cfg()
    # One ADF paragraph per line so multi-line comments render correctly.
    paragraphs = [
        {"type": "paragraph", "content": [{"type": "text", "text": line or " "}]}
        for line in text.split("\n")
    ]
    body = {"body": {"type": "doc", "version": 1, "content": paragraphs}}
    r = requests.post(
        f"{base}/rest/api/3/issue/{key}/comment",
        auth=(email, token),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        json=body, timeout=15,
    )
    r.raise_for_status()
    return True, f"{key}: comment posted"


if __name__ == "__main__":
    from pathlib import Path
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).parent.parent / ".env")
    tickets = fetch_tickets()
    print(f"Project {_project()} — {len(tickets)} ticket(s):\n")
    for t in tickets:
        print(f"  {t['key']:<10} [{t['status']:<12}] {t['title'][:50]:<50} — {t['assignee']}")
    if not tickets:
        print("  (none — check JIRA_PROJECT and that the sprint has tickets)")
