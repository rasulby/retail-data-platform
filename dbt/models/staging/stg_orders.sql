select order_id, customer_id, order_date::date as order_date, status,
       logical_date::date as logical_date
from {{ source('raw', 'raw_orders') }}
