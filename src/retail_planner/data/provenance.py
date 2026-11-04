"""Record input checksums, run configuration, and package versions."""

from __future__ import annotations

import hashlib
import json
import platform
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def fingerprint(path: Path) -> dict:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return {"bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def environment() -> dict:
    versions = {}
    for package in ("retail-demand-planner", "numpy", "lightgbm", "fastapi"):
        try:
            versions[package] = version(package)
        except PackageNotFoundError:
            versions[package] = None
    return {"python": platform.python_version(), "packages": versions}


def write_run_manifest(data_dir: Path, output_dir: Path, options: dict) -> None:
    """Write provenance for a newly completed study."""
    result = json.loads((output_dir / "results.json").read_text(encoding="utf-8"))
    files = ("sales_train_evaluation.csv", "calendar.csv", "sell_prices.csv")
    manifest = {
        "schema_version": 1,
        "kind": "recorded_at_run_completion",
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": environment(),
        "options": {key: str(value) if isinstance(value, Path) else value
                    for key, value in options.items()},
        "sampling_seed": 13,
        "selected_series_sha256": hashlib.sha256(
            "\n".join(sorted(row["id"] for row in result["series"])).encode()
        ).hexdigest(),
        "inputs": {name: fingerprint(data_dir / name) for name in files},
        "results": fingerprint(output_dir / "results.json"),
    }
    (output_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
