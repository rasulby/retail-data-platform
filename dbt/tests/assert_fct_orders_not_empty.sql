select 1 where not exists (select 1 from {{ ref('fct_orders') }})

