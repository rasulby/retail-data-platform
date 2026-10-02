select order_item_id, order_id, product_id, quantity, unit_price,
       quantity * unit_price as line_revenue, logical_date
from {{ ref('stg_order_items') }}
