import json
from pathlib import Path
import shutil
from datetime import datetime, timedelta, timezone

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]


def test_app_loads_the_checksum_verified_world_bank_snapshot(monkeypatch):
    monkeypatch.delenv("DDE_SNAPSHOT_DIR", raising=False)
    manifest = json.loads((ROOT / "data" / "world_bank_manifest.json").read_text(encoding="utf-8"))
    assert (ROOT / "data" / manifest["snapshot_file"]).exists()
    app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=60)
    source = next(widget for widget in app.selectbox if widget.label == "Data source")

    source.set_value("World Bank downloaded snapshot").run(timeout=60)

    assert not app.exception
    captions = " ".join(element.value for element in app.caption)
    assert f"World Bank snapshot · {manifest['retrieved_at'][:10]}" in captions
    assert not any("could not be loaded" in element.value for element in app.warning)


def test_app_keeps_using_a_verified_but_stale_snapshot(tmp_path, monkeypatch):
    source_manifest_path = ROOT / "data" / "world_bank_manifest.json"
    manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    snapshot_name = manifest["snapshot_file"]
    shutil.copyfile(ROOT / "data" / snapshot_name, tmp_path / snapshot_name)
    manifest["retrieved_at"] = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat(timespec="seconds")
    (tmp_path / "world_bank_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setenv("DDE_SNAPSHOT_DIR", str(tmp_path))

    app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=60)
    source = next(widget for widget in app.selectbox if widget.label == "Data source")
    source.set_value("World Bank downloaded snapshot").run(timeout=60)

    assert not app.exception
    captions = " ".join(element.value for element in app.caption)
    warnings = " ".join(element.value for element in app.warning)
    assert "World Bank snapshot ·" in captions
    assert "60 days old" in warnings
    assert "verified data is still in use" in warnings
