import pandas as pd
import re
import ast
from dateutil import parser
from datetime import datetime


def normalize_num_ratings(df, source_col="numRatings", target_col="numRatings_norm"):
    """
    Normalize numRatings column. 
    Since data is already clean, just copy and add quality flag.
    """
    # Copy the values
    df[target_col] = df[source_col]
    
    return df


def normalize_ratings_by_stars(df, source_col="ratingsByStars"):
    """
    Parse ratingsByStars list and create separate columns for each star rating.
    The list format is: [5-star, 4-star, 3-star, 2-star, 1-star]

    process:
    1. Handle missing values (null or empty) by returning None or zeros
    2. Convert string representation of list to actual list using ast.literal_eval
    3. Ensure we have exactly 5 elements (pad with zeros if needed)
    4. Convert each star count to integer and create separate columns for 5-star, 4-star, 3-star, 2-star, and 1-star ratings
    """
    
    def parse_ratings(ratings_str):
        """
        Parse the ratings string and return individual star counts
        Returns: (5-star, 4-star, 3-star, 2-star, 1-star)
        """
        if pd.isna(ratings_str):
            return None, None, None, None, None
        
        try:
            # Convert string representation of list to actual list
            ratings_list = ast.literal_eval(str(ratings_str))
            
            # If empty list, return zeros
            if not ratings_list or len(ratings_list) == 0:
                return 0, 0, 0, 0, 0
            
            # Ensure we have 5 elements, pad with 0 if needed
            while len(ratings_list) < 5:
                ratings_list.append('0')
            
            # Convert strings to integers
            # Order in list: [5-star, 4-star, 3-star, 2-star, 1-star]
            five_star = int(ratings_list[0])
            four_star = int(ratings_list[1])
            three_star = int(ratings_list[2])
            two_star = int(ratings_list[3])
            one_star = int(ratings_list[4])
            
            return five_star, four_star, three_star, two_star, one_star
            
        except (ValueError, SyntaxError, TypeError):
            # If parsing fails, return None
            return None, None, None, None, None
    
    # Apply parsing function
    parsed = df[source_col].apply(parse_ratings)
    
    # Unpack into separate columns
    df['5_star'] = parsed.apply(lambda x: x[0]).astype('Int64')
    df['4_star'] = parsed.apply(lambda x: x[1]).astype('Int64')
    df['3_star'] = parsed.apply(lambda x: x[2]).astype('Int64')
    df['2_star'] = parsed.apply(lambda x: x[3]).astype('Int64')
    df['1_star'] = parsed.apply(lambda x: x[4]).astype('Int64')
    
    return df