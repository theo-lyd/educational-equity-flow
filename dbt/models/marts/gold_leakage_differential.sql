with by_group as (
    select
        ags,
        coalesce(region, 'Unknown') as region,
        year,
        coalesce(dimension_1, 'INSGESAMT') as subject_group,
        sum(case when metric_name = 'ausländisch' then value else 0 end) as international_students,
        sum(case when metric_name = 'deutsch' then value else 0 end) as domestic_students,
        sum(case when metric_name = 'Insgesamt' then value else 0 end) as total_students
    from {{ ref('int_metric_facts') }}
    where dataset = '21311-01-01-4'
      and metric_name in ('Insgesamt', 'deutsch', 'ausländisch')
      and value is not null
    group by 1, 2, 3, 4
),
normalized as (
    select
        ags,
        region,
        year,
        subject_group,
        international_students,
        domestic_students,
        total_students,
        international_students + domestic_students as known_population,
        case
            when coalesce(international_students + domestic_students, 0) > 0
                then international_students / (international_students + domestic_students)
            else null
        end as international_share,
        case
            when coalesce(international_students + domestic_students, 0) > 0
                then domestic_students / (international_students + domestic_students)
            else null
        end as domestic_share
    from by_group
)

select
    ags,
    region,
    year,
    subject_group,
    international_students,
    domestic_students,
    total_students,
    known_population,
    international_share,
    domestic_share,
    case
        when international_share is not null and domestic_share is not null
            then international_share - domestic_share
        else null
    end as leakage_differential
from normalized
