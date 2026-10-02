select customer_id, first_name, last_name, lower(email) as email,
       created_at::date as created_at, logical_date::date as logical_date
from {{ source('raw', 'raw_customers') }}
