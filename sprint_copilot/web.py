"""
web.py — a browser dashboard for Sprint Copilot.

Instead of reading the terminal, open a web page that shows:
  - the sprint tickets and their status
  - which commits/PRs are linked to each ticket
  - what looks stuck
  - a "Run Sprint Copilot" button that moves merged tickets, comments on
    them, writes the standup, and posts it to Slack — and shows the result.

Run:   python -m sprint_copilot.web
Open:  http://localhost:5000            (real GitHub/Jira data)
       http://localhost:5000/?sample=1  (demo data — safe to click Run)

To let others open it, expose it with a tunnel (see README) or deploy it.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, render_template_string, request, jsonify

load_dotenv(Path(__file__).parent.parent / ".env")

from sprint_copilot import match as matcher, jira
from sprint_copilot.stuck import find_stuck
from sprint_copilot.standup import generate_standup
from sprint_copilot.automate import auto_move_merged, evidence_comment
from sprint_copilot.slack import post_message
from datetime import date

app = Flask(__name__)

PAGE = """
<!doctype html>
<html><head><meta charset="utf-8"><title>Sprint Copilot</title>
<style>
  body { font-family: -apple-system, system-ui, sans-serif; background:#0d1117; color:#e6edf3; margin:0; padding:24px; }
  h1 { margin:0 0 4px; } .sub { color:#8b949e; margin-bottom:20px; }
  .grid { display:grid; grid-template-columns: 1fr 1fr; gap:20px; }
  .card { background:#161b22; border:1px solid #30363d; border-radius:10px; padding:16px; margin-bottom:20px; }
  .card h2 { margin:0 0 12px; font-size:15px; color:#8b949e; text-transform:uppercase; letter-spacing:.05em; }
  .ticket { border:1px solid #30363d; border-radius:8px; padding:10px 12px; margin-bottom:10px; }
  .key { font-weight:700; color:#58a6ff; }
  .status { font-size:12px; padding:2px 8px; border-radius:12px; margin-left:6px; }
  .todo { background:#21262d; color:#8b949e; } .prog { background:#1c2a3f; color:#58a6ff; } .done { background:#0d3320; color:#3fb950; }
  .link { font-size:12px; color:#8b949e; margin-top:6px; padding-left:10px; border-left:2px solid #30363d; }
  .stuck { background:#3a1d1d; border:1px solid #f85149; border-radius:8px; padding:10px 12px; margin-bottom:8px; color:#ffa198; }
  .btn { background:#238636; color:#fff; border:0; padding:12px 20px; border-radius:8px; font-size:15px; cursor:pointer; }
  .btn.dry { background:#1f6feb; }
  pre { white-space:pre-wrap; background:#0d1117; border:1px solid #30363d; padding:12px; border-radius:8px; font-size:13px; }
  .muted { color:#6e7681; font-size:12px; }
  a { color:#58a6ff; }
  .pitch { background:linear-gradient(90deg,#1c2a3f,#161b22); border:1px solid #30363d; border-radius:10px; padding:16px 20px; margin-bottom:22px; }
  .pitch-line { font-size:19px; font-weight:700; color:#e6edf3; margin-bottom:8px; }
  .pitch-flow { font-size:13px; color:#8b949e; line-height:1.6; }
  .pitch-flow b { color:#58a6ff; }
  .editrow { margin-top:8px; }
  .editrow select { background:#0d1117; color:#e6edf3; border:1px solid #30363d; border-radius:6px; padding:3px 6px; }
  .setbtn { background:#30363d; color:#e6edf3; border:0; border-radius:6px; padding:4px 10px; margin-left:4px; cursor:pointer; }
</style></head><body>
  <h1>🤖 Sprint Copilot</h1>
  <div class="sub">Repo: {{ repo }} &nbsp;·&nbsp; {{ 'DEMO DATA' if sample else 'live GitHub + Jira' }}
     &nbsp;·&nbsp; <a href="/?sample={{ 0 if sample else 1 }}">switch to {{ 'live' if sample else 'demo' }}</a></div>

  <div class="pitch">
    <div class="pitch-line">Your team's scrum-master busywork — automated.</div>
    <div class="pitch-flow">Reads <b>GitHub</b> + <b>Jira</b> → links commits to tickets by key →
      auto-moves merged tickets to <b>Done</b> (leaving a comment with the commit link) →
      writes an honest per-person <b>standup</b> → posts it to <b>Slack</b>.
      Spots stuck work, and a human can override any link or status.</div>
  </div>

  {% if stuck %}
  <div class="card">
    <h2>⚠️ Stuck / at risk</h2>
    {% for s in stuck %}<div class="stuck">{{ s }}</div>{% endfor %}
  </div>
  {% endif %}

  <div class="grid">
    <div class="card">
      <h2>Tickets & linked work</h2>
      {% for t in tickets %}
      <div class="ticket">
        <span class="key">{{ t.key }}</span>
        <span class="status {{ t.cls }}">{{ t.status }}</span>
        &nbsp; {{ t.title }} <span class="muted">— {{ t.assignee }}</span>
        {% for l in t.links %}<div class="link">{{ l }}</div>{% endfor %}
        {% if not t.links %}<div class="link muted">no linked commits/PRs</div>{% endif %}
        <div class="editrow">
          <select id="sel-{{ t.key }}">
            {% for s in ['To Do','In Progress','In Review','Done'] %}
            <option {{ 'selected' if t.status==s else '' }}>{{ s }}</option>
            {% endfor %}
          </select>
          <button class="setbtn" onclick="move('{{ t.key }}')">Set status</button>
          <span id="msg-{{ t.key }}" class="muted"></span>
        </div>
      </div>
      {% endfor %}
    </div>

    <div>
    <div class="card">
      <h2>Unlinked commits <span class="muted">— agent couldn't match these</span></h2>
      {% for c in unmatched %}
      <div class="ticket">
        <span class="muted">{{ c.short_hash }}</span> {{ c.message.split('\n')[0][:60] }}
        <div class="editrow">
          → <select id="lnk-{{ c.hash }}">{% for k in keys %}<option>{{ k }}</option>{% endfor %}</select>
          <button class="setbtn" onclick="link('{{ c.hash }}')">Link to ticket</button>
          <span id="lmsg-{{ c.hash }}" class="muted"></span>
        </div>
      </div>
      {% endfor %}
      {% if not unmatched %}<div class="muted">All commits are linked.</div>{% endif %}
    </div>
    <div class="card">
      <h2>Run</h2>
      <p class="muted">Reads GitHub + Jira → moves merged tickets to Done (+ comments) → writes standup → posts to Slack.</p>
      <button class="btn dry" onclick="run(false)">Preview (dry run)</button>
      <button class="btn" onclick="run(true)">Run for real ▶</button>
      <div id="out"></div>
    </div>
    </div>
  </div>

<script>
async function link(hash) {
  const sel = document.getElementById('lnk-' + hash);
  const msg = document.getElementById('lmsg-' + hash);
  msg.textContent = ' …';
  const r = await fetch('/link', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({commit: hash, ticket: sel.value})});
  const d = await r.json();
  msg.textContent = ' ' + d.msg;
}
async function move(key) {
  const sel = document.getElementById('sel-' + key);
  const msg = document.getElementById('msg-' + key);
  msg.textContent = ' …';
  const r = await fetch('/move', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({key: key, status: sel.value})});
  const d = await r.json();
  msg.textContent = ' ' + d.msg;
}
async function run(apply) {
  const out = document.getElementById('out');
  out.innerHTML = '<p class="muted">Working…</p>';
  const r = await fetch('/run', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({apply: apply, sample: {{ 'true' if sample else 'false' }} })});
  const d = await r.json();
  let html = '<h2 style="margin-top:16px">Actions</h2><pre>' + d.actions.join('\\n') + '</pre>';
  html += '<h2>Standup' + (apply ? ' (posted to Slack ✅)' : '') + '</h2><pre>' + d.standup + '</pre>';
  out.innerHTML = html;
}
</script>
</body></html>
"""

_CLS = {"to do": "todo", "in progress": "prog", "done": "done"}


def _view(sample: bool):
    wi = matcher._SAMPLE if sample else matcher.build_work_items()
    matched = matcher.match(wi)
    stuck = find_stuck(matched, wi)
    tickets = []
    for key, m in matched["matched"].items():
        t = m["ticket"]
        links = []
        for p in m["prs"]:
            links.append(f"PR #{p['number']} [{p['state']}] {p['title']}")
        for c in m["commits"]:
            links.append(f"commit {c['short_hash']} {c['message'].splitlines()[0][:60]}")
        for b in m["branches"]:
            links.append(f"branch {b}")
        tickets.append({
            "key": key, "title": t["title"], "status": t["status"],
            "assignee": t.get("assignee", ""), "links": links,
            "cls": _CLS.get(t["status"].lower(), "todo"),
        })
    keys = list(matched["matched"].keys())
    unmatched = matched["unmatched_commits"][:20]
    return wi, tickets, stuck, unmatched, keys


@app.route("/")
def dashboard():
    sample = request.args.get("sample") == "1"
    wi, tickets, stuck, unmatched, keys = _view(sample)
    return render_template_string(PAGE, repo=wi["repo"], tickets=tickets, stuck=stuck,
                                  sample=sample, unmatched=unmatched, keys=keys)


@app.route("/link", methods=["POST"])
def link():
    """Manually link an unmatched commit to a ticket (persisted), for when
    the developer forgot to put the ticket key in the commit."""
    data = request.get_json(force=True)
    matcher.save_manual_link(data["commit"], data["ticket"])
    return jsonify({"ok": True, "msg": f"linked to {data['ticket']} — reload to see it under the ticket"})


@app.route("/move", methods=["POST"])
def move():
    """Manual override — set a ticket's status by hand from the UI, for when
    the automatic matching gets it wrong. Also leaves a comment on the card
    so there's an evidence trail (same as the auto-move)."""
    data = request.get_json(force=True)
    key, status = data["key"], data["status"]
    ok, msg = jira.move_issue(key, status, dry_run=False)
    if ok:
        try:
            # Match against live data so the comment cites this ticket's real
            # linked commits/PRs (with URLs), not just manual links.
            matched = matcher.match(matcher.build_work_items())
            m = matched["matched"].get(key, {"prs": [], "commits": []})
            jira.add_comment(key, evidence_comment(m, status), dry_run=False)
            msg += " + comment"
        except Exception as exc:
            msg += f" (comment failed: {exc})"
    return jsonify({"ok": ok, "msg": msg})


@app.route("/run", methods=["POST"])
def run():
    data = request.get_json(force=True)
    apply = bool(data.get("apply"))
    sample = bool(data.get("sample"))
    wi = matcher._SAMPLE if sample else matcher.build_work_items()
    actions = auto_move_merged(wi, dry_run=not apply)
    fresh = matcher._SAMPLE if sample else matcher.build_work_items()
    standup, _ = generate_standup(fresh)
    if apply:
        header = f":sunrise: *Sprint Copilot — Daily Standup ({date.today().isoformat()})*\n\n"
        post_message(header + standup)
    return jsonify({"actions": actions, "standup": standup})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))  # 5000 is taken by AirPlay on macOS
    print(f"Sprint Copilot dashboard → http://localhost:{port}  (add /?sample=1 for demo data)")
    app.run(host="0.0.0.0", port=port, debug=False)
