select o.order_date,
       count(distinct o.order_id) as total_orders,
       sum(i.quantity) as total_items,
       sum(i.line_revenue)::numeric(14,2) as gross_revenue,
       count(distinct o.customer_id) as unique_customers
from {{ ref('fct_orders') }} o
join {{ ref('fct_order_items') }} i using (order_id)
group by o.order_date

