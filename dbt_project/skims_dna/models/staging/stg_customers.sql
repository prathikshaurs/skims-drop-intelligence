with source as (
    select * from {{ source('raw', 'customers') }}
),

renamed as (
    select
        customer_id,
        email,
        signup_date,
        country,
        preferred_size,
        rewards_tier,
        app_installed,

        -- derived flags
        case when rewards_tier = 'ONYX' then true else false end as is_onyx,
        case when rewards_tier in ('MARBLE', 'ONYX') then true else false end as is_rewards_member,
        case when country = 'USA' then 'Domestic' else 'International' end as market_segment

    from source
)

select * from renamed