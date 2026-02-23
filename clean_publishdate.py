import pandas as pd
import re
from dateutil import parser 
from datetime import datetime

def normalize_publish_date(df, source_col="publishDate", target_col="publishDate_norm", 
                          year_col=None, month_col=None, day_col=None, quality_col=None):
    """
    Normalize publish dates into a standard YYYY-MM-DD format.
    Creates additional columns for year, month, day, and a flag for date quality.
    If original date is null, all derived columns remain null.
    
    if day does not exist, default to 1
    Parameters:
    -----------
    df : DataFrame
    source_col : str - source column name
    target_col : str - normalized date column name
    year_col : str - year column name (default: {source_col}_year)
    month_col : str - month column name (default: {source_col}_month)
    day_col : str - day column name (default: {source_col}_day)
    quality_col : str - quality flag column name (default: {source_col}_quality)

    process:
    1. Parse the original date string using dateutil.parser (handles many formats)
    2. If parsing fails, try to extract just the year (if it looks like a year)
    3. If parsing succeeds, normalize to YYYY-MM-DD (default day/month to 1 if missing)
    4. Extract year, month, day into separate columns (use Int64 type to allow nulls)
    5. Create a quality flag: 1 = full date, 2 = year only (defaulted to Jan 1), 3 = failed to parse/null
    """
    
    # Set default column names if not provided
    if year_col is None:
        year_col = f"{source_col.replace('Date', '').lower()}_year"
    if month_col is None:
        month_col = f"{source_col.replace('Date', '').lower()}_month"
    if day_col is None:
        day_col = f"{source_col.replace('Date', '').lower()}_day"
    if quality_col is None:
        quality_col = f"{source_col.replace('Date', '').lower()}_quality"
    
    def parse_single_date(date_str):
        """
        Parse a single date string and return normalized format
        """
        if pd.isna(date_str):
            return None
        
        # Convert to string and strip whitespace
        date_str = str(date_str).strip()
        
        if not date_str or date_str.lower() in ['none', 'nan', 'unknown', '']:
            return None
        
        try:
            # Remove suffixes 
            date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)
            # AI suggested fuzzy parsing to handle more formats, but we will validate the year after parsing to avoid incorrect dates
            parsed_date = parser.parse(date_str, fuzzy=True) # Try to parse with dateutil (handles most formats)
            
            current_year = datetime.now().year
            if parsed_date.year < 1000 or parsed_date.year > current_year + 2: # If year is out of reasonable range, fail parsing 
                return None 

            return parsed_date.strftime('%Y-%m-%d')
            
        except (ValueError, parser.ParserError):
            year_match = re.search(r'\b(19|20)\d{2}\b', date_str) # If parsing fails, try to extract just the year
            if year_match:
                year = year_match.group(0)
                return f"{year}-01-01"  # Default to January 1st if only year
            
            return None
    
    df[target_col] = df[source_col].apply(parse_single_date)  # Apply the parsing function
    df[target_col] = pd.to_datetime(df[target_col], errors='coerce') # Convert to datetime
    
    # Extract year, month, and day using Int64 bc it allows nulls
    df[year_col] = df[target_col].dt.year.astype('Int64')
    df[month_col] = df[target_col].dt.month.astype('Int64')
    df[day_col] = df[target_col].dt.day.astype('Int64')
    
    # For dates that exist, fill missing day/month with 1
    mask_has_date = df[target_col].notna() # AI suggested this!
    df.loc[mask_has_date, day_col] = df.loc[mask_has_date, day_col].fillna(1)
    df.loc[mask_has_date, month_col] = df.loc[mask_has_date, month_col].fillna(1)
    
    # Create a quality flag
    # 1 = full date, 2 = year only (defaulted to Jan 1), 3 = failed to parse/null
    # AI also suggested this flagging
    def date_quality(row):
        if pd.isna(row[target_col]):
            return 3  # Failed to parse or original was null
        elif row[target_col].month == 1 and row[target_col].day == 1:
            # Check if original was year-only
            orig = str(row[source_col]).strip()
            if re.match(r'^\d{4}$', orig):
                return 2  # Year only
        return 1  # Full date
    
    df[quality_col] = df.apply(date_quality, axis=1) # i dont end up using this but it could be useful for filtering or analysis later on
    
    return df