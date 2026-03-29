{% snapshot snap_district_boundaries %}

{{
    config(
      target_schema='snapshots',
      unique_key='ags',
      strategy='check',
      check_cols=['region'],
      invalidate_hard_deletes=True
    )
}}

select
    ags,
    region,
    latest_year,
    current_timestamp as extracted_at
from {{ ref('int_district_current') }}

{% endsnapshot %}
