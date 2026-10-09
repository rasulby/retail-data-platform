select customer_id, first_name, last_name, email, created_at, logical_date
from {{ ref('stg_customers') }}
