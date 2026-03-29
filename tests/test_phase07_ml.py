from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
import pytest

from src.ml.run_all import build_linear_forecast, build_naive_forecast, run_all


def test_build_naive_forecast_single_point():
    series = pd.DataFrame({"year": [2023], "value": [100.0]})
    forecast = build_naive_forecast(series, periods=3)

    assert list(forecast["year"]) == [2024, 2025, 2026]
    assert list(forecast["yhat"]) == [100.0, 100.0, 100.0]


def test_build_linear_forecast_two_points():
    series = pd.DataFrame({"year": [2022, 2023], "value": [100.0, 120.0]})
    forecast = build_linear_forecast(series, periods=2)

    assert list(forecast["year"]) == [2024, 2025]
    assert forecast.loc[0, "yhat"] == pytest.approx(140.0)
    assert forecast.loc[1, "yhat"] == pytest.approx(160.0)


def test_phase07_run_all_writes_artifacts(tmp_path: Path):
    db_path = tmp_path / "analytics.duckdb"
    con = duckdb.connect(str(db_path))

    con.execute(
        """
        create table gold_transition_rates as
        select * from (values
            ('01001','A',2022,2023,2024,2024,2023,100.0,90.0,80.0,70.0,60.0,0.9,0.89,0.88,0.86,0.6,0.61),
            ('01002','B',2022,2023,2024,2024,2023,90.0,80.0,70.0,60.0,50.0,0.88,0.87,0.86,0.85,0.55,0.56),
            ('01003','C',2022,2023,2024,2024,2023,80.0,70.0,60.0,50.0,40.0,0.87,0.86,0.85,0.84,0.5,0.52)
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
        create table gold_leakage_differential as
        select * from (values
            ('01001','A',2024,'INSGESAMT',10.0,90.0,100.0,100.0,0.1,0.9,-0.8),
            ('01002','B',2024,'INSGESAMT',20.0,80.0,100.0,100.0,0.2,0.8,-0.6),
            ('01003','C',2024,'INSGESAMT',30.0,70.0,100.0,100.0,0.3,0.7,-0.4)
        ) t(
            ags,region,year,subject_group,international_students,domestic_students,
            total_students,known_population,international_share,domestic_share,leakage_differential
        )
        """
    )
    con.execute(
        """
        create table gold_subject_resilience as
        select * from (values
            ('01001','A',2023,'HS-FG01','INSGESAMT',40.0,100.0,0.4),
            ('01002','B',2023,'HS-FG02','INSGESAMT',50.0,100.0,0.5),
            ('01003','C',2023,'HS-FG03','INSGESAMT',60.0,100.0,0.6)
        ) t(
            ags,region,year,hs_fg2_group,demographic_group,passed_exams,total_passed_exams,subject_completion_share
        )
        """
    )
    con.execute(
        """
        create table gold_stage_funnel as
        select * from (values
            ('01001','A',null,null,2024,null,2023,100.0,90.0,80.0,70.0,60.0,0.9,0.89,0.88,0.86),
            ('01002','B',null,null,2024,null,2024,90.0,80.0,70.0,60.0,50.0,0.88,0.87,0.86,0.85),
            ('01003','C',null,null,2024,null,2025,80.0,70.0,60.0,50.0,40.0,0.87,0.86,0.85,0.84)
        ) t(
            ags,region,stage_1_year,stage_2_year,stage_3_year,stage_4_year,stage_5_year,
            stage_1_students,stage_2_students,stage_3_graduates,stage_4_university_students,
            stage_5_degree_completions,transition_rate_1_to_2,transition_rate_2_to_3,
            transition_rate_3_to_4,transition_rate_4_to_5
        )
        """
    )
    con.close()

    artifact_dir = tmp_path / "artifacts"
    report = run_all(db_path=db_path, artifact_dir=artifact_dir)

    assert report["cluster_assignment_rows"] == 3
    assert report["cluster_count"] >= 1
    assert report["forecast_rows"] == 5
    assert report["forecast_meta"]["method"] in {"linear_trend", "prophet"}
    assert (artifact_dir / "phase07_cluster_assignments.csv").exists()
    assert (artifact_dir / "phase07_cluster_summary.csv").exists()
    assert (artifact_dir / "phase07_forecast.csv").exists()
    assert (artifact_dir / "phase07_report.json").exists()
