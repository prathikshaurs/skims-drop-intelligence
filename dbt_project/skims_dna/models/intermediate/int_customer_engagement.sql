with events as (
    select * from {{ ref('stg_engagement_events') }}
),

engagement_metrics as (
    select
        customer_id,
        count(event_id)                                                     as total_events,
        sum(case when is_qualifying_action then 1 else 0 end)               as qualifying_actions,
        sum(case when event_type = 'review_written' then 1 else 0 end)      as reviews_written,
        sum(case when event_type = 'friend_referred' then 1 else 0 end)     as friends_referred,
        sum(case when event_type = 'social_share' then 1 else 0 end)        as social_shares,
        sum(case when event_type = 'waitlist_joined' then 1 else 0 end)     as waitlists_joined,
        sum(case when event_type = 'app_login' then 1 else 0 end)           as app_logins,
        min(event_date)                                                     as first_event_date,
        max(event_date)                                                     as last_event_date
    from events
    group by customer_id
)

select * from engagement_metrics