"""Phase 08 quality, governance, and SLA checks."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

import great_expectations as ge


DEFAULT_DB_PATH = Path("warehouse") / "analytics.duckdb"
DEFAULT_ARTIFACT_PATH = Path("warehouse") / "artifacts" / "phase08_quality_report.json"


@dataclass
class QualityThresholds:
    freshness_warn_years: int = 3
    freshness_fail_years: int = 6
    min_cluster_rows: int = 100


def _run_ge_expectations(con: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    frame = con.execute(
        """
        select
            ags,
            end_to_end_completion_rate,
            compounded_transition_rate
        from gold_transition_rates
        """
    ).fetchdf()

    gdf = ge.from_pandas(frame)
    results = [
        gdf.expect_column_values_to_not_be_null("ags"),
        gdf.expect_column_values_to_be_unique("ags"),
        gdf.expect_column_values_to_be_between(
            "end_to_end_completion_rate", min_value=0.0, max_value=2.0, mostly=0.95
        ),
        gdf.expect_column_values_to_be_between(
            "compounded_transition_rate", min_value=0.0, max_value=2.0, mostly=0.95
        ),
    ]

    checks = [
        {
            "expectation": r.expectation_config.expectation_type,
            "success": bool(r.success),
            "unexpected_count": int(
                r.result.get("unexpected_count", 0) if isinstance(r.result, dict) else 0
            ),
        }
        for r in results
    ]

    return {
        "success": all(c["success"] for c in checks),
        "checks": checks,
        "row_count": int(len(frame)),
    }


def _run_referential_integrity_checks(con: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    missing_regions = con.execute(
        """
        select count(*)
        from gold_stage_funnel f
        left join int_district_current d using (ags)
        where f.ags is not null
          and d.ags is null
        """
    ).fetchone()[0]

    missing_transition_ags = con.execute(
        """
        select count(*)
        from gold_transition_rates t
        left join gold_stage_funnel f using (ags)
        where t.ags is not null
          and f.ags is null
        """
    ).fetchone()[0]

    checks = [
        {
            "check": "gold_stage_funnel_ags_exist_in_int_district_current",
            "success": int(missing_regions) == 0,
            "unexpected_count": int(missing_regions),
        },
        {
            "check": "gold_transition_rates_ags_exist_in_gold_stage_funnel",
            "success": int(missing_transition_ags) == 0,
            "unexpected_count": int(missing_transition_ags),
        },
    ]

    return {
        "success": all(c["success"] for c in checks),
        "checks": checks,
    }


def _run_freshness_checks(
    con: duckdb.DuckDBPyConnection,
    thresholds: QualityThresholds,
    as_of_year: int,
) -> dict[str, Any]:
    latest = con.execute(
        """
        select
            max(stage_3_year) as latest_stage_3_year,
            max(stage_5_year) as latest_stage_5_year
        from gold_stage_funnel
        """
    ).fetchone()

    stage_3_year = int(latest[0]) if latest and latest[0] is not None else None
    stage_5_year = int(latest[1]) if latest and latest[1] is not None else None

    checks: list[dict[str, Any]] = []
    for stage_name, year_value in [
        ("stage_3", stage_3_year),
        ("stage_5", stage_5_year),
    ]:
        if year_value is None:
            checks.append(
                {
                    "check": f"{stage_name}_freshness",
                    "status": "fail",
                    "age_years": None,
                    "message": "No year available for freshness evaluation",
                }
            )
            continue

        age = as_of_year - year_value
        if age > thresholds.freshness_fail_years:
            status = "fail"
        elif age > thresholds.freshness_warn_years:
            status = "warn"
        else:
            status = "pass"

        checks.append(
            {
                "check": f"{stage_name}_freshness",
                "status": status,
                "age_years": int(age),
                "latest_year": int(year_value),
            }
        )

    fail_count = sum(1 for c in checks if c["status"] == "fail")
    warn_count = sum(1 for c in checks if c["status"] == "warn")
    return {
        "success": fail_count == 0,
        "warn_count": warn_count,
        "fail_count": fail_count,
        "checks": checks,
    }


def _run_operational_checks(con: duckdb.DuckDBPyConnection, thresholds: QualityThresholds) -> dict[str, Any]:
    cluster_rows = con.execute("select count(*) from gold_transition_rates").fetchone()[0]
    checks = [
        {
            "check": "minimum_transition_rows",
            "success": int(cluster_rows) >= thresholds.min_cluster_rows,
            "actual": int(cluster_rows),
            "expected_min": int(thresholds.min_cluster_rows),
        }
    ]
    return {
        "success": all(c["success"] for c in checks),
        "checks": checks,
    }


def run_quality_checks(
    db_path: Path = DEFAULT_DB_PATH,
    artifact_path: Path = DEFAULT_ARTIFACT_PATH,
    thresholds: QualityThresholds | None = None,
    as_of_year: int | None = None,
) -> dict[str, Any]:
    thresholds = thresholds or QualityThresholds()
    as_of_year = as_of_year or datetime.now(UTC).year

    con = duckdb.connect(str(db_path))

    ge_results = _run_ge_expectations(con)
    referential_results = _run_referential_integrity_checks(con)
    freshness_results = _run_freshness_checks(con, thresholds, as_of_year)
    operational_results = _run_operational_checks(con, thresholds)

    con.close()

    fail_count = 0
    warn_count = 0

    if not ge_results["success"]:
        fail_count += 1
    if not referential_results["success"]:
        fail_count += 1
    if not operational_results["success"]:
        fail_count += 1

    fail_count += int(freshness_results["fail_count"])
    warn_count += int(freshness_results["warn_count"])

    status = "pass" if fail_count == 0 else "fail"

    report = {
        "run_type": "phase_08_quality_governance",
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "db_path": str(db_path),
        "status": status,
        "fail_count": int(fail_count),
        "warn_count": int(warn_count),
        "thresholds": asdict(thresholds),
        "as_of_year": int(as_of_year),
        "checks": {
            "great_expectations": ge_results,
            "referential_integrity": referential_results,
            "freshness": freshness_results,
            "operational": operational_results,
        },
    }

    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Phase 08 quality and governance checks.")
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH), help="Path to DuckDB analytics database")
    parser.add_argument(
        "--artifact-path",
        default=str(DEFAULT_ARTIFACT_PATH),
        help="Path to write quality report JSON",
    )
    parser.add_argument("--freshness-warn-years", type=int, default=3)
    parser.add_argument("--freshness-fail-years", type=int, default=6)
    parser.add_argument("--min-cluster-rows", type=int, default=100)
    parser.add_argument("--as-of-year", type=int, default=None)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report = run_quality_checks(
        db_path=Path(args.db_path),
        artifact_path=Path(args.artifact_path),
        thresholds=QualityThresholds(
            freshness_warn_years=args.freshness_warn_years,
            freshness_fail_years=args.freshness_fail_years,
            min_cluster_rows=args.min_cluster_rows,
        ),
        as_of_year=args.as_of_year,
    )

    print(
        "Phase 08 quality check complete:",
        f"status={report['status']}",
        f"fails={report['fail_count']}",
        f"warns={report['warn_count']}",
        f"artifact={DEFAULT_ARTIFACT_PATH}",
    )

    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
