from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from src.dashboard.phase10 import ags_to_lat_lon, build_sankey_series, load_scd_timeline


def test_ags_to_lat_lon_is_deterministic_and_in_bounds():
    lat_1, lon_1 = ags_to_lat_lon("01001")
    lat_2, lon_2 = ags_to_lat_lon("01001")

    assert (lat_1, lon_1) == (lat_2, lon_2)
    assert 47.2 <= lat_1 <= 55.0
    assert 5.9 <= lon_1 <= 15.1


def test_build_sankey_series_shape():
    frame = pd.DataFrame(
        {
            "stage_1_students": [100.0, 120.0],
            "stage_2_students": [90.0, 110.0],
            "stage_3_graduates": [80.0, 100.0],
            "stage_4_university_students": [70.0, 90.0],
            "stage_5_degree_completions": [60.0, 80.0],
        }
    )

    sankey = build_sankey_series(frame)

    assert len(sankey) == 4
    assert set(sankey.columns) == {"source", "target", "value", "drop_from_previous"}
    assert float(sankey["value"].iloc[0]) == 200.0


def test_load_scd_timeline_current_and_historical(tmp_path: Path):
    db_path = tmp_path / "analytics.duckdb"
    con = duckdb.connect(str(db_path))

    con.execute(
        """
        create table int_district_current as
        select * from (values
            ('01001', 'Region A', 2024),
            ('01002', 'Region B', 2024)
        ) t(ags, region, latest_year)
        """
    )

    con.execute("create schema snapshots")
    con.execute(
        """
        create table snapshots.snap_district_boundaries as
        select * from (values
            ('01001', 'Region A', 2024, now(), 'id1', now(), now(), null),
            ('01002', 'Region B', 2024, now(), 'id2', now(), now(), null)
        ) t(ags, region, latest_year, extracted_at, dbt_scd_id, dbt_updated_at, dbt_valid_from, dbt_valid_to)
        """
    )
    con.close()

    current_df = load_scd_timeline(mode="current", db_path=db_path)
    history_df = load_scd_timeline(mode="historical", db_path=db_path)

    assert len(current_df) == 2
    assert len(history_df) == 2
    assert set(current_df["record_type"]) == {"current"}
    assert set(history_df["record_type"]) == {"historical"}
