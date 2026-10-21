# Local evidence dashboard

This is a local, read-only dashboard backed by SQLite. It joins the 100,000 selected nonempty reviews and the 13 empty-text quarantine records with saved labels, memberships, ranking, claims, and the saved memo. The database is generated locally and is ignored by Git.

## Build and open

From the project root in PowerShell:

```powershell
.\.venv\Scripts\python.exe dashboard\build_database.py
.\.venv\Scripts\python.exe dashboard\server.py
```

Open `http://127.0.0.1:8765/`. To rebuild after saved artifacts change, stop the server and run:

```powershell
.\.venv\Scripts\python.exe dashboard\build_database.py --replace
```

The HTTP service defaults to localhost and exposes read-only JSON routes under `/api/`. A localhost smoke check returned HTTP 200 from `/healthz`, `/api/metrics`, `/api/ranking`, `/api/recommendation`, and `/api/evidence`; it returned 100,013 in-scope IDs, 100,000 completed labels, 13 quarantines, 47,245 memberships, and eight ranking buckets. The assignment dataset contains public app reviews; the deployed dashboard is designed for public, read-only grading access. It does not accept writes or contain provider credentials.

## Deployment preparation

`Dockerfile` builds the SQLite database from the saved, tracked results, then copies only that database and the read-only server into the runtime image. `render.yaml` describes a free Render Web Service with `/healthz` as its health check. The service reads the platform `PORT` and binds to `0.0.0.0` in the container.

The SQLite database is a fixed snapshot baked into each image. That suits this read-only assignment dashboard: new results require a new image build and deploy. It avoids paying for a persistent disk or separate database. Render's free web service sleeps after 15 minutes without traffic, and a wake can take about one minute; it is not a production availability guarantee. The service is live at https://spotify-review-insights-e5lu.onrender.com on the free plan.

## Current limits

- The page reports 100,013 in-scope IDs, 100,000 nonempty classifications, and 13 quarantines separately; its metrics link to the full-source ingestion profile and run manifest.
- The self-check remains `review_required`; the UI reports that state.
- The approved 100,000-review Jev grouping and recommendation calls are complete. Their answers and exact state are saved in `grading/ai_grouping.json` and `grading/ai_recommendation.json`; the claim-checked memo is in `grading/memo.md`. Rebuild the database to refresh the dashboard from those saved outputs without provider calls.
- Live service: https://spotify-review-insights-e5lu.onrender.com. The deployed SQLite database contains 100,013 records. `/healthz`, `/api/metrics`, `/api/ranking`, `/api/recommendation`, `/api/evidence?issue_id=topic-usability`, and the dashboard page were verified against the saved calculations and evidence.
