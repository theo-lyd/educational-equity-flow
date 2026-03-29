{% macro normalize_ags(column_name) -%}
case
  when {{ column_name }} is null then null
  else
    case
      when length(regexp_replace(cast({{ column_name }} as varchar), '[^0-9]', '', 'g')) >= 5 then
        substr(regexp_replace(cast({{ column_name }} as varchar), '[^0-9]', '', 'g'), 1, 5)
      else null
    end
end
{%- endmacro %}
