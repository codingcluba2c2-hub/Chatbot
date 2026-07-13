import re
from typing import List, Dict, Any

class ChunkingEngine:
    @staticmethod
    def chunk_text(text: str, document_id: str = "unknown", strategy: str = "character", max_chars: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
        if not text:
            return []
            
        raw_chunks = []
        if strategy == "character":
            start = 0
            text_len = len(text)
            while start < text_len:
                end = min(start + max_chars, text_len)
                
                # If we're not at the end, try to break at a newline or space
                if end < text_len:
                    last_newline = text.rfind('\n', start, end)
                    last_space = text.rfind(' ', start, end)
                    
                    if last_newline != -1 and last_newline > start + overlap:
                        end = last_newline
                    elif last_space != -1 and last_space > start + overlap:
                        end = last_space
                        
                raw_chunks.append(text[start:end].strip())
                start = end - overlap if end < text_len else end
                
        elif strategy == "paragraph":
            # Simple split by double newline
            paragraphs = re.split(r'\n\s*\n', text)
            current_chunk = ""
            for p in paragraphs:
                p = p.strip()
                if not p:
                    continue
                if len(current_chunk) + len(p) < max_chars:
                    current_chunk += "\n\n" + p if current_chunk else p
                else:
                    if current_chunk:
                        raw_chunks.append(current_chunk)
                    current_chunk = p
            if current_chunk:
                raw_chunks.append(current_chunk)
                
        # Generate robust metadata
        chunks_with_meta = []
        for i, chunk_text in enumerate(raw_chunks):
            if not chunk_text:
                continue
            char_count = len(chunk_text)
            token_est = char_count // 4
            chunks_with_meta.append({
                "content": chunk_text,
                "metadata": {
                    "document_id": document_id,
                    "chunk_number": i + 1,
                    "character_count": char_count,
                    "estimated_tokens": token_est,
                    "page_number": None,
                    "section": None,
                    "heading": None,
                    "embedding_status": "pending",
                    "vector_id": None
                }
            })
            
        return chunks_with_meta
