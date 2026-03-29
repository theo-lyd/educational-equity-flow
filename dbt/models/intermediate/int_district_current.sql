with district_ranked as (
    select
        ags,
        region,
        year,
        row_number() over (
            partition by ags
            order by year desc nulls last, source_file desc
        ) as row_num
    from {{ ref('stg_bronze_events') }}
    where ags is not null
      and region is not null
)

select
    ags,
    region,
    year as latest_year
from district_ranked
where row_num = 1
