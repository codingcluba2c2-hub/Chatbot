# backend/utils/normalizer.py
import re

def normalize_text(text: str) -> str:
    """
    Cleans up the text by removing extra spaces and converting to lowercase.
    """
    if not text:
        return ""
    
    # Convert to lower case
    text = text.lower()
    
    # Remove leading/trailing spaces and multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
