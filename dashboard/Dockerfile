FROM python:3.12-slim AS database-build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

COPY dashboard/build_database.py dashboard/build_database.py
COPY Data/final_scope_100000_plus_empty.csv Data/final_scope_100000_plus_empty.csv
COPY grading/records.jsonl grading/records.jsonl
COPY grading/membership.csv grading/membership.csv
COPY grading/ranking.csv grading/ranking.csv
COPY grading/claims.csv grading/claims.csv
COPY grading/memo.md grading/memo.md
COPY grading/ai_grouping.json grading/ai_grouping.json
COPY grading/ai_recommendation.json grading/ai_recommendation.json
COPY grading/run.json grading/run.json
COPY grading/ingestion.json grading/ingestion.json
COPY grading-self-check.json grading-self-check.json

RUN python dashboard/build_database.py --database /app/spotify.sqlite3

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY dashboard/server.py dashboard/server.py
COPY --from=database-build /app/spotify.sqlite3 /app/spotify.sqlite3

EXPOSE 8765
CMD python dashboard/server.py --database /app/spotify.sqlite3 --host 0.0.0.0 --port "${PORT:-8765}"
