select order_id, customer_id, order_date, status, logical_date
from {{ ref('stg_orders') }}
