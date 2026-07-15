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
    
    # Custom Normalization for Conversation Intelligence
    # Hello variants
    text = re.sub(r'\bh[iey]+[ou]*\b', 'hello', text)
    text = re.sub(r'\bhello+o\b', 'hello', text)
    
    # Thank you variants
    text = re.sub(r'\b(thankuu|thnx|tnx)\b', 'thank you', text)
    
    # Good morning variants
    text = re.sub(r'\b(gud morning|gm)\b', 'good morning', text)
    
    # Remove leading/trailing spaces and multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
