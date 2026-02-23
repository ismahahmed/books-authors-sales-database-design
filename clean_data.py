import warnings
warnings.filterwarnings('ignore', message='This pattern is interpreted as a regular expression')
import pandas as pd
import re
import unicodedata
import ast
from dateutil import parser
from datetime import datetime
# ignore all warnings 
warnings.filterwarnings("ignore")


def load_and_clean_books_data(file_path):
    '''
    load_and_clean_books_data loads the books data from the specified file path, 
    drops unnecessary columns, and returns a cleaned DataFrame 
    '''
    books_data_original = pd.read_csv(file_path, encoding="utf-8", low_memory=False) # avoid dtype warnings for now
    books_data = books_data_original.drop(columns=["characters", "awards", "coverImg", "bbeScore", "bbeVotes", "price", "setting"])
    return books_data

def english_only(df):
    df = df[df["language"] == "English"]
    return(df)

def normalize_text(raw_text: str) -> str:
    '''
    Normalize text by:
    - converting to lowercase
    - trimming edges
    - collapsing multiple whitespace into one space
    (Accents are preserved.)
    '''
    if pd.isna(raw_text):
        return ""
    text_lower = str(raw_text).lower()
    text_single_spaced = re.sub(r"\s+", " ", text_lower).strip() # regex to replace multiple whitespace with single space, then trim
    return text_single_spaced


def normalize_title(raw_title: str) -> str:
    '''
    Normalize a book title for matching:
    - normalize whitespace
    '''
    normalized_title = normalize_text(raw_title)
    return normalized_title

def remove_non_english_titles(df, title_col="title"):
    '''
    Remove rows where the title contains non-ASCII characters.
    Returns a filtered copy of the dataframe
    '''

    english_only = df[title_col].str.contains(r"^[\x00-\x7F]+$", na=False)
    return df[english_only].copy() # english only is True for rows with only ASCII characters


def remove_duplicate_book_ids(df):
    """
    Remove duplicate bookId rows.
    Keeps the first occurrence and drops the rest.
    """

    df = df.drop_duplicates(subset="bookId", keep="first").reset_index(drop=True)
    return df

def normalize_pages(df):
    """
    Convert pages_norm to whole-number 
    """
    df["pages_norm"] = (
    df["pages"].astype(str).str.lower().str.extract(r"(\d+)", expand=False))

    df["pages_norm"] = pd.to_numeric(df["pages_norm"], errors="coerce").astype("Int64")

    return df


def create_book_identifier(df):
    """
    AI helped me design a method and suggested the merge 
    Create a unique identifier for each unique book (title_norm + primary_author_name).
    Format: "{title_norm}-{primary_author_name}"
    Also creates a flag for books that are unique vs have multiple editions

    process:
    1. Create a composite key by concatenating title_norm and primary_author_name
    2. Use pd.factorize to assign a unique integer ID to each unique composite key
    3. Count how many rows/editions exist for each unique book_id
    """
    
    df = df.copy()
    
    if 'edition_count' in df.columns: # Drop edition_count if it already exists (from previous runs) bc we will recalculate it
        df = df.drop(columns=['edition_count'])
    
    df['book_key'] = df['title_norm'].astype(str) + '-' + df['primary_author_name'].astype(str) # this creates unique key
    df['book_uid'] = pd.factorize(df['book_key'])[0] + 1 # this is a numeric ID for each unique book_key, starting from 1
    
    # Ai wrote this
    book_counts = df.groupby('book_uid').size().reset_index(name='edition_count') # testing for later, not used in table
    df = df.merge(book_counts, on='book_uid', how='left') # AI wrote this

    df['has_multiple_editions'] = (df['edition_count'] > 1).astype(int)

    return df


def clean_description(df, source_col="description", target_col="description_norm"):
    """
    Clean and normalize book descriptions.
    - Remove excessive whitespace
    - Normalize newlines
    - Handle non-ASCII characters
    - Strip leading/trailing whitespace
    """
    
    def clean_single_description(desc):
        """
        Clean a single description string
        """
        if pd.isna(desc) or desc == "":
            return None
        
        desc = str(desc) # Convert to string in case it's not already
        desc = re.sub(r'\n+', ' ', desc) # Replace multiple newlines with a single space
        desc = re.sub(r'\s+', ' ', desc) # Replace multiple spaces/tabs with single space
        desc = desc.strip() # Strip leading and trailing whitespace
        return desc if desc else None
    
    df[target_col] = df[source_col].apply(clean_single_description) # apply inner function to each description
    
    return df

def create_is_boxset_flag(df):
    """
    Create is_boxset flag.
    Returns True if series contains a number range pattern like #1-4, #1-5, etc.
    Examples: "A Song of Ice and Fire #1-4", "Harry Potter #1-7"
    """
    
    def check_if_boxset(series_value):
        """
        Check if series contains boxset pattern (#X-Y)
        """
        if pd.isna(series_value) or series_value == '':
            return 0
        
        series_str = str(series_value)
        
        if re.search(r'#\d+-\d+', series_str): # Check for pattern: #digit(s)-digit(s), examples: #1-4, #1-7, #10-15
            return 1
        return 0
    
    df['is_boxset'] = df['series'].apply(check_if_boxset)
    
    return df

