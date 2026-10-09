select distinct order_date as date_key,
       extract(year from order_date)::integer as year,
       extract(month from order_date)::integer as month,
       extract(day from order_date)::integer as day
from {{ ref('stg_orders') }}
