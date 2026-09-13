# 🤖 Sprint Copilot

**The scrum master, automated.** Sprint Copilot is an AI agent that watches a
dev team's GitHub and Jira, moves tickets when work merges, flags what's
stuck, writes an honest daily standup, and posts it to Slack — so nobody has
to do the coordination busywork by hand.

Built for the **Multi-App AI Agent Hackathon** by **Rohith Penninti** & **Shravani Joshi**.

---

## ▶️ Demo & presentation (start here)

- **🎬 Watch the demo video:** https://drive.google.com/drive/folders/1Hhy6s_ScVtAyhebdWioe6N-gGhJBD160?usp=sharing
- **📊 Slides:** `presentation/index.html` (open in a browser — arrow keys to navigate)
- **📑 PowerPoint:** `presentation/Sprint_Copilot.pptx`

---

## 🔌 External apps & APIs we integrated

Sprint Copilot is a **multi-app agent** — it reads from and writes to four
external services through their official APIs:

| App / Service | What we use it for | How it's integrated |
|---|---|---|
| **GitHub** | Read commits, pull requests & branches (the actual work) | GitHub REST API |
| **Jira (Atlassian)** | Read sprint tickets, **move them to Done**, and **comment** on cards | Jira Cloud REST API v3 |
| **Azure OpenAI** | Write the honest, per-person standup from the activity | Azure OpenAI (chat completions) |
| **Slack** | Post the daily standup to the team channel | Slack Incoming Webhooks |

Everything runs on the tools *you* connect via `.env` — nothing is hard-coded
to any account.

---

## What it does — the flow, step by step

```
GitHub + Jira  →  match commit↔ticket by key  →  move merged tickets to Done (+comment)
                                              →  flag stuck work
                                              →  write an AI standup  →  post to Slack
```

1. **Read GitHub** — pulls recent commits & PRs across all branches.
2. **Read Jira** — pulls every ticket across every project (auto-discovered).
3. **Match** — links a commit/PR to a ticket by the ticket key in the branch,
   commit message, or PR title (e.g. `SCRUM-8`).
4. **Act** — when a ticket's PR is merged, it **moves the ticket to Done** and
   **posts a comment** on the card with the PR and commit links.
5. **Flag stuck work** — tickets that have commits but never moved, or PRs open
   too long.
6. **Write the standup** — Azure OpenAI turns the activity into a short,
   honest per-person standup (blockers first; says "no activity" instead of
   inventing work).
7. **Post to Slack** — drops the standup into the team channel.

A **human can override** any link or status from the dashboard, for when the
automatic matching gets something wrong.

---

## How to run it (step by step)

### 1. Install
```bash
git clone https://github.com/penninti/sprint-copilot.git
cd sprint-copilot
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure the four services
```bash
cp .env.example .env      # then fill in the values
```
| Variable | Where to get it |
|---|---|
| `GITHUB_TOKEN`, `GITHUB_REPO` | GitHub token (`gh auth token` or a PAT) + `owner/repo` |
| `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN` | Your Jira site + an API token (id.atlassian.com → API tokens) |
| `JIRA_PROJECT` | `ALL` (every project) or specific keys like `SCRUM,JRVIS20` |
| `AZURE_OPENAI_ENDPOINT`, `_API_KEY`, `_DEPLOYMENT`, `_API_VERSION` | Your Azure OpenAI resource |
| `SLACK_WEBHOOK_URL` | Slack app → Incoming Webhooks |

### 3. Verify all four connect
```bash
python -m sprint_copilot.check_setup
```
You should see **4× PASS** (GitHub, Jira, Azure OpenAI, Slack).

### 4. Run it
```bash
python -m sprint_copilot.web       # open the dashboard → http://localhost:5050
python -m sprint_copilot.run       # run the whole flow (posts standup to Slack)
python -m sprint_copilot.run --apply   # also move merged tickets on the board
```

---

## Evaluating it without our credentials

Judges can prove the core logic with **no keys at all** (built-in demo data):
```bash
python -m sprint_copilot.match --sample             # commit↔ticket matching
python -m sprint_copilot.standup --digest --sample  # exactly what the AI receives
```
With only an **Azure OpenAI** key, see the AI-written standup:
```bash
python -m sprint_copilot.standup --sample
```
The full live flow (moving real tickets, posting to Slack) uses your own
GitHub / Jira / Slack / Azure credentials in `.env`.

## What "working" looks like
- `check_setup` → 4 PASS
- Dashboard shows real tickets with their linked commits/PRs and a red **stuck** flag
- Click **Run for real** → a merged PR's ticket moves to Done, gets a comment
  with the commit link, and an honest standup posts to Slack

---

## Architecture

| Module | Job |
|---|---|
| `github.py` | read commits & PRs across all branches (GitHub API) |
| `jira.py` | read all projects · move tickets · comment (Jira API) |
| `match.py` | link commit↔ticket by key (+ manual links) |
| `stuck.py` | flag stalled work |
| `standup.py` | write the standup (Azure OpenAI) |
| `slack.py` | post to the channel (Slack webhook) |
| `automate.py` | auto-move merged tickets + evidence comment |
| `web.py` | live dashboard + human override |
| `run.py` | the whole flow in one command |
| `check_setup.py` | verify all four services connect |

**Stack:** Python · Flask · GitHub / Jira / Slack REST APIs · Azure OpenAI.

---

*Demo video, slides, and PowerPoint are linked at the top ↑*
