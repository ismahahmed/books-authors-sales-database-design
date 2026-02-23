import pandas as pd
import re
from clean_data import normalize_text
from dateutil import parser
from datetime import datetime


def parse_series(series: str):
    """
    Convert a raw series string into series name and number

    This function handles various formats of the series field, such as:
    - "Series Name #5" -> ("series name", 5)
    - "Series Name #1.5" -> ("series name", 1.5)
    - "Series Name #1-3" -> ("series name", None)  (this will be a boxset)
    """
    # Handle missing values
    if pd.isna(series):
        return ("", None)

    series_text = str(series).strip()

    # Match pattern like: "Series Name #5" (also allows decimals like #1.5)
    single_volume_match = re.match(
        r"^(.*?)(?:\s*#\s*(\d+(?:\.\d+)?))$",
        series_text
    )
    
    if single_volume_match:
        series_name_raw = single_volume_match.group(1)
        series_number_str = single_volume_match.group(2)

        series_name_norm = normalize_text(series_name_raw) 

        # Convert number safely (1.0 -> 1, 1.5 -> 1.5)
        num = float(series_number_str)
        series_number = int(num) if num.is_integer() else num

        return (series_name_norm, series_number)

    # "#1-3" or "# 1 - 3"
    has_range_number = re.search(r"#\s*\d+(?:\.\d+)?\s*-\s*\d+(?:\.\d+)?", series_text)

    if has_range_number:
        series_name_only = re.sub(r"\s*#.*$", "", series_text)
        return (normalize_text(series_name_only), None)

    return (normalize_text(series_text), None)


def is_part_of_series(book_row):
    '''
    Return True if the book belongs to a series, else False.
    '''
    series_name_norm = book_row["series_name_norm"]

    if pd.notna(series_name_norm) and str(series_name_norm).strip() != "":
        return True

    return False


def create_series_identifier(df):
    """
    Create a unique identifier for each series (series_name_norm + primary_author_name).
    Format: "{series_name_norm}-{primary_author_name}"
    Only creates IDs for books that are part of a series.

    process: 
    1. this first creates a composite key by concatenating series_name_norm and primary_author_name, 
    but only for rows where series_name_norm is not null/empty and primary_author_name is not null/empty
    This ensures we only create series keys for books that are actually part of a series and have an identifiable primary author.
    """
    
    # Create a composite key from series_name_norm and primary_author_name
    # Only for books that are part of a series
    def create_series_key(row):
        if pd.isna(row['series_name_norm']) or row['series_name_norm'] == '':
            return None
        if pd.isna(row['primary_author_name']) or row['primary_author_name'] == '':
            return None
        return f"{row['series_name_norm']}-{row['primary_author_name']}"
    
    df['series_key'] = df.apply(create_series_key, axis=1)
    
    series_mask = df['series_key'].notna()
    df.loc[series_mask, 'series_uid'] = pd.factorize(df.loc[series_mask, 'series_key'])[0] + 1
    
    # Convert to Int64 to handle NaN properly
    df['series_uid'] = df['series_uid'].astype('Int64')
    
    # Count how many books in each series
    series_counts = df[df['series_uid'].notna()].groupby('series_uid').size().reset_index(name='books_in_series')
    df = df.merge(series_counts, on='series_uid', how='left')
    
    return df