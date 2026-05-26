with source as (
    select * from {{ source('raw', 'waitlist_signups') }}
),

renamed as (
    select
        waitlist_id,
        customer_id,
        product_id,
        signup_timestamp,
        date(signup_timestamp) as signup_date
    from source
)

select * from renamed