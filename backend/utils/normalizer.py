# backend/utils/normalizer.py
import re
import unicodedata
import time

def normalize_text(text: str) -> str:
    """
    Cleans up the text by removing extra spaces, converting to lowercase,
    unicode normalization, spell correction, and alias expansion.
    """
    if not text:
        return ""
    
    # 1. Unicode normalization
    text = unicodedata.normalize('NFKC', text)
    
    # 2. Convert to lower case
    text = text.lower()
    
    # 3. Spell correction & Alias expansion (basic implementation)
    text = re.sub(r'\bh[iey]+[ou]*\b', 'hello', text)
    text = re.sub(r'\bhello+o\b', 'hello', text)
    text = re.sub(r'\b(thankuu|thnx|tnx)\b', 'thank you', text)
    text = re.sub(r'\b(gud morning|gm)\b', 'good morning', text)
    
    # Additional common typo fixes / spelling correction
    spelling_fixes = {
        "teh": "the",
        "recieve": "receive",
        "adress": "address",
        "acheive": "achieve",
        "tomorow": "tomorrow",
        "accomodate": "accommodate",
        "wich": "which"
    }
    for wrong, right in spelling_fixes.items():
        text = re.sub(r'\b' + wrong + r'\b', right, text)
        
    # Alias expansion
    aliases = {
        "hr": "human resources",
        "ceo": "chief executive officer",
        "pto": "paid time off",
        "wfh": "work from home"
    }
    for alias, expansion in aliases.items():
        text = re.sub(r'\b' + alias + r'\b', expansion, text)
    
    # 4. Remove leading/trailing spaces and multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
