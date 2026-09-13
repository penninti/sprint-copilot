# Sprint Copilot — demo script (rehearsal cheat-sheet)

Private notes for Rohith + Shravani. Judges don't read this — they watch the
live dashboard. Rehearse this twice, same clicks, same order.

## One-liner
> "Every team pays someone to do scrum busywork — chasing updates, moving
> tickets, writing standups. We deleted that job. Watch."

## Before you present (setup — do this once)
- [ ] Dashboard running: `python -m sprint_copilot.web` → http://localhost:5050
- [ ] Three browser tabs open: **Jira board**, **Slack** (#all-sprint-copilot-demo), **dashboard**
- [ ] Slack channel cleared of "please ignore" test messages
- [ ] One ticket (e.g. SCRUM-8) set to **In Progress** with a **merged PR** already existing
- [ ] The red "stuck / at risk" box is showing something
- [ ] Fallback ready: if venue wifi is slow, use **switch to demo** + Run

## The 90-second run

**1. Hook (15s)** — Jira board on screen
> "This is our sprint board. Normally a scrum master moves these tickets,
> spots what's stuck, and writes everyone's standup every morning. We
> automated all of it."

**2. It sees reality (15s)** — dashboard
> "It reads our real GitHub and Jira. Here are the tickets, the commits
> linked to each, and — see the red box — it already flagged stuck work:
> commits exist but the ticket never moved."

**3. THE MOMENT (20s)** — click **Run for real**
> "This PR just merged. I click one button…"
- Flip to **Jira**: "The ticket moved to Done by itself — and left a comment
  with the exact commit and a link to the code."
- Flip to **Slack**: "And it wrote this standup — blockers first, one per
  person. Nobody typed a word of it."

**4. Maturity beat (15s)** — the override
> "AI isn't perfect. If a dev forgets to tag a commit, the agent can't link
> it — so there's a one-click human override to link it or fix a status.
> Automation you can trust."

**5. Close (15s)**
> "Real integrations, real actions, a human in the loop. The scrum master's
> busywork — gone. Next: it updates Notion and cancels the standup meeting
> when there's nothing to say."

## If a judge asks "what's special?"
- **It acts, not reports** — it changes Jira/Slack, not just summarizes.
- **Honest AI** — says "no activity today" instead of inventing work.
- **Human-in-the-loop** — override for links and status; we designed for failure.
- **Real & live** — offer: "want to merge a PR yourself and watch it move?"

## Reset between runs
- Drag the demo ticket back to "In Progress" on the board.
- (Optional) delete the Sprint Copilot comment from the card.

## Commands (backup, if the UI hiccups)
```bash
cd worklog-ai && source venv/bin/activate
python -m sprint_copilot.run --sample --apply   # whole flow on demo data
python -m sprint_copilot.web                     # the dashboard
```
