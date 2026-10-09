select 1
where not exists (select 1 from {{ ref('stg_orders') }})
