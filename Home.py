"""
Main Streamlit app for CStore Dashboard.
Multi-page dashboard for analyzing convenience store transaction data.
"""
import streamlit as st
import polars as pl
import plotly.io as pio
from utils.data_loader import load_stores, get_rigby_store_ids
from utils.data_validation import run_full_validation, display_validation_summary

# Set page config
st.set_page_config(
    page_title="CStore Dashboard",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "CStore Dashboard - Convenience Store Analytics"
    }
)

# Set default plotly template
pio.templates.default = "simple_white"

# Initialize session state for data
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False
if "validation_results" not in st.session_state:
    st.session_state.validation_results = None

# Sidebar navigation and data info
with st.sidebar:
    st.title("CStore Dashboard")
    st.markdown("### Rigby, Ririe & Rexburg Stores Analysis")
    
    # Data validation section
    with st.expander("Data Quality", expanded=False):
        if st.button("Run Validation"):
            with st.spinner("Validating data..."):
                st.session_state.validation_results = run_full_validation()
        
        if st.session_state.validation_results:
            display_validation_summary(st.session_state.validation_results)
    
    # Store information
    try:
        stores = load_stores()
        store_count = len(stores)
        st.info(f"**{store_count}** store(s) loaded (Rigby, Ririe & Rexburg)")
        
        if store_count > 0:
            store_names = stores["STORE_NAME"].unique().to_list()
            if len(store_names) > 0:
                st.markdown("**Store(s):**")
                for name in store_names[:5]:  # Show first 5
                    st.markdown(f"- {name}")
                if len(store_names) > 5:
                    st.caption(f"... and {len(store_names) - 5} more")
    except Exception as e:
        st.error(f"Error loading stores: {str(e)}")
    
    st.markdown("---")
    st.markdown("### Navigation")
    st.markdown("Use the pages menu above to explore different analyses.")

# Main page content
st.title("CStore Dashboard - Rigby, Ririe & Rexburg Stores")
st.markdown("""
Welcome to the CStore Dashboard! This application provides insights into convenience store 
transaction data for Rigby, Ririe, and Rexburg stores.

**Available Analyses:**
1. **Top Products** - Top 5 products by weekly sales (excluding fuels)
2. **Beverage Brands** - Analysis of packaged beverage brands
3. **Payment Comparison** - Cash vs Credit customer analysis
4. **Demographics** - Store area demographic comparison using Census data

Use the sidebar to check data quality and navigate between pages.
""")

# Load and display basic stats
try:
    stores = load_stores()
    rigby_store_ids = get_rigby_store_ids()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Stores", len(stores))
    
    with col2:
        st.metric("Store IDs", len(rigby_store_ids))
    
    with col3:
        if len(stores) > 0 and "STORE_CHAIN_NAME" in stores.columns:
            chains = stores["STORE_CHAIN_NAME"].n_unique()
            st.metric("Chains", chains)
        else:
            st.metric("Chains", "N/A")
    
    with col4:
        if len(stores) > 0 and "CITY" in stores.columns:
            cities = stores["CITY"].unique().to_list()
            st.metric("Cities", len(cities))
        else:
            st.metric("Cities", "N/A")
    
    # Display store details in expander
    with st.expander("Store Details", expanded=False):
        if len(stores) > 0:
            # Select relevant columns for display
            display_cols = ["STORE_ID", "STORE_NAME", "STORE_CHAIN_NAME", "CITY", "STATE", "ZIP_CODE"]
            available_cols = [col for col in display_cols if col in stores.columns]
            st.dataframe(stores.select(available_cols), width='stretch')
        else:
            st.warning("No stores found.")
    
except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.info("Please check that data files are in the `data/` directory.")
