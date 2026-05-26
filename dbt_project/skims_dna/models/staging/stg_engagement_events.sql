with source as (
    select * from {{ source('raw', 'engagement_events') }}
),

renamed as (
    select
        event_id,
        customer_id,
        event_type,
        event_timestamp,
        date(event_timestamp) as event_date,

        -- flag high-value engagement actions (the ones that count toward ONYX)
        case
            when event_type in ('review_written', 'friend_referred', 'social_share', 'waitlist_joined')
            then true else false
        end as is_qualifying_action

    from source
)

select * from renamed