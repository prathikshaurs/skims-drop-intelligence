with source as (
    select * from {{ source('raw', 'order_items') }}
),

renamed as (
    select
        order_id,
        product_id,
        quantity,
        item_price,
        returned_flag,
        return_reason,

        -- derived fields
        item_price * quantity as item_total,
        case when returned_flag = true then item_price * quantity else 0 end as returned_revenue

    from source
)

select * from renamed