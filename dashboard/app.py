"""
SKIMS Drop Intelligence - Executive Dashboard

A Looker-style analytics dashboard built on synthetic SKIMS data.
Demonstrates the kind of self-serve analytics tooling the Data,
Insights and Loyalty team would use internally.

DISCLAIMER: This dashboard uses 100% synthetic data generated for
demonstration purposes. No real SKIMS customer, product, or sales
data is used. I have no affiliation with SKIMS and no access to
internal data.
"""

import warnings
warnings.filterwarnings('ignore')

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import snowflake.connector

# ================================================================
# PAGE CONFIG - must be first Streamlit call
# ================================================================

st.set_page_config(
    page_title="SKIMS Drop Intelligence",
    page_icon="🖤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================================================================
# SKIMS BRAND COLORS
# ================================================================

SKIMS_SEQ = ['#e8ddd4', '#d4c5b5', '#c4a882', '#b8a898', '#8b6f5e', '#4a3728']

SKIMS_CAT = [
    '#c4a882', '#8b6f5e', '#d4a896',
    '#a0522d', '#4a3728', '#d4c5b5',
    '#b8a898', '#1a1a1a'
]

TIER_COLORS = {
    'ONYX':   '#4a3728',
    'MARBLE': '#b8a898',
    'None':   '#e8ddd4'
}

CHART_LAYOUT = dict(
    plot_bgcolor='#f5f0eb',
    paper_bgcolor='#f5f0eb',
    font=dict(family='Jost, sans-serif', color='#1a1a1a'),
    title_font=dict(family='Jost, sans-serif', size=13, color='#1a1a1a'),
    margin=dict(t=40, b=20, l=20, r=20)
)

# ================================================================
# CSS STYLING
# ================================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;500&family=Jost:wght@200;300;400;500&display=swap');

/* ---- Global ---- */
.stApp {
    background-color: #f5f0eb;
    font-family: 'Jost', sans-serif;
}

.stApp p, .stApp li, .stApp div {
    font-family: 'Jost', sans-serif;
    font-weight: 300;
    color: #1a1a1a;
    letter-spacing: 0.02em;
}

/* ---- Headers ---- */
.stApp h1 {
    font-family: 'Cormorant Garamond', serif;
    font-weight: 300;
    font-size: 2.8rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #1a1a1a;
}

.stApp h2 {
    font-family: 'Cormorant Garamond', serif;
    font-weight: 300;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    color: #1a1a1a;
}

.stApp h3 {
    font-family: 'Jost', sans-serif;
    font-weight: 400;
    font-size: 0.85rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #8b6f5e;
    margin-bottom: 16px;
}

/* ---- Metric cards ---- */
[data-testid="metric-container"] {
    background-color: #ffffff;
    border: 1px solid #e8ddd4;
    border-radius: 2px;
    padding: 20px;
    box-shadow: none;
}

[data-testid="metric-container"] label {
    font-family: 'Jost', sans-serif;
    font-size: 0.7rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #8b6f5e !important;
    font-weight: 400;
}

[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'Cormorant Garamond', serif;
    font-size: 2rem;
    font-weight: 300;
    color: #1a1a1a;
}

/* ---- Sidebar ---- */
[data-testid="stSidebar"] {
    background-color: #3d3028 !important;
    border-right: none;
}

[data-testid="stSidebar"] * {
    color: #f5f0eb !important;
    font-family: 'Jost', sans-serif !important;
    letter-spacing: 0.05em;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #c4a882 !important;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    font-size: 0.75rem !important;
}

/* ---- Hide sidebar toggle button completely ---- */
[data-testid="stSidebarCollapsedControl"] { display: none !important; }
[data-testid="stSidebarNavLink"]          { display: none !important; }
[data-testid="collapsedControl"]          { display: none !important; }
button[kind="header"]                     { display: none !important; }
[data-testid="stSidebar"] button          { display: none !important; }
section[data-testid="stSidebarContent"] > div:first-child button { display: none !important; }

/* ---- Sidebar multiselect ---- */
[data-testid="stSidebar"] div[data-baseweb="select"] {
    background-color: #4a3728 !important;
    border: 1px solid #6b4c3b !important;
    border-radius: 2px !important;
    overflow: visible !important;
    padding: 4px !important;
}

[data-testid="stSidebar"] div[data-baseweb="select"] > div {
    background-color: #4a3728 !important;
    overflow: visible !important;
    flex-wrap: wrap !important;
    padding: 4px !important;
}

[data-testid="stSidebar"] input {
    background-color: #4a3728 !important;
    color: #f5f0eb !important;
}

[data-testid="stSidebar"] [role="button"][data-baseweb="tag"] {
    background-color: #c4a882 !important;
    color: #1a1a1a !important;
    border-radius: 2px !important;
    padding: 4px 12px !important;
    margin: 3px !important;
    overflow: visible !important;
    max-width: none !important;
    width: auto !important;
}

[data-testid="stSidebar"] [role="button"][data-baseweb="tag"] > span:first-child {
    color: #1a1a1a !important;
    overflow: visible !important;
    text-overflow: unset !important;
    white-space: nowrap !important;
    max-width: none !important;
    display: inline !important;
    padding-left: 2px !important;
}

[data-testid="stSidebar"] [data-baseweb="popover"] {
    background-color: #3d3028 !important;
}

[data-testid="stSidebar"] [role="option"] {
    background-color: #3d3028 !important;
    color: #f5f0eb !important;
}

[data-testid="stSidebar"] [role="option"]:hover {
    background-color: #4a3728 !important;
}

/* ---- Tabs ---- */
.stTabs [data-baseweb="tab-list"] {
    background-color: transparent;
    border-bottom: 1px solid #d4c5b5;
    gap: 0px;
}

.stTabs [data-baseweb="tab"] {
    font-family: 'Jost', sans-serif;
    font-size: 0.72rem;
    font-weight: 400;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #9e9189;
    padding: 12px 24px;
    background-color: transparent;
    border: none;
}

.stTabs [aria-selected="true"] {
    color: #1a1a1a;
    border-bottom: 2px solid #1a1a1a;
    background-color: transparent;
}

/* ---- Disclaimer ---- */
.disclaimer {
    background-color: #e8ddd4;
    border: 1px solid #d4c5b5;
    border-radius: 2px;
    padding: 12px 20px;
    font-size: 0.75rem;
    color: #8b6f5e;
    letter-spacing: 0.05em;
    margin-bottom: 20px;
    font-family: 'Jost', sans-serif;
}

/* ---- Misc ---- */
hr {
    border: none;
    border-top: 1px solid #e8ddd4;
    margin: 24px 0;
}

.stDataFrame {
    border: 1px solid #e8ddd4;
    border-radius: 2px;
}

/* ---- Hide Streamlit chrome ---- */
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stHeader"]      { display: none !important; }
[data-testid="stToolbar"]     { display: none !important; }
header                        { display: none !important; }
#MainMenu                     { display: none !important; }

.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem;
}
</style>
""", unsafe_allow_html=True)

# ================================================================
# SNOWFLAKE CONNECTION
# ================================================================

@st.cache_resource
def get_connection():
    creds = st.secrets["snowflake"]
    return snowflake.connector.connect(
        account=creds["account"],
        user=creds["user"],
        password=creds["password"],
        database=creds["database"],
        warehouse=creds["warehouse"],
        role=creds["role"]
    )

@st.cache_data(ttl=3600)
def run_query(_conn, sql):
    df = pd.read_sql(sql, _conn)
    df.columns = [c.lower() for c in df.columns]
    return df

conn = get_connection()

# ================================================================
# DATA LOADING
# ================================================================

@st.cache_data(ttl=3600)
def load_all_data(_conn):
    customers = run_query(_conn, """
        SELECT * FROM SKIMS_DROP_INTELLIGENCE.DBT_DEV_MARTS.MART_CUSTOMER_360
    """)

    products = run_query(_conn, """
        SELECT * FROM SKIMS_DROP_INTELLIGENCE.DBT_DEV_MARTS.MART_PRODUCT_PERFORMANCE
    """)

    category_returns = run_query(_conn, """
        SELECT
            p.category,
            COUNT(oi.order_id)                                              AS items_sold,
            SUM(CASE WHEN oi.returned_flag = TRUE THEN 1 ELSE 0 END)        AS items_returned,
            ROUND(100.0 * SUM(CASE WHEN oi.returned_flag = TRUE THEN 1 ELSE 0 END)
                  / COUNT(oi.order_id), 1)                                  AS return_rate_pct,
            SUM(oi.returned_revenue)                                        AS returned_revenue
        FROM SKIMS_DROP_INTELLIGENCE.DBT_DEV_STAGING.STG_ORDER_ITEMS oi
        JOIN SKIMS_DROP_INTELLIGENCE.DBT_DEV_STAGING.STG_PRODUCTS p
            ON oi.product_id = p.product_id
        GROUP BY p.category
        ORDER BY return_rate_pct DESC
    """)

    size_returns = run_query(_conn, """
        SELECT
            p.size,
            COUNT(oi.order_id)                                              AS items_sold,
            SUM(CASE WHEN oi.returned_flag = TRUE THEN 1 ELSE 0 END)        AS items_returned,
            ROUND(100.0 * SUM(CASE WHEN oi.returned_flag = TRUE THEN 1 ELSE 0 END)
                  / COUNT(oi.order_id), 1)                                  AS return_rate_pct,
            SUM(oi.returned_revenue)                                        AS returned_revenue
        FROM SKIMS_DROP_INTELLIGENCE.DBT_DEV_STAGING.STG_ORDER_ITEMS oi
        JOIN SKIMS_DROP_INTELLIGENCE.DBT_DEV_STAGING.STG_PRODUCTS p
            ON oi.product_id = p.product_id
        GROUP BY p.size
        ORDER BY
            CASE p.size
                WHEN 'XXS' THEN 1 WHEN 'XS' THEN 2 WHEN 'S'  THEN 3
                WHEN 'M'   THEN 4 WHEN 'L'  THEN 5 WHEN 'XL' THEN 6
                WHEN '2X'  THEN 7 WHEN '3X' THEN 8 WHEN '4X' THEN 9
            END
    """)

    return_reasons = run_query(_conn, """
        SELECT
            return_reason,
            COUNT(*)                                                        AS returns,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)             AS pct_of_returns,
            SUM(returned_revenue)                                           AS revenue_impact
        FROM SKIMS_DROP_INTELLIGENCE.DBT_DEV_STAGING.STG_ORDER_ITEMS
        WHERE returned_flag = TRUE
        GROUP BY return_reason
        ORDER BY returns DESC
    """)

    return customers, products, category_returns, size_returns, return_reasons

with st.spinner("Loading data from Snowflake..."):
    customers, products, category_returns, size_returns, return_reasons = load_all_data(conn)

# ================================================================
# SIDEBAR
# ================================================================

with st.sidebar:
    st.markdown(
        "<p style='font-family:Jost,sans-serif;font-size:0.75rem;"
        "letter-spacing:0.18em;text-transform:uppercase;color:#c4a882;"
        "font-weight:400;margin-bottom:0;padding-top:8px;'>"
        "SKIMS Drop Intelligence</p>",
        unsafe_allow_html=True
    )
    st.markdown("---")
    st.markdown("**Data last refreshed:** Synthetic dataset")
    st.markdown("**Records loaded:**")
    st.markdown(f"- {len(customers):,} customers")
    st.markdown(f"- {len(products):,} products")
    st.markdown("---")

    tier_filter = st.multiselect(
        "Filter by Rewards Tier",
        options=sorted(customers['rewards_tier'].unique().tolist()),
        default=sorted(customers['rewards_tier'].unique().tolist())
    )

    market_filter = st.multiselect(
        "Filter by Market",
        options=['Domestic', 'International'],
        default=['Domestic', 'International']
    )

    st.markdown("---")
    st.markdown(
        "**About this dashboard**\n\n"
        "Built by Prathiksha Mohan Raje Urs as a portfolio project "
        "for the SKIMS Senior Data Analyst role.\n\n"
        "Stack: Python · Snowflake · dbt · Streamlit"
    )

# Apply filters
filtered_customers = customers[
    (customers['rewards_tier'].isin(tier_filter)) &
    (customers['market_segment'].isin(market_filter))
]

# ================================================================
# DISCLAIMER
# ================================================================

st.markdown("""
<div class="disclaimer">
    ⚠️ <strong>Portfolio Project Disclaimer:</strong>
    This dashboard uses 100% synthetic data generated for demonstration purposes.
    No real SKIMS customer, product, or sales data is used.
    I have no affiliation with SKIMS and no access to internal data.
</div>
""", unsafe_allow_html=True)

# ================================================================
# HEADER
# ================================================================

st.title("SKIMS Drop Intelligence")
st.markdown(
    "<p style='font-family:Jost,sans-serif;font-size:0.8rem;"
    "letter-spacing:0.15em;text-transform:uppercase;color:#8b6f5e;"
    "margin-top:-12px;'>Data, Insights & Loyalty — Portfolio Project</p>",
    unsafe_allow_html=True
)
st.markdown("---")

# ================================================================
# TABS
# ================================================================

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Summary",
    "🚀 Drop Performance",
    "💎 Rewards Health",
    "↩️ Returns Watchlist"
])

# ================================================================
# TAB 1: SUMMARY
# ================================================================

with tab1:
    st.markdown("### Key Performance Indicators")
    st.markdown("*Filtered by selected tier and market segment*")

    total_customers = len(filtered_customers)
    total_revenue   = filtered_customers['net_revenue'].sum()
    avg_aov         = filtered_customers['avg_order_value'].mean()
    onyx_pct        = (filtered_customers['rewards_tier'] == 'ONYX').mean() * 100
    denom           = filtered_customers['total_orders'].sum()
    overall_return_rate = (
        filtered_customers['total_items_returned'].sum() / denom * 100
        if denom > 0 else 0
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Customers",  f"{total_customers:,}")
    c2.metric("Net Revenue",      f"${total_revenue/1_000_000:.2f}M")
    c3.metric("Avg Order Value",  f"${avg_aov:,.2f}")
    c4.metric("ONYX Member Rate", f"{onyx_pct:.1f}%")
    c5.metric("Return Rate",      f"{overall_return_rate:.1f}%")

    st.markdown("---")
    st.markdown("### Revenue by Rewards Tier")

    tier_summary = (
        filtered_customers
        .groupby('rewards_tier')
        .agg(
            customers    =('customer_id', 'count'),
            total_revenue=('net_revenue', 'sum'),
            avg_revenue  =('net_revenue', 'mean'),
            avg_orders   =('total_orders', 'mean')
        )
        .reset_index()
        .sort_values('avg_revenue', ascending=False)
    )

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            tier_summary,
            x='rewards_tier', y='avg_revenue',
            color='rewards_tier',
            color_discrete_map=TIER_COLORS,
            title='Average Net Revenue per Customer by Tier',
            labels={'avg_revenue': 'Avg Net Revenue ($)', 'rewards_tier': 'Rewards Tier'}
        )
        fig.update_layout(showlegend=False, **CHART_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.pie(
            tier_summary,
            values='total_revenue', names='rewards_tier',
            title='Share of Total Revenue by Tier',
            color='rewards_tier',
            color_discrete_map=TIER_COLORS
        )
        fig2.update_layout(**CHART_LAYOUT)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.markdown("### Customer Geography")

    country_summary = (
        filtered_customers
        .groupby('country')
        .agg(customers=('customer_id', 'count'), avg_revenue=('net_revenue', 'mean'))
        .reset_index()
        .sort_values('customers', ascending=False)
        .head(10)
    )

    fig3 = px.bar(
        country_summary,
        x='country', y='customers',
        color='avg_revenue',
        color_continuous_scale=SKIMS_SEQ,
        title='Top 10 Countries by Customer Count',
        labels={'customers': 'Customers', 'country': 'Country', 'avg_revenue': 'Avg Revenue ($)'}
    )
    fig3.update_layout(**CHART_LAYOUT)
    st.plotly_chart(fig3, use_container_width=True)

# ================================================================
# TAB 2: DROP PERFORMANCE
# ================================================================

with tab2:
    st.markdown("### Drop Performance Analysis")
    st.markdown("*Demand signals and size-level performance for limited drop products*")

    limited = products[products['is_limited_drop'] == True].copy()

    c1, c2, c3 = st.columns(3)
    c1.metric("Limited Drop SKUs",      f"{len(limited):,}")
    c2.metric("Avg Waitlist Signups",    f"{limited['total_waitlist_signups'].mean():.0f}")
    c3.metric("Avg Demand Signal Score", f"{limited['demand_signal_score'].mean():.0f}")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Waitlist Signups vs Units Sold")
        fig = px.scatter(
            limited,
            x='total_waitlist_signups', y='units_sold',
            color='category',
            hover_data=['product_id', 'size', 'color'],
            title='Waitlist Predicts Demand',
            labels={
                'total_waitlist_signups': 'Total Waitlist Signups',
                'units_sold': 'Units Sold',
                'category': 'Category'
            },
            color_discrete_sequence=SKIMS_CAT
        )
        fig.update_layout(**CHART_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Demand Signal Score Distribution")
        fig2 = px.histogram(
            limited,
            x='demand_signal_score', nbins=30,
            color='category',
            title='Demand Signal Score by Category',
            labels={'demand_signal_score': 'Demand Signal Score'},
            color_discrete_sequence=SKIMS_CAT
        )
        fig2.update_layout(**CHART_LAYOUT)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Size-Level Performance")

    size_order = ['XXS', 'XS', 'S', 'M', 'L', 'XL', '2X', '3X', '4X']
    size_perf = (
        products.groupby('size')
        .agg(
            units_sold  =('units_sold', 'sum'),
            return_rate =('return_rate_pct', 'mean'),
            net_revenue =('net_revenue', 'sum')
        )
        .reset_index()
    )
    size_perf = size_perf[size_perf['size'].isin(size_order)].copy()
    size_perf['size'] = pd.Categorical(size_perf['size'], categories=size_order, ordered=True)
    size_perf = size_perf.sort_values('size')

    col1, col2 = st.columns(2)

    with col1:
        fig3 = px.bar(
            size_perf, x='size', y='units_sold',
            title='Units Sold by Size',
            color='return_rate',
            color_continuous_scale=SKIMS_SEQ,
            labels={'units_sold': 'Units Sold', 'size': 'Size', 'return_rate': 'Return Rate (%)'}
        )
        fig3.update_layout(**CHART_LAYOUT)
        st.plotly_chart(fig3, use_container_width=True)

    with col2:
        fig4 = px.bar(
            size_perf, x='size', y='return_rate',
            title='Return Rate by Size',
            color='return_rate',
            color_continuous_scale=SKIMS_SEQ,
            labels={'return_rate': 'Return Rate (%)', 'size': 'Size'}
        )
        fig4.add_hline(
            y=size_perf['return_rate'].mean(),
            line_dash="dash", line_color="#4a3728",
            annotation_text="Average"
        )
        fig4.update_layout(**CHART_LAYOUT)
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Top Drop SKUs by Demand Signal Score")

    top_drops = (
        limited.nlargest(10, 'demand_signal_score')
        [[
            'product_id', 'category', 'size', 'color',
            'total_waitlist_signups', 'signups_72hr_pre_launch',
            'demand_signal_score', 'units_sold', 'return_rate_pct'
        ]]
        .reset_index(drop=True)
    )
    top_drops.columns = [
        'Product ID', 'Category', 'Size', 'Color',
        'Total Waitlist', '72hr Signups',
        'Demand Score', 'Units Sold', 'Return Rate %'
    ]

    headers_html = "".join(
        f"<th style='padding:10px 14px;'>{c}</th>" for c in top_drops.columns
    )
    rows_html = "".join(
        f'<tr style="background-color:{"#f5f0eb" if i % 2 == 0 else "#e8ddd4"};">'
        + "".join(
            f"<td style='padding:10px 14px;border-bottom:1px solid #d4c5b5;'>{v}</td>"
            for v in row
        )
        + "</tr>"
        for i, (_, row) in enumerate(top_drops.iterrows())
    )

    st.markdown(f"""
    <div style="overflow-x:auto;">
    <table style="width:100%;border-collapse:collapse;font-family:'Jost',sans-serif;
                  font-size:0.82rem;font-weight:300;color:#1a1a1a;letter-spacing:0.03em;">
        <thead>
            <tr style="background-color:#3d3028;color:#f5f0eb;font-size:0.7rem;
                       letter-spacing:0.12em;text-transform:uppercase;font-weight:400;">
                {headers_html}
            </tr>
        </thead>
        <tbody>{rows_html}</tbody>
    </table>
    </div>
    """, unsafe_allow_html=True)

# ================================================================
# TAB 3: REWARDS HEALTH
# ================================================================

with tab3:
    st.markdown("### Rewards Program Health")
    st.markdown("*MARBLE and ONYX tier performance, funnel, and member segmentation*")

    rewards      = filtered_customers[filtered_customers['rewards_tier'].isin(['MARBLE', 'ONYX'])]
    onyx_rev     = filtered_customers[filtered_customers['rewards_tier'] == 'ONYX']['net_revenue'].mean()
    none_rev     = filtered_customers[filtered_customers['rewards_tier'] == 'None']['net_revenue'].mean()
    multiplier   = onyx_rev / none_rev if none_rev > 0 else 0
    marble_count = len(filtered_customers[filtered_customers['rewards_tier'] == 'MARBLE'])
    onyx_count   = len(filtered_customers[filtered_customers['rewards_tier'] == 'ONYX'])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rewards Members",         f"{len(rewards):,}")
    c2.metric("ONYX Members",            f"{onyx_count:,}")
    c3.metric("ONYX Revenue Multiplier", f"{multiplier:.1f}x")
    c4.metric("MARBLE Members",          f"{marble_count:,}")

    st.markdown("---")

    tier_kpis = (
        filtered_customers
        .groupby('rewards_tier')
        .agg(
            avg_orders  =('total_orders', 'mean'),
            avg_revenue =('net_revenue', 'mean'),
            avg_events  =('total_events', 'mean')
        )
        .reset_index()
    )

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            tier_kpis, x='rewards_tier', y='avg_revenue',
            color='rewards_tier', color_discrete_map=TIER_COLORS,
            title='Average Net Revenue per Customer by Tier',
            labels={'avg_revenue': 'Avg Net Revenue ($)', 'rewards_tier': 'Tier'}
        )
        fig.update_layout(showlegend=False, **CHART_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.bar(
            tier_kpis, x='rewards_tier', y='avg_orders',
            color='rewards_tier', color_discrete_map=TIER_COLORS,
            title='Average Orders per Customer by Tier',
            labels={'avg_orders': 'Avg Orders', 'rewards_tier': 'Tier'}
        )
        fig2.update_layout(showlegend=False, **CHART_LAYOUT)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.markdown("#### MARBLE Member Progress Toward ONYX")

    marble_members  = filtered_customers[filtered_customers['rewards_tier'] == 'MARBLE']
    progress_counts = marble_members['onyx_progress'].value_counts().reset_index()
    progress_counts.columns = ['onyx_progress', 'members']

    progress_labels = {
        'early_stage':              'Early Stage',
        'halfway_engagement':       'Halfway (Engagement)',
        'halfway_purchase':         'Halfway (Purchase)',
        'engagement_path_complete': 'Engagement Complete',
        'purchase_path_complete':   'Purchase Complete',
        'qualified':                'Qualified'
    }
    progress_counts['label'] = progress_counts['onyx_progress'].map(
        lambda x: progress_labels.get(x, x)
    )

    fig3 = px.bar(
        progress_counts, x='label', y='members',
        title='Where Are MARBLE Members in Their ONYX Journey?',
        color='members',
        color_continuous_scale=SKIMS_SEQ,
        labels={'members': 'Number of Members', 'label': 'Progress Stage'}
    )
    fig3.update_layout(showlegend=False, **CHART_LAYOUT)
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")
    st.markdown("#### ONYX Qualification Path Analysis")

    onyx_members = filtered_customers[filtered_customers['rewards_tier'] == 'ONYX'].copy()

    def classify_path(row):
        if row['total_orders'] >= 4 and row['qualifying_actions'] < 10:
            return 'Purchase Path'
        elif row['qualifying_actions'] >= 10 and row['total_orders'] < 4:
            return 'Engagement Path'
        elif row['net_revenue'] >= 200 and row['total_orders'] < 4:
            return 'Spend Path'
        else:
            return 'Multiple Paths'

    onyx_members['path'] = onyx_members.apply(classify_path, axis=1)
    path_summary = (
        onyx_members.groupby('path')
        .agg(
            members         =('customer_id', 'count'),
            avg_net_revenue =('net_revenue', 'mean'),
            avg_orders      =('total_orders', 'mean')
        )
        .reset_index()
    )

    PATH_COLORS = ['#4a3728', '#8b6f5e', '#c4a882', '#e8ddd4']

    col1, col2 = st.columns(2)

    with col1:
        fig4 = px.pie(
            path_summary, values='members', names='path',
            title='ONYX Members by Qualification Path',
            color_discrete_sequence=PATH_COLORS
        )
        fig4.update_layout(**CHART_LAYOUT)
        st.plotly_chart(fig4, use_container_width=True)

    with col2:
        fig5 = px.bar(
            path_summary, x='path', y='avg_net_revenue',
            title='Avg Revenue by Qualification Path',
            color='path',
            color_discrete_sequence=PATH_COLORS,
            labels={'avg_net_revenue': 'Avg Net Revenue ($)', 'path': 'Path'}
        )
        fig5.update_layout(showlegend=False, **CHART_LAYOUT)
        st.plotly_chart(fig5, use_container_width=True)

# ================================================================
# TAB 4: RETURNS WATCHLIST
# ================================================================

with tab4:
    st.markdown("### Returns Watchlist")
    st.markdown("*Return rate analysis by category, size, and reason*")

    total_returned_rev = category_returns['returned_revenue'].sum()
    avg_return_rate    = category_returns['return_rate_pct'].mean()
    worst_category     = category_returns.iloc[0]['category']

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Returned Revenue",  f"${total_returned_rev/1_000_000:.2f}M")
    c2.metric("Avg Return Rate",         f"{avg_return_rate:.1f}%")
    c3.metric("Highest Return Category", worst_category)

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            category_returns.sort_values('return_rate_pct'),
            x='return_rate_pct', y='category',
            orientation='h',
            title='Return Rate by Category',
            color='return_rate_pct',
            color_continuous_scale=SKIMS_SEQ,
            labels={'return_rate_pct': 'Return Rate (%)', 'category': 'Category'}
        )
        fig.update_layout(showlegend=False, **CHART_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.pie(
            return_reasons,
            values='pct_of_returns', names='return_reason',
            title='Why Are Customers Returning?',
            color_discrete_sequence=SKIMS_CAT
        )
        fig2.update_layout(**CHART_LAYOUT)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Return Rate by Size")

    size_order = ['XXS', 'XS', 'S', 'M', 'L', 'XL', '2X', '3X', '4X']
    size_ret = size_returns.copy()
    size_ret['size'] = pd.Categorical(size_ret['size'], categories=size_order, ordered=True)
    size_ret = size_ret.sort_values('size')

    fig3 = px.bar(
        size_ret, x='size', y='return_rate_pct',
        title='Return Rate by Size (XXS and XS are the problem)',
        color='return_rate_pct',
        color_continuous_scale=SKIMS_SEQ,
        labels={'return_rate_pct': 'Return Rate (%)', 'size': 'Size'}
    )
    avg_sr = size_ret['return_rate_pct'].mean()
    fig3.add_hline(
        y=avg_sr, line_dash="dash", line_color="#4a3728",
        annotation_text=f"Average ({avg_sr:.1f}%)"
    )
    fig3.update_layout(showlegend=False, **CHART_LAYOUT)
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Revenue Impact by Return Reason")

    fig4 = px.bar(
        return_reasons.sort_values('revenue_impact', ascending=False),
        x='return_reason', y='revenue_impact',
        color='pct_of_returns',
        color_continuous_scale=SKIMS_SEQ,
        title='Revenue Lost by Return Reason',
        labels={
            'revenue_impact': 'Revenue Lost ($)',
            'return_reason':  'Return Reason',
            'pct_of_returns': '% of Returns'
        }
    )
    fig4.update_layout(**CHART_LAYOUT)
    st.plotly_chart(fig4, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Proposed A/B Test: Enhanced Size Guide")

    st.markdown("""
    <div style="
        background-color:#e8ddd4;
        border:1px solid #c4a882;
        border-left:4px solid #8b6f5e;
        border-radius:2px;
        padding:20px 24px;
        font-family:'Jost',sans-serif;
        font-weight:300;
        color:#1a1a1a;
        letter-spacing:0.03em;
        line-height:1.8;
    ">
        <p style="font-size:0.72rem;letter-spacing:0.18em;text-transform:uppercase;
        color:#8b6f5e;margin-bottom:12px;font-weight:400;">Proposed Experiment</p>
        <p><strong style="font-weight:500;">Hypothesis:</strong> Adding a fit callout
        ("This style runs small — consider sizing up") to the top 15 high-return-rate
        SKUs will reduce returns by 25-50%.</p>
        <p><strong style="font-weight:500;">Primary metric:</strong> Return rate on
        targeted SKUs (baseline ~18%, target &lt;15%)</p>
        <p><strong style="font-weight:500;">Sample size needed:</strong> ~2,400 total
        visitors (calculated in analysis notebook)</p>
        <p><strong style="font-weight:500;">Estimated test duration:</strong> 3-6 weeks
        depending on traffic volume</p>
        <p><strong style="font-weight:500;">Financial case:</strong> Even a 25% improvement
        in returns on problem SKUs recovers meaningful revenue annually with minimal
        engineering cost.</p>
    </div>
    """, unsafe_allow_html=True)