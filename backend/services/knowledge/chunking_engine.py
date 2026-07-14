import re
import hashlib
from typing import List, Dict, Any

class ChunkingEngine:
    @staticmethod
    def chunk_text(text: str, document_id: str = "unknown", strategy: str = "semantic", max_chars: int = 800, overlap: int = 150) -> List[Dict[str, Any]]:
        if not text:
            return []
            
        raw_chunks = []
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=max_chars,
                chunk_overlap=overlap,
                length_function=len,
                is_separator_regex=False,
                separators=[
                    "\n\n",
                    "\n",
                    " ",
                    ""
                ]
            )
            raw_chunks = text_splitter.split_text(text)
        except ImportError:
            # Fallback to a basic implementation if the package is missing for some reason
            # Split by double newline first, then enforce max_chars by splitting at spaces if needed
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
            chunk_hash = hashlib.sha256(chunk_text.encode('utf-8')).hexdigest()
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
                    "hash": chunk_hash,
                    "embedding_status": "pending",
                    "vector_id": None
                }
            })
            
        return chunks_with_meta
