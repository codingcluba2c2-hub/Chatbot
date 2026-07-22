import pdfplumber
import docx
import csv
import time

class ExtractionEngine:
    @staticmethod
    def extract_text(file_path: str, file_type: str):
        raw_text = ""
        text = ""
        stats = {}
        t0 = time.time()
        
        try:
            if file_type == 'pdf':
                with pdfplumber.open(file_path) as pdf:
                    pages_text = []
                    for i, page in enumerate(pdf.pages):
                        page_text = page.extract_text()
                        if page_text:
                            pages_text.append(f"___PAGE_BOUNDARY_{i+1}___\n\n{page_text}")
                    raw_text = "\n\n".join(pages_text)
            elif file_type in ['docx', 'doc']:
                doc = docx.Document(file_path)
                raw_text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            elif file_type == 'csv':
                with open(file_path, newline='', encoding='utf-8', errors='ignore') as csvfile:
                    reader = csv.reader(csvfile)
                    raw_text = "\n".join([", ".join(row) for row in reader])
            else:
                # Default for txt, md, etc.
                with open(file_path, "r", encoding="utf-8", errors='ignore') as f:
                    raw_text = f.read()
                    
            text = raw_text.strip()
            
        except Exception as e:
            stats["extraction_error"] = str(e)
            
        stats["extraction_time"] = round(time.time() - t0, 2)
        stats["characters"] = len(text)
        stats["words"] = len(text.split())
        stats["paragraphs"] = len([p for p in text.split('\n') if p.strip()])
        return raw_text, text, stats
