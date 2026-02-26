/* ------------------------------------------------- */
    /*                  TESTING                 */
/* ------------------------------------------------- */

-- DROP TRIGGER IF EXISTS trigger_name ON table; -- syntax for dropping trigger

/* ------------------*/
-- Book ISBN TESTS              
INSERT INTO book_isbn (book_id, isbn13) VALUES (1, '12345'); -- fails 
INSERT INTO book_isbn (book_id, isbn10) VALUES (1, '123'); -- fails
INSERT INTO book_isbn (book_id) VALUES (1); -- fails
INSERT INTO book_isbn (book_id, isbn13, publish_date) VALUES (1, '1111111111111', '2040-01-01'); -- fails
/* ------------------*/



/* ------------------*/
-- ISBN Rating Tests
INSERT INTO isbn_rating (book_isbn_id, review_type_id, count) VALUES (1, 1, -5); -- fails due TO negative count
/* ------------------*/



/* ------------------*/
-- Author name ( if giving full name only check to see if split)
INSERT INTO author (full_name)  VALUES ('Test Name');
SELECT * FROM author WHERE full_name = 'Test Name';
SELECT * FROM author_logs;
SELECT * FROM author_dim WHERE author_id = 21698; -- should NOT exisit bc STORED procs haven't run
delete FROM author WHERE full_name = 'Test Name';
SELECT * FROM author WHERE full_name = 'Test Name';
SELECT * FROM author_logs;
/* ------------------*/


/* ------------------*/
-- Testing book and book logs
INSERT INTO book (title) VALUES ('testing books');
SELECT * FROM book WHERE title = 'testing books';
SELECT * FROM book_logs;
delete FROM book WHERE title = 'testing books';
SELECT * FROM book WHERE title = 'testing books';
SELECT * FROM book_logs;
/* ------------------*/


/* ------------------*/
-- book_isbn
SELECT * FROM book WHERE book_id = 20;
SELECT * FROM book_isbn WHERE book_id = 20; -- book_isbn_id = 29,137, book_id = 20, format_is = 5, edition_id = 17, publisher = 385 
SELECT * FROM author_isbn WHERE author_isbn.book_isbn_id = 26204;

/*
INSERT INTO book_isbn (book_id, isbn13, isbn10, format_id, edition_id, publisher_id, language_id, 
	is_boxset, publish_date, series_id, series_num, pages )
SELECT 
    book_id,       -- Same book
    '9780439023499', -- Different ISBN13, i checked IF this existed already, it does not
    NULL, -- No ISBN10 for this edition
    4, -- Different format (4 instead of 5)
    edition_id,
    publisher_id,
    language_id,
    is_boxset,
    publish_date,
    series_id,
    series_num,
    pages
FROM book_isbn
WHERE book_isbn_id = 29137; -- just getting the rest OF the info OF this book so i dont have TO WRITE it ALL down
*/

SELECT * FROM book_isbn WHERE isbn13 = '9780439023499'; -- GENERATED book_isbn_id OF 35379
SELECT * FROM book_isbn WHERE book_id = 20;
DELETE FROM book_isbn WHERE isbn13 = '9780439023499';
SELECT * FROM book_isbn WHERE book_id = 20;
/* ------------------*/


/* ------------------*/
-- Testing stored proc on star schema
INSERT INTO synthetic_insert (
    isbn13, month, year,
    in_person_sales, online_sales, wholesale_sales, total_sales,
    average_price, total_revenue, count_returns, net_sales,
    nyt_best_selling_category, loaded_to_warehouse
)
VALUES
    ('1111111111111', 2, 2026, 100, 200, 150, 450, 25.99, 11695.50, 5, 445, 'Best Hardcover', FALSE),
    ('2222222222222', 2, 2026, 120, 180, 140, 440, 18.99, 8355.60, 3, 437, 'Best Paperback', FALSE);

CALL process_monthly_sales(2, 2026);

SELECT * FROM etl_log; -- should NOT LOAD INTO DATA warehouse bc isbn's DO NOT exist but should see the details

SELECT * from synthetic_insert WHERE MONTH = 2 AND YEAR = 2026;
delete from synthetic_insert WHERE MONTH = 2 AND YEAR = 2026;
/* ------------------*/



/* ------------------------------------------------- */
    /*             Common Queries                 */

/* ------------------------------------------------- */

/* ------------------*/
-- ALL TABLES IN  OLTP DESIGN
-- "look up" tables
SELECT * FROM book;
SELECT * FROM language;
SELECT * FROM author;
SELECT * FROM format;
SELECT * FROM edition;
SELECT * FROM genre;
SELECT * FROM publisher;
SELECT * FROM review_type;
SELECT * FROM role;
SELECT * FROM series;
-- bridge tables
SELECT * FROM book_isbn_genre;
SELECT * FROM isbn_rating;
SELECT * FROM author_isbn;
SELECT * FROM book_isbn;
/* ------------------*/


/* ------------------*/
-- book titles, series name, author names 

-- checking how to get authors in a specific book_isbn
-- there are 3 authors for book_isbn_id = 2
SELECT author_isbn.book_isbn_id,  author.full_name,
            ROW_NUMBER() OVER ( -- Assign  numbers 1, 2, 3, 4 and 5 to authors for each book
                PARTITION BY author_isbn.book_isbn_id  -- Restart numbering for each book
                ORDER BY author_isbn.author_isbn_id    -- Number them by author_isbn_id order
            ) as row
        FROM author_isbn JOIN author ON author_isbn.author_id = author.author_id;

SELECT * FROM book_isbn WHERE book_isbn_id = 2;
SELECT * FROM author_isbn WHERE book_isbn_id = 2;

-- checking all authors in book_isbn_id = 2
SELECT author_isbn.*, author.full_name FROM author_isbn JOIN author ON author_isbn.author_id = author.author_id 
WHERE book_isbn_id = 2 ORDER BY author_isbn;

WITH authors AS (
        SELECT 
        book_isbn_id,
        -- If row number = #, take the author's name, otherwise NULL
        -- MAX() + GROUP BY collapses the rows so authors are in the same row 
        -- we clould use any aggregate function since they all ignore nulls
        MAX(CASE WHEN row = 1 THEN full_name END) AS author_1,
        MAX(CASE WHEN row = 2 THEN full_name END) AS author_2,
        MAX(CASE WHEN row = 3 THEN full_name END) AS author_3,
        MAX(CASE WHEN row = 4 THEN full_name END) AS author_4,
        MAX(CASE WHEN row = 5 THEN full_name END) AS author_5
    FROM (
        SELECT 
            author_isbn.book_isbn_id,  
            author.full_name,         
            ROW_NUMBER() OVER (
                PARTITION BY author_isbn.book_isbn_id  
                ORDER BY author_isbn.author_isbn_id    
            ) AS row
        FROM author_isbn
        JOIN author ON author_isbn.author_id = author.author_id
    ) author_nums  
    GROUP BY book_isbn_id 
)
SELECT 
    book.title, series.series_name, book_isbn.series_num,          
    authors.author_1, authors.author_2, authors.author_3, authors.author_4, authors.author_5,  
    book_isbn.isbn13, format.format,publisher.publisher           
FROM book
JOIN book_isbn ON book.book_id = book_isbn.book_id -- Get ISBN details for this book
LEFT JOIN series ON book_isbn.series_id = series.series_id -- LEFT JOIN because not all books have a series
LEFT JOIN format ON book_isbn.format_id = format.format_id -- LEFT JOIN because format might be NULL
LEFT JOIN publisher ON book_isbn.publisher_id = publisher.publisher_id -- LEFT JOIN because publisher might be NULL
LEFT JOIN authors ON book_isbn.book_isbn_id = authors.book_isbn_id -- Get the authors we created in the CTE above;
/* ------------------*/


/* ------------------*/
-- Get all books by Suzanne Collins

SELECT author.full_name, book.title FROM book 
LEFT JOIN book_isbn ON book.book_id = book_isbn.book_id
LEFT JOIN author_isbn ON book_isbn.book_isbn_id = author_isbn.book_isbn_id
LEFT JOIN author ON author_isbn.author_id = author.author_id
WHERE author.full_name = 'suzanne collins';
/* ------------------*/



SELECT * FROM isbn_rating_logs;

SELECT * FROM sales_fact;



/* ------------------*/
-- Star Schema Queries

-- Query sales by author
SELECT 
    author_dim.author_name,
    SUM(sales_fact.total_sales) as total_units_sold,
    AVG(sales_fact.avg_rating) as avg_rating
FROM sales_fact
JOIN author_dim ON sales_fact.author_dim_id_1 = author_dim.author_dim_id
GROUP BY author_dim.author_name
ORDER BY total_units_sold DESC;

-- Track publisher rebrand
SELECT 
    book_dim.publisher,
    book_dim.effective_date,
    book_dim.expire_date 
FROM book_dim
WHERE book_dim.publisher LIKE '%two dollar radio%'
GROUP BY book_dim.publisher, book_dim.effective_date, book_dim.expire_date
ORDER BY book_dim.effective_date;

-- Top Selling Books 

SELECT 
    book_dim.book_title,
    book_dim.publisher,
    SUM(sales_fact.total_sales) as total_units_sold,
    SUM(sales_fact.total_revenue) as total_revenue,
    AVG(sales_fact.avg_rating) as avg_rating
FROM sales_fact
JOIN book_dim ON sales_fact.book_dim_id = book_dim.book_dim_id
WHERE book_dim.current_flag = TRUE
GROUP BY book_dim.book_title, book_dim.publisher
ORDER BY total_units_sold DESC
LIMIT 20;


-- Monthly Sales Trends
SELECT 
    month_year_dim.year,
    month_year_dim.month,
    SUM(sales_fact.total_sales) as total_units,
    SUM(sales_fact.total_revenue) as revenue,
    COUNT(DISTINCT sales_fact.book_dim_id) as unique_books_sold
FROM sales_fact
JOIN month_year_dim ON sales_fact.month_year_dim_id = month_year_dim.month_year_dim_id
GROUP BY month_year_dim.year, month_year_dim.month
ORDER BY month_year_dim.year, month_year_dim.month;


-- Top Authors by Sales
SELECT 
    author_dim.author_name,
    COUNT(DISTINCT sales_fact.book_dim_id) as unique_isbns,
    SUM(sales_fact.total_sales) as total_units_sold,
    AVG(sales_fact.total_sales) as avg_sales_per_book,
    AVG(sales_fact.avg_rating) as avg_rating
FROM sales_fact
JOIN author_dim ON author_dim.author_dim_id IN (
    sales_fact.author_dim_id_1,
    sales_fact.author_dim_id_2,
    sales_fact.author_dim_id_3,
    sales_fact.author_dim_id_4,
    sales_fact.author_dim_id_5
)
GROUP BY author_dim.author_name
HAVING SUM(sales_fact.total_sales) > 1000
ORDER BY total_units_sold DESC
LIMIT 20;



SELECT 
    book_dim.book_title,
    ROUND(AVG(sales_fact.avg_rating), 2) as avg_rating,
    author_dim.author_name  
FROM sales_fact
JOIN book_dim ON sales_fact.book_dim_id = book_dim.book_dim_id
JOIN author_dim ON author_dim.author_dim_id IN (
    sales_fact.author_dim_id_1,
    sales_fact.author_dim_id_2,
    sales_fact.author_dim_id_3,
    sales_fact.author_dim_id_4,
    sales_fact.author_dim_id_5
)
WHERE author_dim.author_name = 'agatha christie'  
  AND book_dim.current_flag = TRUE
GROUP BY book_dim.book_title, author_dim.author_name
ORDER BY avg_rating DESC;


SELECT 
    book_dim.book_title,
    nyt_bestseller_dim.listed_as_desc as nyt_award
FROM sales_fact
JOIN book_dim ON sales_fact.book_dim_id = book_dim.book_dim_id
LEFT JOIN nyt_bestseller_dim ON sales_fact.nyt_bestseller_dim_id = nyt_bestseller_dim.nyt_bestseller_dim_id
JOIN author_dim ON author_dim.author_dim_id IN (
    sales_fact.author_dim_id_1,
    sales_fact.author_dim_id_2,
    sales_fact.author_dim_id_3,
    sales_fact.author_dim_id_4,
    sales_fact.author_dim_id_5
)
WHERE author_dim.author_name = 'agatha christie'  
  AND book_dim.current_flag = TRUE
ORDER BY book_dim.book_title;


SELECT * FROM etl_log;

SELECT * FROM books_staging;





-- testing book log
INSERT INTO book (title) VALUES ('OLD Title testing');
SELECT * FROM book_logs;

UPDATE book SET title = 'NEW Title testing' WHERE title = 'OLD Title testing';
SELECT * FROM book_logs;
Delete from book WHERE title = 'NEW Title testing';

UPDATE publisher SET publisher = 'self published -test' WHERE publisher = 'self-published'


SELECT * FROM book_dim WHERE ;

SELECT * FROM book_dim WHERE publisher IN ('self published -test', 'self-published')

SELECT * FROM book_logs;


SELECT column_name FROM information_schema.columns WHERE table_name = 'nyt_bestseller_dim';


SELECT 
    CONCAT_WS(', ', 
        author1.author_name,
        author2.author_name,
        author3.author_name,
        author4.author_name,
        author5.author_name
    ) AS all_authors,
    book_dim.book_title,
    book_dim.publisher,
    book_dim.format,
    book_dim.language,
    month_year_dim.month,
    month_year_dim.year,
    nyt_bestseller_dim.listed_as_desc,
    sales_fact.*
FROM sales_fact
LEFT JOIN book_dim ON sales_fact.book_dim_id = book_dim.book_dim_id
LEFT JOIN month_year_dim ON sales_fact.month_year_dim_id = month_year_dim.month_year_dim_id
LEFT JOIN nyt_bestseller_dim ON sales_fact.nyt_bestseller_dim_id = nyt_bestseller_dim.nyt_bestseller_dim_id
LEFT JOIN author_dim AS author1 ON sales_fact.author_dim_id_1 = author1.author_dim_id
LEFT JOIN author_dim AS author2 ON sales_fact.author_dim_id_2 = author2.author_dim_id
LEFT JOIN author_dim AS author3 ON sales_fact.author_dim_id_3 = author3.author_dim_id
LEFT JOIN author_dim AS author4 ON sales_fact.author_dim_id_4 = author4.author_dim_id
LEFT JOIN author_dim AS author5 ON sales_fact.author_dim_id_5 = author5.author_dim_id










