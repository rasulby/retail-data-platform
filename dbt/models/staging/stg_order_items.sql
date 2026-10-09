select order_item_id, order_id, product_id, quantity::integer as quantity,
       unit_price::numeric(12,2) as unit_price, logical_date::date as logical_date
from {{ source('raw', 'raw_order_items') }}
