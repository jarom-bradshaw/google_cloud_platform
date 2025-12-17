"""
Page 1: Top 5 Products (Excluding Fuels)
Shows top products by weekly sales with temporal analysis.
"""
import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from great_tables import GT
from utils.data_loader import (
    load_transactions_daily_agg, load_master_gtin,
    filter_by_date_range, join_transactions_with_stores
)
from utils.data_validation import check_missing_data

st.set_page_config(page_title="Top Products", layout="wide")

st.title("Top 5 Products by Weekly Sales")
st.markdown("Analysis of top-selling products (excluding fuels) for Rigby stores.")

# Load data
@st.cache_data
def load_products_data():
    """Load and prepare products data."""
    daily_agg = load_transactions_daily_agg()
    master_gtin = load_master_gtin()
    
    # Join with product master
    # Note: daily_agg already has CATEGORY, BRAND, SKUPOS_DESCRIPTION, but they may be null
    # master_gtin has these too, so we'll get both versions after join
    products = daily_agg.join(master_gtin, on="GTIN", how="left", suffix="_product")
    
    # Coalesce product columns - prefer master_gtin version, fallback to daily_agg version
    coalesce_cols = []
    
    if "SKUPOS_DESCRIPTION_product" in products.columns and "SKUPOS_DESCRIPTION" in products.columns:
        coalesce_cols.append(
            pl.coalesce([
                pl.col("SKUPOS_DESCRIPTION_product"),
                pl.col("SKUPOS_DESCRIPTION")
            ]).alias("SKUPOS_DESCRIPTION")
        )
    elif "SKUPOS_DESCRIPTION_product" in products.columns:
        coalesce_cols.append(pl.col("SKUPOS_DESCRIPTION_product").alias("SKUPOS_DESCRIPTION"))
    elif "SKUPOS_DESCRIPTION" in products.columns:
        coalesce_cols.append(pl.col("SKUPOS_DESCRIPTION").alias("SKUPOS_DESCRIPTION"))
    
    if "BRAND_product" in products.columns and "BRAND" in products.columns:
        coalesce_cols.append(
            pl.coalesce([
                pl.col("BRAND_product"),
                pl.col("BRAND")
            ]).alias("BRAND")
        )
    elif "BRAND_product" in products.columns:
        coalesce_cols.append(pl.col("BRAND_product").alias("BRAND"))
    elif "BRAND" in products.columns:
        coalesce_cols.append(pl.col("BRAND").alias("BRAND"))
    
    if "CATEGORY_product" in products.columns and "CATEGORY" in products.columns:
        coalesce_cols.append(
            pl.coalesce([
                pl.col("CATEGORY_product"),
                pl.col("CATEGORY")
            ]).alias("CATEGORY")
        )
    elif "CATEGORY_product" in products.columns:
        coalesce_cols.append(pl.col("CATEGORY_product").alias("CATEGORY"))
    elif "CATEGORY" in products.columns:
        coalesce_cols.append(pl.col("CATEGORY").alias("CATEGORY"))
    
    if coalesce_cols:
        products = products.with_columns(coalesce_cols)
    
    # Exclude fuels (NONSCAN items) - only include scannable products
    if "SCAN_TYPE" in products.columns:
        products = products.filter(
            pl.col("SCAN_TYPE").is_in(["GTIN", "PLU", "FMT_ERR"])
        )
    
    # Filter to only include products with complete product information
    # This ensures we only show products that have brand, category, and description from either source
    products = products.filter(
        pl.col("SKUPOS_DESCRIPTION").is_not_null() &
        pl.col("BRAND").is_not_null() &
        pl.col("CATEGORY").is_not_null() &
        (pl.col("SKUPOS_DESCRIPTION") != "") &
        (pl.col("BRAND") != "") &
        (pl.col("CATEGORY") != "")
    )
    
    # Join with stores
    stores = load_stores()
    products = products.join(stores, on="STORE_ID", how="left", suffix="_store")
    
    return products

try:
    products_df = load_products_data()
    
    # Date range filter
    st.sidebar.header("Filters")
    
    # Get date range from data
    if "DATE" in products_df.columns and len(products_df) > 0:
        min_date = products_df["DATE"].min()
        max_date = products_df["DATE"].max()
        
        date_range = st.sidebar.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        if len(date_range) == 2:
            start_date, end_date = date_range
            start_date = datetime.combine(start_date, datetime.min.time())
            end_date = datetime.combine(end_date, datetime.max.time())
            products_df = filter_by_date_range(products_df, "DATE", start_date, end_date)
    else:
        st.sidebar.info("Date filtering not available")
    
    # Store selection (if multiple stores)
    stores_info = load_stores()
    
    stores_available = products_df["STORE_ID"].unique().to_list()
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
            format_func=lambda x: store_id_to_display.get(x, f"Store {x}")
        )
        if selected_stores:
            products_df = products_df.filter(pl.col("STORE_ID").is_in(selected_stores))
    else:
        selected_stores = stores_available
    
    if len(products_df) == 0:
        st.warning("No data available for the selected filters.")
        st.stop()
    
    # Calculate weekly sales (note: column is "WEEk" not "WEEK")
    products_df = products_df.with_columns(
        (pl.col("WEEk").cast(pl.Utf8) + "-" + pl.col("CALENDAR_YEAR").cast(pl.Utf8)).alias("WEEK_YEAR")
    )
    
    # After coalesce, we should have SKUPOS_DESCRIPTION, BRAND, CATEGORY columns
    # Aggregate by week and product
    group_cols = ["WEEK_YEAR", "WEEk", "CALENDAR_YEAR", "GTIN"]
    if "SKUPOS_DESCRIPTION" in products_df.columns:
        group_cols.append("SKUPOS_DESCRIPTION")
    if "BRAND" in products_df.columns:
        group_cols.append("BRAND")
    if "CATEGORY" in products_df.columns:
        group_cols.append("CATEGORY")
    
    weekly_sales = products_df.group_by(group_cols).agg([
        pl.sum("TOTAL_REVENUE_AMOUNT").alias("WEEKLY_REVENUE"),
        pl.sum("QUANTITY").alias("WEEKLY_QUANTITY"),
        pl.sum("TRANSACTION_COUNT").alias("WEEKLY_TRANSACTIONS")
    ])
    
    # Get top 5 products by total weekly revenue
    # Include product fields in group_by so they're preserved through aggregation
    top_products = weekly_sales.group_by(["GTIN", "SKUPOS_DESCRIPTION", "BRAND", "CATEGORY"]).agg([
        pl.sum("WEEKLY_REVENUE").alias("TOTAL_REVENUE"),
        pl.sum("WEEKLY_QUANTITY").alias("TOTAL_QUANTITY"),
        pl.sum("WEEKLY_TRANSACTIONS").alias("TOTAL_TRANSACTIONS")
    ]).sort("TOTAL_REVENUE", descending=True).head(5)
    
    # No need to join with master_gtin again - we already have the coalesced data from daily_agg
    
    top_gtins = top_products["GTIN"].to_list()
    
    # Debug: Show sample data to understand what we have
    if st.sidebar.checkbox("Show debug info", value=False):
        st.sidebar.write("Top products sample:")
        st.sidebar.dataframe(top_products.head(2).to_pandas())
        st.sidebar.write("Columns:", top_products.columns)
        if "SKUPOS_DESCRIPTION" in top_products.columns:
            st.sidebar.write("SKUPOS_DESCRIPTION sample:", top_products["SKUPOS_DESCRIPTION"].head(2).to_list())
    
    # KPIs
    st.header("Key Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)
    
    total_revenue = top_products["TOTAL_REVENUE"].sum()
    total_quantity = top_products["TOTAL_QUANTITY"].sum()
    total_transactions = top_products["TOTAL_TRANSACTIONS"].sum()
    avg_revenue_per_product = top_products["TOTAL_REVENUE"].mean()
    
    with col1:
        st.metric("Total Revenue (Top 5)", f"${total_revenue:,.2f}")
    with col2:
        st.metric("Total Quantity Sold", f"{total_quantity:,.0f}")
    with col3:
        st.metric("Total Transactions", f"{total_transactions:,.0f}")
    with col4:
        st.metric("Avg Revenue per Product", f"${avg_revenue_per_product:,.2f}")
    
    # Great Tables summary table
    st.header("Top 5 Products Summary")
    
    # Prepare table data - handle null values
    table_cols = ["TOTAL_REVENUE", "TOTAL_QUANTITY", "TOTAL_TRANSACTIONS"]
    if "SKUPOS_DESCRIPTION" in top_products.columns:
        table_cols.insert(0, "SKUPOS_DESCRIPTION")
    if "BRAND" in top_products.columns:
        table_cols.append("BRAND")
    if "CATEGORY" in top_products.columns:
        table_cols.append("CATEGORY")
    
    table_data = top_products.select(table_cols).with_columns(
        (pl.col("TOTAL_REVENUE") / pl.col("TOTAL_QUANTITY")).alias("AVG_PRICE")
    )
    
    # Don't fill nulls - leave them as null (will display as empty in table)
    
    # Convert to pandas for Great Tables
    table_pd = table_data.to_pandas()
    
    # Don't replace nulls - let them display naturally (Great Tables handles nulls)
    
    table_pd = table_pd.rename(columns={
        "SKUPOS_DESCRIPTION": "Product",
        "BRAND": "Brand",
        "CATEGORY": "Category",
        "TOTAL_REVENUE": "Total Revenue",
        "TOTAL_QUANTITY": "Quantity",
        "TOTAL_TRANSACTIONS": "Transactions",
        "AVG_PRICE": "Avg Price"
    })
    
    # Create Great Table (don't format numbers as strings - let GT do it)
    gt_table = (
        GT(table_pd)
        .tab_header(title="Top 5 Products by Weekly Sales")
        .fmt_currency(columns=["Total Revenue", "Avg Price"], currency="USD", decimals=2)
        .fmt_number(columns=["Quantity", "Transactions"], decimals=0)
        .data_color(
            columns=["Total Revenue"],
            palette=["#f0f0f0", "#2E86AB"],
            domain=[table_pd["Total Revenue"].min(), table_pd["Total Revenue"].max()]
        )
    )
    
    st.html(gt_table.as_raw_html())
    
    # Charts section with columns layout
    st.header("Temporal Analysis")
    
    # Prepare data for charts
    top_weekly = weekly_sales.filter(pl.col("GTIN").is_in(top_gtins))
    
    # Join with top_products to get product names
    join_cols = ["GTIN"]
    if "SKUPOS_DESCRIPTION" in top_products.columns:
        join_cols.append("SKUPOS_DESCRIPTION")
    
    top_weekly = top_weekly.join(
        top_products.select(join_cols),
        on="GTIN",
        how="left"
    )
    
    # Sort by week
    top_weekly = top_weekly.sort(["CALENDAR_YEAR", "WEEk"])
    
    # Convert to pandas for plotly
    chart_select_cols = ["WEEK_YEAR", "WEEKLY_REVENUE"]
    if "SKUPOS_DESCRIPTION" in top_weekly.columns:
        chart_select_cols.insert(1, "SKUPOS_DESCRIPTION")
    
    chart_df = top_weekly.select(chart_select_cols).to_pandas()
    
    # Threshold input on its own row
    threshold = st.number_input(
        "Sales Threshold ($)",
        min_value=0.0,
        value=float(chart_df["WEEKLY_REVENUE"].quantile(0.5)) if len(chart_df) > 0 else 0.0,
        step=100.0,
        key="threshold_1"
    )
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # Weekly sales trend for top 5 products
        if len(chart_df) > 0 and "SKUPOS_DESCRIPTION" in chart_df.columns:
            # Filter out null product names
            chart_df_clean = chart_df.dropna(subset=["SKUPOS_DESCRIPTION"])
            
            if len(chart_df_clean) > 0:
                fig1 = px.line(
                    chart_df_clean,
                    x="WEEK_YEAR",
                    y="WEEKLY_REVENUE",
                    color="SKUPOS_DESCRIPTION",
                    title="Weekly Sales Trend - Top 5 Products",
                    labels={"WEEKLY_REVENUE": "Weekly Revenue ($)", "WEEK_YEAR": "Week"}
                )
                fig1.update_layout(showlegend=True, height=400)
                
                # Add interactive threshold line
                fig1.add_hline(y=threshold, line_dash="dash", line_color="red", 
                              annotation_text=f"Threshold: ${threshold:,.0f}")
                
                st.plotly_chart(fig1, width='stretch')
            else:
                st.warning("No data available for the chart.")
        else:
            st.warning("Product description data not available.")
    
    with col_chart2:
        # Product comparison bar chart
        comparison_df = top_products.select([
            "SKUPOS_DESCRIPTION", "TOTAL_REVENUE", "TOTAL_QUANTITY"
        ]).to_pandas()
        
        # Filter out null product names
        comparison_df = comparison_df.dropna(subset=["SKUPOS_DESCRIPTION"])
        
        if len(comparison_df) > 0:
            fig2 = px.bar(
                comparison_df,
                x="SKUPOS_DESCRIPTION",
                y="TOTAL_REVENUE",
                title="Total Revenue by Product",
                labels={"TOTAL_REVENUE": "Total Revenue ($)", "SKUPOS_DESCRIPTION": "Product"},
                color="TOTAL_REVENUE",
                color_continuous_scale="Blues"
            )
            fig2.update_layout(showlegend=False, height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig2, width='stretch')
        else:
            st.warning("No product data available for the chart.")
    
    # Additional analysis in expander
    with st.expander("Additional Metrics", expanded=False):
        st.subheader("Revenue Distribution")
        
        # Calculate percentage of total
        top_products_pct = top_products.with_columns(
            (pl.col("TOTAL_REVENUE") / total_revenue * 100).alias("PCT_OF_TOTAL")
        )
        
        pct_df = top_products_pct.select(["SKUPOS_DESCRIPTION", "PCT_OF_TOTAL"]).to_pandas()
        
        fig3 = px.pie(
            pct_df,
            values="PCT_OF_TOTAL",
            names="SKUPOS_DESCRIPTION",
            title="Revenue Share - Top 5 Products"
        )
        st.plotly_chart(fig3, width='stretch')

except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    import traceback
    st.code(traceback.format_exc())
