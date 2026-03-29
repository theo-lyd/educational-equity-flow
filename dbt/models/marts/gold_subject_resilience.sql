with stage5_subject as (
    select
        ags,
        coalesce(region, 'Unknown') as region,
        year,
        dimension_1 as hs_fg2_group,
        dimension_2 as demographic_group,
        sum(value) as passed_exams
    from {{ ref('int_metric_facts') }}
    where dataset = '21321-01-01-4_flat'
      and metric_name = 'Bestandene Prüfungen'
      and dimension_1 is not null
      and dimension_1 <> 'INSGESAMT'
      and value is not null
    group by 1, 2, 3, 4, 5
),
totals as (
    select
        ags,
        year,
        sum(passed_exams) as total_passed_exams
    from stage5_subject
    where coalesce(demographic_group, 'INSGESAMT') = 'INSGESAMT'
    group by 1, 2
)

select
    s.ags,
    s.region,
    s.year,
    s.hs_fg2_group,
    s.demographic_group,
    s.passed_exams,
    t.total_passed_exams,
    case
        when coalesce(t.total_passed_exams, 0) > 0 then s.passed_exams / t.total_passed_exams
        else null
    end as subject_completion_share
from stage5_subject s
left join totals t
    on s.ags = t.ags
   and s.year = t.year
