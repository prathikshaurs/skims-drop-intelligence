with product_metrics as (
    select * from {{ ref('int_product_return_rates') }}
),

products as (
    select
        product_id,
        launch_date
    from {{ ref('stg_products') }}
),

waitlist_raw as (
    select
        w.product_id,
        w.waitlist_id,
        w.signup_timestamp,
        p.launch_date
    from {{ ref('stg_waitlist_signups') }} w
    left join products p on w.product_id = p.product_id
),

waitlist as (
    select
        product_id,
        count(waitlist_id) as total_waitlist_signups,
        sum(
            case
                -- when signup_timestamp >= dateadd('hour', -72, launch_date::timestamp)
                when signup_timestamp >= (launch_date::timestamp - INTERVAL 72 HOUR)
                then 1 else 0
            end
        ) as signups_72hr_pre_launch
    from waitlist_raw
    group by product_id
),

final as (
    select
        pm.*,
        coalesce(w.total_waitlist_signups, 0)    as total_waitlist_signups,
        coalesce(w.signups_72hr_pre_launch, 0)   as signups_72hr_pre_launch,

        -- demand signal score (simple composite)
        coalesce(w.total_waitlist_signups, 0) * 2 +
        coalesce(w.signups_72hr_pre_launch, 0) * 5 as demand_signal_score

    from product_metrics pm
    left join waitlist w on pm.product_id = w.product_id
)

select * from final