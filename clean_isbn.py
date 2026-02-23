import pandas as pd
import re
from clean_data import normalize_text
from dateutil import parser
from datetime import datetime



def split_isbn(isbn_value):
    if pd.isna(isbn_value):
        return (None, None)

    # convert to string and remove spaces + hyphens
    isbn_clean = re.sub(r"[\s\-]", "", str(isbn_value)).strip()

    # ISBN-10 pattern
    if re.fullmatch(r"\d{9}[\dXx]", isbn_clean):
        return (isbn_clean.upper(), None)

    # ISBN-13 pattern
    if re.fullmatch(r"\d{13}", isbn_clean):
        return (None, isbn_clean)

    # invalid ISBN
    return (None, None)


def create_isbn_cols(df):
    df = df.copy()

    isbn_split = df["isbn"].apply(split_isbn)
    df["isbn10"] = isbn_split.str[0]
    df["isbn13"] = isbn_split.str[1]

    return df

def remove_fake_isbn13(df):
    """
    Remove rows where isbn13 == 9999999999999
    """
    return df[df["isbn13"].astype(str) != "9999999999999"]


def keep_one_per_isbn13(df):
    '''
    Remove duplicate isbn13 rows, keeping only one row per isbn13.
    Null isbn13 values are not deduplicated.
    '''
    # Separate rows with and without isbn13
    with_isbn = df[df["isbn13"].notna()]
    without_isbn = df[df["isbn13"].isna()]

    # Drop duplicates only where isbn13 exists
    with_isbn_deduped = with_isbn.drop_duplicates(subset="isbn13", keep="first")

    # Combine back together
    return pd.concat([with_isbn_deduped, without_isbn], ignore_index=True)


def keep_one_per_isbn10(df):
    '''
    Remove duplicate isbn10 rows, keeping only one row per isbn10.
    Null isbn10 values are not deduplicated.
    '''
    # Separate rows with and without isbn10
    with_isbn = df[df["isbn10"].notna()]
    without_isbn = df[df["isbn10"].isna()]

    # Drop duplicates only where isbn10 exists
    with_isbn_deduped = with_isbn.drop_duplicates(subset="isbn10", keep="first")

    # Combine back together
    return pd.concat([with_isbn_deduped, without_isbn], ignore_index=True)

def remove_rows_without_isbn(df):
    """
    Keep only rows where at least one ISBN exists (isbn10 or isbn13).
    """
    return df[
        df["isbn10"].notna() | df["isbn13"].notna()
    ]