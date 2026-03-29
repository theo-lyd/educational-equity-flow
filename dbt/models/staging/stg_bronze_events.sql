with source_events as (
    select
        cast(dataset as varchar) as dataset,
        cast(source_file as varchar) as source_file,
        nullif(trim(cast(year as varchar)), '') as year_raw,
        {{ normalize_ags('ags') }} as ags,
        nullif(trim(cast(region as varchar)), '') as region,
        nullif(trim(cast(dimension_1 as varchar)), '') as dimension_1,
        nullif(trim(cast(dimension_2 as varchar)), '') as dimension_2,
        nullif(trim(cast(dimension_3 as varchar)), '') as dimension_3,
        nullif(trim(cast(metric_name as varchar)), '') as metric_name,
        nullif(trim(cast(raw_value as varchar)), '') as raw_value,
        cast(value as double) as value,
        lower(nullif(trim(cast(quality as varchar)), '')) as quality
    from read_parquet('../data/bronze/**/*.parquet', hive_partitioning = true)
    where coalesce(cast(dataset as varchar), '') <> 'RAW_STATE_LOCK'
),
normalized as (
    select
        dataset,
        source_file,
        case
            when regexp_matches(year_raw, '^(19|20)[0-9]{2}$') then cast(year_raw as integer)
            else null
        end as year,
        ags,
        region,
        dimension_1,
        dimension_2,
        dimension_3,
        metric_name,
        raw_value,
        value,
        coalesce(quality, '-') as quality
    from source_events
)

select *
from normalized
where ags is not null
