with customers as (
    select * from {{ ref('stg_customers') }}
),

order_metrics as (
    select * from {{ ref('int_customer_orders') }}
),

engagement as (
    select * from {{ ref('int_customer_engagement') }}
),

final as (
    select
        -- identity
        c.customer_id,
        c.email,
        c.signup_date,
        c.country,
        c.market_segment,
        c.preferred_size,
        c.rewards_tier,
        c.is_rewards_member,
        c.is_onyx,
        c.app_installed,

        -- order metrics
        coalesce(o.total_orders, 0)             as total_orders,
        coalesce(o.total_revenue, 0)            as total_revenue,
        coalesce(o.avg_order_value, 0)          as avg_order_value,
        coalesce(o.total_returned_revenue, 0)   as total_returned_revenue,
        coalesce(o.total_items_returned, 0)     as total_items_returned,
        o.first_order_date,
        o.last_order_date,
        o.customer_lifespan_days,
        coalesce(o.app_orders, 0)               as app_orders,
        coalesce(o.web_orders, 0)               as web_orders,

        -- engagement metrics
        coalesce(e.total_events, 0)             as total_events,
        coalesce(e.qualifying_actions, 0)       as qualifying_actions,
        coalesce(e.reviews_written, 0)          as reviews_written,
        coalesce(e.friends_referred, 0)         as friends_referred,
        coalesce(e.social_shares, 0)            as social_shares,
        coalesce(e.waitlists_joined, 0)         as waitlists_joined,

        -- derived LTV proxy
        coalesce(o.total_revenue, 0) - coalesce(o.total_returned_revenue, 0) as net_revenue,

        -- ONYX qualification progress (for non-ONYX members)
        case
            when c.rewards_tier = 'ONYX' then 'qualified'
            when coalesce(o.total_orders, 0) >= 4 then 'purchase_path_complete'
            when coalesce(e.qualifying_actions, 0) >= 10 then 'engagement_path_complete'
            when coalesce(o.total_orders, 0) >= 2 then 'halfway_purchase'
            when coalesce(e.qualifying_actions, 0) >= 5 then 'halfway_engagement'
            else 'early_stage'
        end as onyx_progress

    from customers c
    left join order_metrics o on c.customer_id = o.customer_id
    left join engagement e on c.customer_id = e.customer_id
)

select * from final