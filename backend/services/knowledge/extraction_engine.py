import os
import io
import re
import unicodedata
from typing import Tuple, Dict
from core.logger import get_logger

logger = get_logger(__name__)

class ExtractionEngine:
    @staticmethod
    def clean_text(text: str) -> str:
        # 1. Unicode Normalization
        text = unicodedata.normalize("NFKC", text)
        
        # 2. Control Character Removal
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # 3. Header/Footer/Page Number Removal
        # e.g. "Page 1 of 10", "Confidential", etc.
        text = re.sub(r'(?im)^page\s+\d+(\s+of\s+\d+)?\s*$', '', text)
        text = re.sub(r'(?im)^confidential\s*$', '', text)
        text = re.sub(r'(?im)^\d+\s*\|\s*page\s*$', '', text)
        
        # 4. Hyphenated Word Repair
        # e.g., "appli- \ncation" -> "application"
        text = re.sub(r'([a-zA-Z]+)-\s*\n\s*([a-zA-Z]+)', r'\1\2', text)
        
        # 5. Wrapped Line Repair
        # If line ends with word char/comma and next starts with lower case
        text = re.sub(r'([a-zA-Z0-9,])[ \t]*\n[ \t]*([a-z])', r'\1 \2', text)
        
        # 6. Paragraph Reconstruction
        # If line ends with period/question/exclamation, it might be end of paragraph. Ensure double newline.
        text = re.sub(r'([.!?])[ \t]*\n[ \t]*([A-Z])', r'\1\n\n\2', text)
        
        # 7. Remove Empty Lines and Extra Whitespace
        # Merge multiple newlines into two to preserve paragraph structure
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Clean trailing/leading spaces on lines
        text = '\n'.join([line.strip() for line in text.split('\n')])
        
        # 8. Remove extra spaces between words
        text = re.sub(r'[ \t]+', ' ', text)
        
        return text.strip()

    @staticmethod
    def extract_text(file_path: str, file_type: str) -> Tuple[str, str, Dict[str, int]]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        ext = file_type.lower()
        text = ""
        
        if ext in ['txt', 'md', 'csv']:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        elif ext == 'pdf':
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for i, page in enumerate(reader.pages):
                        page_text = page.extract_text()
                        if page_text:
                            text += f"\n\n__PAGE_BOUNDARY_{i+1}__\n\n"
                            text += page_text + "\n"
            except ImportError:
                raise RuntimeError("PyPDF2 not installed. Cannot extract PDF.")
        elif ext == 'docx':
            try:
                import docx
                doc = docx.Document(file_path)
                text = "\n".join([p.text for p in doc.paragraphs])
            except ImportError:
                raise RuntimeError("python-docx not installed. Cannot extract DOCX.")
        else:
            raise ValueError(f"Unsupported file type: {ext}")
            
        # If extraction is completely blank
        if not text.strip():
            raise ValueError("Extracted text is empty. Document may be an image or corrupted.")
            
        # Clean text
        cleaned_text = ExtractionEngine.clean_text(text)
        
        # If text is empty after cleaning
        if not cleaned_text.strip():
            raise ValueError("Extracted text is empty after cleaning.")
            
        # Calculate stats
        char_count = len(cleaned_text)
        words = cleaned_text.split()
        word_count = len(words)
        paragraphs = [p for p in cleaned_text.split('\n\n') if p.strip()]
        
        stats = {
            "characters": char_count,
            "words": word_count,
            "paragraphs": len(paragraphs)
        }
        
        return text, cleaned_text, stats
