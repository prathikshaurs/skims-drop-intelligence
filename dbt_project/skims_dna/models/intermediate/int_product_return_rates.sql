with items as (
    select * from {{ ref('stg_order_items') }}
),

products as (
    select * from {{ ref('stg_products') }}
),

product_metrics as (
    select
        p.product_id,
        p.category,
        p.size,
        p.size_group,
        p.color,
        p.price,
        p.price_tier,
        p.is_limited_drop,
        count(i.order_id)                                                           as times_ordered,
        sum(i.quantity)                                                             as units_sold,
        sum(case when i.returned_flag then i.quantity else 0 end)                   as units_returned,
        round(100.0 * sum(case when i.returned_flag then 1 else 0 end)
              / nullif(count(i.order_id), 0), 2)                                    as return_rate_pct,
        sum(i.item_total)                                                           as gross_revenue,
        sum(i.returned_revenue)                                                     as returned_revenue,
        sum(i.item_total) - sum(i.returned_revenue)                                 as net_revenue
    from items i
    join products p on i.product_id = p.product_id
    group by 1, 2, 3, 4, 5, 6, 7, 8
)

select * from product_metrics