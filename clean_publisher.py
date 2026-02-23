import pandas as pd
import re
from dateutil import parser
from datetime import datetime


def remove_non_english_publishers(df):
    '''
    Removes rows where publisher contains non latin characters
    Keeps rows where publisher is empty or standard English text
    '''

    clean_df = df.copy()

    # keep rows where publisher has ONLY latin letters, numbers, spaces, & basic punctuation
    mask_english = clean_df["publisher"].fillna("").str.match(r"^[a-zA-Z0-9\s&\-\.',/]*$")

    clean_df = clean_df[mask_english].reset_index(drop=True)

    return clean_df



def normalize_publishers(df, source_col="publisher", target_col="publisher_norm"):
    """
    Normalize publisher names into a cleaned, standardized column.

    Process:    
    1. Basic normalization: lowercase, trim, remove accents, replace common punctuation variations, remove country names, etc.
    2. Remove junk placeholders like "not available", "none", "unknown", etc.
    3. Apply ordered family rules to map imprints to parent publishers, and standardize common publisher names.
    4. Final cleanup: remove trailing punctuation, collapse whitespace, and set empty values to "unknown".

    This will help ensure that different variations of the same publisher are consistently represented, 
    and that junk or non-informative values are cleaned out
    """
    # BASIC NORMALIZATION 
    df[target_col] = df[source_col]

    df[target_col] = (
        df[target_col]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace("\u00a0", " ", regex=False)
        .str.replace(r"[''`]", "'", regex=True)
        .str.replace(r"[–—]", "-", regex=True)
        .str.replace(r"\s*\(.*?\)", "", regex=True)
        .str.replace(r"\b(uk|usa?|australia|india|canada)\b", "", regex=True)
        .str.replace(r"(?<=\b[a-z])\.(?=[a-z])", "", regex=True)
        .str.replace(r"\b([a-z]{1,3})\.\b", r"\1", regex=True)
        .str.replace(r"[.\s]+$", "", regex=True)
        .str.replace(r"\s*&\s*", " & ", regex=True)
        .str.replace(r"\b(inc|inc\.|ltd|ltd\.|llc|plc|co|co\.|corp|corp\.|gmbh|sa|s\.a\.|pte|pty)\b", "", regex=True)
        .str.replace(r"\s*-\s*(au|uk|us|usa|ca|nz)\b", "", regex=True)
        .str.replace(r"\b(pub|pub\.|publications)\b", "publishing", regex=True)
        .str.replace(r"\b(publishers|publishing)\b", "publishing", regex=True)
        .str.replace(r"\bcompanyy\b", "company", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.replace(r",+$", "", regex=True)
        .str.strip()
    )

    #  REMOVE "NOT AVAILABLE" AND OTHER JUNK PLACEHOLDERS 
    junk_patterns = [
        r"\bnot\s+avail(?:able)?\b",
        r"^s$",
        r"^self$",
        r"^none$",
        r"^n/a$",
        r"^unknown$",
        r"^see notes$",
    ]
    
    for pattern in junk_patterns:
        df.loc[df[target_col].str.contains(pattern, na=False), target_col] = ""

    # --- SELF-PUBLISHED VARIATIONS ---
    self_pub_pattern = r"(^self[\s-]?published|^independently published|^createspace|^kindle direct|^lulu|^smashwords|^amazon[\s-]?publishing|^author[\s-]?house|^xlibris|^iuniverse|^bookbaby)"
    df.loc[df[target_col].str.contains(self_pub_pattern, na=False), target_col] = "self-published"

    # --- ORDERED FAMILY RULES ---
    publisher_rules = [
        # Major Publishers - Big 5
        (r"^.*penguin.*random.*house.*$", "penguin random house"),
        (r"^.*harpercollins.*$", "harpercollins"),
        (r"^.*harper\s*collins.*$", "harpercollins"),
        (r"^.*simon\s*&?\s*schuster.*$", "simon & schuster"),
        (r"^.*hachette.*$", "hachette"),
        (r"^.*macmillan.*$", "macmillan"),
        
        # Penguin Random House Imprints
        (r"^.*penguin.*$", "penguin"),
        (r"^.*random\s*house.*$", "random house"),
        (r"^.*bantam.*$", "penguin"),
        (r"^.*del\s*rey.*$", "penguin"),
        (r"^.*ballantine.*$", "penguin"),
        (r"^.*viking.*$", "penguin"),
        (r"^.*riverhead.*$", "penguin"),
        (r"^.*putnam.*$", "penguin"),
        (r"^.*doubleday.*$", "penguin"),
        (r"^.*knopf.*$", "penguin"),
        (r"^.*anchor.*$", "penguin"),
        (r"^.*vintage.*$", "penguin"),
        (r"^.*berkley.*$", "penguin"),
        (r"^.*ace\s*books.*$", "penguin"),
        (r"^.*roc\b.*$", "penguin"),
        (r"^.*daw\b.*$", "penguin"),
        (r"^.*dial.*$", "penguin"),
        (r"^.*dutton.*$", "penguin"),
        (r"^.*plume.*$", "penguin"),
        (r"^.*signet.*$", "penguin"),
        (r"^.*nal\b.*$", "penguin"),
        
        # HarperCollins Imprints
        (r"^.*harper.*$", "harpercollins"),
        (r"^.*william\s*morrow.*$", "harpercollins"),
        (r"^.*avon.*$", "harpercollins"),
        (r"^.*ecco.*$", "harpercollins"),
        (r"^.*harlequin.*$", "harpercollins"),
        (r"^.*mira\b.*$", "harpercollins"),
        (r"^.*mills\s*&\s*boon.*$", "harpercollins"),
        (r"^.*voyager.*$", "harpercollins"),
        
        # Simon & Schuster Imprints
        (r"^.*atria.*$", "simon & schuster"),
        (r"^.*gallery.*$", "simon & schuster"),
        (r"^.*scribner.*$", "simon & schuster"),
        (r"^.*pocket\s*books.*$", "simon & schuster"),
        (r"^.*touchstone.*$", "simon & schuster"),
        
        # Hachette Imprints
        (r"^.*little\s*,?\s*brown.*$", "hachette"),
        (r"^.*orbit.*$", "hachette"),
        (r"^.*grand\s*central.*$", "hachette"),
        (r"^.*faithwords.*$", "hachette"),
        
        # Macmillan Imprints
        (r"^.*tor\b.*$", "macmillan"),
        (r"^.*forge.*$", "macmillan"),
        (r"^.*st\.?\s*martin.*$", "macmillan"),
        (r"^.*farrar.*straus.*giroux.*$", "macmillan"),
        (r"^.*picador.*$", "macmillan"),
        (r"^.*holt.*$", "macmillan"),
        
        # Other Major Publishers
        (r"^.*scholastic.*$", "scholastic"),
        (r"^.*bloomsbury.*$", "bloomsbury"),
        (r"^.*disney.*$", "disney"),
        (r"^.*marvel.*$", "marvel"),
        (r"^.*dc\s*comics.*$", "dc comics"),
        (r"^.*oxford\s*university\s*press.*$", "oxford university press"),
        (r"^.*cambridge\s*university\s*press.*$", "cambridge university press"),
        
        # Specific Publishers
        (r"^.*grove.*atlantic.*$", "grove/atlantic"),
        (r"^.*orion.*$", "orion"),
        (r"^.*titan\s*books.*$", "titan books"),
        (r"^.*baen.*$", "baen"),
        (r"^.*tor\.com.*$", "tor.com"),
        (r"^.*subterranean.*$", "subterranean press"),
        (r"^.*tachyon.*$", "tachyon"),
        (r"^.*night\s*shade.*$", "night shade books"),
        (r"^.*angry\s*robot.*$", "angry robot"),
        (r"^.*gollancz.*$", "gollancz"),
        (r"^.*hodder.*$", "hodder & stoughton"),
        (r"^.*faber.*$", "faber & faber"),
        (r"^.*pan\s*macmillan.*$", "pan macmillan"),
        (r"^.*candlewick.*$", "candlewick"),
        (r"^.*chronicle.*$", "chronicle books"),
        (r"^.*abrams.*$", "abrams"),
        (r"^.*quirk.*$", "quirk books"),
        (r"^.*sourcebooks.*$", "sourcebooks"),
        (r"^.*kensington.*$", "kensington"),
        (r"^.*entangled.*$", "entangled publishing"),
        (r"^.*montlake.*$", "montlake"),
    ]

    for pattern, replacement in publisher_rules:
        df[target_col] = df[target_col].str.replace(pattern, replacement, regex=True)

    df[target_col] = (
        df[target_col]
        .str.replace(r"\s+,", ",", regex=True)
        .str.replace(r",\s*$", "", regex=True)
        .str.replace(r"[.\s]+$", "", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )
    
    df.loc[df[target_col] == "", target_col] = "unknown"

    return df