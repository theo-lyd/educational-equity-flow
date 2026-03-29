with stage_1 as (
    select
        ags,
        max(year) as stage_1_year,
        sum(value) as stage_1_students
    from {{ ref('int_metric_facts') }}
    where dataset = '21111-01-03-4'
      and metric_name = '7. Klassenstufe'
      and coalesce(dimension_1, 'Insgesamt') = 'Insgesamt'
      and value is not null
    group by ags
),
stage_2 as (
    select
        ags,
        max(year) as stage_2_year,
        sum(value) as stage_2_students
    from {{ ref('int_metric_facts') }}
    where dataset = '21111-01-03-4'
      and metric_name = '11. Jahrgangsstufe / Einführungsphase'
      and coalesce(dimension_1, 'Insgesamt') = 'Insgesamt'
      and value is not null
    group by ags
),
stage_3 as (
    select
        ags,
        max(year) as stage_3_year,
        sum(value) as stage_3_graduates
    from {{ ref('int_metric_facts') }}
    where dataset = '21111-02-06-4-B'
      and metric_name = 'Absolvierende/Abgehende allgemeinbildender Schulen nach dem Abschluss | mit Allgemeiner und fachgebundener Hochschulreife | Insgesamt'
      and value is not null
    group by ags
),
stage_4 as (
    select
        ags,
        max(year) as stage_4_year,
        sum(value) as stage_4_university_students
    from {{ ref('int_metric_facts') }}
    where dataset = '21311-01-01-4-B'
      and metric_name = 'Insgesamt'
      and coalesce(dimension_1, 'Insgesamt') = 'Insgesamt'
      and value is not null
    group by ags
),
stage_5 as (
    select
        ags,
        max(year) as stage_5_year,
        sum(value) as stage_5_degree_completions
    from {{ ref('int_metric_facts') }}
    where dataset = '21321-01-01-4_flat'
      and metric_name = 'Bestandene Prüfungen'
      and dimension_1 = 'INSGESAMT'
      and dimension_2 = 'INSGESAMT'
      and value is not null
    group by ags
),
all_ags as (
    select ags from stage_1
    union
    select ags from stage_2
    union
    select ags from stage_3
    union
    select ags from stage_4
    union
    select ags from stage_5
)

select
    a.ags,
    d.region,
    s1.stage_1_year,
    s2.stage_2_year,
    s3.stage_3_year,
    s4.stage_4_year,
    s5.stage_5_year,
    s1.stage_1_students,
    s2.stage_2_students,
    s3.stage_3_graduates,
    s4.stage_4_university_students,
    s5.stage_5_degree_completions,
    case
        when coalesce(s1.stage_1_students, 0) > 0 then s2.stage_2_students / s1.stage_1_students
        else null
    end as transition_rate_1_to_2,
    case
        when coalesce(s2.stage_2_students, 0) > 0 then s3.stage_3_graduates / s2.stage_2_students
        else null
    end as transition_rate_2_to_3,
    case
        when coalesce(s3.stage_3_graduates, 0) > 0 then s4.stage_4_university_students / s3.stage_3_graduates
        else null
    end as transition_rate_3_to_4,
    case
        when coalesce(s4.stage_4_university_students, 0) > 0 then s5.stage_5_degree_completions / s4.stage_4_university_students
        else null
    end as transition_rate_4_to_5
from all_ags a
left join stage_1 s1 using (ags)
left join stage_2 s2 using (ags)
left join stage_3 s3 using (ags)
left join stage_4 s4 using (ags)
left join stage_5 s5 using (ags)
left join {{ ref('int_district_current') }} d using (ags)
