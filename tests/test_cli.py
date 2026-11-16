import json
import subprocess
import sys
from pathlib import Path

import pytest

from retail_planner.cli import main


def test_demo_and_analysis_cli_preserve_separate_outputs(tmp_path, monkeypatch, capsys):
    report = tmp_path / "demo"
    exports = tmp_path / "portfolio"
    monkeypatch.setattr(sys, "argv", ["retail-planner", "demo", "--output-dir", str(report)])
    main()
    result = json.loads((report / "results.json").read_text())
    assert result["source"] == "synthetic demonstration"
    assert (report / "run_manifest.json").is_file()
    monkeypatch.setattr(sys, "argv", ["retail-planner", "analyze", "--output-dir", str(report),
                                      "--analysis-dir", str(exports)])
    main()
    assert (exports / "case_study.md").is_file()
    assert (report / "analysis.sqlite").is_file()
    assert "SQL analysis" in capsys.readouterr().out
    script = Path(__file__).resolve().parents[1] / "scripts" / "run_query.py"
    query = subprocess.run([sys.executable, str(script), "store_performance",
                            "--database", str(report / "analysis.sqlite"), "--limit", "1"],
                           check=True, capture_output=True, text=True)
    assert query.stdout.startswith("store_id,series_count,actual_units")
    assert len(query.stdout.splitlines()) == 2


def test_default_analysis_preserves_published_portfolio(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    portfolio = tmp_path / "reports" / "portfolio"
    portfolio.mkdir(parents=True)
    published = portfolio / "case_study.md"
    published.write_text("Published M5 study", encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["retail-planner", "demo"])
    main()
    monkeypatch.setattr(sys, "argv", ["retail-planner", "analyze"])
    main()

    assert (tmp_path / "reports" / "analysis" / "case_study.md").is_file()
    assert (tmp_path / "reports" / "latest" / "analysis.sqlite").is_file()
    assert published.read_text(encoding="utf-8") == "Published M5 study"


def test_missing_report_has_actionable_cli_error(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["retail-planner", "analyze", "--output-dir", str(tmp_path)])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2
    assert "results.json" in capsys.readouterr().err


def test_json_profile_applies_reproducible_defaults(tmp_path, monkeypatch):
    profile = tmp_path / "profile.json"
    profile.write_text(json.dumps({"folds": 2, "rounds": 3, "threads": 1}))
    report = tmp_path / "configured"
    monkeypatch.setattr(sys, "argv", [
        "retail-planner", "demo", "--config", str(profile), "--output-dir", str(report),
    ])

    main()

    result = json.loads((report / "results.json").read_text())
    manifest = json.loads((report / "run_manifest.json").read_text())
    assert len(result["validation_starts"]) == 2
    assert manifest["options"]["config"] == str(profile)
