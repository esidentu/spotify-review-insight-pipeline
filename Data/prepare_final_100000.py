"""Create the deterministic 100,000-review final-run input, without API calls.

The sample contains the 100,000 eligible source rows with the lowest
SHA-256(seed + ':' + review_id) ranks. It includes the Golden 50 review texts;
their expected labels are never added to this input.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import heapq
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = Path(__file__).resolve().parent
SEED = "berkeley-fall-2026-assignment-5-v1"
FIELDS = ["review_id", "review_text", "review_rating", "review_likes", "app_version", "review_timestamp"]
TARGET = 100_000


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DATA / "spotify_reviews_18months.csv")
    parser.add_argument("--out", type=Path, default=DATA / "final_100000.csv")
    args = parser.parse_args()
    source = args.source.resolve()
    out = args.out.resolve()
    manifest_path = DATA / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_source = manifest["files"]["spotify_reviews_18months.csv"]["sha256"]
    actual_source = sha256_file(source)
    if actual_source != expected_source:
        raise SystemExit("Source CSV checksum does not match Data/manifest.json")

    # Keep the TARGET lowest deterministic ranks in O(TARGET) memory.
    heap: list[tuple[int, str, dict[str, str]]] = []
    seen_ids: set[str] = set()
    with source.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not set(FIELDS).issubset(reader.fieldnames or []):
            raise SystemExit("Source CSV does not have the expected six columns")
        for row in reader:
            review_id = row["review_id"]
            text = row["review_text"]
            if not review_id or review_id in seen_ids:
                if review_id in seen_ids:
                    raise SystemExit(f"Duplicate source review ID: {review_id}")
                continue
            seen_ids.add(review_id)
            if not text.strip() or row["review_rating"] not in {"1", "2", "3", "4", "5"}:
                continue
            rank = int.from_bytes(hashlib.sha256(f"{SEED}:{review_id}".encode("utf-8")).digest(), "big")
            item = (-rank, review_id, {field: row[field] for field in FIELDS})
            if len(heap) < TARGET:
                heapq.heappush(heap, item)
            elif rank < -heap[0][0]:
                heapq.heapreplace(heap, item)

    if len(heap) != TARGET:
        raise SystemExit(f"Found {len(heap)} eligible reviews; expected {TARGET}")
    selected = [item[2] for item in sorted(heap, key=lambda item: (-item[0], item[1]))]
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(selected)

    entry = {"bytes": out.stat().st_size, "sha256": sha256_file(out)}
    manifest.setdefault("files", {})[out.name] = entry
    manifest.setdefault("samples", {})["final_100000"] = (
        "100,000 eligible source reviews with the lowest SHA-256(seed + ':' + review_id) ranks; "
        "includes Golden 50 review texts, but never their expected labels."
    )
    manifest["assignment_scope"]["selected_final_rows"] = TARGET
    manifest["assignment_scope"]["selected_final_input"] = out.name
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(selected), "source_sha256": actual_source, "output": str(out), **entry}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
