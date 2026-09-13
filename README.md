# 🤖 Sprint Copilot

**The scrum master, automated.** An agent that watches a team's GitHub & Jira,
moves tickets when work merges, flags what's stuck, writes an honest per-person
standup, and posts it to Slack — every action a real change in the tools the
team already uses.

Built for the Multi-App AI Agent Hackathon by **Rohith Penninti** & **Shravani Joshi**.

---

## What it does

```
GitHub + Jira  →  link commit↔ticket by key  →  move merged tickets to Done (+ comment)
                                              →  flag stuck work
                                              →  write an AI standup  →  post to Slack
```

A developer just tags a commit with the ticket key (e.g. `SCRUM-8`). Sprint
Copilot links it, moves the ticket when the PR merges, leaves the commit link
as a comment on the card, writes the standup, and posts it to Slack. A human
can override any link or status from the dashboard.

## Architecture

| Module | Job |
|---|---|
| `github.py` | read commits & PRs across all branches |
| `jira.py` | read tickets · move them · comment |
| `match.py` | link commit↔ticket by key (+ manual links) |
| `stuck.py` | flag stalled work |
| `standup.py` | write the standup (Azure OpenAI) |
| `slack.py` | post to the channel |
| `automate.py` | auto-move merged tickets + evidence comment |
| `web.py` | live dashboard + human override |
| `run.py` | the whole flow in one command |
| `check_setup.py` | verify all credentials connect |

Stack: Python · Flask · GitHub/Jira/Slack REST · Azure OpenAI.

---

## Run it

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in the values
python -m sprint_copilot.check_setup     # want 4x PASS
python -m sprint_copilot.web             # dashboard at http://localhost:5050
```

`.env` values are documented in `.env.example` (GitHub, Jira, Azure OpenAI,
Slack). The app runs entirely on the tools **you** connect — nothing is hard
-coded to any account.

## Try it without full credentials

No keys needed — proves the core logic on built-in demo data:
```bash
python -m sprint_copilot.match --sample             # commit↔ticket matching
python -m sprint_copilot.standup --digest --sample  # the exact input the AI gets
```
Only an Azure OpenAI key needed:
```bash
python -m sprint_copilot.standup --sample           # the AI-written standup
```

## The dashboard
`python -m sprint_copilot.web` → http://localhost:5050

Shows each ticket with its linked commits/PRs, stuck-work flags, and buttons to
run the whole flow or override any ticket by hand.

## Presentation
- `presentation/index.html` — slide deck (open in a browser, arrow keys)
- `presentation/Sprint_Copilot.pptx` — PowerPoint version
