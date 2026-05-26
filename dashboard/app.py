"""
SKIMS Drop Intelligence - Executive Dashboard

A Looker-style analytics dashboard built on synthetic SKIMS data.
Demonstrates the kind of self-serve analytics tooling the Data,
Insights and Loyalty team would use internally.

DISCLAIMER: This dashboard uses 100% synthetic data. No real SKIMS
customer, product, or sales data is used. I have no
affiliation with SKIMS.
"""

import warnings
warnings.filterwarnings('ignore')

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import snowflake.connector

# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="SKIMS Drop Intelligence",
    page_icon="🖤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== STYLING ==========
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #fafafa; }

    /* Metric cards */
    [data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #111111;
    }
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab"] {
        font-size: 14px;
        font-weight: 600;
        color: #6c757d;
    }
    .stTabs [aria-selected="true"] {
        color: #111111;
        border-bottom: 2px solid #111111;
    }

    /* Disclaimer banner */
    .disclaimer {
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 6px;
        padding: 10px 16px;
        font-size: 12px;
        color: #856404;
        margin-bottom: 16px;
    }

    /* Section headers */
    h3 { color: #111111; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# ========== SNOWFLAKE CONNECTION ==========
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
def query(_conn, sql):
    df = pd.read_sql(sql, _conn)
    df.columns = [c.lower() for c in df.columns]
    return df

conn = get_connection()

# ========== DATA LOADING ==========
@st.cache_data(ttl=3600)
def load_all_data(_conn):
    customers = query(_conn, """
        SELECT * FROM SKIMS_DROP_INTELLIGENCE.DBT_DEV_MARTS.MART_CUSTOMER_360
    """)

    products = query(_conn, """
        SELECT * FROM SKIMS_DROP_INTELLIGENCE.DBT_DEV_MARTS.MART_PRODUCT_PERFORMANCE
    """)

    category_returns = query(_conn, """
        SELECT
            p.category,
            COUNT(oi.order_id)                                          AS items_sold,
            SUM(CASE WHEN oi.returned_flag = TRUE THEN 1 ELSE 0 END)    AS items_returned,
            ROUND(100.0 * SUM(CASE WHEN oi.returned_flag = TRUE
                THEN 1 ELSE 0 END) / COUNT(oi.order_id), 1)            AS return_rate_pct,
            SUM(oi.returned_revenue)                                    AS returned_revenue
        FROM SKIMS_DROP_INTELLIGENCE.DBT_DEV_STAGING.STG_ORDER_ITEMS oi
        JOIN SKIMS_DROP_INTELLIGENCE.DBT_DEV_STAGING.STG_PRODUCTS p
            ON oi.product_id = p.product_id
        GROUP BY p.category
        ORDER BY return_rate_pct DESC
    """)

    size_returns = query(_conn, """
        SELECT
            p.size,
            COUNT(oi.order_id)                                          AS items_sold,
            SUM(CASE WHEN oi.returned_flag = TRUE THEN 1 ELSE 0 END)    AS items_returned,
            ROUND(100.0 * SUM(CASE WHEN oi.returned_flag = TRUE
                THEN 1 ELSE 0 END) / COUNT(oi.order_id), 1)            AS return_rate_pct,
            SUM(oi.returned_revenue)                                    AS returned_revenue
        FROM SKIMS_DROP_INTELLIGENCE.DBT_DEV_STAGING.STG_ORDER_ITEMS oi
        JOIN SKIMS_DROP_INTELLIGENCE.DBT_DEV_STAGING.STG_PRODUCTS p
            ON oi.product_id = p.product_id
        GROUP BY p.size
        ORDER BY
            CASE p.size
                WHEN 'XXS' THEN 1 WHEN 'XS' THEN 2 WHEN 'S' THEN 3
                WHEN 'M' THEN 4 WHEN 'L' THEN 5 WHEN 'XL' THEN 6
                WHEN '2X' THEN 7 WHEN '3X' THEN 8 WHEN '4X' THEN 9
            END
    """)

    return_reasons = query(_conn, """
        SELECT
            return_reason,
            COUNT(*)                                    AS returns,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*))
                OVER (), 1)                             AS pct_of_returns,
            SUM(returned_revenue)                       AS revenue_impact
        FROM SKIMS_DROP_INTELLIGENCE.DBT_DEV_STAGING.STG_ORDER_ITEMS
        WHERE returned_flag = TRUE
        GROUP BY return_reason
        ORDER BY returns DESC
    """)

    return customers, products, category_returns, size_returns, return_reasons

with st.spinner("Loading data from Snowflake..."):
    customers, products, category_returns, size_returns, return_reasons = load_all_data(conn)

# ========== SIDEBAR ==========
with st.sidebar:
    st.markdown("## 🖤 SKIMS Drop Intelligence")
    st.markdown("---")
    st.markdown("**Data last refreshed:** Synthetic dataset")
    st.markdown("**Records loaded:**")
    st.markdown(f"- {len(customers):,} customers")
    st.markdown(f"- {len(products):,} products")
    st.markdown("---")

    tier_filter = st.multiselect(
        "Filter by Rewards Tier",
        options=customers['rewards_tier'].unique().tolist(),
        default=customers['rewards_tier'].unique().tolist()
    )

    market_filter = st.multiselect(
        "Filter by Market",
        options=['domestic', 'international'],
        default=['domestic', 'international']
    )

    st.markdown("---")
    st.markdown("""
    **About this dashboard**

    Built by Prathiksha Mohan Raje Urs as a portfolio project
    for the SKIMS Senior Data Analyst role.

    Stack: Python, Snowflake, dbt, Streamlit
    """)

# Applying filters
filtered_customers = customers[
    (customers['rewards_tier'].isin(tier_filter)) &
    (customers['market_segment'].isin(market_filter))
]

# ========== DISCLAIMER ==========
st.markdown("""
<div class="disclaimer">
    ⚠️ <strong>Portfolio Project Disclaimer:</strong> This dashboard uses 100% synthetic data
    generated for demonstration purposes. No real SKIMS customer, product, or sales data is used.
    I have no affiliation with SKIMS and no access to internal data.
</div>
""", unsafe_allow_html=True)

# ========== HEADER ==========
st.title("SKIMS Drop Intelligence")
st.markdown("*Executive analytics dashboard — Data, Insights & Loyalty Team*")
st.markdown("---")

# ========== TABS ==========
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Executive Summary",
    "🚀 Drop Performance",
    "💎 Rewards Health",
    "↩️ Returns Watchlist"
])

# ========== TAB 1: EXECUTIVE SUMMARY ==========
with tab1:
    st.markdown("### Key Performance Indicators")
    st.markdown("*Filtered by selected tier and market segment*")

    col1, col2, col3, col4, col5 = st.columns(5)

    total_customers = len(filtered_customers)
    total_revenue = filtered_customers['net_revenue'].sum()
    avg_aov = filtered_customers['avg_order_value'].mean()
    onyx_pct = (filtered_customers['rewards_tier'] == 'ONYX').mean() * 100
    overall_return_rate = (
        filtered_customers['total_items_returned'].sum() /
        filtered_customers['total_orders'].sum() * 100
        if filtered_customers['total_orders'].sum() > 0 else 0
    )

    col1.metric("Total Customers", f"{total_customers:,}")
    col2.metric("Net Revenue", f"${total_revenue:,.0f}")
    col3.metric("Avg Order Value", f"${avg_aov:,.2f}")
    col4.metric("ONYX Member Rate", f"{onyx_pct:.1f}%")
    col5.metric("Return Rate", f"{overall_return_rate:.1f}%")

    st.markdown("---")
    st.markdown("### Revenue by Rewards Tier")

    tier_summary = filtered_customers.groupby('rewards_tier').agg(
        customers=('customer_id', 'count'),
        total_revenue=('net_revenue', 'sum'),
        avg_revenue=('net_revenue', 'mean'),
        avg_orders=('total_orders', 'mean')
    ).reset_index().sort_values('avg_revenue', ascending=False)

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            tier_summary,
            x='rewards_tier',
            y='avg_revenue',
            color='rewards_tier',
            color_discrete_map={
                'ONYX': '#111111',
                'MARBLE': '#6c757d',
                'none': '#ced4da'
            },
            title='Average Net Revenue per Customer by Tier',
            labels={'avg_revenue': 'Avg Net Revenue ($)',
                    'rewards_tier': 'Rewards Tier'}
        )
        fig.update_layout(showlegend=False, plot_bgcolor='white',
                          paper_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.pie(
            tier_summary,
            values='total_revenue',
            names='rewards_tier',
            title='Share of Total Revenue by Tier',
            color='rewards_tier',
            color_discrete_map={
                'ONYX': '#111111',
                'MARBLE': '#6c757d',
                'none': '#ced4da'
            }
        )
        fig2.update_layout(plot_bgcolor='white', paper_bgcolor='white')
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.markdown("### Customer Geography")

    country_summary = filtered_customers.groupby('country').agg(
        customers=('customer_id', 'count'),
        avg_revenue=('net_revenue', 'mean')
    ).reset_index().sort_values('customers', ascending=False).head(10)

    fig3 = px.bar(
        country_summary,
        x='country',
        y='customers',
        color='avg_revenue',
        color_continuous_scale='Greys',
        title='Top 10 Countries by Customer Count',
        labels={'customers': 'Customers', 'country': 'Country',
                'avg_revenue': 'Avg Revenue ($)'}
    )
    fig3.update_layout(plot_bgcolor='white', paper_bgcolor='white')
    st.plotly_chart(fig3, use_container_width=True)

# ========== TAB 2: DROP PERFORMANCE ==========
with tab2:
    st.markdown("### Drop Performance Analysis")
    st.markdown("*Demand signals and size-level performance for limited drop products*")

    limited = products[products['is_limited_drop'] == True].copy()

    col1, col2, col3 = st.columns(3)
    col1.metric("Limited Drop SKUs", f"{len(limited):,}")
    col2.metric("Avg Waitlist Signups", f"{limited['total_waitlist_signups'].mean():.0f}")
    col3.metric("Avg Demand Signal Score", f"{limited['demand_signal_score'].mean():.0f}")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Waitlist Signups vs Units Sold")
        fig = px.scatter(
            limited,
            x='total_waitlist_signups',
            y='units_sold',
            color='category',
            hover_data=['product_id', 'size', 'color'],
            title='Waitlist Predicts Demand',
            labels={
                'total_waitlist_signups': 'Total Waitlist Signups',
                'units_sold': 'Units Sold',
                'category': 'Category'
            },
        )
        fig.update_layout(plot_bgcolor='white', paper_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Demand Signal Score Distribution")
        fig2 = px.histogram(
            limited,
            x='demand_signal_score',
            nbins=30,
            color='category',
            title='Demand Signal Score by Category',
            labels={'demand_signal_score': 'Demand Signal Score',
                    'count': 'SKUs'}
        )
        fig2.update_layout(plot_bgcolor='white', paper_bgcolor='white')
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Size-Level Performance")

    size_order = ['XXS', 'XS', 'S', 'M', 'L', 'XL', '2X', '3X', '4X']
    size_perf = products.groupby('size').agg(
        units_sold=('units_sold', 'sum'),
        return_rate=('return_rate_pct', 'mean'),
        net_revenue=('net_revenue', 'sum')
    ).reset_index()
    size_perf = size_perf[size_perf['size'].isin(size_order)]
    size_perf['size'] = pd.Categorical(size_perf['size'], categories=size_order, ordered=True)
    size_perf = size_perf.sort_values('size')

    col1, col2 = st.columns(2)

    with col1:
        fig3 = px.bar(
            size_perf,
            x='size',
            y='units_sold',
            title='Units Sold by Size',
            color='return_rate',
            color_continuous_scale='RdYlGn_r',
            labels={'units_sold': 'Units Sold', 'size': 'Size',
                    'return_rate': 'Return Rate (%)'}
        )
        fig3.update_layout(plot_bgcolor='white', paper_bgcolor='white')
        st.plotly_chart(fig3, use_container_width=True)

    with col2:
        fig4 = px.bar(
            size_perf,
            x='size',
            y='return_rate',
            title='Return Rate by Size',
            color='return_rate',
            color_continuous_scale='RdYlGn_r',
            labels={'return_rate': 'Return Rate (%)', 'size': 'Size'}
        )
        fig4.add_hline(y=size_perf['return_rate'].mean(),
                       line_dash="dash", line_color="black",
                       annotation_text="Average")
        fig4.update_layout(plot_bgcolor='white', paper_bgcolor='white')
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Top Drop SKUs by Demand Signal Score")
    top_drops = limited.nlargest(10, 'demand_signal_score')[[
        'product_id', 'category', 'size', 'color',
        'total_waitlist_signups', 'signups_72hr_pre_launch',
        'demand_signal_score', 'units_sold', 'return_rate_pct'
    ]].reset_index(drop=True)
    st.dataframe(top_drops, use_container_width=True)

# ========== TAB 3: REWARDS HEALTH ==========
with tab3:
    st.markdown("### Rewards Program Health")
    st.markdown("*MARBLE and ONYX tier performance, funnel, and member segmentation*")

    rewards = filtered_customers[
        filtered_customers['rewards_tier'].isin(['MARBLE', 'ONYX'])
    ]
    non_rewards = filtered_customers[filtered_customers['rewards_tier'] == 'none']

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Rewards Members", f"{len(rewards):,}")
    col2.metric("ONYX Members",
                f"{len(filtered_customers[filtered_customers['rewards_tier']=='ONYX']):,}")

    onyx_rev = filtered_customers[
        filtered_customers['rewards_tier'] == 'ONYX']['net_revenue'].mean()
    none_rev = filtered_customers[
        filtered_customers['rewards_tier'] == 'none']['net_revenue'].mean()
    multiplier = onyx_rev / none_rev if none_rev > 0 else 0
    col3.metric("ONYX Revenue Multiplier", f"{multiplier:.1f}x",
                help="vs non-rewards customers")

    marble_count = len(filtered_customers[filtered_customers['rewards_tier'] == 'MARBLE'])
    col4.metric("MARBLE Members", f"{marble_count:,}")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        tier_kpis = filtered_customers.groupby('rewards_tier').agg(
            avg_orders=('total_orders', 'mean'),
            avg_revenue=('net_revenue', 'mean'),
            avg_events=('total_events', 'mean')
        ).reset_index()

        fig = px.bar(
            tier_kpis,
            x='rewards_tier',
            y='avg_revenue',
            color='rewards_tier',
            color_discrete_map={
                'ONYX': '#111111', 'MARBLE': '#6c757d', 'none': '#ced4da'
            },
            title='Average Net Revenue per Customer by Tier',
            labels={'avg_revenue': 'Avg Net Revenue ($)',
                    'rewards_tier': 'Tier'}
        )
        fig.update_layout(showlegend=False, plot_bgcolor='white',
                          paper_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.bar(
            tier_kpis,
            x='rewards_tier',
            y='avg_orders',
            color='rewards_tier',
            color_discrete_map={
                'ONYX': '#111111', 'MARBLE': '#6c757d', 'none': '#ced4da'
            },
            title='Average Orders per Customer by Tier',
            labels={'avg_orders': 'Avg Orders', 'rewards_tier': 'Tier'}
        )
        fig2.update_layout(showlegend=False, plot_bgcolor='white',
                           paper_bgcolor='white')
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.markdown("#### MARBLE Member Progress Toward ONYX")

    marble_members = filtered_customers[
        filtered_customers['rewards_tier'] == 'MARBLE'
    ]

    progress_counts = marble_members['onyx_progress'].value_counts().reset_index()
    progress_counts.columns = ['onyx_progress', 'members']

    progress_labels = {
        'early_stage': 'Early Stage',
        'halfway_engagement': 'Halfway (Engagement)',
        'halfway_purchase': 'Halfway (Purchase)',
        'engagement_path_complete': 'Engagement Complete',
        'purchase_path_complete': 'Purchase Complete',
        'qualified': 'Qualified'
    }
    progress_counts['label'] = progress_counts['onyx_progress'].map(
        lambda x: progress_labels.get(x, x)
    )

    fig3 = px.bar(
        progress_counts,
        x='label',
        y='members',
        title='Where Are MARBLE Members in Their ONYX Journey?',
        color='members',
        color_continuous_scale='Greys',
        labels={'members': 'Number of Members', 'label': 'Progress Stage'}
    )
    fig3.update_layout(plot_bgcolor='white', paper_bgcolor='white',
                       showlegend=False)
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")
    st.markdown("#### ONYX Qualification Path Analysis")

    onyx_members = filtered_customers[
        filtered_customers['rewards_tier'] == 'ONYX'
    ].copy()

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

    path_summary = onyx_members.groupby('path').agg(
        members=('customer_id', 'count'),
        avg_net_revenue=('net_revenue', 'mean'),
        avg_orders=('total_orders', 'mean')
    ).reset_index()

    col1, col2 = st.columns(2)

    with col1:
        fig4 = px.pie(
            path_summary,
            values='members',
            names='path',
            title='ONYX Members by Qualification Path',
            color_discrete_sequence=['#111111', '#6c757d', '#adb5bd', '#dee2e6']
        )
        fig4.update_layout(plot_bgcolor='white', paper_bgcolor='white')
        st.plotly_chart(fig4, use_container_width=True)

    with col2:
        fig5 = px.bar(
            path_summary,
            x='path',
            y='avg_net_revenue',
            title='Avg Revenue by Qualification Path',
            color='path',
            color_discrete_sequence=['#111111', '#6c757d', '#adb5bd', '#dee2e6'],
            labels={'avg_net_revenue': 'Avg Net Revenue ($)', 'path': 'Path'}
        )
        fig5.update_layout(showlegend=False, plot_bgcolor='white',
                           paper_bgcolor='white')
        st.plotly_chart(fig5, use_container_width=True)

# ========== TAB 4: RETURNS WATCHLIST ==========
with tab4:
    st.markdown("### Returns Watchlist")
    st.markdown("*Return rate analysis by category, size, and reason*")

    total_returned_rev = category_returns['returned_revenue'].sum()
    avg_return_rate = category_returns['return_rate_pct'].mean()
    worst_category = category_returns.iloc[0]['category']

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Returned Revenue", f"${total_returned_rev:,.0f}")
    col2.metric("Avg Return Rate", f"{avg_return_rate:.1f}%")
    col3.metric("Highest Return Category", worst_category)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            category_returns.sort_values('return_rate_pct'),
            x='return_rate_pct',
            y='category',
            orientation='h',
            title='Return Rate by Category',
            color='return_rate_pct',
            color_continuous_scale='RdYlGn_r',
            labels={'return_rate_pct': 'Return Rate (%)', 'category': 'Category'}
        )
        fig.update_layout(plot_bgcolor='white', paper_bgcolor='white',
                          showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.pie(
            return_reasons,
            values='pct_of_returns',
            names='return_reason',
            title='Why Are Customers Returning?',
            color_discrete_sequence=[
                '#d7191c', '#f4a582', '#92c5de',
                '#2c7bb6', '#0571b0', '#999999'
            ]
        )
        fig2.update_layout(plot_bgcolor='white', paper_bgcolor='white')
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Return Rate by Size")

    size_order = ['XXS', 'XS', 'S', 'M', 'L', 'XL', '2X', '3X', '4X']
    size_returns_ordered = size_returns.copy()
    size_returns_ordered['size'] = pd.Categorical(
        size_returns_ordered['size'], categories=size_order, ordered=True
    )
    size_returns_ordered = size_returns_ordered.sort_values('size')

    fig3 = px.bar(
        size_returns_ordered,
        x='size',
        y='return_rate_pct',
        title='Return Rate by Size (XXS and XS are the problem)',
        color='return_rate_pct',
        color_continuous_scale='RdYlGn_r',
        labels={'return_rate_pct': 'Return Rate (%)', 'size': 'Size'}
    )
    avg_size_return = size_returns_ordered['return_rate_pct'].mean()
    fig3.add_hline(y=avg_size_return, line_dash="dash",
                   line_color="black", annotation_text=f"Average ({avg_size_return:.1f}%)")
    fig3.update_layout(plot_bgcolor='white', paper_bgcolor='white',
                       showlegend=False)
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Revenue Impact by Return Reason")

    fig4 = px.bar(
        return_reasons.sort_values('revenue_impact', ascending=False),
        x='return_reason',
        y='revenue_impact',
        color='pct_of_returns',
        color_continuous_scale='Reds',
        title='Revenue Lost by Return Reason',
        labels={
            'revenue_impact': 'Revenue Lost ($)',
            'return_reason': 'Return Reason',
            'pct_of_returns': '% of Returns'
        }
    )
    fig4.update_layout(plot_bgcolor='white', paper_bgcolor='white')
    st.plotly_chart(fig4, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Proposed A/B Test: Enhanced Size Guide")
    st.info("""
    **Hypothesis:** Adding a fit callout ("This style runs small — consider sizing up")
    to the top 15 high-return-rate SKUs will reduce returns by 25-50%.

    **Primary metric:** Return rate on targeted SKUs (baseline ~18%, target <15%)

    **Sample size needed:** ~2,400 total visitors (calculated in analysis notebook)

    **Estimated test duration:** 3-6 weeks depending on traffic volume

    **Financial case:** Even a 25% improvement in returns on problem SKUs
    recovers meaningful revenue annually with minimal engineering cost.
    """)