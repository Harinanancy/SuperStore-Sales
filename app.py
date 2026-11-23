
import streamlit as st
import pandas as pd
import plotly.express as px


# --------------------------------
# 1. PAGE CONFIGURATION
# --------------------------------

st.set_page_config(
    page_title="Superstore Sales Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Superstore Sales Analytics Dashboard")
st.markdown("Interactive Sales and Profit Analysis")

# --------------------------------
# 2. DATA UPLOAD
# --------------------------------

uploaded = st.file_uploader(
    "Upload Superstore CSV Dataset",
    type=["csv"]
)

try:
    if uploaded is not None:

        try:
            df = pd.read_csv(uploaded, encoding="cp1252")

        except UnicodeDecodeError:
            uploaded.seek(0)
            df = pd.read_csv(uploaded, encoding="latin1")

    else:

        try:
            df = pd.read_csv("data.csv", encoding="cp1252")

        except UnicodeDecodeError:
            df = pd.read_csv("data.csv", encoding="latin1")

except FileNotFoundError:
    st.error(
        "Please upload your CSV file or place data.csv "
        "in your project folder."
    )
    st.stop()

# --------------------------------
# 3. CLEAN COLUMN NAMES
# --------------------------------

df.columns = df.columns.str.strip()

st.success(
    f"Dataset loaded successfully! Total Records: {len(df):,}"
)

st.write("Dataset Shape:", df.shape)

st.dataframe(df.head(), use_container_width=True)

# 3. DATA CLEANING
# --------------------------------

required_columns = [
    "Order ID", "Order Date", "Ship Date",
    "Ship Mode", "Customer ID", "Customer Name",
    "Segment", "State", "Region", "Category",
    "Sub-Category", "Product Name",
    "Sales", "Quantity", "Discount", "Profit"
]

missing = [col for col in required_columns if col not in df.columns]

if missing:
    st.error(f"Missing columns in dataset: {missing}")
    st.stop()

# Convert date columns
df["Order Date"] = pd.to_datetime(
    df["Order Date"],
    format="mixed",
    errors="coerce"
)

df["Ship Date"] = pd.to_datetime(
    df["Ship Date"],
    format="mixed",
    errors="coerce"
)

# Convert numeric columns
numeric_columns = ["Sales", "Quantity", "Discount", "Profit"]

for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Remove duplicate records
df.drop_duplicates(inplace=True)

# Remove rows with missing essential values
df.dropna(
    subset=[
        "Order ID", "Order Date", "Customer ID",
        "State", "Category", "Sales", "Quantity",
        "Discount", "Profit"
    ],
    inplace=True
)

# Create additional columns
df["Order Month"] = df["Order Date"].dt.to_period("M").astype(str)

df["Order Year"] = df["Order Date"].dt.year

df["Discount %"] = df["Discount"] * 100

st.success(f"Dataset loaded successfully! Total records: {len(df):,}")

# --------------------------------
# 4. SIDEBAR FILTERS
# --------------------------------

st.sidebar.header("🔍 Dashboard Filters")

states = sorted(df["State"].dropna().unique())
categories = sorted(df["Category"].dropna().unique())
segments = sorted(df["Segment"].dropna().unique())
regions = sorted(df["Region"].dropna().unique())

selected_states = st.sidebar.multiselect(
    "Select State",
    states,
    default=states
)

selected_categories = st.sidebar.multiselect(
    "Select Category",
    categories,
    default=categories
)

selected_segments = st.sidebar.multiselect(
    "Select Customer Segment",
    segments,
    default=segments
)

selected_regions = st.sidebar.multiselect(
    "Select Region",
    regions,
    default=regions
)

min_date = df["Order Date"].min().date()
max_date = df["Order Date"].max().date()

selected_dates = st.sidebar.date_input(
    "Select Order Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date, end_date = min_date, max_date

# --------------------------------
# 5. APPLY FILTERS
# --------------------------------

filtered = df[
    (df["State"].isin(selected_states)) &
    (df["Category"].isin(selected_categories)) &
    (df["Segment"].isin(selected_segments)) &
    (df["Region"].isin(selected_regions)) &
    (df["Order Date"].dt.date >= start_date) &
    (df["Order Date"].dt.date <= end_date)
].copy()

if filtered.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# --------------------------------
# 6. KPI METRICS
# --------------------------------

total_sales = filtered["Sales"].sum()
total_profit = filtered["Profit"].sum()
total_orders = filtered["Order ID"].nunique()
total_customers = filtered["Customer ID"].nunique()
total_quantity = filtered["Quantity"].sum()

avg_order_value = total_sales / total_orders if total_orders else 0

profit_margin = (
    (total_profit / total_sales) * 100
    if total_sales else 0
)

st.subheader("📌 Business Performance")

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Total Sales", f"${total_sales:,.2f}")
c2.metric("Total Profit", f"${total_profit:,.2f}")
c3.metric("Total Orders", f"{total_orders:,}")
c4.metric("Customers", f"{total_customers:,}")
c5.metric("Total Quantity", f"{total_quantity:,}")

c6, c7 = st.columns(2)

c6.metric("Average Order Value", f"${avg_order_value:,.2f}")
c7.metric("Profit Margin", f"{profit_margin:.2f}%")

st.divider()

# --------------------------------
# 7. DATASET VIEW
# --------------------------------

st.subheader("📋 Sales Dataset")

st.write(f"Filtered Records: {len(filtered):,}")

st.dataframe(
    filtered,
    use_container_width=True,
    height=350
)

st.divider()

# --------------------------------
# 8. MONTHLY SALES ANALYSIS
# --------------------------------

st.subheader("📈 Monthly Sales Trend")

monthly_sales = (
    filtered.groupby("Order Month")["Sales"]
    .sum()
    .reset_index()
)

fig = px.line(
    monthly_sales,
    x="Order Month",
    y="Sales",
    markers=True,
    title="Monthly Sales Trend"
)

st.plotly_chart(fig, use_container_width=True)

# --------------------------------
# 9. SALES BY REGION
# --------------------------------

st.subheader("🌍 Sales by Region")

region_sales = (
    filtered.groupby("Region")["Sales"]
    .sum()
    .reset_index()
    .sort_values("Sales", ascending=False)
)

fig = px.bar(
    region_sales,
    x="Region",
    y="Sales",
    color="Sales",
    title="Regional Sales Performance",
    text_auto=".2s"
)

st.plotly_chart(fig, use_container_width=True)

# --------------------------------
# 10. SALES BY STATE
# --------------------------------

st.subheader("🏙️ Sales by State")

state_sales = (
    filtered.groupby("State")["Sales"]
    .sum()
    .sort_values(ascending=False)
    .head(15)
    .reset_index()
)

fig = px.bar(
    state_sales,
    x="State",
    y="Sales",
    color="Sales",
    title="Top 15 States by Sales"
)

st.plotly_chart(fig, use_container_width=True)

# --------------------------------
# 11. CATEGORY CONTRIBUTION
# --------------------------------

st.subheader("📦 Category Analysis")

category_sales = (
    filtered.groupby("Category")["Sales"]
    .sum()
    .reset_index()
)

fig = px.pie(
    category_sales,
    names="Category",
    values="Sales",
    title="Sales Contribution by Category",
    hole=0.4
)

st.plotly_chart(fig, use_container_width=True)

# --------------------------------
# 12. SUB-CATEGORY ANALYSIS
# --------------------------------

st.subheader("📊 Sales by Sub-Category")

sub_category = (
    filtered.groupby("Sub-Category")["Sales"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)

fig = px.bar(
    sub_category,
    x="Sales",
    y="Sub-Category",
    orientation="h",
    color="Sales",
    title="Sub-Category Sales Performance"
)

st.plotly_chart(fig, use_container_width=True)

# --------------------------------
# 13. TOP 10 PRODUCTS
# --------------------------------

st.subheader("🏆 Top 10 Products")

top_products = (
    filtered.groupby("Product Name")["Sales"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)

fig = px.bar(
    top_products,
    x="Sales",
    y="Product Name",
    orientation="h",
    color="Sales",
    title="Top 10 Best-Selling Products"
)

fig.update_layout(yaxis={"categoryorder": "total ascending"})

st.plotly_chart(fig, use_container_width=True)

# --------------------------------
# 14. PROFIT ANALYSIS
# --------------------------------

st.subheader("💰 Profit by Category")

profit_category = (
    filtered.groupby("Category")["Profit"]
    .sum()
    .reset_index()
)

fig = px.bar(
    profit_category,
    x="Category",
    y="Profit",
    color="Profit",
    title="Profit Analysis by Category"
)

st.plotly_chart(fig, use_container_width=True)

# --------------------------------
# 15. CUSTOMER SEGMENT ANALYSIS
# --------------------------------

st.subheader("👥 Customer Segment Analysis")

segment_sales = (
    filtered.groupby("Segment")["Sales"]
    .sum()
    .reset_index()
)

fig = px.pie(
    segment_sales,
    names="Segment",
    values="Sales",
    title="Sales by Customer Segment"
)

st.plotly_chart(fig, use_container_width=True)

# --------------------------------
# 16. SHIPPING MODE ANALYSIS
# --------------------------------

st.subheader("🚚 Shipping Mode Analysis")

shipping = (
    filtered.groupby("Ship Mode")
    .agg(
        Orders=("Order ID", "nunique"),
        Sales=("Sales", "sum")
    )
    .reset_index()
)

fig = px.bar(
    shipping,
    x="Ship Mode",
    y="Orders",
    color="Ship Mode",
    title="Orders by Shipping Mode"
)

st.plotly_chart(fig, use_container_width=True)

# --------------------------------
# 17. DISCOUNT VS PROFIT
# --------------------------------

st.subheader("📉 Discount vs Profit Analysis")

fig = px.scatter(
    filtered,
    x="Discount %",
    y="Profit",
    color="Category",
    size="Sales",
    hover_data=["Product Name", "Sales"],
    title="Relationship Between Discount and Profit"
)

st.plotly_chart(fig, use_container_width=True)

# --------------------------------
# 18. QUANTITY ANALYSIS
# --------------------------------

st.subheader("📦 Quantity Sold by Category")

quantity_category = (
    filtered.groupby("Category")["Quantity"]
    .sum()
    .reset_index()
)

fig = px.bar(
    quantity_category,
    x="Category",
    y="Quantity",
    color="Category",
    title="Quantity Sold by Category"
)

st.plotly_chart(fig, use_container_width=True)

# --------------------------------
# 19. BUSINESS SUMMARY
# --------------------------------

st.divider()

st.subheader("📝 Business Insights")

best_state = (
    filtered.groupby("State")["Sales"]
    .sum()
    .idxmax()
)

best_product = (
    filtered.groupby("Product Name")["Sales"]
    .sum()
    .idxmax()
)

best_category = (
    filtered.groupby("Category")["Sales"]
    .sum()
    .idxmax()
)

best_region = (
    filtered.groupby("Region")["Sales"]
    .sum()
    .idxmax()
)

st.write("🏙️ Highest Sales State:", best_state)
st.write("🏆 Best-Selling Product:", best_product)
st.write("📦 Highest Sales Category:", best_category)
st.write("🌍 Best Performing Region:", best_region)
st.write("💰 Total Revenue:", f"${total_sales:,.2f}")
st.write("📈 Total Profit:", f"${total_profit:,.2f}")
st.write("👥 Total Customers:", f"{total_customers:,}")

# --------------------------------
# 20. DOWNLOAD FILTERED DATA
# --------------------------------

st.divider()

csv = filtered.to_csv(index=False).encode("utf-8")

st.download_button(
    label="⬇️ Download Filtered Sales Data",
    data=csv,
    file_name="Superstore_Filtered_Sales.csv",
    mime="text/csv"
)

st.success("Sales Analytics Dashboard Successfully Loaded!")

