import os
import re
import unicodedata
from typing import Tuple, Dict, List, Any

class ContentNormalizer:
    @staticmethod
    def normalize(text: str) -> str:
        text = unicodedata.normalize("NFKC", text)
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # Remove PDF artifacts
        text = re.sub(r'(?im)^\s*page\s+\d+(\s+of\s+\d+)?\s*$', '', text)
        text = re.sub(r'(?i)https?://[^\s]+', '', text)
        text = re.sub(r'(?i)about:blank', '', text)
        text = re.sub(r'(?i)^\s*Print\s*$', '', text)
        
        # Remove excessive spaces
        text = re.sub(r'[ \t]{2,}', ' ', text)
        
        # Merge wrapped lines (stitch sentences broken in middle)
        blocks = re.split(r'\n{2,}', text)
        cleaned_blocks = []
        for block in blocks:
            if '|' in block:
                cleaned_blocks.append(block.strip())
                continue
                
            lines = block.split('\n')
            stitched_lines = []
            for line in lines:
                line = line.strip()
                if not line: continue
                
                if not stitched_lines:
                    stitched_lines.append(line)
                    continue
                    
                prev = stitched_lines[-1]
                if not re.search(r'[.:?!]$', prev) and not re.match(r'^[\*\-•\d+]\s', line) and not line.startswith('|'):
                    stitched_lines[-1] = prev + " " + line
                else:
                    stitched_lines.append(line)
            cleaned_blocks.append('\n'.join(stitched_lines))
            
        text = '\n\n'.join(cleaned_blocks)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

class BulletNormalizer:
    @staticmethod
    def normalize(text: str) -> str:
        # Pull orphan labels like "Mission:" into bullets
        lines = text.split('\n')
        normalized_lines = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.endswith(':') and len(line.split()) <= 4 and not line.startswith(('•', '*', '-')):
                # Look ahead for content
                j = i + 1
                next_content = ""
                while j < len(lines):
                    next_line = lines[j].strip()
                    if next_line:
                        next_content = next_line
                        break
                    j += 1
                
                if next_content and not re.match(r'^(?:#{1,6}\s+|\d+(?:\.\d+)*\.\s+|[A-Z].*:)', next_content) and not next_content.startswith('|'):
                    normalized_lines.append(f"• {line} {next_content}")
                    i = j + 1
                    continue
            normalized_lines.append(lines[i])
            i += 1
        return '\n'.join(normalized_lines)

class TableNormalizer:
    @staticmethod
    def extract_from_pdf(page) -> str:
        text = ""
        tables = page.extract_tables()
        for table in tables:
            if table:
                text += "\n\n"
                for row_idx, row in enumerate(table):
                    clean_row = [str(cell).replace('\n', ' ').strip() if cell is not None else "" for cell in row]
                    text += "| " + " | ".join(clean_row) + " |\n"
                    if row_idx == 0:
                        text += "|" + "|".join(["---"] * len(clean_row)) + "|\n"
                text += "\n\n"
        return text

class PDFLayoutParser:
    @staticmethod
    def parse(file_path: str) -> str:
        try:
            import pdfplumber
        except ImportError:
            raise RuntimeError("pdfplumber not installed.")
            
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n\n__PAGE_BOUNDARY_{i+1}__\n\n"
                    text += page_text + "\n"
                
                text += TableNormalizer.extract_from_pdf(page)
        return text

class ExtractionEngine:
    @staticmethod
    def extract_text(file_path: str, file_type: str) -> Tuple[str, str, Dict[str, int]]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        ext = file_type.lower()
        raw_text = ""
        
        if ext in ['txt', 'md', 'csv']:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                raw_text = f.read()
        elif ext == 'pdf':
            raw_text = PDFLayoutParser.parse(file_path)
        elif ext == 'docx':
            try:
                import docx
                doc = docx.Document(file_path)
                text_parts = []
                for element in doc.element.body:
                    if element.tag.endswith('p'):
                        p = docx.text.paragraph.Paragraph(element, doc)
                        text_parts.append(p.text)
                    elif element.tag.endswith('tbl'):
                        t = docx.table.Table(element, doc)
                        for row_idx, row in enumerate(t.rows):
                            row_text = [cell.text.replace('\n', ' ').strip() for cell in row.cells]
                            text_parts.append("| " + " | ".join(row_text) + " |")
                            if row_idx == 0:
                                text_parts.append("|" + "|".join(["---"] * len(row.cells)) + "|")
                        text_parts.append("\n")
                raw_text = "\n\n".join(text_parts)
            except ImportError:
                raise RuntimeError("python-docx not installed.")
        else:
            raise ValueError(f"Unsupported file type: {ext}")
            
        if not raw_text.strip():
            raise ValueError("Extracted text is empty.")
            
        # Pipeline normalization
        cleaned_text = ContentNormalizer.normalize(raw_text)
        cleaned_text = BulletNormalizer.normalize(cleaned_text)
        
        # Separate blocks cleanly with double newlines
        cleaned_text = re.sub(r'([^\n])\n([\*\-•])', r'\1\n\n\2', cleaned_text)
        cleaned_text = re.sub(r'([^\n])\n(#{1,6}\s+|\d+\.\d*\s+)', r'\1\n\n\2', cleaned_text)
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
        
        stats = {
            "characters": len(cleaned_text),
            "words": len(cleaned_text.split()),
            "paragraphs": len([p for p in cleaned_text.split('\n\n') if p.strip()])
        }
        
        return raw_text, cleaned_text, stats
