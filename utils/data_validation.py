"""
Data validation and exploration utilities for CStore dashboard.
Helps catch errors, duplicates, and data quality issues.
"""
import streamlit as st
import polars as pl
from typing import Dict, List, Tuple
from utils.data_loader import (
    load_stores, load_master_gtin, load_transaction_sets,
    load_transaction_items, load_payments, load_discounts
)


def check_duplicate_store_ids(stores: pl.DataFrame) -> Tuple[bool, pl.DataFrame]:
    """
    Check for duplicate STORE_IDs in stores table.
    Returns (has_duplicates, duplicate_details).
    """
    duplicates = stores.group_by("STORE_ID").agg(pl.len().alias("count")).filter(pl.col("count") > 1)
    has_duplicates = len(duplicates) > 0
    
    if has_duplicates:
        duplicate_details = stores.filter(pl.col("STORE_ID").is_in(duplicates["STORE_ID"]))
        return True, duplicate_details
    return False, pl.DataFrame()


def check_duplicate_street_addresses(stores: pl.DataFrame) -> Tuple[bool, pl.DataFrame]:
    """
    Check for duplicate STREET_ADDRESSes in stores table.
    Returns (has_duplicates, duplicate_details).
    """
    if "STREET_ADDRESS" not in stores.columns:
        return False, pl.DataFrame()
    
    # Normalize street address for comparison
    stores_normalized = stores.with_columns(
        pl.col("STREET_ADDRESS")
        .str.to_lowercase()
        .str.strip_chars()
        .alias("_normalized_address")
    )
    
    duplicates = stores_normalized.group_by("_normalized_address").agg(pl.len().alias("count")).filter(pl.col("count") > 1)
    has_duplicates = len(duplicates) > 0
    
    if has_duplicates:
        duplicate_addresses = duplicates["_normalized_address"].to_list()
        duplicate_details = stores_normalized.filter(
            pl.col("_normalized_address").is_in(duplicate_addresses)
        ).drop("_normalized_address")
        return True, duplicate_details
    return False, pl.DataFrame()


def check_duplicate_transaction_ids(transaction_sets: pl.DataFrame) -> Tuple[bool, pl.DataFrame]:
    """Check for duplicate TRANSACTION_SET_IDs."""
    duplicates = transaction_sets.group_by("TRANSACTION_SET_ID").agg(pl.count()).filter(pl.col("count") > 1)
    has_duplicates = len(duplicates) > 0
    
    if has_duplicates:
        duplicate_details = transaction_sets.filter(
            pl.col("TRANSACTION_SET_ID").is_in(duplicates["TRANSACTION_SET_ID"])
        )
        return True, duplicate_details
    return False, pl.DataFrame()


def check_duplicate_item_ids(transaction_items: pl.DataFrame) -> Tuple[bool, pl.DataFrame]:
    """Check for duplicate TRANSACTION_ITEM_IDs."""
    duplicates = transaction_items.group_by("TRANSACTION_ITEM_ID").agg(pl.len().alias("count")).filter(pl.col("count") > 1)
    has_duplicates = len(duplicates) > 0
    
    if has_duplicates:
        duplicate_details = transaction_items.filter(
            pl.col("TRANSACTION_ITEM_ID").is_in(duplicates["TRANSACTION_ITEM_ID"])
        )
        return True, duplicate_details
    return False, pl.DataFrame()


def check_referential_integrity(
    transaction_items: pl.DataFrame,
    stores: pl.DataFrame,
    master_gtin: pl.DataFrame
) -> Dict[str, int]:
    """
    Check referential integrity:
    - Transaction items must have valid STORE_IDs
    - Transaction items must have valid GTINs (or handle NONSCAN)
    """
    issues = {}
    
    # Check for orphaned transaction items (STORE_ID not in stores)
    valid_store_ids = set(stores["STORE_ID"].to_list())
    orphaned_stores = transaction_items.filter(
        ~pl.col("STORE_ID").is_in(list(valid_store_ids))
    )
    issues["orphaned_store_ids"] = len(orphaned_stores)
    
    # Check for transaction items with GTIN not in master_gtin (excluding NONSCAN)
    valid_gtins = set(master_gtin["GTIN"].to_list())
    items_with_gtin = transaction_items.filter(pl.col("SCAN_TYPE") != "NONSCAN")
    orphaned_gtins = items_with_gtin.filter(
        ~pl.col("GTIN").is_in(list(valid_gtins))
    )
    issues["orphaned_gtins"] = len(orphaned_gtins)
    
    return issues


def validate_data_types(df: pl.DataFrame, expected_types: Dict[str, type]) -> List[str]:
    """Validate data types match expected types."""
    issues = []
    
    for col, expected_type in expected_types.items():
        if col not in df.columns:
            issues.append(f"Missing column: {col}")
            continue
        
        actual_dtype = df[col].dtype
        if expected_type == datetime and actual_dtype != pl.Datetime:
            issues.append(f"{col}: Expected datetime, got {actual_dtype}")
        elif expected_type in [int, float] and actual_dtype not in [pl.Int64, pl.Int32, pl.Float64, pl.Float32]:
            issues.append(f"{col}: Expected numeric, got {actual_dtype}")
    
    return issues


def check_value_ranges(
    transaction_items: pl.DataFrame,
    transaction_sets: pl.DataFrame
) -> Dict[str, any]:
    """Check value ranges for reasonableness."""
    issues = {}
    
    # Check for negative amounts
    if "GRAND_TOTAL_AMOUNT" in transaction_items.columns:
        negative_amounts = transaction_items.filter(pl.col("GRAND_TOTAL_AMOUNT") < 0)
        issues["negative_item_amounts"] = len(negative_amounts)
    
    if "UNIT_QUANTITY" in transaction_items.columns:
        negative_quantities = transaction_items.filter(pl.col("UNIT_QUANTITY") < 0)
        issues["negative_quantities"] = len(negative_quantities)
    
    # Check for extreme outliers (amounts > $10,000 or quantities > 1000)
    if "GRAND_TOTAL_AMOUNT" in transaction_items.columns:
        outliers = transaction_items.filter(pl.col("GRAND_TOTAL_AMOUNT") > 10000)
        issues["extreme_amount_outliers"] = len(outliers)
    
    if "UNIT_QUANTITY" in transaction_items.columns:
        outliers = transaction_items.filter(pl.col("UNIT_QUANTITY") > 1000)
        issues["extreme_quantity_outliers"] = len(outliers)
    
    # Check date ranges (should be 2019-present, no future dates)
    if "DATE_TIME" in transaction_items.columns:
        from datetime import datetime
        now = datetime.now()
        future_dates = transaction_items.filter(pl.col("DATE_TIME") > now)
        issues["future_dates"] = len(future_dates)
        
        dates_before_2019 = transaction_items.filter(pl.col("DATE_TIME") < datetime(2019, 1, 1))
        issues["dates_before_2019"] = len(dates_before_2019)
    
    return issues


def check_missing_data(df: pl.DataFrame, critical_fields: List[str]) -> Dict[str, float]:
    """Check null percentages in critical fields."""
    null_percentages = {}
    total_rows = len(df)
    
    if total_rows == 0:
        return null_percentages
    
    for field in critical_fields:
        if field in df.columns:
            null_count = df.filter(pl.col(field).is_null()).height
            null_percentages[field] = (null_count / total_rows) * 100
        else:
            null_percentages[field] = 100.0  # Field doesn't exist
    
    return null_percentages


def check_data_consistency(
    transaction_items: pl.DataFrame,
    transaction_sets: pl.DataFrame,
    stores: pl.DataFrame
) -> Dict[str, any]:
    """Check data consistency."""
    issues = {}
    
    # Check SCAN_TYPE values
    expected_scan_types = ["GTIN", "PLU", "FMT_ERR", "NONSCAN"]
    if "SCAN_TYPE" in transaction_items.columns:
        invalid_scan_types = transaction_items.filter(
            ~pl.col("SCAN_TYPE").is_in(expected_scan_types)
        )
        issues["invalid_scan_types"] = len(invalid_scan_types)
        if len(invalid_scan_types) > 0:
            issues["invalid_scan_type_values"] = invalid_scan_types["SCAN_TYPE"].unique().to_list()
    
    # Check PAYMENT_TYPE values (common values: cash, debit, credit)
    if "PAYMENT_TYPE" in transaction_sets.columns:
        payment_types = transaction_sets["PAYMENT_TYPE"].drop_nulls().unique().to_list()
        issues["payment_types_found"] = payment_types
    
    # Check store cities are all Rigby, Ririe, or Rexburg
    if "CITY" in stores.columns:
        non_target_stores = stores.filter(
            ~pl.col("CITY").str.to_lowercase().is_in(["rigby", "ririe", "rexburg"])
        )
        issues["non_target_stores"] = len(non_target_stores)
    
    # Check POS_TYPE_ID values (should be 1-4)
    if "POS_TYPE_ID" in transaction_sets.columns:
        invalid_pos = transaction_sets.filter(
            (pl.col("POS_TYPE_ID") < 1) | (pl.col("POS_TYPE_ID") > 4)
        )
        issues["invalid_pos_type_ids"] = len(invalid_pos)
    
    return issues


def check_business_logic(
    transaction_items: pl.DataFrame,
    transaction_sets: pl.DataFrame
) -> Dict[str, any]:
    """Check business logic consistency."""
    issues = {}
    
    # Check GRAND_TOTAL_AMOUNT equals SUBTOTAL_AMOUNT + TAX_AMOUNT (within rounding)
    if all(col in transaction_sets.columns for col in ["GRAND_TOTAL_AMOUNT", "SUBTOTAL_AMOUNT", "TAX_AMOUNT"]):
        calculated_total = (
            transaction_sets["SUBTOTAL_AMOUNT"].fill_null(0) + 
            transaction_sets["TAX_AMOUNT"].fill_null(0)
        )
        differences = transaction_sets.with_columns(
            (pl.col("GRAND_TOTAL_AMOUNT") - calculated_total).abs().alias("diff")
        ).filter(pl.col("diff") > 0.01)  # Allow $0.01 rounding difference
        
        issues["total_mismatches"] = len(differences)
    
    # Check discount amounts don't exceed item prices
    if all(col in transaction_items.columns for col in ["DISCOUNT_AMOUNT", "UNIT_PRICE", "UNIT_QUANTITY"]):
        item_value = transaction_items["UNIT_PRICE"].fill_null(0) * transaction_items["UNIT_QUANTITY"].fill_null(1)
        excessive_discounts = transaction_items.filter(
            pl.col("DISCOUNT_AMOUNT") > item_value
        )
        issues["excessive_discounts"] = len(excessive_discounts)
    
    return issues


def check_data_volume() -> Dict[str, int]:
    """Check data volume and row counts."""
    volumes = {}
    
    try:
        stores = load_stores()
        volumes["stores"] = len(stores)
    except Exception as e:
        volumes["stores_error"] = str(e)
    
    try:
        transaction_sets = load_transaction_sets()
        volumes["transaction_sets"] = len(transaction_sets)
    except Exception as e:
        volumes["transaction_sets_error"] = str(e)
    
    try:
        transaction_items = load_transaction_items()
        volumes["transaction_items"] = len(transaction_items)
    except Exception as e:
        volumes["transaction_items_error"] = str(e)
    
    try:
        master_gtin = load_master_gtin()
        volumes["master_gtin"] = len(master_gtin)
    except Exception as e:
        volumes["master_gtin_error"] = str(e)
    
    return volumes


@st.cache_data
def run_full_validation() -> Dict[str, any]:
    """Run full data validation suite."""
    validation_results = {
        "duplicates": {},
        "referential_integrity": {},
        "value_ranges": {},
        "missing_data": {},
        "consistency": {},
        "business_logic": {},
        "data_volume": {}
    }
    
    try:
        stores = load_stores()
        transaction_sets = load_transaction_sets()
        transaction_items = load_transaction_items()
        master_gtin = load_master_gtin()
        
        # Check duplicates
        has_dup_stores, dup_stores = check_duplicate_store_ids(stores)
        validation_results["duplicates"]["store_ids"] = {
            "has_duplicates": has_dup_stores,
            "count": len(dup_stores) if has_dup_stores else 0
        }
        
        has_dup_sets, dup_sets = check_duplicate_transaction_ids(transaction_sets)
        validation_results["duplicates"]["transaction_set_ids"] = {
            "has_duplicates": has_dup_sets,
            "count": len(dup_sets) if has_dup_sets else 0
        }
        
        has_dup_items, dup_items = check_duplicate_item_ids(transaction_items)
        validation_results["duplicates"]["transaction_item_ids"] = {
            "has_duplicates": has_dup_items,
            "count": len(dup_items) if has_dup_items else 0
        }
        
        # Check referential integrity
        validation_results["referential_integrity"] = check_referential_integrity(
            transaction_items, stores, master_gtin
        )
        
        # Check value ranges
        validation_results["value_ranges"] = check_value_ranges(transaction_items, transaction_sets)
        
        # Check missing data
        validation_results["missing_data"]["transaction_items"] = check_missing_data(
            transaction_items,
            ["STORE_ID", "DATE_TIME", "GTIN", "GRAND_TOTAL_AMOUNT"]
        )
        validation_results["missing_data"]["transaction_sets"] = check_missing_data(
            transaction_sets,
            ["STORE_ID", "DATE_TIME", "TRANSACTION_SET_ID"]
        )
        
        # Check consistency
        validation_results["consistency"] = check_data_consistency(
            transaction_items, transaction_sets, stores
        )
        
        # Check business logic
        validation_results["business_logic"] = check_business_logic(
            transaction_items, transaction_sets
        )
        
        # Check data volume
        validation_results["data_volume"] = check_data_volume()
        
    except Exception as e:
        validation_results["error"] = str(e)
    
    return validation_results


def display_validation_summary(validation_results: Dict[str, any]):
    """Display validation results in Streamlit."""
    st.subheader("Data Quality Validation")
    
    # Overall status
    has_issues = False
    
    # Check for critical issues
    if validation_results.get("duplicates", {}).get("store_ids", {}).get("has_duplicates", False):
        st.warning("Duplicate STORE_IDs found (handled by deduplication)")
        has_issues = True
    
    ref_integrity = validation_results.get("referential_integrity", {})
    if ref_integrity.get("orphaned_store_ids", 0) > 0:
        st.error(f"Error: {ref_integrity['orphaned_store_ids']} transaction items with invalid STORE_IDs")
        has_issues = True
    
    if ref_integrity.get("orphaned_gtins", 0) > 0:
        st.warning(
            f"Warning: {ref_integrity['orphaned_gtins']:,} transaction items with GTINs not in master table. "
            "This is expected - some products may not be in the master GTIN table yet, or may be new products. "
            "These items will show without product details (brand, category, etc.) in the analysis."
        )
        has_issues = True
    
    value_ranges = validation_results.get("value_ranges", {})
    if value_ranges.get("future_dates", 0) > 0:
        st.error(f"Error: {value_ranges['future_dates']} records with future dates")
        has_issues = True
    
    if not has_issues:
        st.success("No critical data quality issues detected")
    
    # Data volume
    volumes = validation_results.get("data_volume", {})
    if volumes:
        st.info(f"Data loaded: {volumes.get('stores', 0)} stores, "
                f"{volumes.get('transaction_items', 0):,} transaction items")
