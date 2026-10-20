#!/usr/bin/env python3
"""Serve the local dashboard and read-only JSON API from the SQLite evidence database."""

from __future__ import annotations

import argparse
import json
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "dashboard" / "spotify.sqlite3"

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Spotify review analysis</title><style>
body{font:16px/1.5 system-ui,sans-serif;max-width:1120px;margin:2rem auto;padding:0 1rem;color:#18212b;background:#f5f7f9}
h1,h2{line-height:1.2}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:1rem}.card,section{background:white;border:1px solid #d9e0e7;border-radius:10px;padding:1rem;margin:1rem 0}.value{font-size:1.6rem;font-weight:700}small,.muted{color:#526170}table{width:100%;border-collapse:collapse;background:white}th,td{text-align:left;padding:.65rem;border-bottom:1px solid #e2e7eb}button{padding:.45rem .7rem;cursor:pointer}#evidence li{margin:.8rem 0}.badge{font-size:.85rem;background:#fff3cd;padding:.2rem .45rem;border-radius:5px}
</style></head><body>
<h1>Spotify review analysis</h1><p class="muted">Evidence dashboard for the selected 100,000-review run. This local app reads processed records and aggregates from SQLite.</p>
<p><span class="badge" id="check">Loading audit status…</span> <span class="muted" id="scope"></span></p>
<div class="grid" id="metrics"></div>
<section><h2>Issue ranking</h2><table><thead><tr><th>Rank</th><th>Issue</th><th>Complaint/cancellation reviews</th><th>Mean severity</th><th>Priority score</th><th></th></tr></thead><tbody id="ranking"></tbody></table></section>
<section><h2>Recommendation</h2><p class="muted" id="rec-origin"></p><pre id="recommendation" style="white-space:pre-wrap;font:inherit"></pre></section>
<section><h2>Supporting review evidence</h2><p class="muted">Choose an issue above to load source reviews and labels from the database.</p><ul id="evidence"></ul></section>
<script>
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function load(){
 const m=await (await fetch('/api/metrics')).json();
 document.querySelector('#check').textContent=`Self-check: ${m.self_check_status} · ${m.completed.toLocaleString()}/${m.expected.toLocaleString()} classified`;
 document.querySelector('#scope').textContent=`Run ${m.pipeline_run_id} · source SHA-256 ${m.source_file_sha256}`;
 document.querySelector('#metrics').innerHTML=[['Source rows',m.source_rows],['Selected rows',m.expected],['Completed labels',m.completed],['Needs review',m.needs_review],['Complaint memberships',m.memberships],['Issue buckets',m.issue_count]].map(([k,v])=>`<div class="card"><div>${k}</div><div class="value">${Number(v).toLocaleString()}</div></div>`).join('');
 const ranking=await (await fetch('/api/ranking')).json();
 document.querySelector('#ranking').innerHTML=ranking.map(x=>`<tr><td>${x.rank}</td><td>${esc(x.issue_id)}</td><td>${Number(x.complaint_count).toLocaleString()}</td><td>${esc(x.mean_severity)}</td><td>${Number(x.priority_score).toLocaleString()}</td><td><button data-issue="${esc(x.issue_id)}">Evidence</button></td></tr>`).join('');
 const rec=await (await fetch('/api/recommendation')).json();document.querySelector('#rec-origin').textContent=rec.origin;document.querySelector('#recommendation').textContent=rec.markdown;
 document.querySelectorAll('[data-issue]').forEach(b=>b.onclick=()=>evidence(b.dataset.issue));
}
async function evidence(issue){const rows=await (await fetch('/api/evidence?issue_id='+encodeURIComponent(issue))).json();document.querySelector('#evidence').innerHTML=rows.map(r=>`<li><b>${esc(r.review_id)}</b> · ${esc(r.topic)} / ${esc(r.intent)} · severity ${r.severity}<br>${esc(r.review_text)}</li>`).join('')||'<li>No examples found.</li>';}
load().catch(e=>{document.querySelector('#check').textContent='Dashboard data error: '+e;});
</script></body></html>"""


def handler_for(db_path: Path):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            print("dashboard:", fmt % args)

        def send_json(self, value, code=200):
            body = json.dumps(value, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            parsed = urlparse(self.path)
            con = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
            con.row_factory = sqlite3.Row
            try:
                if parsed.path == "/":
                    body = PAGE.encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                elif parsed.path == "/api/metrics":
                    q = con.execute("""SELECT COUNT(*) total,
                        SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) completed,
                        SUM(CASE WHEN needs_review=1 THEN 1 ELSE 0 END) needs_review
                        FROM reviews""").fetchone()
                    meta = dict(con.execute("SELECT key,value FROM metadata"))
                    self.send_json({
                        "source_rows": int(meta["source_rows"]), "expected": int(meta["analysis_count"]),
                        "completed": int(q["completed"] or 0), "needs_review": int(q["needs_review"] or 0),
                        "memberships": con.execute("SELECT COUNT(*) FROM issue_membership").fetchone()[0],
                        "issue_count": con.execute("SELECT COUNT(*) FROM ranking").fetchone()[0],
                        "pipeline_run_id": meta["pipeline_run_id"], "source_file_sha256": meta["source_file_sha256"],
                        "self_check_status": meta["self_check_status"],
                    })
                elif parsed.path == "/api/ranking":
                    self.send_json([dict(row) for row in con.execute("SELECT * FROM ranking ORDER BY rank")])
                elif parsed.path == "/api/recommendation":
                    meta = dict(con.execute("SELECT key,value FROM metadata"))
                    self.send_json({"origin": meta["recommendation_origin"], "markdown": meta["recommendation_markdown"]})
                elif parsed.path == "/api/evidence":
                    issue_id = parse_qs(parsed.query).get("issue_id", [""])[0]
                    rows = con.execute("""SELECT r.review_id,r.review_text,r.topic,r.intent,r.severity
                        FROM issue_membership m JOIN reviews r USING(review_id)
                        WHERE m.issue_id=? ORDER BY r.severity DESC,r.review_id LIMIT 20""", (issue_id,))
                    self.send_json([dict(row) for row in rows])
                else:
                    self.send_json({"error": "not found"}, 404)
            except sqlite3.Error as exc:
                self.send_json({"error": str(exc)}, 500)
            finally:
                con.close()

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DB)
    parser.add_argument("--host", default="127.0.0.1", help="defaults to localhost; use 0.0.0.0 only behind a configured deployment proxy")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    db_path = args.database.resolve()
    if not db_path.is_file():
        raise SystemExit(f"Database not found: {db_path}. First run dashboard/build_database.py.")
    server = ThreadingHTTPServer((args.host, args.port), handler_for(db_path))
    print(f"Serving local dashboard at http://{args.host}:{args.port}/ (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
