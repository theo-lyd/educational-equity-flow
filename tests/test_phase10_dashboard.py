from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from src.dashboard.phase10 import (
    ags_to_lat_lon,
    build_sankey_series,
    load_anomaly_map_data,
    load_geojson_centroids,
    load_scd_timeline,
)


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
        )
        t(
            ags, region, latest_year, extracted_at, dbt_scd_id,
            dbt_updated_at, dbt_valid_from, dbt_valid_to
        )
        """
    )
    con.close()

    current_df = load_scd_timeline(mode="current", db_path=db_path)
    history_df = load_scd_timeline(mode="historical", db_path=db_path)

    assert len(current_df) == 2
    assert len(history_df) == 2
    assert set(current_df["record_type"]) == {"current"}
    assert set(history_df["record_type"]) == {"historical"}


def test_load_geojson_centroids(tmp_path: Path):
        geojson_path = tmp_path / "districts.geojson"
        geojson_path.write_text(
                """
                {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "id": "1001",
                            "properties": {"ags": "01001"},
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": [
                                    [
                                        [10.0, 50.0],
                                        [10.4, 50.0],
                                        [10.4, 50.4],
                                        [10.0, 50.4],
                                        [10.0, 50.0]
                                    ]
                                ]
                            }
                        }
                    ]
                }
                """,
                encoding="utf-8",
        )

        centroids = load_geojson_centroids(geojson_path=geojson_path)

        assert len(centroids) == 1
        assert set(centroids.columns) == {"ags", "lat", "lon"}
        assert centroids.iloc[0]["ags"] == "01001"


def test_load_anomaly_map_data_uses_geojson_and_fallback(tmp_path: Path):
        db_path = tmp_path / "analytics.duckdb"
        con = duckdb.connect(str(db_path))

        con.execute(
                """
                create table gold_transition_rates as
                select * from (values
                        ('01001', 'Region A', 0.62, 0.60),
                        ('01002', 'Region B', 0.55, 0.53)
                ) t(ags, region, end_to_end_completion_rate, compounded_transition_rate)
                """
        )
        con.execute(
                """
                create table gold_leakage_differential as
                select * from (values
                        ('01001', 'Region A', -0.03),
                        ('01002', 'Region B', -0.02)
                ) t(ags, region, leakage_differential)
                """
        )
        con.close()

        geojson_path = tmp_path / "districts.geojson"
        geojson_path.write_text(
                """
                {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "properties": {"ags": "01001"},
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": [
                                    [
                                        [10.0, 50.0],
                                        [10.4, 50.0],
                                        [10.4, 50.4],
                                        [10.0, 50.4],
                                        [10.0, 50.0]
                                    ]
                                ]
                            }
                        }
                    ]
                }
                """,
                encoding="utf-8",
        )

        out = load_anomaly_map_data(db_path=db_path, geojson_path=geojson_path)

        assert len(out) == 2
        assert set(out["map_source"]).issubset({"geojson", "pseudo"})
        assert "geojson" in set(out["map_source"])
        assert "pseudo" in set(out["map_source"])
        assert out["lat"].notna().all()
        assert out["lon"].notna().all()
