import pandas as pd
import re
from dateutil import parser
import warnings
warnings.filterwarnings('ignore', message='This pattern is interpreted as a regular expression')
warnings.filterwarnings("ignore")

# import everything 
from clean_data import(load_and_clean_books_data, english_only, normalize_text, normalize_title, remove_non_english_titles, 
remove_duplicate_book_ids, create_book_identifier, clean_description, create_is_boxset_flag, normalize_pages)
from clean_author import normalize_author_text, normalize_author, normalize_author_roles, create_author_role_columns, filter_invalid_authors
from clean_rating import normalize_num_ratings, normalize_ratings_by_stars
from clean_genre import normalize_genre, clean_genres_column    
from clean_publisher import normalize_publishers, remove_non_english_publishers
from clean_isbn import create_isbn_cols, remove_fake_isbn13, keep_one_per_isbn13, keep_one_per_isbn10, remove_rows_without_isbn
from clean_series import parse_series, is_part_of_series, create_series_identifier
from clean_bookformat import  normalize_book_format
from clean_edition import normalize_edition
from clean_publisher import normalize_publishers
from clean_publishdate import normalize_publish_date

def run_cleaning(books_data):

    books_data = english_only(books_data) # filter to English language books only

    books_data["author"] = normalize_author_text(books_data["author"]) 
    books_data = normalize_author(books_data, "author", "author_norm")  # This creates author_norm, primary_author, etc.
    books_data = normalize_author_roles(books_data, "author_norm")
    books_data = create_author_role_columns(books_data, max_authors=5)

    books_data[["series_name_norm", "series_num"]] = (
        books_data["series"].apply(parse_series).apply(pd.Series)
    )
    books_data["is_series"] = books_data.apply(is_part_of_series, axis=1)

    books_data["title_norm"] = books_data["title"].apply(normalize_title)
    books_data = remove_non_english_titles(books_data)

    books_data = create_isbn_cols(books_data)
    books_data = remove_fake_isbn13(books_data)
    books_data = keep_one_per_isbn13(books_data)
    books_data = keep_one_per_isbn10(books_data)
    books_data = remove_rows_without_isbn(books_data)

    books_data = clean_genres_column(books_data)
    books_data['genres_norm'] = books_data['genres'].apply(normalize_genre)

    books_data = remove_non_english_publishers(books_data)
    books_data = normalize_publishers(books_data)

    books_data = normalize_book_format(books_data, source_col="bookFormat", target_col="bookFormat_norm")

    books_data['edition_norm'] = books_data['edition'].apply(normalize_edition)

    books_data = normalize_publish_date(
        books_data, 
        source_col="publishDate", 
        target_col="publishDate_norm",
        year_col="publish_year",
        month_col="publish_month",
        day_col="publish_day",
        quality_col="publish_date_quality"
    )

    books_data = normalize_publish_date(
        books_data, 
        source_col="firstPublishDate", 
        target_col="firstPublishDate_norm",
        year_col="first_publish_year",
        month_col="first_publish_month",
        day_col="first_publish_day",
        quality_col="first_publish_quality"
    )

    books_data = normalize_num_ratings(books_data, "numRatings", "numRatings_norm")
    books_data = normalize_ratings_by_stars(books_data, "ratingsByStars")

    books_data = normalize_pages(books_data)

    books_data = remove_duplicate_book_ids(books_data)

    books_data = create_book_identifier(books_data)
    books_data = create_series_identifier(books_data)

    books_data = clean_description(books_data, "description", "description_norm")
    books_data = create_is_boxset_flag(books_data)

    books_data = filter_invalid_authors(books_data)


    return books_data

