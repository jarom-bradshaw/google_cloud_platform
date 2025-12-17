"""
Page 0: Basic Data EDA using Polars
Shows heads, schema, row counts, and null statistics for key tables.
"""
import streamlit as st
from pathlib import Path
import polars as pl
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder


st.set_page_config(page_title="Data Overview (EDA)", layout="wide")

st.title("Data Overview (EDA)")
st.markdown(
    """
Basic exploratory analysis of the Idaho convenience store data.

Use this page to quickly inspect table schemas, sample rows, and null-value patterns
for the core parquet datasets.
"""
)


DATA_DIR = Path("data")

# Map friendly table names to parquet locations
TABLES = {
    "Stores (`cstore_stores`)": DATA_DIR / "cstore_stores.parquet",
    "Store Status (`cstore_store_status`)": DATA_DIR / "cstore_store_status.parquet",
    "Master GTIN / Products (`cstore_master_ctin`)": DATA_DIR / "cstore_master_ctin.parquet",
    "Transactions Daily Aggregate (`cstore_transactions_daily_agg`)": DATA_DIR
    / "cstore_transactions_daily_agg.parquet",
    "Transaction Sets (`cstore_transaction_sets`)": DATA_DIR / "cstore_transaction_sets.parquet",
    "Transaction Items (partitioned)": DATA_DIR / "transaction_items",
    "Payments (`cstore_payments`)": DATA_DIR / "cstore_payments.parquet",
    "Discounts (`cstore_discounts`)": DATA_DIR / "cstore_discounts.parquet",
    "Shopper (`cstore_shopper`)": DATA_DIR / "cstore_shopper.parquet",
}


@st.cache_data
def load_table(table_label: str):
    """Load a table as a Polars DataFrame."""
    path = TABLES[table_label]
    
    # transaction_items is a directory of parquet parts; others are single files
    if path.is_dir():
        # Read all parquet files in the directory
        return pl.read_parquet(path / "*.parquet")
    else:
        return pl.read_parquet(path)


@st.cache_data
def get_available_cities():
    """Get list of all available cities from stores table."""
    from utils.data_loader import load_all_stores
    stores = load_all_stores()
    if "CITY" in stores.columns:
        cities = stores["CITY"].drop_nulls().unique().sort().to_list()
        return cities
    return []


st.sidebar.header("Data Selection")
table_label = st.sidebar.selectbox("Choose a table", options=list(TABLES.keys()))

# City filter for stores tables
available_cities = get_available_cities()
default_cities = ["Rigby", "Ririe", "Rexburg"]
# Ensure default cities exist in available cities
default_cities = [city for city in default_cities if city in available_cities]

# Only show city filter for stores tables
table_name = table_label.split()[0]
if table_name in ["Stores", "Store Status"]:
    selected_cities = st.sidebar.multiselect(
        "Filter by City",
        options=available_cities,
        default=default_cities,
        key="city_filter_eda"
    )
else:
    selected_cities = None

# AgGrid pagination settings
page_size = st.sidebar.slider(
    "Rows per page",
    min_value=10,
    max_value=100,
    value=25,
    step=5,
)

try:
    df = load_table(table_label)
    
    # Apply city filter for stores tables
    if table_name in ["Stores", "Store Status"] and selected_cities:
        if "CITY" in df.columns:
            df = df.filter(pl.col("CITY").is_in(selected_cities))
            if len(df) == 0:
                st.warning(f"No stores found in selected cities: {', '.join(selected_cities)}")
                st.stop()
            else:
                # Show city breakdown
                city_counts = df.group_by("CITY").agg(pl.len().alias("count")).sort("CITY")
                city_info = ", ".join([f"{row['CITY']} ({row['count']})" for row in city_counts.to_dicts()])
                st.info(f"**Selected cities:** {city_info}")

    # Basic info
    st.subheader("Table Summary")
    row_count = len(df)
    col_count = len(df.columns)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Rows", f"{row_count:,}")
    with col2:
        st.metric("Columns", col_count)
    with col3:
        st.metric("Table", table_label.split()[0])

    # Schema
    st.subheader("Schema")
    schema_data = [
        {
            "column": col_name,
            "type": str(dtype),
        }
        for col_name, dtype in df.schema.items()
    ]
    schema_df = pd.DataFrame(schema_data)
    st.dataframe(schema_df, width='stretch')

    # Interactive data table with pagination and search
    st.subheader("Interactive Data Table")
    st.markdown("Use the search box and pagination controls below to explore the data.")
    
    # Define essential columns for each table type
    essential_columns = {
        "Stores": ["STORE_ID", "STORE_NAME", "STORE_CHAIN_NAME", "CITY", "STATE", "ZIP_CODE", "STREET_ADDRESS"],
        "Store Status": ["STORE_ID", "STORE_NAME", "STORE_CHAIN_NAME", "CITY", "STATE", "ACTIVE_STATUS", "STORE_FLAG"],
    }
    
    # For stores tables, only show essential columns
    if table_name in essential_columns:
        available_cols = [col for col in essential_columns[table_name] if col in df.columns]
        if available_cols:
            df = df.select(available_cols)
            st.info(f"Showing essential columns only: {', '.join(available_cols)}")
    
    # Convert to pandas for AgGrid
    data_pd = df.to_pandas()
    
    # Fix display issues - convert object columns to string
    for col in data_pd.columns:
        if data_pd[col].dtype == 'object':
            # Convert object columns to string to avoid "object Object" display
            data_pd[col] = data_pd[col].astype(str).replace('nan', '')
    
    # Configure AgGrid
    gb = GridOptionsBuilder.from_dataframe(data_pd)
    gb.configure_pagination(
        paginationAutoPageSize=False,
        paginationPageSize=page_size
    )
    gb.configure_default_column(
        resizable=True,
        sortable=True,
        filterable=True,
        editable=False
    )
    gb.configure_selection('single')  # Allow row selection if needed
    
    grid_options = gb.build()
    
    # Display the AgGrid table
    AgGrid(
        data_pd,
        gridOptions=grid_options,
        update_on='MODEL_CHANGED',
        height=600,
        width='100%',
        theme='streamlit',
        allow_unsafe_jscode=True
    )

    # Duplicate check for stores tables
    if table_name in ["Stores", "Store Status"]:
        st.subheader("Duplicate Check")
        from utils.data_validation import check_duplicate_store_ids, check_duplicate_street_addresses
        
        # Check for duplicate STORE_IDs
        has_dup_ids, dup_ids_df = check_duplicate_store_ids(df)
        if has_dup_ids:
            st.warning(f"Found {len(dup_ids_df)} records with duplicate STORE_IDs")
            with st.expander("View duplicate STORE_IDs", expanded=False):
                st.dataframe(dup_ids_df.to_pandas(), width='stretch')
        else:
            st.success("No duplicate STORE_IDs found")
        
        # Check for duplicate street addresses
        has_dup_addresses, dup_addresses_df = check_duplicate_street_addresses(df)
        if has_dup_addresses:
            st.warning(f"Found {len(dup_addresses_df)} records with duplicate street addresses")
            with st.expander("View duplicate street addresses", expanded=False):
                st.dataframe(dup_addresses_df.to_pandas(), width='stretch')
        else:
            st.success("No duplicate street addresses found")

    # Null counts and percentages
    st.subheader("Null Values by Column")
    if row_count > 0:
        null_stats = []
        for col in df.columns:
            null_count = df[col].null_count()
            null_pct = (null_count / row_count) * 100.0
            null_stats.append({
                "column": col,
                "null_count": null_count,
                "null_pct": round(null_pct, 2),
            })
        
        null_df = pd.DataFrame(null_stats)
        null_df = null_df.sort_values("null_pct", ascending=False).reset_index(drop=True)
        st.dataframe(null_df, width='stretch')
    else:
        st.info("Table has zero rows; null statistics are not applicable.")

except Exception as e:
    st.error(f"Error loading or analyzing `{table_label}`: {e}")
    import traceback
    st.code(traceback.format_exc())
