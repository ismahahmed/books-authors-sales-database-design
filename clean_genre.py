import pandas as pd
import re
from clean_data import normalize_text
import ast
from dateutil import parser
from datetime import datetime

def clean_genres_column(books_data):
    '''
    Clean genres column by:
    - converting stringified lists to real lists
    - lowercasing and trimming genre text
    - removing duplicates within each row

    Process:
    1. Use ast.literal_eval to safely convert string representations of lists into actual Python lists
    2. For each genre in the list, strip leading/trailing whitespace and convert to lowercase
    3. Remove any non-string entries from the genre lists, and ensure that empty or null genres become empty lists
    '''
    df = books_data.copy()
    # convert string lists into real lists
    df["genres"] = df["genres"].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) else []
    )
    # normalize genre text
    df["genres"] = df["genres"].apply(
        lambda lst: [g.strip().lower() for g in lst if isinstance(g, str)]
    )
    return df


def normalize_genre(genre_list):
    """
    Normalize a list of genres into standardized categories

    I gave AI a list of genres in the dataset and asked it to create a 
    comprehensive mapping so that different variations of the same genre would be categorized together
    """
    if genre_list is None or (isinstance(genre_list, float) and pd.isna(genre_list)):
        return []
    if not isinstance(genre_list, list) or len(genre_list) == 0:
        return []
    normalized = []
    
    for genre in genre_list:
        if pd.isna(genre):
            continue

        genre_lower = str(genre).lower().strip()
        
        # Fiction Categories
        if any(x in genre_lower for x in ['science fiction', 'sci fi', 'sci-fi', 'scifi']):
            if 'romance' in genre_lower:
                normalized.append('science fiction romance')
            elif 'military' in genre_lower:
                normalized.append('military science fiction')
            else:
                normalized.append('science fiction')
        
        elif any(x in genre_lower for x in ['fantasy']) and 'sci fi fantasy' not in genre_lower:
            if 'urban' in genre_lower:
                normalized.append('urban fantasy')
            elif 'epic' in genre_lower or 'high fantasy' in genre_lower:
                normalized.append('epic fantasy')
            elif 'dark' in genre_lower:
                normalized.append('dark fantasy')
            elif 'historical' in genre_lower:
                normalized.append('historical fantasy')
            elif 'paranormal' in genre_lower:
                normalized.append('paranormal fantasy')
            elif 'romance' in genre_lower:
                normalized.append('fantasy romance')
            elif 'young adult' in genre_lower:
                normalized.append('young adult fantasy')
            else:
                normalized.append('fantasy')
        
        elif any(x in genre_lower for x in ['romance']):
            if 'contemporary' in genre_lower:
                normalized.append('contemporary romance')
            elif 'historical' in genre_lower:
                normalized.append('historical romance')
            elif 'paranormal' in genre_lower:
                normalized.append('paranormal romance')
            elif 'erotic' in genre_lower:
                normalized.append('erotic romance')
            elif 'regency' in genre_lower:
                normalized.append('regency romance')
            elif 'christian' in genre_lower:
                normalized.append('christian romance')
            elif 'm m' in genre_lower or 'gay' in genre_lower:
                normalized.append('lgbtq+ romance')
            elif 'lesbian' in genre_lower:
                normalized.append('lgbtq+ romance')
            elif 'sports' in genre_lower:
                normalized.append('sports romance')
            elif 'western' in genre_lower:
                normalized.append('western romance')
            elif 'military' in genre_lower:
                normalized.append('military romance')
            elif 'young adult' in genre_lower:
                normalized.append('young adult romance')
            else:
                normalized.append('romance')
        
        elif any(x in genre_lower for x in ['mystery', 'whodunit', 'detective']):
            if 'cozy' in genre_lower:
                normalized.append('cozy mystery')
            elif 'historical' in genre_lower:
                normalized.append('historical mystery')
            elif 'paranormal' in genre_lower:
                normalized.append('paranormal mystery')
            else:
                normalized.append('mystery')
        
        elif any(x in genre_lower for x in ['thriller', 'suspense']):
            if 'psychological' in genre_lower:
                normalized.append('psychological thriller')
            elif 'legal' in genre_lower:
                normalized.append('legal thriller')
            elif 'spy' in genre_lower:
                normalized.append('spy thriller')
            elif 'romantic' in genre_lower:
                normalized.append('romantic suspense')
            else:
                normalized.append('thriller')
        
        elif any(x in genre_lower for x in ['horror', 'splatterpunk']):
            if 'gothic' in genre_lower:
                normalized.append('gothic horror')
            elif 'erotic' in genre_lower:
                normalized.append('erotic horror')
            else:
                normalized.append('horror')
        
        elif any(x in genre_lower for x in ['historical fiction', 'historical']):
            if 'naval' in genre_lower:
                normalized.append('historical fiction')
            elif 'christian' in genre_lower:
                normalized.append('christian historical fiction')
            elif 'young adult' in genre_lower:
                normalized.append('young adult historical fiction')
            else:
                normalized.append('historical fiction')
        
        # Young Adult & Children's
        elif any(x in genre_lower for x in ['young adult', 'ya ']):
            if 'contemporary' in genre_lower:
                normalized.append('young adult contemporary')
            elif 'paranormal' in genre_lower:
                normalized.append('young adult paranormal')
            else:
                normalized.append('young adult')
        
        elif any(x in genre_lower for x in ['middle grade', 'chapter books']):
            normalized.append('middle grade')
        
        elif any(x in genre_lower for x in ['childrens', 'picture books', 'kids']):
            normalized.append('children\'s')
        
        # Non-Fiction Categories
        elif any(x in genre_lower for x in ['biography', 'autobiography', 'memoir']):
            normalized.append('biography & memoir')
        
        elif any(x in genre_lower for x in ['history', 'historical']):
            if 'military' in genre_lower:
                normalized.append('military history')
            elif 'world war' in genre_lower:
                normalized.append('military history')
            elif 'american' in genre_lower:
                normalized.append('american history')
            else:
                normalized.append('history')
        
        elif any(x in genre_lower for x in ['philosophy', 'eastern philosophy']):
            normalized.append('philosophy')
        
        elif any(x in genre_lower for x in ['psychology', 'psychiatry', 'psychoanalysis']):
            normalized.append('psychology')
        
        elif any(x in genre_lower for x in ['self help', 'personal development', 'self-help']):
            normalized.append('self-help')
        
        elif any(x in genre_lower for x in ['business', 'entrepreneurship', 'management', 'leadership']):
            normalized.append('business')
        
        elif any(x in genre_lower for x in ['science', 'physics', 'biology', 'chemistry', 'astronomy']):
            normalized.append('science')
        
        elif any(x in genre_lower for x in ['religion', 'christian', 'christianity', 'islam', 'judaism', 'buddhism', 'spirituality', 'theology']):
            normalized.append('religion & spirituality')
        
        elif any(x in genre_lower for x in ['travel', 'travelogue']):
            normalized.append('travel')
        
        elif any(x in genre_lower for x in ['cookbook', 'cooking', 'food']):
            normalized.append('food & cooking')
        
        elif any(x in genre_lower for x in ['art', 'photography', 'design']):
            normalized.append('art & design')
        
        elif any(x in genre_lower for x in ['true crime']):
            normalized.append('true crime')
        
        # Literature & Classics
        elif any(x in genre_lower for x in ['classics', 'classic literature']):
            normalized.append('classics')
        
        elif any(x in genre_lower for x in ['literary fiction', 'literary']):
            normalized.append('literary fiction')
        
        elif any(x in genre_lower for x in ['poetry', 'poems']):
            normalized.append('poetry')
        
        # Comics & Graphic Novels
        elif any(x in genre_lower for x in ['graphic novel', 'comic', 'manga', 'manhwa']):
            normalized.append('graphic novels & comics')
        
        # Speculative Fiction
        elif any(x in genre_lower for x in ['dystopia', 'dystopian']):
            normalized.append('dystopian')
        
        elif any(x in genre_lower for x in ['post apocalyptic', 'apocalyptic']):
            normalized.append('post-apocalyptic')
        
        elif any(x in genre_lower for x in ['steampunk']):
            normalized.append('steampunk')
        
        elif any(x in genre_lower for x in ['cyberpunk']):
            normalized.append('cyberpunk')
        
        elif any(x in genre_lower for x in ['time travel']):
            normalized.append('time travel')
        
        elif any(x in genre_lower for x in ['alternate history']):
            normalized.append('alternate history')
        
        # Other Fiction
        elif any(x in genre_lower for x in ['crime', 'noir']):
            normalized.append('crime')
        
        elif any(x in genre_lower for x in ['western']):
            normalized.append('western')
        
        elif any(x in genre_lower for x in ['adventure']):
            normalized.append('adventure')
        
        elif any(x in genre_lower for x in ['humor', 'comedy']):
            normalized.append('humor')
        
        elif any(x in genre_lower for x in ['erotica', 'erotic']):
            normalized.append('erotica')
        
        elif any(x in genre_lower for x in ['paranormal', 'supernatural']):
            normalized.append('paranormal')
        
        elif any(x in genre_lower for x in ['chick lit', "women's fiction", 'womens fiction']):
            normalized.append('women\'s fiction')
        
        elif any(x in genre_lower for x in ['short stories', 'short story']):
            normalized.append('short stories')
        
        # LGBTQ+
        elif any(x in genre_lower for x in ['lgbt', 'gay', 'lesbian', 'queer', 'bisexual', 'transgender', 'm m ', 'f f ']):
            normalized.append('lgbtq+')
        
        # General categories
        elif genre_lower in ['fiction', 'novels', 'adult fiction']:
            normalized.append('fiction')
        
        elif genre_lower in ['nonfiction', 'non-fiction']:
            normalized.append('nonfiction')
        
        # If doesn't match any category, keep original lowercase
        else:
            # Skip time periods, grades, and very specific tags
            if any(x in genre_lower for x in ['century', 'grade', 'own', 'mine', 'unfinished', 'did not finish']):
                continue
            
            normalized.append(genre_lower)
    
    # Remove duplicates while preserving order
    seen = set()
    result = []
    for item in normalized:
        if item not in seen:
            seen.add(item)
            result.append(item)
    
    return result if result else ['uncategorized']

