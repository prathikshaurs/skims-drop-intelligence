with orders as (
    select * from {{ ref('stg_orders') }}
),

order_items as (
    select * from {{ ref('stg_order_items') }}
),

order_metrics as (
    select
        o.customer_id,
        count(distinct o.order_id)                              as total_orders,
        min(o.order_date)                                       as first_order_date,
        max(o.order_date)                                       as last_order_date,
        -- datediff('day', min(o.order_date), max(o.order_date))   as customer_lifespan_days,
        date_diff('day', min(o.order_date), max(o.order_date))   as customer_lifespan_days,
        sum(o.order_total)                                      as total_revenue,
        avg(o.order_total)                                      as avg_order_value,
        sum(oi.returned_revenue)                                as total_returned_revenue,
        count(case when oi.returned_flag then 1 end)            as total_items_returned,
        count(case when o.channel = 'app' then 1 end)           as app_orders,
        count(case when o.channel = 'web' then 1 end)           as web_orders
    from orders o
    left join order_items oi on o.order_id = oi.order_id
    group by o.customer_id
)

select * from order_metrics