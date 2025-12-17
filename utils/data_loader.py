"""
Data loading utilities for CStore dashboard.
Handles loading Parquet files, filtering to Rigby, Ririe, and Rexburg stores, and store deduplication.
"""
import streamlit as st
import polars as pl
from pathlib import Path
from datetime import datetime
from typing import Optional, List


DATA_DIR = Path("data")


@st.cache_data
def load_all_stores() -> pl.DataFrame:
    """Load all stores data without city filtering."""
    stores_path = DATA_DIR / "cstore_stores.parquet"
    stores = pl.read_parquet(stores_path)

    # Ensure STORE_ID is consistently treated as string for joins/filters
    stores = stores.with_columns(pl.col("STORE_ID").cast(pl.Utf8))
    
    # Deduplicate stores with multiple owners/records
    stores = deduplicate_stores(stores)
    
    return stores


@st.cache_data
def load_stores_by_cities(cities: List[str]) -> pl.DataFrame:
    """Load stores data filtered by specified cities."""
    stores = load_all_stores()
    
    # Normalize city names for filtering (case-insensitive)
    cities_lower = [city.lower() for city in cities]
    stores = stores.filter(pl.col("CITY").str.to_lowercase().is_in(cities_lower))
    
    return stores


@st.cache_data
def load_stores() -> pl.DataFrame:
    """Load stores data and filter to Rigby, Ririe, and Rexburg stores (default)."""
    return load_stores_by_cities(["rigby", "ririe", "rexburg"])


def deduplicate_stores(stores: pl.DataFrame) -> pl.DataFrame:
    """
    Deduplicate stores with multiple records.
    Checks for duplicates by both STORE_ID and STREET_ADDRESS.
    Takes the most recent record (by UPDATED_AT) or most complete record.
    """
    # Add sort date column for deduplication
    stores = stores.with_columns(
        pl.coalesce([pl.col("UPDATED_AT"), pl.col("CREATED_AT")]).alias("_sort_date")
    )
    
    # First, deduplicate by STORE_ID
    duplicate_by_id = stores.group_by("STORE_ID").agg(pl.len().alias("count")).filter(pl.col("count") > 1)
    if len(duplicate_by_id) > 0:
        # Sort by date descending and take first record per STORE_ID
        stores = stores.sort("_sort_date", descending=True)
        stores = stores.unique(subset=["STORE_ID"], keep="first")
    
    # Then, deduplicate by normalized street address (if STREET_ADDRESS exists)
    if "STREET_ADDRESS" in stores.columns:
        # Normalize street address: lowercase, strip whitespace
        stores = stores.with_columns(
            pl.col("STREET_ADDRESS")
            .str.to_lowercase()
            .str.strip_chars()
            .alias("_normalized_address")
        )
        
        # Check for duplicates by normalized address
        duplicate_by_address = stores.group_by("_normalized_address").agg(pl.len().alias("count")).filter(pl.col("count") > 1)
        if len(duplicate_by_address) > 0:
            # Sort by date descending and take first record per normalized address
            stores = stores.sort("_sort_date", descending=True)
            stores = stores.unique(subset=["_normalized_address"], keep="first")
        
        # Drop the temporary normalized address column
        stores = stores.drop("_normalized_address")
    
    # Drop the temporary sort column
    stores = stores.drop("_sort_date")
    
    return stores


@st.cache_data
def get_rigby_store_ids() -> List[int]:
    """Get list of Rigby, Ririe, and Rexburg store IDs."""
    stores = load_stores()
    # Ensure STORE_ID is consistently treated as string to match other tables
    stores = stores.with_columns(pl.col("STORE_ID").cast(pl.Utf8))
    rigby_ids = stores["STORE_ID"].to_list()

    # region agent log
    try:
        import json, time
        log_entry = {
            "sessionId": "debug-session",
            "runId": "pre-fix",
            "hypothesisId": "H1",
            "location": "utils/data_loader.py:get_rigby_store_ids",
            "message": "Rigby store IDs dtype and sample",
            "data": {
                "store_id_dtype": str(stores["STORE_ID"].dtype),
                "first_id_type": str(type(rigby_ids[0])) if rigby_ids else None,
                "count": len(rigby_ids),
            },
            "timestamp": int(time.time() * 1000),
        }
        with open(r"c:\Users\jarom\School\google_cloud_platform\.cursor\debug.log", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass
    # endregion agent log

    return rigby_ids


@st.cache_data
def load_master_gtin() -> pl.DataFrame:
    """Load master GTIN (product) data."""
    gtin_path = DATA_DIR / "cstore_master_ctin.parquet"
    return pl.read_parquet(gtin_path)


@st.cache_data
def load_transaction_sets() -> pl.DataFrame:
    """Load transaction sets (basket-level) data, filtered to Rigby, Ririe, and Rexburg stores."""
    sets_path = DATA_DIR / "cstore_transaction_sets.parquet"
    transaction_sets = pl.read_parquet(sets_path)

    # region agent log
    try:
        import json, time
        log_entry = {
            "sessionId": "debug-session",
            "runId": "pre-fix",
            "hypothesisId": "H1",
            "location": "utils/data_loader.py:load_transaction_sets",
            "message": "Transaction sets STORE_ID dtype before filter",
            "data": {
                "store_id_dtype": str(transaction_sets["STORE_ID"].dtype),
            },
            "timestamp": int(time.time() * 1000),
        }
        with open(r"c:\Users\jarom\School\google_cloud_platform\.cursor\debug.log", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass
    # endregion agent log

    # Filter to Rigby, Ririe, and Rexburg stores
    rigby_store_ids = get_rigby_store_ids()
    transaction_sets = transaction_sets.filter(pl.col("STORE_ID").is_in(rigby_store_ids))
    
    # Convert DATE_TIME to datetime if it's not already
    if transaction_sets["DATE_TIME"].dtype != pl.Datetime:
        transaction_sets = transaction_sets.with_columns(
            pl.col("DATE_TIME").str.to_datetime()
        )
    
    return transaction_sets


@st.cache_data
def load_transaction_items() -> pl.DataFrame:
    """
    Load all transaction items from partitioned files.
    Filtered to Rigby, Ririe, and Rexburg stores and excludes fuels.
    """
    items_dir = DATA_DIR / "transaction_items"
    
    # Read all parquet files in the directory
    transaction_items = pl.read_parquet(items_dir / "*.parquet")
    
    # Filter to Rigby, Ririe, and Rexburg stores
    rigby_store_ids = get_rigby_store_ids()
    transaction_items = transaction_items.filter(pl.col("STORE_ID").is_in(rigby_store_ids))
    
    # Exclude fuels by filtering SCAN_TYPE (only GTIN, PLU, FMT_ERR)
    transaction_items = transaction_items.filter(
        pl.col("SCAN_TYPE").is_in(["GTIN", "PLU", "FMT_ERR"])
    )
    
    # Convert DATE_TIME to datetime if it's not already
    if "DATE_TIME" in transaction_items.columns:
        if transaction_items["DATE_TIME"].dtype != pl.Datetime:
            transaction_items = transaction_items.with_columns(
                pl.col("DATE_TIME").str.to_datetime()
            )
    
    return transaction_items


@st.cache_data
def load_transactions_daily_agg() -> pl.DataFrame:
    """Load daily aggregated transaction items, filtered to Rigby, Ririe, and Rexburg stores."""
    agg_path = DATA_DIR / "cstore_transactions_daily_agg.parquet"
    daily_agg = pl.read_parquet(agg_path)

    # region agent log
    try:
        import json, time
        log_entry = {
            "sessionId": "debug-session",
            "runId": "pre-fix",
            "hypothesisId": "H1",
            "location": "utils/data_loader.py:load_transactions_daily_agg",
            "message": "Daily agg STORE_ID dtype before filter",
            "data": {
                "store_id_dtype": str(daily_agg["STORE_ID"].dtype),
            },
            "timestamp": int(time.time() * 1000),
        }
        with open(r"c:\Users\jarom\School\google_cloud_platform\.cursor\debug.log", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass
    # endregion agent log

    # Filter to Rigby, Ririe, and Rexburg stores
    rigby_store_ids = get_rigby_store_ids()
    daily_agg = daily_agg.filter(pl.col("STORE_ID").is_in(rigby_store_ids))
    
    # Exclude fuels
    daily_agg = daily_agg.filter(pl.col("SCAN_TYPE").is_in(["GTIN", "PLU", "FMT_ERR"]))
    
    # Convert DATE to datetime if needed
    if "DATE" in daily_agg.columns:
        date_dtype = daily_agg["DATE"].dtype

        # region agent log
        try:
            import json, time
            log_entry = {
                "sessionId": "debug-session",
                "runId": "pre-fix-date",
                "hypothesisId": "H2",
                "location": "utils/data_loader.py:load_transactions_daily_agg",
                "message": "Daily agg DATE dtype before conversion",
                "data": {
                    "date_dtype": str(date_dtype),
                },
                "timestamp": int(time.time() * 1000),
            }
            with open(r"c:\Users\jarom\School\google_cloud_platform\.cursor\debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            pass
        # endregion agent log

        if date_dtype == pl.Utf8:
            daily_agg = daily_agg.with_columns(
                pl.col("DATE").str.to_datetime()
            )
        elif date_dtype == pl.Date:
            daily_agg = daily_agg.with_columns(
                pl.col("DATE").cast(pl.Datetime)
            )
    
    return daily_agg


@st.cache_data
def load_payments() -> pl.DataFrame:
    """Load payments data, filtered to Rigby, Ririe, and Rexburg stores."""
    payments_path = DATA_DIR / "cstore_payments.parquet"
    payments = pl.read_parquet(payments_path)
    
    # Filter to Rigby, Ririe, and Rexburg stores
    rigby_store_ids = get_rigby_store_ids()
    payments = payments.filter(pl.col("STORE_ID").is_in(rigby_store_ids))
    
    # Convert DATE_TIME to datetime if needed
    if "DATE_TIME" in payments.columns:
        if payments["DATE_TIME"].dtype != pl.Datetime:
            payments = payments.with_columns(
                pl.col("DATE_TIME").str.to_datetime()
            )
    
    return payments


@st.cache_data
def load_discounts() -> pl.DataFrame:
    """Load discounts data, filtered to Rigby, Ririe, and Rexburg stores."""
    discounts_path = DATA_DIR / "cstore_discounts.parquet"
    discounts = pl.read_parquet(discounts_path)
    
    # Filter to Rigby, Ririe, and Rexburg stores
    rigby_store_ids = get_rigby_store_ids()
    discounts = discounts.filter(pl.col("STORE_ID").is_in(rigby_store_ids))
    
    # Convert DATE_TIME to datetime if needed
    if "DATE_TIME" in discounts.columns:
        if discounts["DATE_TIME"].dtype != pl.Datetime:
            discounts = discounts.with_columns(
                pl.col("DATE_TIME").str.to_datetime()
            )
    
    return discounts


@st.cache_data
def load_shopper() -> pl.DataFrame:
    """Load shopper data."""
    shopper_path = DATA_DIR / "cstore_shopper.parquet"
    return pl.read_parquet(shopper_path)


@st.cache_data
def join_transactions_with_products(
    transaction_items: Optional[pl.DataFrame] = None,
    master_gtin: Optional[pl.DataFrame] = None
) -> pl.DataFrame:
    """
    Join transaction items with product master data.
    """
    if transaction_items is None:
        transaction_items = load_transaction_items()
    if master_gtin is None:
        master_gtin = load_master_gtin()
    
    # Left join to preserve all transaction items (including NONSCAN)
    result = transaction_items.join(
        master_gtin,
        on="GTIN",
        how="left"
    )
    
    return result


@st.cache_data
def join_transactions_with_stores(
    transactions: pl.DataFrame,
    stores: Optional[pl.DataFrame] = None
) -> pl.DataFrame:
    """
    Join transactions with store data.
    """
    if stores is None:
        stores = load_stores()
    
    result = transactions.join(
        stores,
        on="STORE_ID",
        how="left"
    )
    
    return result


@st.cache_data
def filter_by_date_range(
    df: pl.DataFrame,
    date_column: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> pl.DataFrame:
    """
    Filter dataframe by date range.
    """
    if start_date is not None:
        df = df.filter(pl.col(date_column) >= start_date)
    if end_date is not None:
        df = df.filter(pl.col(date_column) <= end_date)
    
    return df


@st.cache_data
def filter_by_store_ids(
    df: pl.DataFrame,
    store_ids: List[int]
) -> pl.DataFrame:
    """
    Filter dataframe by store IDs.
    """
    if not store_ids:
        return df
    
    return df.filter(pl.col("STORE_ID").is_in(store_ids))

