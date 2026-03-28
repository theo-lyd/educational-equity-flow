import json
from pathlib import Path

from src.ingestion.run import run_ingestion


def test_phase04_ingestion_manifest_idempotent(tmp_path):
    source = tmp_path / "raw"
    source.mkdir(parents=True)

    # Minimal shape compatible with statistical CSV parser.
    (source / "sample-B.csv").write_text(
        "title\nmeta\nyear;AGS;region;metric\n2021;11000;Berlin;123\n",
        encoding="iso-8859-1",
    )

    target = tmp_path / "bronze"

    first = run_ingestion(source=str(source), target=str(target))
    assert first["raw_file_count"] == 1
    assert first["processed_file_count"] == 1
    assert first["skipped_file_count"] == 0

    second = run_ingestion(source=str(source), target=str(target))
    assert second["processed_file_count"] == 0
    assert second["skipped_file_count"] == 1

    manifest_path = target / "ingestion_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "sample-B.csv" in manifest["files"]


def test_phase04_ingestion_writes_partitioned_parquet(tmp_path):
    source = tmp_path / "raw"
    source.mkdir(parents=True)
    (source / "sample-B.csv").write_text(
        "title\nmeta\nyear;AGS;region;metric\n2022;09162;München;42\n",
        encoding="iso-8859-1",
    )

    target = tmp_path / "bronze"
    result = run_ingestion(source=str(source), target=str(target), force=True)

    assert result["rows_written"] >= 1
    expected = target / "dataset=sample-B" / "year=2022" / "sample-B.parquet"
    assert expected.exists()

    payload_path = Path("warehouse") / "artifacts" / "ingest_bronze.json"
    assert payload_path.exists()


def test_phase04_reprocess_removes_stale_partitions(tmp_path):
    source = tmp_path / "raw"
    source.mkdir(parents=True)
    sample = source / "sample-B.csv"

    sample.write_text(
        "title\nmeta\nyear;AGS;region;metric\n2022;09162;München;42\n",
        encoding="iso-8859-1",
    )

    target = tmp_path / "bronze"
    first = run_ingestion(source=str(source), target=str(target), force=True)
    assert first["processed_file_count"] == 1
    year_2022 = target / "dataset=sample-B" / "year=2022" / "sample-B.parquet"
    assert year_2022.exists()

    sample.write_text(
        "title\nmeta\nyear;AGS;region;metric\n2023;09162;München;43\n",
        encoding="iso-8859-1",
    )

    second = run_ingestion(source=str(source), target=str(target))
    assert second["processed_file_count"] == 1

    year_2023 = target / "dataset=sample-B" / "year=2023" / "sample-B.parquet"
    assert year_2023.exists()
    assert not year_2022.exists()
