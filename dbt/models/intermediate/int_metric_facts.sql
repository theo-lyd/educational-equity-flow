select
    dataset,
    source_file,
    year,
    ags,
    coalesce(region, 'Unknown') as region,
    dimension_1,
    dimension_2,
    dimension_3,
    metric_name,
    raw_value,
    value,
    quality,
    case
        when year is not null then concat(cast(year as varchar), '_', ags)
        else concat('unknown_', ags)
    end as cohort_key
from {{ ref('stg_bronze_events') }}
