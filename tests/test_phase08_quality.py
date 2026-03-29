from __future__ import annotations

import json
from pathlib import Path

import duckdb

from src.quality.run_checks import QualityThresholds, run_quality_checks


def _seed_quality_tables(db_path: Path) -> None:
    con = duckdb.connect(str(db_path))

    con.execute(
        """
        create table gold_transition_rates as
        select * from (values
            ('01001','A',2022,2023,2024,2024,2023,100.0,90.0,80.0,70.0,60.0,0.9,0.89,0.88,0.86,0.6,0.61),
            ('01002','B',2022,2023,2024,2024,2023,90.0,80.0,70.0,60.0,50.0,0.88,0.87,0.86,0.85,0.55,0.56)
        ) t(
            ags,region,stage_1_year,stage_2_year,stage_3_year,stage_4_year,stage_5_year,
            stage_1_students,stage_2_students,stage_3_graduates,stage_4_university_students,
            stage_5_degree_completions,transition_rate_1_to_2,transition_rate_2_to_3,
            transition_rate_3_to_4,transition_rate_4_to_5,end_to_end_completion_rate,
            compounded_transition_rate
        )
        """
    )

    con.execute(
        """
        create table int_district_current as
        select * from (values
            ('01001','A',2024),
            ('01002','B',2024)
        ) t(ags, region, latest_year)
        """
    )

    con.execute(
        """
        create table gold_stage_funnel as
        select * from (values
            ('01001','A',2022,2023,2024,2024,2023,100.0,90.0,80.0,70.0,60.0,0.9,0.89,0.88,0.86),
            ('01002','B',2022,2023,2024,2024,2023,90.0,80.0,70.0,60.0,50.0,0.88,0.87,0.86,0.85)
        ) t(
            ags,region,stage_1_year,stage_2_year,stage_3_year,stage_4_year,stage_5_year,
            stage_1_students,stage_2_students,stage_3_graduates,stage_4_university_students,
            stage_5_degree_completions,transition_rate_1_to_2,transition_rate_2_to_3,
            transition_rate_3_to_4,transition_rate_4_to_5
        )
        """
    )

    con.close()


def test_phase08_quality_checks_report(tmp_path: Path):
    db_path = tmp_path / "analytics.duckdb"
    artifact_path = tmp_path / "quality_report.json"
    _seed_quality_tables(db_path)

    report = run_quality_checks(
        db_path=db_path,
        artifact_path=artifact_path,
        thresholds=QualityThresholds(freshness_warn_years=3, freshness_fail_years=8, min_cluster_rows=1),
        as_of_year=2026,
    )

    assert report["status"] == "pass"
    assert report["fail_count"] == 0
    assert artifact_path.exists()

    persisted = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert persisted["run_type"] == "phase_08_quality_governance"
    assert "checks" in persisted
