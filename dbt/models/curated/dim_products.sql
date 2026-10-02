select product_id, product_name, category, unit_price, logical_date
from {{ ref('stg_products') }}
