#!/usr/bin/env python3
"""Fetch a reproducible World Bank indicator snapshot for the explorer."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from catalog import COUNTRIES, INDICATORS  # noqa: E402

BASE_URL = "https://api.worldbank.org/v2"
SCHEMA_VERSION = 1
FIELDS = ("country", "code", "year", "series", "value")
SERIES_CODES = sorted(set(INDICATORS.values()))


def make_session() -> requests.Session:
    retry = Retry(
        total=5,
        connect=3,
        read=3,
        status=4,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update({"User-Agent": "Development-Divergence-Explorer/1.0"})
    return session


def fetch_series(
    session: requests.Session, code: str, country_codes: str, start_year: int, end_year: int
) -> list[dict[str, Any]]:
    url = f"{BASE_URL}/country/{country_codes}/indicator/{code}"
    rows: list[dict[str, Any]] = []
    page = 1
    total_pages = 1
    names = {country_code: country for country, country_code in COUNTRIES.items()}
    while page <= total_pages:
        response = session.get(
            url,
            params={
                "date": f"{start_year}:{end_year}",
                "format": "json",
                "per_page": 20000,
                "page": page,
            },
            timeout=(10, 60),
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list) or not payload or not isinstance(payload[0], dict):
            raise ValueError(f"World Bank returned an unexpected response for {code}.")
        if len(payload) < 2:
            messages = payload[0].get("message", [])
            detail = "; ".join(str(message.get("value", message)) for message in messages) if isinstance(messages, list) else str(messages)
            raise ValueError(f"World Bank did not return observations for {code}: {detail or 'missing response payload'}")
        metadata, observations = payload
        if metadata.get("message"):
            raise ValueError(f"World Bank error for {code}: {metadata['message']}")
        total_pages = int(metadata.get("pages", 1))
        if observations is None:
            observations = []
        if not isinstance(observations, list):
            raise ValueError(f"World Bank returned invalid observations for {code}, page {page}.")
        for observation in observations:
            value = observation.get("value")
            country_code = observation.get("countryiso3code")
            if value is None or country_code not in names:
                continue
            rows.append(
                {
                    "country": names[country_code],
                    "code": country_code,
                    "year": int(observation["date"]),
                    "series": code,
                    "value": float(value),
                }
            )
        page += 1
    return rows


def atomic_write(path: Path, contents: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(handle, "wb") as temporary:
            temporary.write(contents)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temp_name, path)
    except Exception:
        Path(temp_name).unlink(missing_ok=True)
        raise


def write_snapshot(rows: list[dict[str, Any]], output_dir: Path, start_year: int, end_year: int) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "world_bank_manifest.json"

    import io

    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(sorted(rows, key=lambda row: (row["code"], row["series"], row["year"])))
    csv_bytes = buffer.getvalue().encode("utf-8")
    digest = hashlib.sha256(csv_bytes).hexdigest()
    csv_name = f"world_bank_snapshot-{digest}.csv"
    csv_path = output_dir / csv_name
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "World Bank Indicators API",
        "source_url": BASE_URL,
        "snapshot_file": csv_name,
        "start_year": start_year,
        "end_year": end_year,
        "country_codes": list(COUNTRIES.values()),
        "series_codes": SERIES_CODES,
        "record_count": len(rows),
        "record_counts_by_series": {
            code: sum(1 for row in rows if row["series"] == code) for code in SERIES_CODES
        },
        "sha256": digest,
    }
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")

    # The immutable CSV is written first; the manifest is the atomic current-snapshot pointer.
    atomic_write(csv_path, csv_bytes)
    atomic_write(manifest_path, manifest_bytes)
    keep = {csv_name}
    older = sorted(output_dir.glob("world_bank_snapshot-*.csv"), key=lambda path: path.stat().st_mtime, reverse=True)
    keep.update(path.name for path in older[:2])
    for old_snapshot in older:
        if old_snapshot.name not in keep:
            old_snapshot.unlink(missing_ok=True)
    return manifest


def refresh(start_year: int, end_year: int, output_dir: Path) -> dict[str, Any]:
    session = make_session()
    codes = ";".join(COUNTRIES.values())
    rows: list[dict[str, Any]] = []
    for index, series_code in enumerate(SERIES_CODES, start=1):
        print(f"[{index}/{len(SERIES_CODES)}] Fetching {series_code}", flush=True)
        rows.extend(fetch_series(session, series_code, codes, start_year, end_year))
    if not rows:
        raise ValueError("World Bank returned no observed values; existing snapshot was not changed.")
    return write_snapshot(rows, output_dir, start_year, end_year)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-year", type=int, default=1960)
    parser.add_argument("--end-year", type=int, default=datetime.now(timezone.utc).year)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data")
    args = parser.parse_args()
    if args.start_year < 1960 or args.end_year < args.start_year:
        parser.error("years must satisfy 1960 <= start-year <= end-year")
    try:
        manifest = refresh(args.start_year, args.end_year, args.output_dir)
    except (requests.RequestException, ValueError, KeyError, OSError) as error:
        print(f"Refresh failed; existing snapshot was not intentionally replaced: {error}", file=sys.stderr)
        return 1
    print(
        f"Wrote {manifest['record_count']:,} observations to {args.output_dir.resolve()} "
        f"(sha256 {manifest['sha256']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
