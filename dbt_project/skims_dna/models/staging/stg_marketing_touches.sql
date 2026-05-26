with source as (
    select * from {{ source('raw', 'marketing_touches') }}
),

renamed as (
    select
        touch_id,
        customer_id,
        channel,
        touch_timestamp,
        spend_allocated,
        date(touch_timestamp) as touch_date,

        case
            when channel in ('Email', 'SMS') then 'owned'
            when channel in ('Meta', 'Google', 'TikTok') then 'paid_digital'
            when channel = 'TV' then 'paid_traditional'
            when channel = 'Influencer' then 'influencer'
        end as channel_type

    from source
)

select * from renamed