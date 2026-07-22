import re

class ChunkingEngine:
    @staticmethod
    def chunk_text(text: str, document_id: str = None, max_chunk_size: int = 1000, overlap: int = 200):
        if not text:
            return []
            
        chunks = []
        chunk_number = 0
        
        # Split by page boundaries if they exist
        pages = re.split(r'___PAGE_BOUNDARY_(\d+)___', text)
        
        if len(pages) > 1:
            # pages will look like [intro_text, page_num_1, page_content_1, page_num_2, page_content_2, ...]
            # The first element is text before the first boundary (usually empty)
            page_blocks = []
            if pages[0].strip():
                page_blocks.append((None, pages[0]))
            
            for i in range(1, len(pages), 2):
                page_num = pages[i]
                page_content = pages[i+1] if i+1 < len(pages) else ""
                page_blocks.append((page_num, page_content))
        else:
            page_blocks = [(None, text)]
            
        for page_num, page_text in page_blocks:
            if not page_text.strip():
                continue
                
            # Semantic sentence splitting
            sentences = re.split(r'(?<=[.!?])\s+', page_text)
            current_chunk = ""
            
            for sentence in sentences:
                if len(current_chunk) + len(sentence) > max_chunk_size and current_chunk:
                    meta = {"chunk_number": chunk_number}
                    if page_num:
                        meta["page_number"] = page_num
                        
                    chunks.append({
                        "content": current_chunk.strip(),
                        "metadata": meta
                    })
                    chunk_number += 1
                    
                    overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                    space_idx = overlap_text.find(" ")
                    if space_idx != -1:
                        overlap_text = overlap_text[space_idx:]
                    current_chunk = overlap_text.strip() + " " + sentence
                else:
                    current_chunk += (" " + sentence if current_chunk else sentence)
                    
            if current_chunk.strip():
                meta = {"chunk_number": chunk_number}
                if page_num:
                    meta["page_number"] = page_num
                    
                chunks.append({
                    "content": current_chunk.strip(),
                    "metadata": meta
                })
                chunk_number += 1
                
        return chunks
