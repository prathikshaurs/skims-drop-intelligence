USE DATABASE SKIMS_DROP_INTELLIGENCE;
USE SCHEMA RAW;

-- 1) CUSTOMERS
CREATE OR REPLACE TABLE CUSTOMERS (
    customer_id      VARCHAR,
    email            VARCHAR,
    signup_date      DATE,
    country          VARCHAR,
    preferred_size   VARCHAR,
    rewards_tier     VARCHAR,
    app_installed    BOOLEAN
);

-- 2) PRODUCTS
CREATE OR REPLACE TABLE PRODUCTS (
    product_id        VARCHAR,
    category          VARCHAR,
    color             VARCHAR,
    size              VARCHAR,
    price             NUMBER(10, 2),
    launch_date       DATE,
    is_limited_drop   BOOLEAN
);

-- 3) ORDERS
CREATE OR REPLACE TABLE ORDERS (
    order_id      VARCHAR,
    customer_id   VARCHAR,
    order_date    DATE,
    channel       VARCHAR,
    order_total   NUMBER(12, 2)
);

-- 4) ORDER_ITEMS
CREATE OR REPLACE TABLE ORDER_ITEMS (
    order_id        VARCHAR,
    product_id      VARCHAR,
    quantity        NUMBER(5, 0),
    item_price      NUMBER(10, 2),
    returned_flag   BOOLEAN,
    return_reason   VARCHAR
);

-- 5) WAITLIST_SIGNUPS
CREATE OR REPLACE TABLE WAITLIST_SIGNUPS (
    waitlist_id        VARCHAR,
    customer_id        VARCHAR,
    product_id         VARCHAR,
    signup_timestamp   TIMESTAMP
);

-- 6) ENGAGEMENT_EVENTS
CREATE OR REPLACE TABLE ENGAGEMENT_EVENTS (
    event_id          VARCHAR,
    customer_id       VARCHAR,
    event_type        VARCHAR,
    event_timestamp   TIMESTAMP
);

-- 7) MARKETING_TOUCHES
CREATE OR REPLACE TABLE MARKETING_TOUCHES (
    touch_id           VARCHAR,
    customer_id        VARCHAR,
    channel            VARCHAR,
    touch_timestamp    TIMESTAMP,
    spend_allocated    NUMBER(8, 2)
);