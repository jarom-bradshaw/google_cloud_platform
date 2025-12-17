# Convenience Store Transactions Data Dictionary

## Overview

This dataset contains detailed transaction data for convenience stores, reporting on items purchased within transactions at independent convenience stores. Each row represents a transaction and may consist of multiple items.

**Data Source:** [PDI Technologies via Dewey Data](https://docs.deweydata.io/docs/convenience_store_transactions_data)

| Data Information | Value |
|------------------|-------|
| Refresh Cadence | Adhoc |
| Historical Coverage | 2019-present |
| Geographic Coverage | United States |

## Data Files

The data is organized in the following Parquet files:

- `cstore_stores.parquet` - Store information and locations
- `cstore_store_status.parquet` - Store status and metadata
- `cstore_master_ctin.parquet` - Product master data (GTIN attributes)
- `cstore_transaction_sets.parquet` - Transaction basket-level data
- `cstore_discounts.parquet` - Discount information
- `cstore_payments.parquet` - Payment transaction details
- `cstore_shopper.parquet` - Shopper identification data
- `cstore_transactions_daily_agg.parquet` - Daily aggregated transaction items
- `transaction_items/` - Individual transaction items (partitioned across multiple files)

## Key Concepts

### Joining Tables

There are 10 total tables that make up the full Convenience Store Transaction Dataset. These datasets relate to each other through unique identifiers for shoppers, stores, transactions, and payments.

### Frequently Used Tables

The following four tables can be used to conduct almost any type of market analysis. All tables can be joined together using their unique ID fields:

**Dimensional Tables:**
- **STORES** - Contains store and locational attributes for geolocation-based analytics. Join to transactional tables on `STORE_ID`.
- **MASTER_GTIN** - Contains GTIN attributes for category, brand, and product-level analytics. Join to `TRANSACTION_ITEMS` on `GTIN`.

**Transactional Tables:**
- **TRANSACTION_ITEMS** - Contains information on transactions at the individual item level.
- **TRANSACTION_SETS** - Contains information on transactions at the basket level.

### Filtering Best Practices

To speed up queries and ensure you're looking at the most relevant data, use filters such as:

- **SCAN_TYPE** - Filter for in-store merchandise transactions: `where scan_type in ('GTIN','PLU','FMT_ERR')`
- **DATE_TIME** - Filter for specific time periods: `where date_time between '<start_date>' and '<end_date>'`
- **STORE_ID** - Filter for specific stores: `where store_id = <store_id>` or `where store_id in (<id1>, <id2>, ...)`

---

## Table Schemas

### STORES (`cstore_stores.parquet`)

Store information and locational attributes.

| Column Name | Description | Rows Populated |
|-------------|-------------|----------------|
| STORE_ID | Primary key of the stores table | 24,122 (100%) |
| STORE_NAME | The store name | 24,122 (100%) |
| STORE_CHAIN_ID | Unique store chain identifier | 24,122 (100%) |
| STORE_CHAIN_NAME | The store chain name | 24,122 (100%) |
| STREET_ADDRESS | The street address | 24,122 (100%) |
| CITY | The city | 24,122 (100%) |
| STATE | The state | 24,122 (100%) |
| ZIP_CODE | The zip code | 24,122 (100%) |
| LATITUDE | Latitude | 24,122 (100%) |
| LONGITUDE | Longitude | 24,122 (100%) |
| START_DATE | The start date for the store with Skupos | 24,109 (99.95%) |
| START_WEEK_CONTINUOUS_DATA | Start week with continuous data (no gaps) | 24,109 (99.95%) |
| CHAIN_SIZE | Number of stores in the chain | 24,121 (99.99%) |
| CREATED_AT | Date-time record was created | 24,122 (100%) |
| UPDATED_AT | Date-time record was last updated | 24,122 (100%) |

**Join Key:** `STORE_ID` - Use to join with transactional tables.

---

### STORE_STATUS (`cstore_store_status.parquet`)

Store status and additional metadata.

| Column Name | Description | Rows Populated |
|-------------|-------------|----------------|
| STORE_ID | Primary key of the stores table | 24,122 (100%) |
| STORE_NAME | The store name | 24,122 (100%) |
| STORE_CHAIN_ID | Unique store chain identifier | 14,521 (100%) |
| STORE_CHAIN_NAME | The store chain name | 24,122 (100%) |
| STORE_FLAG | Flag for store status | 24,122 (100%) |
| ACTIVE_STATUS | The status of the store (active/inactive) | 24,122 (100%) |
| STREET_ADDRESS | The street address of the store | 24,122 (100%) |
| CITY | The city where the store is located | 24,122 (100%) |
| STATE | The state where the store is located | 24,122 (100%) |
| ZIP_CODE | The zip code for the store | 24,122 (100%) |
| LATITUDE | Latitude of the store location | 23,263 (100%) |
| LONGITUDE | Longitude of the store location | 23,202 (100%) |
| CHAIN_SIZE | The number of stores in the chain | 79 (99.99%) |
| START_DATE | The start date for the store with Skupos | 1,729 (99.95%) |
| START_WEEK_CONTINUOUS_DATA | The week the store's continuous data starts | 281 (99.95%) |
| CREATED_AT | Date and time when the record was created | 189 (100%) |
| UPDATED_AT | Date and time when the record was last updated | 390 (100%) |

**Join Key:** `STORE_ID` - Use to join with other tables.

---

### MASTER_GTIN (`cstore_master_ctin.parquet`)

Product master data containing GTIN (Global Trade Item Number) attributes for category, brand, and product-level analytics.

| Column Name | Description | Rows Populated |
|-------------|-------------|----------------|
| GTIN | A 14-digit product identifier | 80,361 (100%) |
| CATEGORY | The Skupos-defined item category | 80,361 (100%) |
| SUBCATEGORY | The Skupos-defined item subcategory | 80,361 (100%) |
| MANUFACTURER_PARENT | The parent manufacturer | 30,938 (38.5%) |
| MANUFACTURER | The manufacturer | 63,627 (79.18%) |
| BRAND | The brand | 80,361 (100%) |
| PRODUCT_TYPE | The Skupos-defined product type | 51,374 (63.93%) |
| SUB_PRODUCT_TYPE | The Skupos-defined subproduct type | 7,293 (9.08%) |
| FLAVOR | The flavor | 43,858 (54.58%) |
| UNIT_SIZE | The unit size | 43,930 (54.67%) |
| PACK_SIZE | The pack size | 68,155 (84.81%) |
| PACKAGE | The item packaging | 30,903 (38.46%) |
| SKUPOS_DESCRIPTION | The Skupos-assigned item description | 80,361 (100%) |
| CREATED_AT | Date time when this record was created | 80,361 (100%) |
| UPDATED_AT | Date time when this record was last updated | 80,361 (100%) |

**Join Key:** `GTIN` - Use to join with `TRANSACTION_ITEMS` table to pull in product attributes.

---

### TRANSACTION_SETS (`cstore_transaction_sets.parquet`)

Transaction information at the basket level. Contains one record per transaction.

| Column Name | Description | Rows Populated |
|-------------|-------------|----------------|
| TRANSACTION_SET_ID | Primary key of the transaction sets table | 13,768,943,831 (100%) |
| STORE_ID | Primary key of the stores table | 24,122 (100%) |
| POS_TYPE_ID | Type of Vendor (1 - Verifone, 2 - Gilbarco, 3 - Clover, 4 - NCR) | 13,768,943,831 (100%) |
| DATE_TIME | Date time of the transaction from t-log file | 13,768,943,831 (100%) |
| TIME_ZONE | Time zone value from t-log file (only for Verifone) | 13,768,943,831 (100%) |
| PAYMENT_TYPE | Transaction payment type (debit, cash, etc.) | 13,417,894,911 (97.45%) |
| SUBTOTAL_AMOUNT | Amount paid for the transaction without tax | 312,991 (100%) |
| TAXABLE_AMOUNT | Taxable amount (0 for gas) | 92,845 (100%) |
| TAX_AMOUNT | Tax amount paid for the item | 49,869 (100%) |
| TAX_RATE | Tax rate for the item (if multiple rates exist, only one is shown) | 796 (100%) |
| GRAND_TOTAL_AMOUNT | Total amount paid including tax (subtotal + tax) | 293,344 (100%) |
| TENDER_RECEIVED_AMOUNT | Received cash amount from customer | 198,289 (100%) |
| TENDER_GIVEN_AMOUNT | Given cash amount to customer | 210,932 (100%) |
| CREATED_AT | Date time when this record was created | 586 (100%) |
| UPDATED_AT | Date time when this record was last updated | 586 (100%) |

**Join Keys:**
- `TRANSACTION_SET_ID` - Primary key for joining with transaction items, payments, and discounts
- `STORE_ID` - Join with stores table

---

### TRANSACTION_ITEMS (`transaction_items/`)

Transaction information at the individual item level. Contains one record per item in each transaction. This table is partitioned across multiple Parquet files.

| Column Name | Description | Rows Populated |
|-------------|-------------|----------------|
| TRANSACTION_ITEM_ID | Primary key of the transaction items table | 25,749,432,650 (100%) |
| TRANSACTION_SET_ID | Primary key of the transaction sets table | 13,768,943,831 (100%) |
| STORE_ID | Primary key of the stores table | 24,122 (100%) |
| DATE_TIME | Date time of transaction from t-log file | 169,635,346 (100%) |
| GTIN | A 14-digit product identifier | 25,749,432,650 (100%) |
| POS_DESCRIPTION | The POS-assigned item description | 25,749,432,650 (100%) |
| UNIT_PRICE | Unit price of the item | 9,024,657 (100%) |
| UNIT_QUANTITY | Quantity of the item purchased | 318,904 (100%) |
| DISCOUNT_AMOUNT | Discount amount applied to the items | 36,409 (100%) |
| TAXABLE_AMOUNT | Taxable amount (0 for gas) | 60,137 (35.39%) |
| TAX_RATE | Tax rate applied to the item | 802 (35.39%) |
| GRAND_TOTAL_AMOUNT | Total amount paid including tax | 258,230 (100%) |
| SCAN_TYPE | How the product details were captured (GTIN, PLU, FMT_ERR, NONSCAN) | 25,749,432,650 (100%) |
| NONSCAN_CATEGORY | The NACS category | 7,050,166,914 (27.38%) |
| NONSCAN_SUBCATEGORY | The NACS subcategory | 7,050,166,914 (27.38%) |
| NONSCAN_DETAIL | The NACS detail | 7,050,166,914 (27.38%) |
| CREATED_AT | Date time when this record was created | 586 (100%) |
| UPDATED_AT | Date time when this record was last updated | 586 (100%) |

**Join Keys:**
- `TRANSACTION_SET_ID` - Join with transaction sets
- `STORE_ID` - Join with stores table
- `GTIN` - Join with master GTIN table for product attributes

**Filtering:** Use `SCAN_TYPE` to filter for in-store merchandise: `where scan_type in ('GTIN','PLU','FMT_ERR')`

---

### TRANSACTION_ITEMS_DAILY_AGGREGATION (`cstore_transactions_daily_agg.parquet`)

Daily aggregated transaction items data. Pre-aggregated for faster analysis.

| Column Name | Description | Rows Populated |
|-------------|-------------|----------------|
| ID | Primary key of the record | 8,345,534,084 (100%) |
| GTIN | A 14-digit product identifier | 8,345,534,084 (100%) |
| STORE_ID | Primary key of the stores table | 24,109 (100%) |
| SCAN_TYPE | How the product details were captured | 8,345,534,084 (100%) |
| NONSCAN_CATEGORY | The NACS category | 164,685,841 (1.97%) |
| NONSCAN_SUBCATEGORY | The NACS subcategory | 164,685,841 (1.97%) |
| NONSCAN_DETAIL | The NACS detail | 164,685,841 (1.97%) |
| DATE | Date of the transaction | 8,345,534,084 (100%) |
| DAY_OF_WEEK | The day of the week (1 to 7) | 8,345,534,084 (100%) |
| WEEK | Week number of the transaction | 8,345,534,084 (100%) |
| CALENDAR_MONTH | The calendar month (1 to 12) | 8,345,534,084 (100%) |
| CALENDAR_YEAR | The calendar year | 8,345,534,084 (100%) |
| CATEGORY | The Skupos-defined item category | 6,865,182,394 (82.26%) |
| SUBCATEGORY | The Skupos-defined item subcategory | 6,865,182,394 (82.26%) |
| MANUFACTURER | The manufacturer | 6,695,450,957 (80.23%) |
| BRAND | The brand | 6,865,182,394 (82.26%) |
| PRODUCT_TYPE | The Skupos-defined product type | 4,885,717,544 (58.54%) |
| SUB_PRODUCT_TYPE | The Skupos-defined subproduct type | 2,152,705,980 (25.79%) |
| UNIT_SIZE | The unit size of the product | 5,026,372,878 (60.23%) |
| PACK_SIZE | The pack size of the product | 6,678,283,814 (80.02%) |
| SKUPOS_DESCRIPTION | The Skupos-assigned item description | 6,865,182,394 (82.26%) |
| QUANTITY | The quantity of items | 4,993,463 (100%) |
| TRANSACTION_COUNT | The number of transactions | 2,537 (100%) |
| TOTAL_REVENUE_AMOUNT | The total revenue amount for the product | 2,297,803 (100%) |
| QUANTITY_WITH_DISCOUNT | The quantity of items with a discount | 14,197 (100%) |
| TRANSACTION_COUNT_WITH_DISCOUNT | The number of transactions with a discount | 1,569 (100%) |
| CREATED_AT | Date time when this record was created | 585 (100%) |
| UPDATED_AT | Date time when this record was last updated | 585 (100%) |

**Join Keys:**
- `STORE_ID` - Join with stores table
- `GTIN` - Join with master GTIN table

---

### DISCOUNTS (`cstore_discounts.parquet`)

Discount information applied to transaction items.

| Column Name | Description | Rows Populated |
|-------------|-------------|----------------|
| DISCOUNT_ID | Primary key of the discounts table | 3,051,800,905 (100%) |
| TRANSACTION_ITEM_ID | Primary key of the transaction items table | 3,051,800,905 (100%) |
| TRANSACTION_SET_ID | Primary key of the transaction sets table | 3,051,800,905 (100%) |
| STORE_ID | Primary key of the stores table | 3,051,800,905 (100%) |
| POS_TYPE_ID | Type of vendor from pos_types table | 3,051,800,905 (100%) |
| DATE_TIME | Date time of transaction from t-log file | 3,051,800,905 (100%) |
| DISCOUNT_TYPE | Correspondence to discount type from t-log file | 3,051,800,905 (100%) |
| DISCOUNT_NAME | Name of the item that discount applied from t-log file | 2,991,214,450 (98.01%) |
| DISCOUNT_NUMBER | Discount number | 706,952,409 (23.17%) |
| QUANTITY | The discount quantity | 3,051,800,905 (100%) |
| ADJUSTMENT_AMOUNT | Discount adjustment amount | 3,051,800,905 (100%) |
| DISCOUNT_AMOUNT | Discount amount applied to items | 3,051,800,905 (100%) |
| GRAND_TOTAL_AMOUNT | Total amount paid including tax | 3,051,800,905 (100%) |
| CREATED_AT | Date time when this record was created | 3,051,800,905 (100%) |
| UPDATED_AT | Date time when this record was last updated | 3,051,800,905 (100%) |

**Join Keys:**
- `TRANSACTION_ITEM_ID` - Join with transaction items
- `TRANSACTION_SET_ID` - Join with transaction sets
- `STORE_ID` - Join with stores table

---

### PAYMENTS (`cstore_payments.parquet`)

Payment transaction details including payment type, card information, and tender amounts.

| Column Name | Description | Rows Populated |
|-------------|-------------|----------------|
| PAYMENT_ID | Primary key of the payments table | 17,751,455,590 (100%) |
| TRANSACTION_SET_ID | Primary key of the transaction sets table | 17,751,455,590 (100%) |
| STORE_ID | Primary key of the stores table | 17,751,455,590 (100%) |
| POS_TYPE_ID | Type of Vendor from pos_types table | 17,751,455,590 (100%) |
| DATE_TIME | Transaction date-time from t-log file | 17,751,455,590 (100%) |
| PAYMENT_NUMBER | Corresponds to payment number (Clover only) | 17,751,455,590 (100%) |
| PAYMENT_TYPE | Transaction payment type (debit, cash, etc.) | 17,498,699,955 (98.58%) |
| PAYMENT_ENTRY | Payment entry type (Swipe, etc.) | 17,751,455,590 (100%) |
| CARD_TYPE | Card type (Debit, Personal, etc.) | 4,536,780,411 (25.56%) |
| MERCHANT_ID | Merchant ID from t-log file (Verifone only) | 9,574,257,428 (53.94%) |
| TERMINAL_ID | Terminal ID from t-log file (Verifone only) | 9,670,793,642 (54.48%) |
| PAYMENT_LOCALE | Currency type of payment | 17,751,455,590 (100%) |
| CURRENCY_LOCALE | Local currency value (USD, Dollars, etc.) | 17,751,455,590 (100%) |
| TENDER | Amount customer gives as payment or gets back as change | 17,751,455,590 (100%) |
| CHANGE | Indicates if a customer gets back change | 17,751,455,590 (100%) |
| ACQUIRER_REFERENCE_NUMBER | Acquirer reference number from t-log | 5,588,632,616 (31.48%) |
| CARD_AUTH_CODE | Card authorization code | 7,290,645,040 (41.07%) |
| CREATED_AT | Record creation date-time | 17,751,455,590 (100%) |
| UPDATED_AT | Record last update date-time | 17,751,455,590 (100%) |

**Join Keys:**
- `TRANSACTION_SET_ID` - Join with transaction sets
- `STORE_ID` - Join with stores table

**Key Field:** `PAYMENT_TYPE` - Use to distinguish between cash and credit customers (e.g., 'cash', 'debit', 'credit').

---

### SHOPPER_ID (`cstore_shopper.parquet`)

Shopper identification data linking payments to unique shoppers.

| Column Name | Description | Rows Populated |
|-------------|-------------|----------------|
| PAYMENT_ID | Primary key of the payments table | 3,788,217,957 (100%) |
| TRANSACTION_SET_ID | Primary key of the transaction sets table | 3,788,217,957 (100%) |
| SHOPPER_ID | Skupos-defined ID for unique shoppers | 3,788,217,957 (100%) |
| CREATED_AT | Record creation date-time | 3,788,217,957 (100%) |
| UPDATED_AT | Record last update date-time | 3,788,217,957 (100%) |

**Join Keys:**
- `PAYMENT_ID` - Join with payments table
- `TRANSACTION_SET_ID` - Join with transaction sets
- `SHOPPER_ID` - Use to identify unique customers across transactions

---

## Common Query Patterns

### Filtering for In-Store Merchandise Only

To exclude fuel and other non-scannable items:

```python
# Using Polars
df = pl.read_parquet("transaction_items/*.parquet")
df_filtered = df.filter(pl.col("SCAN_TYPE").is_in(["GTIN", "PLU", "FMT_ERR"]))
```

### Joining Tables for Complete Analysis

```python
# Example: Join transaction items with product master and stores
transactions = pl.read_parquet("transaction_items/*.parquet")
products = pl.read_parquet("data/cstore_master_ctin.parquet")
stores = pl.read_parquet("data/cstore_stores.parquet")

# Join to get product details
transactions_with_products = transactions.join(
    products, on="GTIN", how="left"
)

# Join to get store details
complete_data = transactions_with_products.join(
    stores, on="STORE_ID", how="left"
)
```

### Filtering by Date Range

```python
# Filter transactions for a specific date range
from datetime import datetime

start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 12, 31)

df_filtered = df.filter(
    (pl.col("DATE_TIME") >= start_date) & 
    (pl.col("DATE_TIME") <= end_date)
)
```

### Filtering by Store

```python
# Filter for specific stores (e.g., Rigby and Ririe stores)
# First, identify store IDs from stores table
stores = pl.read_parquet("data/cstore_stores.parquet")
rigby_ririe_stores = stores.filter(
    pl.col("CITY").is_in(["Rigby", "Ririe"])
)

store_ids = rigby_ririe_stores["STORE_ID"].to_list()

# Then filter transactions
transactions = pl.read_parquet("transaction_items/*.parquet")
filtered_transactions = transactions.filter(
    pl.col("STORE_ID").is_in(store_ids)
)
```

---

## Notes

- All date-time fields are in the format from the original t-log files
- `SCAN_TYPE` values: `GTIN`, `PLU`, `FMT_ERR`, `NONSCAN`
- `PAYMENT_TYPE` values include: `cash`, `debit`, `credit`, etc.
- `POS_TYPE_ID` values: 1 (Verifone), 2 (Gilbarco), 3 (Clover), 4 (NCR)
- Some fields may have NULL values; check the "Rows Populated" percentage for data completeness
- The `transaction_items` table is partitioned across multiple files for performance

---

## References

- [Dewey Data - Convenience Store Transactions Documentation](https://docs.deweydata.io/docs/convenience_store_transactions_data)
- PDI Technologies - Data Provider
