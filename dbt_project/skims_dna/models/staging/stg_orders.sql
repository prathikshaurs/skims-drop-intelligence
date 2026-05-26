with source as (
    select * from {{ source('raw', 'orders') }}
),

renamed as (
    select
        order_id,
        customer_id,
        order_date,
        channel,
        order_total,

        -- derived fields
        date_trunc('month', order_date) as order_month,
        date_trunc('week', order_date) as order_week,
        dayofweek(order_date) as order_day_of_week,
        case when channel = 'app' then true else false end as is_app_order

    from source
)

select * from renamed