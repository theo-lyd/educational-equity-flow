from src.ingestion.run import run_smoke
from src.tools.dbt_runner import run_dbt


def test_ingestion_smoke_creates_output(tmp_path):
    source = tmp_path / "raw"
    source.mkdir()
    (source / "sample.csv").write_text("a,b\n1,2\n", encoding="utf-8")

    target = tmp_path / "bronze"
    result = run_smoke(source=str(source), target=str(target))

    assert result["raw_file_count"] == 1
    assert target.exists()


def test_dbt_runner_skips_missing_project(tmp_path):
    missing = tmp_path / "missing_dbt"
    code = run_dbt(command="run", dbt_dir=str(missing))
    assert code == 0
