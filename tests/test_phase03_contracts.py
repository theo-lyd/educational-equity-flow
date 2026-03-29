import json

from openpyxl import Workbook

from src.profiling.profile_raw_sources import run


def test_phase03_profile_outputs_contracts(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    out_dir = tmp_path / "artifacts"

    csv_body = "AGS;JAHR;WERT\n01001;2023;100\n01002;2024;120\n"
    for name in [
        "21111-02-06-4-B.csv",
        "21111-02-06-4.csv",
        "21311-01-01-4-B.csv",
        "21321-01-01-4_flat.csv",
    ]:
        (raw_dir / name).write_text(csv_body, encoding="utf-8")

    for name in ["21111-01-03-4.xlsx", "21311-01-01-4.xlsx"]:
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(["AGS", "JAHR", "WERT"])
        sheet.append(["01001", "2023", 100])
        sheet.append(["01002", "2024", 120])
        workbook.save(raw_dir / name)

    xml_body = (
        '<ROOT><VARIABLE NAME="JAHR"/><AXIS VARIABLE="JAHR"/>'
        '<VALUE QUALITY="ok" COORDINATE="2023"/></ROOT>'
    )
    for name in ["21321-01-01-4-B.xml", "dummy.xml"]:
        (raw_dir / name).write_text(xml_body, encoding="utf-8")

    summary = run(raw_dir=raw_dir, out_dir=out_dir)

    assert summary["profile_count"] >= 8
    assert (out_dir / "schema_snapshots.json").exists()
    assert (out_dir / "source_contracts.json").exists()

    contracts = json.loads((out_dir / "source_contracts.json").read_text(encoding="utf-8"))
    assert "21321-01-01-4-B.xml" in contracts
    assert "21111-02-06-4-B.csv" in contracts

    xml_contract = contracts["21321-01-01-4-B.xml"]
    assert "must_include_time_key" in xml_contract["required_rules"]
