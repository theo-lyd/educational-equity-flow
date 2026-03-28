import json
from pathlib import Path

from src.profiling.profile_raw_sources import run


def test_phase03_profile_outputs_contracts(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    raw_dir = repo_root / "data" / "raw"
    out_dir = tmp_path / "artifacts"

    summary = run(raw_dir=raw_dir, out_dir=out_dir)

    assert summary["profile_count"] >= 8
    assert (out_dir / "schema_snapshots.json").exists()
    assert (out_dir / "source_contracts.json").exists()

    contracts = json.loads((out_dir / "source_contracts.json").read_text(encoding="utf-8"))
    assert "21321-01-01-4-B.xml" in contracts
    assert "21111-02-06-4-B.csv" in contracts

    xml_contract = contracts["21321-01-01-4-B.xml"]
    assert "must_include_time_key" in xml_contract["required_rules"]
