/*-----------------------------------------------------------*/
				/*		TRIGGERS		*/
/*-----------------------------------------------------------*/

/*-----------------------------------------------*/
/* updated_at trigger */
/*-----------------------------------------------*/

/*
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

CREATE TRIGGER book_updated_at_trigger
    BEFORE UPDATE ON book
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER author_updated_at_trigger
    BEFORE UPDATE ON author
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER publisher_updated_at_trigger
    BEFORE UPDATE ON publisher
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER format_updated_at_trigger
    BEFORE UPDATE ON format
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER edition_updated_at_trigger
    BEFORE UPDATE ON edition
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER language_updated_at_trigger
    BEFORE UPDATE ON language
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER series_updated_at_trigger
    BEFORE UPDATE ON series
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER genre_updated_at_trigger
    BEFORE UPDATE ON genre
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER role_updated_at_trigger
    BEFORE UPDATE ON role
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER book_isbn_updated_at_trigger
    BEFORE UPDATE ON book_isbn
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER book_isbn_genre_updated_at_trigger
    BEFORE UPDATE ON book_isbn_genre
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER author_isbn_updated_at_trigger
    BEFORE UPDATE ON author_isbn
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER review_type_updated_at_trigger
    BEFORE UPDATE ON review_type
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER isbn_rating_updated_at_trigger
    BEFORE UPDATE ON isbn_rating
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
*/

/*-----------------------------------------------*/
/* ISBN Validation Trigger */
-- before insert or update make sure isbn 10 is length 10
-- before insert or update make sure isbn 13 is length 13
/*-----------------------------------------------*/
/*
CREATE OR REPLACE FUNCTION isbn_length_validate_func()
RETURNS TRIGGER 
LANGUAGE plpgsql
AS $trigfunc$
BEGIN
    IF NEW.isbn13 IS NOT NULL AND LENGTH(NEW.isbn13) != 13 THEN
        RAISE EXCEPTION 
        USING MESSAGE = 'ISBN13 must be exactly 13 characters',
        ERRCODE = 'P0001';
    END IF;
    
    IF NEW.isbn10 IS NOT NULL AND LENGTH(NEW.isbn10) != 10 THEN
        RAISE EXCEPTION 
        USING MESSAGE = 'ISBN10 must be exactly 10 characters',
        ERRCODE = 'P0001';
    END IF;
    IF NEW.isbn10 IS NULL AND NEW.isbn13 IS NULL THEN
        RAISE EXCEPTION 
        USING MESSAGE = 'At least one ISBN (ISBN10 or ISBN13) must be provided',
        ERRCODE = 'P0001';
    END IF;
	RETURN NEW;
    
END;
$trigfunc$;

DROP TRIGGER IF EXISTS isbn_length_validate ON book_isbn;

CREATE TRIGGER isbn_length_validate
BEFORE INSERT OR UPDATE ON book_isbn
FOR EACH ROW
EXECUTE FUNCTION isbn_length_validate_func();

*/
-- TESTING
INSERT INTO book_isbn (book_id, isbn13) VALUES (1, '1234'); -- too short
INSERT INTO book_isbn (book_id, isbn10)  VALUES (1, '1234567891011'); -- too long
INSERT INTO book_isbn (book_id) VALUES (1); -- NO isbn

INSERT INTO book_isbn (book_id, isbn13)  VALUES (1, '9781234567890'); -- shoukd work
select * FROM book_isbn WHERE isbn13 = '9781234567890';
DELETE FROM book_isbn WHERE isbn13 = '9781234567890';

/*-----------------------------------------------*/
/* Publish_Dates */
-- publish dates can not be in the future
/*-----------------------------------------------*/

/*
CREATE OR REPLACE FUNCTION publish_dates_func()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $trigfunc$
BEGIN
    IF NEW.publish_date IS NOT NULL AND NEW.publish_date > CURRENT_DATE THEN
        RAISE EXCEPTION 
        USING MESSAGE = 'Publish date cannot be in the future',
        ERRCODE = 'P0001';
    END IF;
    
    IF NEW.original_publish_date IS NOT NULL AND NEW.original_publish_date > CURRENT_DATE THEN
        RAISE EXCEPTION 
        USING MESSAGE = 'Original publish date cannot be in the future',
        ERRCODE = 'P0001';
    END IF;
    RETURN NEW;
END;
$trigfunc$;

CREATE TRIGGER publish_dates_check
BEFORE INSERT OR UPDATE ON book_isbn
FOR EACH ROW
EXECUTE FUNCTION publish_dates_func();
*/

-- testing 
INSERT INTO book_isbn (book_id, isbn13, publish_date) VALUES (1, '1234567890123', '2030-01-01'); -- fail
INSERT INTO book_isbn (book_id, isbn13, original_publish_date) VALUES (1, '1234567890123', '2030-01-01'); -- fail
INSERT INTO book_isbn (book_id, isbn13, publish_date) VALUES (1, '1234567890123', CURRENT_DATE); -- works
DELETE FROM book_isbn WHERE isbn13 = '1234567890123'; -- DELETE test


/*-----------------------------------------------*/
/* Ratings Trigger */
-- count ratings can't be negative
/*-----------------------------------------------*/

/*
CREATE OR REPLACE FUNCTION ratings_count_check_func()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $trigfunc$
BEGIN
    IF NEW.count < 0 THEN
	    RAISE EXCEPTION 
	    USING MESSAGE = 'Rating count cannot be negative',
	    ERRCODE = 'P0001';
    END IF;
    RETURN NEW;
END;
$trigfunc$;

CREATE TRIGGER ratings_count_check
BEFORE INSERT OR UPDATE ON isbn_rating
FOR EACH ROW
EXECUTE FUNCTION ratings_count_check_func();
*/

INSERT INTO isbn_rating (book_isbn_id, review_type_id, count) VALUES (1, 1, -5); -- fail
UPDATE isbn_rating SET count = -10 WHERE book_isbn_id = 1 AND review_type_id = 1; -- fail



/*-----------------------------------------------*/
/* Author Name Trigger */
-- help from AI!
-- parses first, middle and last name if full_name is only given
/*-----------------------------------------------*/

/*
CREATE OR REPLACE FUNCTION parse_author_name()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    parts text[];
BEGIN
    -- Only run if full_name exists and other fields are empty
    IF NEW.full_name IS NOT NULL
       AND NEW.first_name IS NULL
       AND NEW.middle_name IS NULL
       AND NEW.last_name IS NULL
    THEN
        parts := regexp_split_to_array(trim(NEW.full_name), '\s+');

        IF array_length(parts,1) = 1 THEN
            NEW.first_name := parts[1];

        ELSIF array_length(parts,1) = 2 THEN
            NEW.first_name := parts[1];
            NEW.last_name  := parts[2];

        ELSE
            NEW.first_name := parts[1];
            NEW.last_name  := parts[array_length(parts,1)];
            NEW.middle_name :=
                array_to_string(parts[2:array_length(parts,1)-1], ' ');
        END IF;
    END IF;

    RETURN NEW;
END;
$$;


CREATE TRIGGER trg_parse_author_name
BEFORE INSERT ON author
FOR EACH ROW
EXECUTE FUNCTION parse_author_name();
*/

INSERT INTO author(full_name) VALUES ('Test First Middle Last');
SELECT * FROM author WHERE full_name = 'Test First Middle Last';
SELECT * FROM author_logs;
DELETE from author WHERE full_name = 'Test First Middle Last';
SELECT * FROM author_logs;

INSERT INTO author(full_name) VALUES ('Testing_Only_First');
SELECT * FROM author WHERE full_name = 'Testing_Only_First';
SELECT * FROM author ORDER BY updated_at desc;
DELETE from author WHERE full_name = 'Testing_Only_First';
SELECT * FROM author WHERE full_name = 'Testing_Only_First';
SELECT * FROM author_logs;



/*-----------------------------------------------------------*/
		/*		LOG TABLES USING TRIGGERS		*/
/*-----------------------------------------------------------*/


/*-----------------------------------------------*/
				/* Book_Log */
-- https://www.youtube.com/watch?v=V81Smc6xrBY
-- at insert and delete, update log table
/*-----------------------------------------------*/
/*
CREATE TABLE book_logs ( 
    booklog_id INT PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY, 
    book_id INT,
    title text,
    log_message TEXT,  
    log_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP  
);


CREATE OR REPLACE FUNCTION trigger_afterbookinsert_func()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $trigfunc$
BEGIN
    INSERT INTO book_logs(book_id, title, log_message, log_date)
    VALUES (
        NEW.book_id,
		NEW.title,
        'New Book Added = ' || NEW.book_id,  
        CURRENT_TIMESTAMP
    );
    RETURN NEW;
END;
$trigfunc$;


CREATE TRIGGER trigger_afterbookinsert
AFTER INSERT ON book  
FOR EACH ROW
EXECUTE FUNCTION trigger_afterbookinsert_func();
*/


SELECT setval('book_book_id_seq', (SELECT MAX(book_id) FROM book));
INSERT INTO book (title) VALUES ('testing new book trigger');
SELECT * FROM book WHERE title = 'testing new book trigger';
SELECT * FROM book_logs;

/*
CREATE OR REPLACE FUNCTION trigger_afterdeletebook_func()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $trigfunc$
BEGIN
    INSERT INTO book_logs(book_id, title, log_message, log_date)
    VALUES (
        OLD.book_id,
		OLD.title,
        'Book Deleted = ' || OLD.book_id,  
        CURRENT_TIMESTAMP
    );
    RETURN NEW;
END;
$trigfunc$;

CREATE TRIGGER trigger_afterdeletebook
AFTER DELETE ON book
FOR EACH ROW
EXECUTE FUNCTION trigger_afterdeletebook_func();
*/

Delete from book WHERE title = 'testing new book trigger';
SELECT * FROM book_logs;


/*
CREATE OR REPLACE FUNCTION trigger_afterupdatebook_func()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $trigfunc$
BEGIN
    INSERT INTO book_logs(book_id, title, log_message, log_date)
    VALUES (
        NEW.book_id, 
        NEW.title,     
        'Book Updated from ' || OLD.title || ' to ' || NEW.title,  
        CURRENT_TIMESTAMP
    );
    RETURN NEW;
END;
$trigfunc$;

CREATE TRIGGER trigger_afterupdatebook
AFTER UPDATE ON book
FOR EACH ROW
EXECUTE FUNCTION trigger_afterupdatebook_func();
*/


INSERT INTO book (title) VALUES ('OLD Title testing');
SELECT * FROM book_logs;

UPDATE book SET title = 'NEW Title testing' WHERE title = 'OLD Title testing';
SELECT * FROM book_logs;
Delete from book WHERE title = 'NEW Title testing';
SELECT * FROM book_logs;


/*-----------------------------------------------*/
			/* Author_Log */
-- https://www.youtube.com/watch?v=V81Smc6xrBY
-- at insert and delete, update log table
/*-----------------------------------------------*/

/*
CREATE TABLE author_logs ( 
    authorlog_id INT PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY, 
    author_id INT,
    full_name text,
    log_message TEXT,  
    log_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP  
);
*/


-- Insert trigger into log

/*
CREATE OR REPLACE FUNCTION trigger_afterauthorinsert_func()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $trigfunc$
BEGIN
    INSERT INTO author_logs(author_id, full_name, log_message, log_date)
    VALUES (
        NEW.author_id,
		NEW.full_name,
        'New Author Added = ' || NEW.author_id,  
        CURRENT_TIMESTAMP
    );
    RETURN NEW;
END;
$trigfunc$;

-- DROP TRIGGER IF EXISTS trigger_afterauthorinsert ON author;


CREATE TRIGGER trigger_afterauthorinsert
AFTER INSERT ON author
FOR EACH ROW
EXECUTE FUNCTION trigger_afterauthorinsert_func();
*/


INSERT INTO author (full_name) VALUES ('author insert');
SELECT * FROM author_logs;


-- delete trigger into log

/*
CREATE OR REPLACE FUNCTION trigger_afterdeleteauthor_func()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $trigfunc$
BEGIN
    INSERT INTO author_logs(author_id, full_name, log_message, log_date)
    VALUES (
        OLD.author_id,
		OLD.full_name,
        'Author Deleted = ' || OLD.author_id,  
        CURRENT_TIMESTAMP
    );
    RETURN NEW;
END;
$trigfunc$;

CREATE TRIGGER trigger_afterdeleteauthor
AFTER DELETE ON author
FOR EACH ROW
EXECUTE FUNCTION trigger_afterdeleteauthor_func();
*/

DELETE from author WHERE full_name = 'author insert';
SELECT * FROM author_logs;

-- update trigger into log
/*
CREATE OR REPLACE FUNCTION trigger_afterupdateauthor_func()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $trigfunc$
BEGIN
    INSERT INTO author_logs(author_id, full_name, log_message, log_date)
    VALUES (
        NEW.author_id, 
        NEW.full_name,     
        'Name updated from ' || OLD.full_name || ' to ' || NEW.full_name,  
        CURRENT_TIMESTAMP
    );
    RETURN NEW;
END;
$trigfunc$;

CREATE TRIGGER trigger_afterupdateauthor
AFTER UPDATE ON author
FOR EACH ROW
EXECUTE FUNCTION trigger_afterupdateauthor_func();
*/

INSERT INTO author (full_name) VALUES ('test name update');
select * FROM author WHERE full_name = 'test name update';
SELECT * FROM author_logs;

UPDATE author SET full_name = 'NEW update' WHERE full_name = 'test name update';
SELECT * FROM author_logs;
DELETE from author WHERE full_name = 'NEW update';
SELECT * FROM author_logs;



/*-----------------------------------------------*/
			/* Ratings_Log */
-- https://www.youtube.com/watch?v=V81Smc6xrBY
-- at insert and delete, update log table
/*-----------------------------------------------*/
/*
CREATE TABLE isbn_rating_logs (
    isbn_rating_log_id INT PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
    isbn_rating_id INT,
    book_isbn_id INT,
    review_type_id INT,
    review_type_name TEXT,  
    operation_type VARCHAR(10),  
    old_count INT,
    new_count INT,
    log_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- INSERT trigger
CREATE OR REPLACE FUNCTION trigger_isbn_rating_insert()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO isbn_rating_logs (
		isbn_rating_id, book_isbn_id, review_type_id, review_type_name, 
		operation_type, old_count, new_count) 
    SELECT 
        NEW.isbn_rating_id, NEW.book_isbn_id, NEW.review_type_id, review_type.review_type,
        'INSERT', NEW.count, NEW.count
    FROM review_type
    WHERE review_type.review_type_id = NEW.review_type_id;
    RETURN NULL;
END;
$$;


-- UPDATE trigger
CREATE OR REPLACE FUNCTION trigger_isbn_rating_update()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.count != NEW.count THEN
        INSERT INTO isbn_rating_logs (
            isbn_rating_id, book_isbn_id, review_type_id, review_type_name,
            operation_type, old_count, new_count
        )
        SELECT 
            NEW.isbn_rating_id, NEW.book_isbn_id, NEW.review_type_id,
            review_type.review_type,
            'UPDATE', OLD.count, NEW.count
        FROM review_type
        WHERE review_type.review_type_id = NEW.review_type_id;
    END IF;
    RETURN NULL;
END;
$$;


-- DELETE trigger
CREATE OR REPLACE FUNCTION trigger_isbn_rating_delete()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO isbn_rating_logs (
        isbn_rating_id, book_isbn_id, review_type_id, review_type_name,
        operation_type, old_count, new_count
    )
    SELECT 
        OLD.isbn_rating_id, OLD.book_isbn_id, OLD.review_type_id,
        review_type.review_type,
        'DELETE', OLD.count, 0
    FROM review_type
    WHERE review_type.review_type_id = OLD.review_type_id;
    RETURN NULL;
END;
$$;



CREATE TRIGGER log_isbn_rating_insert_trigger
AFTER INSERT ON isbn_rating
FOR EACH ROW
EXECUTE FUNCTION trigger_isbn_rating_insert();

CREATE TRIGGER log_isbn_rating_update_trigger
AFTER UPDATE ON isbn_rating
FOR EACH ROW
EXECUTE FUNCTION trigger_isbn_rating_update();

CREATE TRIGGER log_isbn_rating_delete_trigger
AFTER DELETE ON isbn_rating
FOR EACH ROW
EXECUTE FUNCTION trigger_isbn_rating_delete();

*/


/*-----------------------------------------------------------*/
		/*		TESTING LOGS AND TRIGGERS		*/
/*-----------------------------------------------------------*/


-- INSERT INTO book (title) VALUES ('Testing Postgres Triggers');
SELECT * FROM book_logs ORDER BY log_date DESC LIMIT 5;
SELECT book_id, title FROM book WHERE title = 'Testing Postgres Triggers';

--INSERT INTO author (full_name) VALUES ('Test Author');
SELECT * FROM author_logs ORDER BY log_date DESC LIMIT 5;
SELECT author_id, full_name, first_name, middle_name, last_name FROM author  WHERE full_name = 'Test Author';

/*
INSERT INTO book_isbn (book_id, isbn13, isbn10,publish_date) 
	VALUES (35345,  -- NEW book tested above
    '1234567890123',
    '1234567890',
    '2024-01-01');
*/

SELECT book_isbn_id, isbn13, isbn10  FROM book_isbn  WHERE isbn13 = '1234567890123'; -- KEEP note OF book_isbn_id bc will DO checks below


--INSERT INTO author_isbn (book_isbn_id, author_id, role_id) VALUES (35374, 21697, NULL); 

SELECT * FROM review_type;

/*
INSERT INTO isbn_rating (book_isbn_id, review_type_id, count) VALUES (35374, 1, 100);
INSERT INTO isbn_rating (book_isbn_id, review_type_id, count) VALUES (35374, 2, 90);
INSERT INTO isbn_rating (book_isbn_id, review_type_id, count) VALUES (35374, 3, 80);
INSERT INTO isbn_rating (book_isbn_id, review_type_id, count) VALUES (35374, 4, 70);
INSERT INTO isbn_rating (book_isbn_id, review_type_id, count) VALUES (35374, 5, 60);
*/

SELECT * FROM isbn_rating_logs WHERE book_isbn_id = 35374 ORDER BY log_date;


--UPDATE isbn_rating SET count = 300  WHERE book_isbn_id = 35374 AND review_type_id = 1;  
--UPDATE isbn_rating SET count = 80 WHERE book_isbn_id = 35374 AND review_type_id = 5;

SELECT review_type_name,operation_type,old_count,new_count,log_date
FROM isbn_rating_logs WHERE book_isbn_id = 35374 ORDER BY log_date;

-- Update the book title (triggers book_logs + updated_at)
--UPDATE book SET title = 'Updated Test Book Title'  WHERE book_id = 35345;
SELECT * FROM book_logs WHERE book_id = 35345 ORDER BY log_date;
SELECT book_id, title, updated_at FROM book WHERE book_id = 35345;


--DELETE FROM isbn_rating WHERE book_isbn_id = 35374;
--DELETE FROM author_isbn WHERE book_isbn_id = 35374;
--DELETE FROM book_isbn WHERE book_isbn_id = 35374;
--DELETE FROM author WHERE author_id = 21697;
--DELETE FROM book WHERE book_id = 35345;

SELECT * FROM book_logs ORDER BY log_date DESC LIMIT 10;
SELECT * FROM author_logs ORDER BY log_date DESC LIMIT 10;
SELECT * FROM isbn_rating_logs ORDER BY log_date DESC LIMIT 10;



