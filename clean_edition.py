import pandas as pd
import re
from dateutil import parser
from datetime import datetime


def normalize_edition(edition):
    """
    Normalize edition strings to consistent format
    """
    if pd.isna(edition):
        return None
    
    # Convert to string and strip whitespace
    edition = str(edition).strip()
    
    # Convert to lowercase for consistency
    edition_lower = edition.lower()
    
    # Remove common patterns that aren't useful
    # Remove URLs
    if edition_lower.startswith('http'):
        return 'Other'
    
    # Remove catalog IDs, ISBNs, etc.
    if any(x in edition_lower for x in ['lcc ', 'catalog id', '#v', 'isbn']):
        return 'Other'
    
    # Standardize ordinal numbers (1st, 2nd, 3rd, etc.)
    edition_lower = re.sub(r'\b1st\b', 'first', edition_lower)
    edition_lower = re.sub(r'\b2nd\b', 'second', edition_lower)
    edition_lower = re.sub(r'\b3rd\b', 'third', edition_lower)
    edition_lower = re.sub(r'\b(\d+)th\b', r'\1th', edition_lower)
    
    # Standardize common variations
    replacements = {
        'ed.': 'edition',
        'ed ': 'edition ',
        'edtion': 'edition',
        'editio': 'edition',
        'aniv': 'anniversary',
        'us/can': 'us/canada',
        'u.s.': 'us',
        'u.k.': 'uk',
        'e-book': 'ebook',
        'e-audio': 'eaudio',
    }
    
    for old, new in replacements.items():
        edition_lower = edition_lower.replace(old, new)
    
    # Categorize into major types
    if any(x in edition_lower for x in ['first edition', 'first ed', '1st edition']):
        return 'First Edition'
    elif re.search(r'(second|2nd) edition', edition_lower):
        return 'Second Edition'
    elif re.search(r'(third|3rd) edition', edition_lower):
        return 'Third Edition'
    elif re.search(r'(\d+th|fourth|fifth|sixth|seventh|eighth|ninth|tenth) edition', edition_lower):
        return 'Later Edition'
    elif 'anniversary' in edition_lower:
        return 'Anniversary Edition'
    elif any(x in edition_lower for x in ['movie tie', 'film tie', 'tv tie']):
        return 'Media Tie-In'
    elif any(x in edition_lower for x in ['deluxe', 'collector', 'limited', 'special edition']):
        return 'Special Edition'
    elif any(x in edition_lower for x in ['reprint', 'reissue', 'revised']):
        return 'Revised/Reprint'
    elif any(x in edition_lower for x in ['large print', 'large-print']):
        return 'Large Print'
    elif any(x in edition_lower for x in ['abridged']):
        return 'Abridged'
    elif any(x in edition_lower for x in ['unabridged']):
        return 'Unabridged'
    elif any(x in edition_lower for x in ['audiobook', 'audio', 'eaudio']):
        return 'Audio'
    elif any(x in edition_lower for x in ['ebook', 'kindle', 'nook', 'digital']):
        return 'Digital'
    elif any(x in edition_lower for x in ['graphic novel', 'illustrated']):
        return 'Illustrated/Graphic'
    elif any(x in edition_lower for x in ['penguin classics', 'modern classics', 'classic']):
        return 'Classic Series'
    elif 'box' in edition_lower or 'boxed' in edition_lower or 'volume set' in edition_lower:
        return 'Box Set'
    elif edition_lower in ['', 'regular', 'standard', 'original']:
        return 'Standard'
    else:
        return 'Other'