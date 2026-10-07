"""
STAGE 4 - THE INTERACTIVE DASHBOARD
Run from the project root:  streamlit run python/app.py
"""
import streamlit as st
import plotly.express as px
import dash_logic as dl

st.set_page_config(page_title="Olist E-Commerce Dashboard", layout="wide")


@st.cache_data
def get_data():
    return dl.load_data()


try:
    fact, pay = get_data()
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()

st.title("Olist E-Commerce Sales Dashboard")
st.caption("Real public data: Brazilian e-commerce orders (Olist). Delivered orders only; "
           "revenue = item price, excluding freight.")

# ---------------------------------------------------------------- filters
st.sidebar.header("Filters")
years = sorted(fact["year"].dropna().unique())
states = sorted(fact["state"].dropna().unique())
cats = sorted(fact["category"].dropna().unique())

sel_years = st.sidebar.multiselect("Year", years, default=years)
sel_states = st.sidebar.multiselect("State", states, default=states)
sel_cats = st.sidebar.multiselect("Category", cats, default=cats)

df = fact[fact["year"].isin(sel_years) & fact["state"].isin(sel_states) & fact["category"].isin(sel_cats)]
if df.empty:
    st.warning("No data for this filter combination. Adjust the filters in the sidebar.")
    st.stop()

# ------------------------------------------------------------------- KPIs
k = dl.kpis(df)
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Revenue", f"{k['revenue']:,.0f}")
c2.metric("Orders", f"{k['orders']:,}")
c3.metric("Avg order value", f"{k['aov']:,.2f}")
c4.metric("Avg review score", f"{k['avg_review']:.2f}")
c5.metric("Late deliveries", f"{k['late_pct']:.1f}%")
c6.metric("Avg delivery days", f"{k['avg_delivery_days']:.1f}")

st.divider()

# ----------------------------------------------------------------- charts
left, right = st.columns(2)

with left:
    m = dl.monthly_revenue(df)
    st.plotly_chart(px.line(m, x="order_month", y="revenue", markers=True,
                            title="Monthly revenue"), use_container_width=True)
    s = dl.revenue_by_state(df)
    st.plotly_chart(px.bar(s, x="state", y="revenue", title="Top 10 states by revenue"),
                    use_container_width=True)
    p = dl.payment_mix(df, pay)
    st.plotly_chart(px.bar(p, x="payment_type", y="orders", title="Orders by payment type"),
                    use_container_width=True)

with right:
    t = dl.top_categories(df).sort_values("revenue")
    st.plotly_chart(px.bar(t, x="revenue", y="category", orientation="h",
                           title="Top 10 categories by revenue"), use_container_width=True)
    r = dl.review_by_delivery(df)
    st.plotly_chart(px.bar(r, x="delivery", y="avg_review_score",
                           title="Average review score: late vs on-time delivery",
                           range_y=[0, 5]), use_container_width=True)

with st.expander("What these numbers mean"):
    st.write("Revenue is the sum of item prices for delivered orders. Order-level measures "
             "(review score, delivery time, late %) are calculated once per order, not once per item. "
             "Late = delivered after the estimated delivery date.")
