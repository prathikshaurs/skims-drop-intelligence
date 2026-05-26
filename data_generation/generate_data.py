"""
SKIMS Drop Intelligence - Synthetic Data Generator
Will be generating 7 realistic CSV files mimicking what SKIMS' actual data warehouse
might contain. Patterns are intentionally baked in to mirror real-world DTC
apparel behavior:
  - Limited drops sell out fast, with waitlist signals
  - Certain categories (Sculpt, Swim) return more often
  - Smaller sizes (XXS, XS) return more often
  - ONYX-tier customers order more, engage more, join more waitlists

DISCLAIMER: This dashboard uses 100% synthetic data
generated for demonstration purposes. No real SKIMS customer, product, or
sales data is used. I have no affiliation with SKIMS and no access to
internal data.
"""

import os
import random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from faker import Faker


########## CONFIG ##########
SEED = 42  
random.seed(SEED)
np.random.seed(SEED)
fake = Faker()
Faker.seed(SEED)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Scale of the tables
N_CUSTOMERS = 50_000
N_PRODUCTS = 500
N_ORDERS = 250_000
N_WAITLIST = 75_000
N_ENGAGEMENT = 400_000
N_MARKETING = 600_000

START_DATE = datetime(2022, 1, 1)
END_DATE = datetime(2025, 11, 1)


def random_date_between(start, end):
    """Returns a random datetime between two datetimes."""
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=random_seconds)


########## 1. CUSTOMERS ##########
def generate_customers():
    print("Generating customers...")
    countries = ["USA"] * 40 + ["UK"] * 25 + ["Germany"] * 5 + ["France"] * 5 + \
                ["Italy"] * 5 + ["Australia"] * 10 + ["Canada"] * 5 + \
                ["Mexico"] * 3 + ["Brazil"] * 2

    sizes = ["XXS", "XS", "S", "M", "L", "XL", "2X", "3X", "4X"]
    size_weights = [2, 8, 18, 25, 22, 15, 6, 3, 1]

    tiers = ["none"] * 60 + ["MARBLE"] * 30 + ["ONYX"] * 10

    rows = []
    for i in range(1, N_CUSTOMERS + 1):
        signup = random_date_between(START_DATE, END_DATE)
        tier = random.choice(tiers)
        app = random.random() < (0.7 if tier != "none" else 0.3)

        rows.append({
            "customer_id": f"C{i:07d}",
            "email": fake.email(),
            "signup_date": signup.date(),
            "country": random.choice(countries),
            "preferred_size": random.choices(sizes, weights=size_weights)[0],
            "rewards_tier": tier,
            "app_installed": app,
        })

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUTPUT_DIR, "customers.csv"), index=False)
    print(f"  Saved {len(df):,} customers")
    return df


########## 2. PRODUCTS ##########
def generate_products():
    print("Generating products...")
    categories = {
        "Fits Everybody": {"price_range": (32, 78), "limited_rate": 0.05},
        "Sculpt": {"price_range": (42, 128), "limited_rate": 0.10},
        "Soft Lounge": {"price_range": (38, 98), "limited_rate": 0.05},
        "Swim": {"price_range": (38, 88), "limited_rate": 0.15},
        "Cotton": {"price_range": (14, 58), "limited_rate": 0.03},
        "Mens": {"price_range": (22, 68), "limited_rate": 0.05},
        "Outerwear": {"price_range": (78, 498), "limited_rate": 0.30},
    }
    colors = ["Sienna", "Onyx", "Marble", "Cocoa", "Sand", "Clay", "Bone",
              "Garnet", "Mica", "Oxide", "Smoke", "Heather Grey", "Soot"]
    sizes = ["XXS", "XS", "S", "M", "L", "XL", "2X", "3X", "4X"]

    rows = []
    for i in range(1, N_PRODUCTS + 1):
        cat = random.choice(list(categories.keys()))
        cat_info = categories[cat]
        price = round(random.uniform(*cat_info["price_range"]), 2)
        is_limited = random.random() < cat_info["limited_rate"]

        rows.append({
            "product_id": f"P{i:05d}",
            "category": cat,
            "color": random.choice(colors),
            "size": random.choice(sizes),
            "price": price,
            "launch_date": random_date_between(START_DATE, END_DATE).date(),
            "is_limited_drop": is_limited,
        })

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUTPUT_DIR, "products.csv"), index=False)
    print(f"  Saved {len(df):,} products")
    return df


########## 3. ORDERS + ORDER_ITEMS ##########
def generate_orders_and_items(customers, products):
    print("Generating orders and order items...")

    # Weighing customers by tier so ONYX orders more, MARBLE next, none least
    tier_weight = {"none": 1, "MARBLE": 2.5, "ONYX": 4}
    customers = customers.copy()
    customers["weight"] = customers["rewards_tier"].map(tier_weight)
    customer_ids = customers["customer_id"].values
    customer_weights = customers["weight"].values / customers["weight"].sum()
    customer_signup = dict(zip(customers["customer_id"], customers["signup_date"]))

    # Returns rate setup by category
    category_return_rate = {
        "Sculpt": 0.18, "Swim": 0.18, "Fits Everybody": 0.10,
        "Cotton": 0.08, "Mens": 0.10, "Outerwear": 0.09,
        "Soft Lounge": 0.06,
    }
    size_return_multiplier = {
        "XXS": 2.0, "XS": 1.8, "S": 1.1, "M": 0.9, "L": 0.9,
        "XL": 1.0, "2X": 1.1, "3X": 1.2, "4X": 1.3,
    }
    return_reasons = (["too_small"] * 35 + ["too_large"] * 20 +
                      ["not_as_expected"] * 20 + ["color_different"] * 10 +
                      ["quality_issue"] * 5 + ["other"] * 10)

    orders = []
    order_items = []
    product_lookup = products.set_index("product_id").to_dict("index")
    product_ids = products["product_id"].values

    for i in range(1, N_ORDERS + 1):
        cust_id = np.random.choice(customer_ids, p=customer_weights)
        signup = customer_signup[cust_id]
        signup_dt = datetime.combine(signup, datetime.min.time())
        order_date = random_date_between(signup_dt, END_DATE)

        channel = random.choices(
            ["web", "app", "retail", "wholesale"],
            weights=[75, 18, 5, 2]
        )[0]

        n_items = random.choices([1, 2, 3, 4, 5], weights=[40, 30, 15, 10, 5])[0]
        order_id = f"O{i:08d}"
        order_total = 0

        for j in range(n_items):
            prod_id = random.choice(product_ids)
            prod = product_lookup[prod_id]
            quantity = random.choices([1, 2, 3], weights=[80, 15, 5])[0]
            item_total = prod["price"] * quantity
            order_total += item_total

            base_return = category_return_rate[prod["category"]]
            size_mult = size_return_multiplier[prod["size"]]
            return_prob = min(base_return * size_mult, 0.5)
            returned = random.random() < return_prob
            reason = random.choice(return_reasons) if returned else None

            order_items.append({
                "order_id": order_id,
                "product_id": prod_id,
                "quantity": quantity,
                "item_price": prod["price"],
                "returned_flag": returned,
                "return_reason": reason,
            })

        orders.append({
            "order_id": order_id,
            "customer_id": cust_id,
            "order_date": order_date.date(),
            "channel": channel,
            "order_total": round(order_total, 2),
        })

        if i % 50_000 == 0:
            print(f"  {i:,} orders generated...")

    orders_df = pd.DataFrame(orders)
    items_df = pd.DataFrame(order_items)
    orders_df.to_csv(os.path.join(OUTPUT_DIR, "orders.csv"), index=False)
    items_df.to_csv(os.path.join(OUTPUT_DIR, "order_items.csv"), index=False)
    print(f"  Saved {len(orders_df):,} orders and {len(items_df):,} order items")
    return orders_df, items_df


########## 4. WAITLIST SIGNUPS ##########
def generate_waitlist(customers, products):
    print("Generating waitlist signups...")
    limited = products[products["is_limited_drop"] == True]
    if len(limited) == 0:
        print("  No limited drops, skipping")
        return pd.DataFrame()

    tier_weight = {"none": 1, "MARBLE": 2, "ONYX": 3}
    customers = customers.copy()
    customers["weight"] = customers["rewards_tier"].map(tier_weight)
    cust_ids = customers["customer_id"].values
    weights = customers["weight"].values / customers["weight"].sum()

    rows = []
    for i in range(N_WAITLIST):
        prod = limited.sample(1).iloc[0]
        launch = datetime.combine(prod["launch_date"], datetime.min.time())
        # 80% of signups in the 72 hours before launch
        if random.random() < 0.8:
            hours_before = random.uniform(0, 72)
        else:
            hours_before = random.uniform(72, 720)  # up to 30 days before
        signup_time = launch - timedelta(hours=hours_before)

        rows.append({
            "waitlist_id": f"W{i+1:07d}",
            "customer_id": np.random.choice(cust_ids, p=weights),
            "product_id": prod["product_id"],
            "signup_timestamp": signup_time,
        })

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUTPUT_DIR, "waitlist_signups.csv"), index=False)
    print(f"  Saved {len(df):,} waitlist signups")
    return df


########## 5. ENGAGEMENT EVENTS ##########
def generate_engagement(customers):
    print("Generating engagement events...")
    event_types = ["review_written", "friend_referred", "social_share",
                   "waitlist_joined", "app_login", "push_clicked"]
    event_weights = [10, 5, 15, 15, 40, 15]

    tier_weight = {"none": 1, "MARBLE": 2.5, "ONYX": 5}
    customers = customers.copy()
    customers["weight"] = customers["rewards_tier"].map(tier_weight)
    cust_ids = customers["customer_id"].values
    weights = customers["weight"].values / customers["weight"].sum()
    cust_signup = dict(zip(customers["customer_id"], customers["signup_date"]))

    rows = []
    for i in range(N_ENGAGEMENT):
        cust = np.random.choice(cust_ids, p=weights)
        signup_dt = datetime.combine(cust_signup[cust], datetime.min.time())
        ts = random_date_between(signup_dt, END_DATE)
        rows.append({
            "event_id": f"E{i+1:08d}",
            "customer_id": cust,
            "event_type": random.choices(event_types, weights=event_weights)[0],
            "event_timestamp": ts,
        })

        if (i + 1) % 100_000 == 0:
            print(f"  {i+1:,} events generated...")

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUTPUT_DIR, "engagement_events.csv"), index=False)
    print(f"  Saved {len(df):,} engagement events")
    return df


########## 6. MARKETING TOUCHES ##########
def generate_marketing(customers):
    print("Generating marketing touches...")
    channels = ["Meta", "Google", "TikTok", "Email", "SMS", "TV", "Influencer"]
    channel_weights = [25, 22, 15, 18, 8, 7, 5]

    cust_ids = customers["customer_id"].values
    cust_signup = dict(zip(customers["customer_id"], customers["signup_date"]))

    rows = []
    for i in range(N_MARKETING):
        cust = random.choice(cust_ids)
        signup_dt = datetime.combine(cust_signup[cust], datetime.min.time())
        ts = random_date_between(signup_dt, END_DATE)
        channel = random.choices(channels, weights=channel_weights)[0]
        spend = round(random.uniform(0.05, 4.50), 2)
        rows.append({
            "touch_id": f"M{i+1:09d}",
            "customer_id": cust,
            "channel": channel,
            "touch_timestamp": ts,
            "spend_allocated": spend,
        })

        if (i + 1) % 200_000 == 0:
            print(f"  {i+1:,} touches generated...")

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUTPUT_DIR, "marketing_touches.csv"), index=False)
    print(f"  Saved {len(df):,} marketing touches")
    return df


########## MAIN ##########
def main():
    print("=" * 60)
    print("SKIMS Drop Intelligence - Synthetic Data Generation")
    print("=" * 60)
    customers = generate_customers()
    products = generate_products()
    orders, items = generate_orders_and_items(customers, products)
    generate_waitlist(customers, products)
    generate_engagement(customers)
    generate_marketing(customers)
    print("=" * 60)
    print(f"Done. Files written to: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()