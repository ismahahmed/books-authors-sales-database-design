import pandas as pd
import re
from dateutil import parser
from datetime import datetime

def normalize_book_format(df, source_col="bookFormat", target_col="bookFormat_norm"):
    """
    Normalize book formats into canonical buckets.

    Produces target_col with values like:
      audio, ebook, hardcover, paperback, mass_market_paperback, board_book,
      boxed_set, library_binding, spiral_bound, comic, pamphlet, unbound,
      digital_other, unknown, other
    """

    s = (
        df[source_col]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace("\u00a0", " ", regex=False)
        .str.replace(r"[’‘`]", "'", regex=True)
        .str.replace(r"[–—]", "-", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    # Remove diacritics to make matching easy (e.g., "broché")
    s = s.str.normalize("NFKD").str.encode("ascii", "ignore").str.decode("ascii")

    # Quick standardizations
    s = (
        s.replace({"mass_market": "mass market", "paper": "paperback"})
         .str.replace(r"\be-?book\b", "ebook", regex=True)
         .str.replace(r"\bkindle edition\b", "kindle", regex=True)
    )

    # Ordered rules
    rules = [
        # Audio
        (r"\b(audible|audiobook|audio cd|audio cassette|audio play|mp3 cd|audio)\b", "audio"),
        # Ebook / digital readers
        (r"\b(ebook|kindle|nook|digital)\b", "ebook"),
        # Boxed / sets / slipcased
        (r"\b(box set|boxed set|box-set|book set|hardcover boxed set|hardcover slipcased|slipcased hardcover)\b", "boxed_set"),
        # Board books
        (r"\b(board|board book)\b", "board_book"),
        # Library bindings / school bindings / turtleback
        (r"\b(library binding|school & library binding|turtleback)\b", "library_binding"),
        # Hardcover
        (r"\b(hardcover|hardback|casebound|cloth|capa dura|pasta dura|leather bound)\b", "hardcover"),
        # Mass market paperback
        (r"\b(mass market paperback|mass market)\b", "mass_market_paperback"),
        # Trade paperback / paperback / softcover
        (r"\b(trade paperback|paperback|perfect paperback|softcover|capa comum|broche|paper)\b", "paperback"),
        # Spiral
        (r"\b(spiral-bound|spiral bound)\b", "spiral_bound"),
        # Comics / graphic novels
        (r"\b(comic|comics|graphic novels)\b", "comic"),

        # Pamphlet
        (r"\b(pamphlet)\b", "pamphlet"),
        # Unbound
        (r"\b(unbound)\b", "unbound"),
        # Unknown-ish
        (r"\b(unknown binding|unknown|other)\b", "unknown"),
    ]
    
    out = s.copy()
    out[:] = "unknown"

    for pattern, label in rules:
        m = out.eq("unknown") & s.str.contains(pattern, regex=True, na=False)
        out = out.mask(m, label)

    # If it was empty originally, set unknown
    out = out.mask(s.eq(""), "unknown")

    df[target_col] = out
    return df