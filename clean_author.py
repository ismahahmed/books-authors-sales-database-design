import pandas as pd
import re
from dateutil import parser
from datetime import datetime

'''
Functions: normalize_author_text, normalize_author_roles, normalize_author, create_author_role_columns

normalize_author_text: basic text normalization for author names, while preserving roles in parentheses. This includes:
- converting to lowercase
- removing periods from initials 
- standardizing multi-author separators &, and, ; to ,  

normalize_author_roles: extract and normalize roles from author field, using a 
comprehensive mapping for English roles and marking non-English roles as "unknown". This includes:
- splitting multiple authors by comma
- checking for roles in parentheses and normalizing them to standard English terms 
(e.g., "translator", "editor", "illustrator", etc.)
- if the author name contains non-English characters, replace it with "unknown"

normalize_author: comprehensive normalization that combines the above 
steps and also extracts the primary author (the first one listed) into a separate column. This includes:
- removing "(Goodreads Author)" text
- applying normalize_author_text to clean the author field while preserving roles
- extracting the primary author (first in list, including role if present) into a new column
- applying normalize_author_roles to standardize roles and mark non-English entries as "unknown"

create_author_role_columns: takes the normalized author field and creates separate columns for up to 5 authors and their roles. 
This includes:
- parsing the normalized author field to extract names and roles into a structured format (e.g., list of tuples)
- for each author position (2 through max_authors), creating a column for the author name and a column for the role

To summarize, first in normalize_author, we clean the author text and extract the primary author. 
Then in normalize_author_roles, we standardize the roles and mark non-English entries as "unknown". 
Finally, in create_author_role_columns, we take the cleaned and normalized author field and create 
structured columns for each author and their role.
'''

def normalize_author_text(series):  
    '''
    may be redunant since normalize_author_roles also does some text normalization, 
    but this is a more basic pass that focuses on cleaning the author names while preserving roles in parentheses

    imput: a pandas Series containing author names as strings
    output: a pandas Series with normalized author names, where:
    - all names are converted to lowercase
    - periods after single-letter initials are removed when followed by a space or end of string
    - periods after single-letter initials are removed anywhere in the string
    - repeated whitespace is normalized to a single space
    - multi-author separators (&, "and", ;) are standardized to ", "
    '''
    s = series.where(series.notna(), None)

    return (
        s.astype("string")
        .str.lower()
        # remove period after single-letter initial when next is space or end
        .str.replace(r"\b([a-z])\.(?=\s|$)", r"\1", regex=True)
        # remove periods after single-letter initials anywhere r.r. -> rr, j.k. -> jk
        .str.replace(r"(?<=\b[a-z])\.", "", regex=True)
        # normalize repeated whitespace
        .str.replace(r"\s+", " ", regex=True)
        # standardize multi-author separators
        .str.replace(r"\s*(?:&|\band\b|;)\s*", ", ", regex=True)
        .str.strip()
    )


def normalize_author_roles(df, source_col="author_norm"):
    """
    Normalize roles in author field to standard English terms.
    Non-English roles and non-English author names become "unknown"

    Process: 
    1. Split author field by comma to handle multiple authors separately
    2. For each author, check if there's a role in parentheses
    3. Normalize the role using a comprehensive mapping and fuzzy matching for English text
    4. If the author name contains non-ascii characters, replace it with "unknown"
    """
    
    # Comprehensive role normalization mapping (English only)
    role_mapping = {
        # Translator variations (English)
        'translator': 'translator',
        'translation': 'translator',
        'trans': 'translator',
        'translator ': 'translator',
        'trn': 'translator',
        '-translator': 'translator',
        
        # Editor variations (English)
        'editor': 'editor',
        'ed.': 'editor',
        'editor ': 'editor',
        '(editor': 'editor',
        'book editor': 'editor',
        'chief editor': 'editor',
        'general editor': 'editor',
        'managing editor': 'editor',
        'project editor': 'editor',
        'series editor': 'editor',
        'founding editor': 'editor',
        'co-editor': 'co-editor',
        'associate editor': 'editor',
        'editor-in-chief': 'editor',
        'editor-in-charge': 'editor',
        'chief sub editor': 'editor',
        'senior sub editor': 'editor',
        'sub editor': 'editor',
        'editor and author': 'editor, author',
        'editor and translator': 'editor, translator',
        
        # Illustrator variations (English)
        'illustrator': 'illustrator',
        'illustrator ': 'illustrator',
        'illustato': 'illustrator',
        'illustratar': 'illustrator',
        'illustrated by': 'illustrator',
        'illustrations': 'illustrator',
        'llustrator': 'illustrator',
        
        # Narrator variations (English)
        'narrator': 'narrator',
        'narrator ': 'narrator',
        'narrated by': 'narrator',
        'read by': 'narrator',
        'reader': 'narrator',
        'reading': 'narrator',
        'spiritual narrator': 'narrator',
        
        # Introduction/Foreword/Preface (English)
        'introduction': 'introduction',
        'introduction ': 'introduction',
        'introducer': 'introduction',
        'introd.': 'introduction',
        'foreword': 'foreword',
        'foreward': 'foreword',
        'forward': 'foreword',
        'preface': 'preface',
        'preface by': 'preface',
        'prologue': 'preface',
        
        # Afterword/Epilogue
        'afterword': 'afterword',
        'afterword ': 'afterword',
        'epilogue': 'afterword',
        'new afterword': 'afterword',
        
        # Notes/Annotations
        'notes': 'notes',
        'noted by': 'notes',
        'annotations': 'notes',
        'commentary': 'notes',
        'commentaries by': 'notes',
        'endnotes': 'notes',
        'footnotes': 'notes',
        
        # Artist/Art variations
        'artist': 'artist',
        'art': 'artist',
        'art by': 'artist',
        'cover artist': 'cover artist',
        'cover art': 'cover artist',
        'cover artwork': 'cover artist',
        'cover illustration': 'cover artist',
        'cover illustrator': 'cover artist',
        'cover illustrator ': 'cover artist',
        'color artist': 'colorist',
        'colorist': 'colorist',
        'colorist ': 'colorist',
        'color': 'colorist',
        'colors': 'colorist',
        'colourist': 'colorist',
        'colourist, cover artist': 'colorist',
        'colours': 'colorist',
        'cover colourist': 'colorist',
        
        # Writer variations
        'writer': 'writer',
        'co-writer': 'co-writer',
        'scriptwriter/illustrator': 'writer',
        'screenwriter': 'writer',
        'screenplay': 'writer',
        'script': 'writer',
        'teleplay': 'writer',
        'dramatist': 'writer',
        
        # Author variations
        'author': 'author',
        'co-author': 'co-author',
        'joint author': 'co-author',
        'original author': 'author',
        'primary contributor': 'author',
        'one of the authors': 'author',
        'author notes': 'author',
        
        # Adapter variations
        'adapter': 'adapter',
        'adaptation': 'adapter',
        'adaptator': 'adapter',
        'adapted by': 'adapter',
        'adaptor': 'adapter',
        'english adaptation': 'adapter',
        'retelling': 'adapter',
        'retold by': 'adapter',
        'adapter, illustrator': 'adapter, illustrator',
        'adapter/illustrator': 'adapter, illustrator',
        
        # Compiler/Anthologist
        'compiler': 'compiler',
        'compiler ': 'compiler',
        'compiled by': 'compiler',
        'compilation': 'compiler',
        'anthologist': 'compiler',
        'selected by': 'compiler',
        
        # Contributor
        'contributor': 'contributor',
        'contributer': 'contributor',
        'contribution by': 'contributor',
        'contributors': 'contributor',
        
        # Designer
        'designer': 'designer',
        'design': 'designer',
        'cover designer': 'cover designer',
        'cover design': 'cover designer',
        'coverdesign': 'cover designer',
        'book design': 'designer',
        'graphic designer': 'designer',
        'designed by': 'designer',
        'logo designer': 'designer',
        'coverpage designer': 'designer',
        'fashion designer': 'designer',
        'cover and interior designer': 'designer',
        
        # Photographer
        'photographer': 'photographer',
        'photographs': 'photographer',
        'photography': 'photographer',
        'photographer, author': 'photographer, author',
        
        # Comics-specific roles
        'penciler': 'penciler',
        'penciller': 'penciler',
        'pencils': 'penciler',
        'cover penciler': 'penciler',
        'inker': 'inker',
        'inks': 'inker',
        'cover inker': 'inker',
        'letterer': 'letterer',
        'lettering': 'letterer',
        'letter': 'letterer',
        
        # Other roles
        'pseudonym': 'pseudonym',
        'pseudonym ': 'pseudonym',
        'pseud.': 'pseudonym',
        'pen name': 'pseudonym',
        "author's pen name": 'pseudonym',
        'nom de plume': 'pseudonym',
        'aka.': 'pseudonym',
        'heteronym': 'pseudonym',
        
        'creator': 'creator',
        'created by': 'creator',
        'original creator': 'creator',
        'series creator': 'creator',
        
        'novelization': 'novelization',
        'novelist': 'author',
        
        'abridged by': 'abridger',
        
        'as told by': 'as told by',
        'as told to': 'as told to',
        'told by': 'as told by',
        
        'based on the novels': 'based on',
        'based on the tv series': 'based on',
        'based on work by': 'based on',
        'original story': 'original story',
        'original story by': 'original story',
        'story': 'story',
        'story by': 'story',
        
        'poet': 'poet',
        'verses': 'poet',
        
        'composer': 'composer',
        'music': 'composer',
        'song writer': 'composer',
        
        'cartographer': 'cartographer',
        'calligraphy': 'calligrapher',
        
        'producer': 'producer',
        'produced by': 'producer',
        'executive producer': 'producer',
        
        'director': 'director',
        'project director': 'director',
        
        'revised': 'reviser',
        'revised by': 'reviser',
        
        'proofreader': 'proofreader',
        
        'character design': 'designer',
        'mechanical design': 'designer',
        
        'ghostwriter': 'ghostwriter',
        
        'interviewer': 'interviewer',
        
        'essay': 'essayist',
        
        'guide': 'guide',
        
        'chronology and appendix': 'notes',
        
        'digital painter': 'artist',
        'digital painting': 'artist',
        
        'layout': 'designer',
        'typography': 'designer',
        
        'storyboards': 'artist',
        
        'comicization': 'adapter',
        
        'text': 'author',
        
        'preparation': 'editor',
        
        'touch-up artist/ letterer': 'letterer',
        'touch-up artsist/letterer': 'letterer',
        
        'retouch and lettering': 'letterer',
        
        'gray-toner': 'colorist',
        
        'vignettes': 'artist',
        'visual art': 'artist',
        
        'student': 'unknown',
        'testimony': 'unknown',
        'topic': 'unknown',
        'idea': 'unknown',
        'concept by': 'creator',
        'original idea': 'creator',
        
        # Multi-role entries
        'author and illustrator': 'author, illustrator',
        'author, illustrator': 'author, illustrator',
        'author/illustrator': 'author, illustrator',
        'writer, illustrator': 'writer, illustrator',
        'writer/illustrator': 'writer, illustrator',
        'editor, translator': 'editor, translator',
        'translator, editor': 'translator, editor',
        'translator/editor': 'translator, editor',
        'editor/translator': 'editor, translator',
        'co-author and illustrator': 'co-author, illustrator',
        'translator, introduction': 'translator, introduction',
        'editor, introduction': 'editor, introduction',
        'author, narrator': 'author, narrator',
        'author/narrator': 'author, narrator',
    }
    
    def is_english_text(text):
        """
        Check if text contains only English/ASCII characters (and common punctuation)
        """
        if not text:
            return True
        # Allow ASCII letters, numbers, spaces, and common punctuation
        return all(ord(char) < 128 for char in text)
    
    def normalize_single_role(role_str):
        """
        Normalize a single role string, return "unknown" for non-English roles
        """
        role_lower = role_str.lower().strip()
        
        # Check if role is in English
        if not is_english_text(role_lower):
            return 'unknown'
        
        # Check exact match first
        if role_lower in role_mapping:
            return role_mapping[role_lower]
        
        # Fuzzy matching for English text
        if any(x in role_lower for x in ['translat', 'trad']):
            return 'translator'
        
        if 'editor' in role_lower or 'edit' in role_lower:
            return 'editor'
        
        if 'illustrat' in role_lower:
            return 'illustrator'
        
        if 'intro' in role_lower:
            return 'introduction'
        
        # If it's English but unrecognized, keep original
        return role_lower
    
    def process_author_field(author_str):
        """
        Process entire author field and normalize all roles.
        Replace non-English author names with "unknown".
        """
        if pd.isna(author_str):
            return None
        
        author_str = str(author_str)
        
        # Split by comma to process each author separately
        authors = author_str.split(',')
        processed_authors = []
        
        for author in authors:
            author = author.strip()
            
            # Check if author has a role in parentheses
            role_match = re.search(r'\(([^)]+)\)$', author)
            
            if role_match:
                # Extract name and role
                role = role_match.group(1)
                name = author[:role_match.start()].strip()
                
                # Normalize the role
                normalized_role = normalize_single_role(role)
                
                # Check if name is English
                if is_english_text(name):
                    processed_authors.append(f"{name} ({normalized_role})")
                else:
                    processed_authors.append(f"unknown ({normalized_role})")
            else:
                # No role, just check the name
                if is_english_text(author):
                    processed_authors.append(author)
                else:
                    processed_authors.append("unknown")
        
        return ', '.join(processed_authors)
    
    # Create new column with normalized roles and author names
    df['author_roles_norm'] = df[source_col].apply(process_author_field)
    
    return df



def normalize_author(df, source_col="author", target_col="author_norm"):
    """
    Comprehensive author normalization:
    - Remove "(Goodreads Author)" text
    - Lowercase and clean text
    - Remove periods from initials
    - Standardize separators
    - Extract primary author (with role if present)
    - Create author count
    - KEEPS roles like (Illustrator), (Editor), (Translator) for later parsing

    process:
    1. Clean the author string while preserving roles in parentheses
    2. Extract the primary author (first in list, including role if present)
    3. Extract just the primary author name without role for easier analysis

    Result:
    example input: "J. K. Rowling (Goodreads Author), John Doe (Translator), Jane Smith (Editor)"
    example output:
    author_norm: "j k rowling, john doe (translator), jane smith (editor)"
    primary_author: "j k rowling"
    primary_author_name: "j k rowling"
    """
    
    def clean_single_author(author_str):
        """
        Clean a single author name while preserving roles
        """
        if pd.isna(author_str) or author_str == "":
            return None
        
        # Convert to string and lowercase
        author_str = str(author_str).lower().strip()
        
        # Remove ONLY "(goodreads author)" case-insensitive
        # Use word boundaries to avoid partial matches
        author_str = re.sub(r"\s*\(goodreads\s+author\)", "", author_str, flags=re.IGNORECASE)
        
        # Remove period after single-letter initial when followed by space or end
        # e.g., "j. k. rowling" -> "j k rowling"
        # But be careful not to touch periods inside parentheses (roles)
        author_str = re.sub(r"\b([a-z])\.(?=\s|$)", r"\1", author_str)
        
        # Remove periods after single-letter initials (j.k. -> jk)
        # But not inside parentheses
        author_str = re.sub(r"(?<=\b[a-z])\.(?!\))", "", author_str)
        
        # Normalize repeated whitespace
        author_str = re.sub(r"\s+", " ", author_str)
        
        # Standardize multi-author separators (& or "and" or ;) to comma
        # But be careful with "and" inside parentheses
        author_str = re.sub(r"\s*(?:&|;)\s*", ", ", author_str)
        # Replace " and " only when not inside parentheses
        author_str = re.sub(r"\s+and\s+(?![^(]*\))", ", ", author_str)
        
        # Final strip
        author_str = author_str.strip()
        
        return author_str if author_str else None
    
    # Apply cleaning to create normalized column
    df[target_col] = df[source_col].apply(clean_single_author)
    
    # Extract primary author (first author in list, including role)
    def get_primary_author(author_field):
        """
        Extract the first/primary author from the list (with role if present)
        """
        if pd.isna(author_field) or author_field == "":
            return None
        
        # Split by comma and take first
        first = str(author_field).split(",")[0].strip()
        return first if first else None
    
    df['primary_author'] = df[target_col].apply(get_primary_author)
    
    # Extract primary author name only (without role)
    def get_primary_author_name_only(author_field):
        """
        Extract just the name without role for the primary author
        """
        if pd.isna(author_field):
            return None
        
        # Remove anything in parentheses
        name_only = re.sub(r"\s*\([^)]*\)", "", str(author_field))
        return name_only.strip() if name_only.strip() else None
    
    df['primary_author_name'] = df['primary_author'].apply(get_primary_author_name_only)
    
    # Count number of authors (contributors)
    def count_authors(author_field):
        """
        Count how many authors/contributors in the field
        """
        if pd.isna(author_field) or author_field == "":
            return 0
        
        # Split by comma and count non-empty entries
        authors = [a.strip() for a in str(author_field).split(",") if a.strip()]
        return len(authors)
    

    
    return df


def create_author_role_columns(df, max_authors=5):
    """
    Create separate columns for each author and their role.
    Skips author_1 (already exists as primary_author/primary_author_name)
    Creates: author_2, author_3, author_4, author_5
    And: author_1_role, author_2_role, author_3_role, author_4_role, author_5_role

    process:
    1. Parse the normalized author field to extract names and roles into a structured format (e.g., list of tuples)
    2. For each author position (2 through max_authors), create a column for the author name and a column for the role
    3. Handle cases where there are fewer than max_authors by filling with None
    """
    
    def parse_authors_and_roles(author_field):
        """
        Parse author field and return list of (name, role) tuples
        """
        if pd.isna(author_field) or author_field == "":
            return []
        
        # Split by comma
        authors = [a.strip() for a in str(author_field).split(",")]
        
        result = []
        for author in authors:
            # Check if author has a role in parentheses
            role_match = re.search(r'\(([^)]+)\)$', author)
            
            if role_match:
                role = role_match.group(1)
                name = author[:role_match.start()].strip()
                result.append((name, role))
            else:
                # No role
                result.append((author, None))
        
        return result
    
    # Parse all authors and roles
    df['_parsed_authors'] = df['author_roles_norm'].apply(parse_authors_and_roles)
    
    # Create columns for author positions 2 through max_authors
    for i in range(2, max_authors + 1):
        # Author name column
        df[f'author_{i}'] = df['_parsed_authors'].apply(
            lambda x: x[i-1][0] if len(x) >= i else None
        )
        
    # Create role columns for all positions (1 through max_authors)
    for i in range(1, max_authors + 1):
        # Role column
        df[f'author_{i}_role'] = df['_parsed_authors'].apply(
            lambda x: x[i-1][1] if len(x) >= i else None
        )
    
    # Clean up temporary column
    df.drop('_parsed_authors', axis=1, inplace=True)
    
    return df

def filter_invalid_authors(df):
    """
    Remove junk entries from author_2 through author_5 columns
    Removes entries that start with # or are just )
    
    Parameters:
        df: DataFrame to clean
    
    Returns:
        DataFrame with cleaned author columns
    """
    df = df.copy()
    
    author_cols = ['author_2', 'author_3', 'author_4', 'author_5']
    
    for col in author_cols:
        if col in df.columns:
            # Replace with None if starts with # or is just )
            df.loc[
                df[col].astype(str).str.startswith('#', na=False) | 
                (df[col] == ')'),
                col
            ] = None
    
    return df