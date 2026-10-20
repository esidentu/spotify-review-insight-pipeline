# Local evidence dashboard

This is a local, read-only dashboard backed by SQLite. It joins the selected input text with saved labels, memberships, ranking, claims, and the saved memo. The database is generated locally and is ignored by Git.

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

The HTTP service defaults to localhost and exposes read-only JSON routes under `/api/`. It has no authentication and is intended for local inspection. Do not expose it publicly as-is.

## Current limits

- The page reports 100,000 selected records; its metrics link to the full-source ingestion profile and run manifest.
- The self-check remains `review_required`; the UI reports that state.
- The recommendation is read from the saved local-template memo. It is clearly labeled as not model-generated. The assignment's AI-generated recommendation requirement remains open until a separately logged memo-role call is made and reviewed.
- This is not deployed. A public deployment still needs a hosting target, secure database, access policy, deployment, and live verification. Do not put provider keys in the browser or this application.
