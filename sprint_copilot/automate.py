"""
automate.py — Phase 7: act on the tools, not just report.

The core action: when a ticket's PR has been merged, move that ticket to
Done automatically. Safe by default — dry_run=True reports what it *would*
do and changes nothing. Pass --apply (CLI) or dry_run=False to actually move
tickets on the board.
"""

from sprint_copilot import match as matcher, jira


def evidence_comment(m: dict, status: str) -> str:
    """Build a Jira comment citing the linked PRs and commits (with GitHub
    URLs) for a ticket — the evidence trail left on the card."""
    lines = [f"✅ Sprint Copilot: moved to {status}."]
    for p in m.get("prs", []):
        url = p.get("url", "")
        lines.append(f"• PR #{p['number']}: {p['title']} {url}".rstrip())
    for c in m.get("commits", [])[:5]:
        subj = c["message"].split("\n")[0][:70]
        url = c.get("url", "")
        lines.append(f"• commit {c['short_hash']}: {subj} {url}".rstrip())
    if not m.get("prs") and not m.get("commits"):
        lines.append("• (no linked commits or PRs found)")
    return "\n".join(lines)


def auto_move_merged(work_items: dict | None = None, target: str = "Done", dry_run: bool = True) -> list[str]:
    """For every ticket that has a merged PR and isn't already at `target`,
    move it (or report the move under dry_run). Returns human-readable lines."""
    if work_items is None:
        work_items = matcher.build_work_items()
    matched = matcher.match(work_items)

    actions: list[str] = []
    for key, m in matched["matched"].items():
        merged = [p for p in m["prs"] if p.get("merged")]
        if not merged:
            continue
        status = m["ticket"].get("status", "")
        if target.lower() in status.lower():
            actions.append(f"{key}: already '{status}' — skip")
            continue

        pr_nums = ", ".join(f"#{p['number']}" for p in merged)
        ok, msg = jira.move_issue(key, target, dry_run=dry_run)
        actions.append(f"{msg}   (merged PR {pr_nums})")

        # Leave visible evidence on the Jira card: PRs + commits with URLs.
        _, cmsg = jira.add_comment(key, evidence_comment(m, target), dry_run=dry_run)
        actions.append(f"     ↳ {cmsg}")

    if not actions:
        actions.append("No merged PRs linked to a ticket. Seed one: a branch/PR "
                       "whose name has a ticket key (e.g. feature/SCRUM-1-login), then merge it.")
    return actions


if __name__ == "__main__":
    import sys
    from pathlib import Path
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).parent.parent / ".env")

    work_items = matcher._SAMPLE if "--sample" in sys.argv else None
    dry = "--apply" not in sys.argv

    print("=== Auto-move merged PRs' tickets to Done ===")
    print("(DRY RUN — nothing changed; pass --apply to move for real)\n" if dry
          else "(APPLYING — this will change your Jira board)\n")
    for line in auto_move_merged(work_items, dry_run=dry):
        print("  " + line)
