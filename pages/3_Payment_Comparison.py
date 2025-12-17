"""
Page 3: Cash vs Credit Customer Comparison
Compares cash and credit customers across multiple dimensions.
"""
import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from great_tables import GT
from utils.data_loader import (
    load_transaction_sets, load_transaction_items,
    load_payments, load_master_gtin,
    filter_by_date_range, join_transactions_with_products
)

st.set_page_config(page_title="Payment Comparison", layout="wide")

st.title("Cash vs Credit Customer Comparison")
st.markdown("Compare cash and credit customers across products, purchase amounts, and item counts.")

# Load data
@st.cache_data
def load_payment_data():
    """Load and prepare payment comparison data."""
    transaction_sets = load_transaction_sets()
    transaction_items = load_transaction_items()
    payments = load_payments()
    master_gtin = load_master_gtin()
    
    # Join transaction sets with payments to get payment type
    transactions_with_payment = transaction_sets.join(
        payments.select(["TRANSACTION_SET_ID", "PAYMENT_TYPE", "CARD_TYPE"]),
        on="TRANSACTION_SET_ID",
        how="left"
    )
    
    # Join transaction items with products
    items_with_products = transaction_items.join(
        master_gtin,
        on="GTIN",
        how="left"
    )
    
    # Join items with payment info
    items_with_payment = items_with_products.join(
        transactions_with_payment.select(["TRANSACTION_SET_ID", "PAYMENT_TYPE"]),
        on="TRANSACTION_SET_ID",
        how="left"
    )
    
    return transactions_with_payment, items_with_payment

try:
    transactions_df, items_df = load_payment_data()
    
    # Filters
    st.sidebar.header("Filters")
    
    # Date range
    if "DATE_TIME" in transactions_df.columns and len(transactions_df) > 0:
        min_date = transactions_df["DATE_TIME"].min()
        max_date = transactions_df["DATE_TIME"].max()
        
        date_range = st.sidebar.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="payment_date_range"
        )
        
        if len(date_range) == 2:
            start_date, end_date = date_range
            start_date = datetime.combine(start_date, datetime.min.time())
            end_date = datetime.combine(end_date, datetime.max.time())
            transactions_df = filter_by_date_range(transactions_df, "DATE_TIME", start_date, end_date)
            items_df = filter_by_date_range(items_df, "DATE_TIME", start_date, end_date)
    
    # Payment type filter
    if "PAYMENT_TYPE" in transactions_df.columns:
        payment_types = transactions_df["PAYMENT_TYPE"].drop_nulls().unique().to_list()
        # Normalize payment types - categorize as cash or credit
        cash_types = ["cash", "Cash", "CASH"]
        credit_types = ["credit", "Credit", "CREDIT", "debit", "Debit", "DEBIT", "card", "Card"]
        
        # Create payment category
        transactions_df = transactions_df.with_columns(
            pl.when(pl.col("PAYMENT_TYPE").str.to_lowercase().is_in([t.lower() for t in cash_types]))
            .then(pl.lit("Cash"))
            .when(pl.col("PAYMENT_TYPE").str.to_lowercase().is_in([t.lower() for t in credit_types]))
            .then(pl.lit("Credit"))
            .otherwise(pl.lit("Other"))
            .alias("PAYMENT_CATEGORY")
        )
        
        items_df = items_df.join(
            transactions_df.select(["TRANSACTION_SET_ID", "PAYMENT_CATEGORY"]),
            on="TRANSACTION_SET_ID",
            how="left"
        )
        
        selected_categories = st.sidebar.multiselect(
            "Payment Types",
            options=["Cash", "Credit", "Other"],
            default=["Cash", "Credit"],
            key="payment_categories"
        )
        
        if selected_categories:
            transactions_df = transactions_df.filter(pl.col("PAYMENT_CATEGORY").is_in(selected_categories))
            items_df = items_df.filter(pl.col("PAYMENT_CATEGORY").is_in(selected_categories))
    
    # Store selection
    from utils.data_loader import load_stores
    stores_info = load_stores()
    
    stores_available = transactions_df["STORE_ID"].unique().to_list()
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
            key="payment_stores"
        )
        if selected_stores:
            transactions_df = transactions_df.filter(pl.col("STORE_ID").is_in(selected_stores))
            items_df = items_df.filter(pl.col("STORE_ID").is_in(selected_stores))
    
    if len(transactions_df) == 0:
        st.warning("No data available for the selected filters.")
        st.stop()
    
    # KPIs
    st.header("Key Performance Indicators")
    
    # Calculate metrics by payment category
    payment_metrics = transactions_df.group_by("PAYMENT_CATEGORY").agg([
        pl.len().alias("TRANSACTION_COUNT"),
        pl.sum("GRAND_TOTAL_AMOUNT").alias("TOTAL_AMOUNT"),
        pl.mean("GRAND_TOTAL_AMOUNT").alias("AVG_TRANSACTION_AMOUNT")
    ])
    
    # Get item counts by payment category
    item_counts = items_df.group_by("PAYMENT_CATEGORY").agg([
        pl.len().alias("ITEM_COUNT"),
        pl.sum("UNIT_QUANTITY").alias("TOTAL_QUANTITY")
    ])
    
    # Combine metrics
    payment_summary = payment_metrics.join(item_counts, on="PAYMENT_CATEGORY", how="left")
    
    # Display KPIs in columns
    col1, col2, col3, col4 = st.columns(4)
    
    cash_data = payment_summary.filter(pl.col("PAYMENT_CATEGORY") == "Cash")
    credit_data = payment_summary.filter(pl.col("PAYMENT_CATEGORY") == "Credit")
    
    cash_transactions = cash_data["TRANSACTION_COUNT"].sum() if len(cash_data) > 0 else 0
    credit_transactions = credit_data["TRANSACTION_COUNT"].sum() if len(credit_data) > 0 else 0
    cash_total = cash_data["TOTAL_AMOUNT"].sum() if len(cash_data) > 0 else 0
    credit_total = credit_data["TOTAL_AMOUNT"].sum() if len(credit_data) > 0 else 0
    cash_avg = cash_data["AVG_TRANSACTION_AMOUNT"].mean() if len(cash_data) > 0 else 0
    credit_avg = credit_data["AVG_TRANSACTION_AMOUNT"].mean() if len(credit_data) > 0 else 0
    cash_items = cash_data["ITEM_COUNT"].sum() if len(cash_data) > 0 else 0
    credit_items = credit_data["ITEM_COUNT"].sum() if len(credit_data) > 0 else 0
    
    with col1:
        st.metric("Cash Transactions", f"{cash_transactions:,}", 
                 delta=f"{cash_transactions - credit_transactions:,}" if credit_transactions > 0 else None)
        st.metric("Credit Transactions", f"{credit_transactions:,}")
    with col2:
        st.metric("Cash Total Amount", f"${cash_total:,.2f}",
                 delta=f"${cash_total - credit_total:,.2f}" if credit_total > 0 else None)
        st.metric("Credit Total Amount", f"${credit_total:,.2f}")
    with col3:
        st.metric("Cash Avg Transaction", f"${cash_avg:,.2f}",
                 delta=f"${cash_avg - credit_avg:,.2f}" if credit_avg > 0 else None)
        st.metric("Credit Avg Transaction", f"${credit_avg:,.2f}")
    with col4:
        st.metric("Cash Items Purchased", f"{cash_items:,}",
                 delta=f"{cash_items - credit_items:,}" if credit_items > 0 else None)
        st.metric("Credit Items Purchased", f"{credit_items:,}")
    
    # Layout with columns and sidebar
    col_main, col_side = st.columns([3, 1])
    
    with col_main:
        # Great Tables - Product preferences by payment type
        st.header("Product Preferences by Payment Type")
        
        # Top products by payment type
        product_preferences = items_df.group_by(["PAYMENT_CATEGORY", "SKUPOS_DESCRIPTION", "BRAND", "CATEGORY"]).agg([
            pl.len().alias("PURCHASE_COUNT"),
            pl.sum("GRAND_TOTAL_AMOUNT").alias("TOTAL_REVENUE"),
            pl.sum("UNIT_QUANTITY").alias("TOTAL_QUANTITY")
        ]).sort(["PAYMENT_CATEGORY", "PURCHASE_COUNT"], descending=[False, True])
        
        # Get top 10 products for each payment type
        top_cash = product_preferences.filter(pl.col("PAYMENT_CATEGORY") == "Cash").head(10)
        top_credit = product_preferences.filter(pl.col("PAYMENT_CATEGORY") == "Credit").head(10)
        
        # Combine for table
        top_products_combined = pl.concat([top_cash, top_credit])
        
        table_pd = top_products_combined.select([
            "PAYMENT_CATEGORY", "SKUPOS_DESCRIPTION", "BRAND",
            "PURCHASE_COUNT", "TOTAL_REVENUE", "TOTAL_QUANTITY"
        ]).to_pandas()
        
        table_pd = table_pd.rename(columns={
            "PAYMENT_CATEGORY": "Payment Type",
            "SKUPOS_DESCRIPTION": "Product",
            "BRAND": "Brand",
            "PURCHASE_COUNT": "Purchases",
            "TOTAL_REVENUE": "Total Revenue",
            "TOTAL_QUANTITY": "Quantity"
        })
        
        # Create Great Table (don't format numbers as strings - let GT do it)
        gt_table = (
            GT(table_pd)
            .tab_header(title="Top Products by Payment Type")
            .fmt_currency(columns=["Total Revenue"], currency="USD", decimals=2)
            .fmt_number(columns=["Purchases", "Quantity"], decimals=0)
            .data_color(
                columns=["Total Revenue"],
                palette=["#e3f2fd", "#1976d2"],
                domain=[table_pd["Total Revenue"].min(), table_pd["Total Revenue"].max()]
            )
        )
        
        st.html(gt_table.as_raw_html())
        
        # Charts
        st.header("Payment Type Trends")
        
        # Prepare data for charts
        transactions_monthly = transactions_df.with_columns(
            pl.col("DATE_TIME").dt.strftime("%Y-%m").alias("YEAR_MONTH")
        )
        
        monthly_payment = transactions_monthly.group_by(["YEAR_MONTH", "PAYMENT_CATEGORY"]).agg([
            pl.len().alias("TRANSACTION_COUNT"),
            pl.sum("GRAND_TOTAL_AMOUNT").alias("TOTAL_AMOUNT")
        ]).sort("YEAR_MONTH")
        
        chart_df = monthly_payment.to_pandas()
        
        # Dropdown on its own row
        avg_amount = st.number_input(
            "Average Transaction Amount ($)",
            min_value=0.0,
            value=float(transactions_df["GRAND_TOTAL_AMOUNT"].mean()),
            step=1.0,
            key="payment_avg"
        )
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            # Payment type trends over time
            fig1 = px.line(
                chart_df,
                x="YEAR_MONTH",
                y="TOTAL_AMOUNT",
                color="PAYMENT_CATEGORY",
                title="Monthly Revenue by Payment Type",
                labels={"TOTAL_AMOUNT": "Revenue ($)", "YEAR_MONTH": "Month"}
            )
            fig1.update_layout(height=400, showlegend=True)
            
            # Add interactive average line
            fig1.add_hline(y=avg_amount, line_dash="dash", line_color="green",
                          annotation_text=f"Avg: ${avg_amount:,.2f}")
            
            st.plotly_chart(fig1, width='stretch')
        
        with col_chart2:
            # Product comparison by payment type
            product_comparison = items_df.group_by(["PAYMENT_CATEGORY", "SKUPOS_DESCRIPTION"]).agg([
                pl.len().alias("PURCHASE_COUNT")
            ]).sort("PURCHASE_COUNT", descending=True).head(20)
            
            comp_df = product_comparison.to_pandas()
            
            fig2 = px.bar(
                comp_df,
                x="SKUPOS_DESCRIPTION",
                y="PURCHASE_COUNT",
                color="PAYMENT_CATEGORY",
                title="Top Products by Purchase Count",
                labels={"PURCHASE_COUNT": "Purchase Count", "SKUPOS_DESCRIPTION": "Product"},
                barmode="group"
            )
            fig2.update_layout(height=400, xaxis_tickangle=-45, showlegend=True)
            st.plotly_chart(fig2, width='stretch')
    
    with col_side:
        st.sidebar.markdown("### Payment Type Distribution")
        
        # Payment type distribution
        payment_dist = payment_summary.select(["PAYMENT_CATEGORY", "TRANSACTION_COUNT"]).to_pandas()
        
        if len(payment_dist) > 0:
            fig3 = px.pie(
                payment_dist,
                values="TRANSACTION_COUNT",
                names="PAYMENT_CATEGORY",
                title="Transaction Distribution"
            )
            st.sidebar.plotly_chart(fig3, width='stretch')
        
        # Summary stats
        st.sidebar.markdown("### Summary")
        st.sidebar.metric("Total Transactions", f"{payment_summary['TRANSACTION_COUNT'].sum():,}")
        st.sidebar.metric("Total Revenue", f"${payment_summary['TOTAL_AMOUNT'].sum():,.2f}")

except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    import traceback
    st.code(traceback.format_exc())
