"""
Page 2: Beverage Brand Analysis
Analyzes packaged beverage brands to identify which should be dropped.
"""
import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from great_tables import GT
from utils.data_loader import (
    load_transactions_daily_agg, load_master_gtin,
    filter_by_date_range, join_transactions_with_stores
)

st.set_page_config(page_title="Beverage Brands", layout="wide")

st.title("Beverage Brand Analysis")
st.markdown("Analyze packaged beverage brands to identify which should be dropped if necessary.")

# Load data
@st.cache_data
def load_beverage_data():
    """Load and prepare beverage data."""
    daily_agg = load_transactions_daily_agg()
    master_gtin = load_master_gtin()
    
    # Join with product master
    products = daily_agg.join(master_gtin, on="GTIN", how="left")
    
    # Filter to packaged beverages category
    # Common beverage categories: "Packaged Beverages", "Beverages", etc.
    beverage_keywords = ["beverage", "drink", "soda", "juice", "water", "energy"]
    products = products.filter(
        pl.col("CATEGORY").str.to_lowercase().str.contains("|".join(beverage_keywords)) |
        pl.col("SUBCATEGORY").str.to_lowercase().str.contains("|".join(beverage_keywords))
    )
    
    return products

try:
    beverage_df = load_beverage_data()
    
    # Filters
    st.sidebar.header("Filters")
    
    # Date range
    if "DATE" in beverage_df.columns and len(beverage_df) > 0:
        min_date = beverage_df["DATE"].min()
        max_date = beverage_df["DATE"].max()
        
        date_range = st.sidebar.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="beverage_date_range"
        )
        
        if len(date_range) == 2:
            start_date, end_date = date_range
            start_date = datetime.combine(start_date, datetime.min.time())
            end_date = datetime.combine(end_date, datetime.max.time())
            beverage_df = filter_by_date_range(beverage_df, "DATE", start_date, end_date)
    
    # Category filter
    if "CATEGORY" in beverage_df.columns:
        categories = beverage_df["CATEGORY"].drop_nulls().unique().to_list()
        if len(categories) > 0:
            selected_categories = st.sidebar.multiselect(
                "Beverage Categories",
                options=categories,
                default=categories
            )
            if selected_categories:
                beverage_df = beverage_df.filter(pl.col("CATEGORY").is_in(selected_categories))
    
    # Store selection
    from utils.data_loader import load_stores
    stores_info = load_stores()
    
    stores_available = beverage_df["STORE_ID"].unique().to_list()
    if len(stores_available) > 1:
        # Get store info for available stores
        available_stores_info = stores_info.filter(pl.col("STORE_ID").is_in(stores_available))
        
        # Create display names like demographics page
        store_options = available_stores_info.select(["STORE_ID", "STORE_NAME", "STREET_ADDRESS"]).to_pandas()
        store_options["display"] = store_options["STORE_NAME"] + " - " + store_options["STREET_ADDRESS"]
        
        # Create mapping for display
        store_id_to_display = dict(zip(store_options["STORE_ID"], store_options["display"]))
        
        selected_stores = st.sidebar.multiselect(
            "Select Stores",
            options=stores_available,
            default=stores_available,
            format_func=lambda x: store_id_to_display.get(x, f"Store {x}"),
            key="beverage_stores"
        )
        if selected_stores:
            beverage_df = beverage_df.filter(pl.col("STORE_ID").is_in(selected_stores))
    
    if len(beverage_df) == 0:
        st.warning("No beverage data available for the selected filters.")
        st.stop()
    
    # Aggregate by brand
    brand_performance = beverage_df.group_by(["BRAND", "CATEGORY", "MANUFACTURER"]).agg([
        pl.sum("TOTAL_REVENUE_AMOUNT").alias("TOTAL_REVENUE"),
        pl.sum("QUANTITY").alias("TOTAL_QUANTITY"),
        pl.sum("TRANSACTION_COUNT").alias("TOTAL_TRANSACTIONS"),
        pl.mean("TOTAL_REVENUE_AMOUNT").alias("AVG_REVENUE_PER_TRANSACTION")
    ]).sort("TOTAL_REVENUE", descending=True)
    
    # KPIs
    st.header("Key Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)
    
    total_brands = len(brand_performance)
    total_revenue = brand_performance["TOTAL_REVENUE"].sum()
    avg_revenue_per_brand = brand_performance["TOTAL_REVENUE"].mean()
    
    # Calculate drop recommendations (bottom 20% by revenue)
    threshold_percentile = 20
    revenue_threshold = brand_performance["TOTAL_REVENUE"].quantile(threshold_percentile / 100)
    brands_to_drop = brand_performance.filter(pl.col("TOTAL_REVENUE") <= revenue_threshold)
    drop_count = len(brands_to_drop)
    
    with col1:
        st.metric("Total Brands", total_brands)
    with col2:
        st.metric("Total Revenue", f"${total_revenue:,.2f}")
    with col3:
        st.metric("Avg Revenue per Brand", f"${avg_revenue_per_brand:,.2f}")
    with col4:
        st.metric("Brands to Consider Dropping", drop_count, 
                 delta=f"Bottom {threshold_percentile}%")
    
    # Tabs layout
    tab1, tab2, tab3 = st.tabs(["Brand Performance", "Drop Recommendations", "Trend Analysis"])
    
    with tab1:
        # Great Tables - Brand Performance
        st.subheader("Brand Performance Summary")
        
        table_data = brand_performance.select([
            "BRAND", "CATEGORY", "MANUFACTURER",
            "TOTAL_REVENUE", "TOTAL_QUANTITY", "TOTAL_TRANSACTIONS", "AVG_REVENUE_PER_TRANSACTION"
        ]).with_columns(
            (pl.col("TOTAL_REVENUE") / pl.col("TOTAL_QUANTITY")).alias("AVG_PRICE")
        )
        
        table_pd = table_data.to_pandas()
        table_pd = table_pd.rename(columns={
            "BRAND": "Brand",
            "CATEGORY": "Category",
            "MANUFACTURER": "Manufacturer",
            "TOTAL_REVENUE": "Total Revenue",
            "TOTAL_QUANTITY": "Quantity",
            "TOTAL_TRANSACTIONS": "Transactions",
            "AVG_REVENUE_PER_TRANSACTION": "Avg Revenue/Transaction",
            "AVG_PRICE": "Avg Price"
        })
        
        # Create Great Table (don't format numbers as strings - let GT do it)
        gt_table = (
            GT(table_pd)
            .tab_header(title="Brand Performance Analysis")
            .fmt_currency(columns=["Total Revenue", "Avg Revenue/Transaction", "Avg Price"], currency="USD", decimals=2)
            .fmt_number(columns=["Quantity", "Transactions"], decimals=0)
            .data_color(
                columns=["Total Revenue"],
                palette=["#fee5d9", "#fcae91", "#fb6a4a", "#de2d26", "#a50f15"],
                domain=[table_pd["Total Revenue"].min(), table_pd["Total Revenue"].max()]
            )
        )
        
        st.html(gt_table.as_raw_html())
    
    with tab2:
        st.subheader("Brands to Consider Dropping")
        st.markdown(f"Brands in the bottom {threshold_percentile}% by revenue:")
        
        if len(brands_to_drop) > 0:
            drop_table = brands_to_drop.select([
                "BRAND", "CATEGORY", "TOTAL_REVENUE", "TOTAL_QUANTITY", "TOTAL_TRANSACTIONS"
            ]).sort("TOTAL_REVENUE")
            
            drop_pd = drop_table.to_pandas()
            drop_pd = drop_pd.rename(columns={
                "BRAND": "Brand",
                "CATEGORY": "Category",
                "TOTAL_REVENUE": "Total Revenue",
                "TOTAL_QUANTITY": "Quantity",
                "TOTAL_TRANSACTIONS": "Transactions"
            })
            
            drop_pd["Total Revenue"] = drop_pd["Total Revenue"].apply(lambda x: f"${x:,.2f}")
            drop_pd["Quantity"] = drop_pd["Quantity"].apply(lambda x: f"{x:,.0f}")
            drop_pd["Transactions"] = drop_pd["Transactions"].apply(lambda x: f"{x:,.0f}")
            
            st.dataframe(drop_pd, width='stretch')
            
            # Show potential revenue loss
            potential_loss = brands_to_drop["TOTAL_REVENUE"].sum()
            st.info(f"Warning: Dropping these brands would result in approximately **${potential_loss:,.2f}** in lost revenue.")
        else:
            st.info("No brands identified for dropping based on current criteria.")
    
    with tab3:
        # Temporal analysis
        st.subheader("Brand Sales Over Time")
        
        # Aggregate by month and brand
        beverage_df_monthly = beverage_df.with_columns(
            (pl.col("CALENDAR_YEAR").cast(pl.Utf8) + "-" + 
             pl.col("CALENDAR_MONTH").cast(pl.Utf8).str.zfill(2)).alias("YEAR_MONTH")
        )
        
        monthly_brand = beverage_df_monthly.group_by(["YEAR_MONTH", "BRAND"]).agg([
            pl.sum("TOTAL_REVENUE_AMOUNT").alias("MONTHLY_REVENUE")
        ]).sort("YEAR_MONTH")
        
        # Get top 10 brands for visualization
        top_brands = brand_performance.head(10)["BRAND"].to_list()
        monthly_top = monthly_brand.filter(pl.col("BRAND").is_in(top_brands))
        
        chart_df = monthly_top.to_pandas()
        
        fig1 = px.line(
            chart_df,
            x="YEAR_MONTH",
            y="MONTHLY_REVENUE",
            color="BRAND",
            title="Monthly Sales Trend - Top 10 Brands",
            labels={"MONTHLY_REVENUE": "Monthly Revenue ($)", "YEAR_MONTH": "Month"}
        )
        fig1.update_layout(height=500, showlegend=True)
        
        # Add interactive threshold
        threshold = st.number_input(
            "Minimum Sales Threshold ($)",
            min_value=0.0,
            value=float(chart_df["MONTHLY_REVENUE"].quantile(0.25)),
            step=100.0,
            key="beverage_threshold"
        )
        fig1.add_hline(y=threshold, line_dash="dash", line_color="red",
                      annotation_text=f"Threshold: ${threshold:,.0f}")
        
        st.plotly_chart(fig1, width='stretch')
        
        # Brand comparison chart
        st.subheader("Brand Comparison")
        
        comparison_df = brand_performance.head(20).select([
            "BRAND", "TOTAL_REVENUE"
        ]).to_pandas()
        
        fig2 = px.bar(
            comparison_df,
            x="BRAND",
            y="TOTAL_REVENUE",
            title="Top 20 Brands by Revenue",
            labels={"TOTAL_REVENUE": "Total Revenue ($)", "BRAND": "Brand"},
            color="TOTAL_REVENUE",
            color_continuous_scale="Blues"
        )
        fig2.update_layout(height=500, xaxis_tickangle=-45, showlegend=False)
        st.plotly_chart(fig2, width='stretch')

except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    import traceback
    st.code(traceback.format_exc())
