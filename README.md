# Book, Authors and Synthetic Sales

## Data Sources:
- Lorena Casanova Lozano, & Sergio Costa Planells. (2020). Best Books Ever Dataset (1.0.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.4265096
- Synthetic Sales Data Created by AI

## Design

- OLTP: 14 normalized tables with triggers tracking last changed times
- Log Tables: 4 log tables (book_logs, author_logs, isbn_rating_logs, etl_log)
- Data Warehouse: Star schema (4 dims + 1 fact including the book_dim which is SCD type 2)
- ETL: 6 stored procedures for monthly loads
- History: Complete audit trail + publisher change history

## Data Flow
<img src="https://github.com/user-attachments/assets/86e97585-5444-4650-8ec2-767b0c190337" width="600">

## ETL Pipeline Steps 

### EXTRACT
- Download Goodreads CSV from Kaggle
- Download synthetic sales CSV (synthetic data via AI)

### TRANSFORM (Python)
- Clean Goodreads data (remove nulls, fix formats, parse genres...etc)
- Create books_staging.csv

###  LOAD to OLTP
- Load books_staging.csv into PostgreSQL books_staging table
- Create 14 normalized tables (author, book, publisher, format, etc.)
- Insert data from books_staging into normalized tables using CTEs and joins

### NORMALIZE & ADD TRIGGERS
- Add updated_at columns to all tables
- Create validation triggers (ISBN length, dates, ratings)
- Create auto triggers (auto-parse names, auto-update timestamps)
- Create log triggers (log inserts/updates/deletes to book_logs, author_logs, isbn_rating_logs)

###  DATA WAREHOUSE SETUP
- Create star schema (4 dimension tables + 1 fact table)
- Create month_year_dim, author_dim, nyt_bestseller_dim, book_dim (with SCD Type 2 for changes in publisher)
  - Create `trigger_publisher_rebrand` which automatically expires old book_dim records and creates new ones when publisher name changes

- Create sales_fact table
- Initial load: populate dimensions and facts from OLTP and synthetic_sales
- Create synthetic_insert staging table (tracks loaded_to_warehouse flag)
- Create etl_log table (tracks all ETL runs)
- Backfill synthetic_insert

### STORED PROCEDURES
- Create `update_month_year_dim()` : updates and syncs month/year dimension
- Create `update_nyt_bestseller_dim()` : updates and syncs NYT category dimension
- Create `update_author_dim()` : update and syncs authors from OLTP (via updated_at)
- Create `update_book_dim()` : update and syncs books from OLTP (via updated_at)
- Create `load_sales_to_warehouse()` : loads sales_fact with pivoted authors and avg_rating
- Create `process_monthly_sales()` : master stored proc call, calls all 5 procedures above

### Summary of Monthly ETL
- Receive new monthly sales
- Load into synthetic_insert with loaded_to_warehouse = FALSE
- Run process_monthly_sales(month, year)
  - Procedure updates all dimensions from OLTP changes using updated_at > last run date
  - Procedure loads new sales into sales_fact
  - Marks synthetic_insert as loaded_to_warehouse = TRUE
  - Everything logged to etl_log


## LOG & AUDIT TABLES: 4
#### book_logs:
- Tracks: INSERT, UPDATE, DELETE on book table
- `trigger_afterbookinsert_func`,`trigger_afterdeletebook_func`,`trigger_afterupdatebook_func` runs and inserts into book_logs
- Columns: booklog_id, book_id, title, log_message, log_date

#### author_logs
- Tracks: INSERT, UPDATE, DELETE on author table
- `trigger_afterauthorinsert_func`,`trigger_afterdeleteauthor_func`,`trigger_afterupdateauthor_func` runs and inserts into book_logs
= Columns: authorlog_id, author_id, full_name, log_message, log_date

#### isbn_rating_logs
- Tracks: INSERT, UPDATE, DELETE on isbn_rating table
- `log_isbn_rating_insert_trigger`,`log_isbn_rating_delete_trigger`,`isbn_rating_updated_at_trigger` runs and inserts into isbn_rating_logs
- Columns: isbn_rating_log_id, isbn_rating_id, book_isbn_id, review_type_id, review_type_name, operation_type, old_count, new_count, log_date
  - Separate triggers for INSERT/UPDATE/DELETE
  - UPDATE logging if count changed

#### etl_log (Data Warehouse)
- Tracks: All ETL process executions
- `process_monthly_sales()` logs to etl_log 
- Columns: etl_log_id, run_date, source ('synthetic' or 'oltp'), details (process name), rows_from_raw_data, rows_inserted_to_dw, rows_updated, rows_failed
- Logs: Every dimension update, fact load, and monthly runs


## OLTP Model
<img src="https://github.com/user-attachments/assets/be969e6f-ef65-49ed-91bf-99445f74c155" width="600">

*Note: All tables in oltp has a `updated_at` column*

### Tables: 14
- book: book_id, and titles
- author: author_id, names and parsed full name (first, middle and last)
- publisher: lookup for publisher
- format: book formats (hardcover, paperback, ebook... etc)
- edition: edition types
- language: language lookup (current only english due to testing + cleaning)
- series: book series names
- genre: genre lookup
- role: author roles (translator, illustrator... etc)
- book_isbn: ISBN records, unique isbn's
- review_type: rating types (5_star, 4_star, 3_star, 2_star, 1_star)
- isbn_rating: bridge table between review_type and book_isbn, counts for each review type for a specific book_isbn
- author_isbn: author book bridge table
- book_isbn_genre: book genre bridge table

## Star Schema

<img src="https://github.com/user-attachments/assets/8c4d6636-3203-4f05-b4e1-c409aa8871ea" width="600"/>



### Dimension Tables: 4
- month_year_dim - Time dimension (month, year)
- author_dim - Author dimension (simplified from OLTP)
- book_dim - Book dimension (SCD Type 2 for publisher changes)
- nyt_bestseller_dim - NYT category lookup

### Fact Table: 1
- sales_fact: monthly sales by book (with 5 author columns, avg_rating)

### Staging Tables: 2

- synthetic_insert: validated sales data, tracks loaded_to_warehouse
- synthetic_unmatched: orphaned ISBNs (not implemented, created but not used. maybe implement later)

  





















