select
    ags,
    region,
    stage_1_year,
    stage_2_year,
    stage_3_year,
    stage_4_year,
    stage_5_year,
    stage_1_students,
    stage_2_students,
    stage_3_graduates,
    stage_4_university_students,
    stage_5_degree_completions,
    transition_rate_1_to_2,
    transition_rate_2_to_3,
    transition_rate_3_to_4,
    transition_rate_4_to_5,
    case
        when coalesce(stage_1_students, 0) > 0 then stage_5_degree_completions / stage_1_students
        else null
    end as end_to_end_completion_rate,
    case
        when transition_rate_1_to_2 is not null
         and transition_rate_2_to_3 is not null
         and transition_rate_3_to_4 is not null
         and transition_rate_4_to_5 is not null
        then transition_rate_1_to_2 * transition_rate_2_to_3 * transition_rate_3_to_4 * transition_rate_4_to_5
        else null
    end as compounded_transition_rate
from {{ ref('gold_stage_funnel') }}
