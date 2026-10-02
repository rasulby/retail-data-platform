select product_id, product_name, category, unit_price::numeric(12,2) as unit_price,
       logical_date::date as logical_date
from {{ source('raw', 'raw_products') }}
