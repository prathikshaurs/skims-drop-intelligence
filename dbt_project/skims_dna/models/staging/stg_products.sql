with source as (
    select * from {{ source('raw', 'products') }}
),

renamed as (
    select
        product_id,
        category,
        color,
        size,
        price,
        launch_date,
        is_limited_drop,

        -- derived fields
        case
            when size in ('XXS', 'XS') then 'extra_small'
            when size in ('S', 'M') then 'small_medium'
            when size in ('L', 'XL') then 'large'
            when size in ('2X', '3X', '4X') then 'plus'
        end as size_group,

        case
            when price < 40 then 'entry'
            when price < 100 then 'mid'
            when price < 200 then 'premium'
            else 'luxury'
        end as price_tier

    from source
)

select * from renamed