import re
import hashlib
import unicodedata
from typing import List, Dict, Any, Tuple

class ChunkingEngine:
    @staticmethod
    def preprocess_text(text: str) -> str:
        # Normalize unicode
        text = unicodedata.normalize('NFKC', text)
        # Fix broken wrapped PDF lines ending with hyphen
        text = re.sub(r'-\s*\n\s*', '', text)
        # Replace other single newlines that aren't double newlines (simple wrapping)
        # However, lists might use single newlines. So we must be careful.
        # We will just normalize consecutive spaces.
        text = re.sub(r'[ \t]+', ' ', text)
        return text.strip()

    @staticmethod
    def find_chunk_boundaries(text: str, max_chars: int, overlap: int) -> List[Tuple[int, str]]:
        # Semantic chunking: prefer paragraphs, then sentences, then line breaks, then words
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            # If remaining text fits in max_chars, take it all
            if text_len - start <= max_chars:
                chunks.append((start, text[start:]))
                break
                
            # We need to find the best split point between start + max_chars - 200 and start + max_chars
            end_search_max = min(start + max_chars, text_len)
            end_search_min = max(start + max_chars - (max_chars // 2), start + 1)
            
            search_window = text[end_search_min:end_search_max]
            
            # Find boundaries in the search window (working backwards)
            split_idx = -1
            
            # Priority 1: Paragraph boundary
            para_match = list(re.finditer(r'\n\s*\n', search_window))
            if para_match:
                split_idx = end_search_min + para_match[-1].end()
                
            # Priority 2: Sentence boundary
            if split_idx == -1:
                sent_match = list(re.finditer(r'(?<=[.!?])\s+(?=[A-Z])', search_window))
                if sent_match:
                    split_idx = end_search_min + sent_match[-1].end()
                    
            # Priority 3: Line break
            if split_idx == -1:
                line_match = list(re.finditer(r'\n', search_window))
                if line_match:
                    split_idx = end_search_min + line_match[-1].end()
                    
            # Priority 4: Word boundary
            if split_idx == -1:
                word_match = list(re.finditer(r'\s+', search_window))
                if word_match:
                    split_idx = end_search_min + word_match[-1].end()
                    
            # Priority 5: Character boundary (fallback)
            if split_idx == -1:
                split_idx = end_search_max
                
            # Validate boundaries to ensure no broken words or sentences
            while split_idx > start and split_idx < text_len:
                if text[split_idx-1].isalnum() and text[split_idx].isalnum():
                    # Broken word, move back to last space
                    last_space = text.rfind(' ', start, split_idx)
                    if last_space != -1:
                        split_idx = last_space
                    else:
                        break
                else:
                    break
                    
            chunk_content = text[start:split_idx].strip()
            
            if chunk_content and chunk_content[0].isalnum() or chunk_content[0] in '“"\'([{¿¡':
                chunks.append((start, chunk_content))
            elif chunk_content:
                # If chunk starts with bad punctuation, strip it
                chunks.append((start, re.sub(r'^[^a-zA-Z0-9]+', '', chunk_content).strip()))
            
            # Calculate next start with overlap, snapping to nearest word/sentence boundary
            next_start_raw = split_idx - overlap
            if next_start_raw <= start:
                next_start_raw = start + 1  # Progress forward
                
            # Snap overlap start to word boundary
            overlap_search = text[max(0, next_start_raw - 50):min(text_len, next_start_raw + 50)]
            # Find nearest space backwards or forwards
            space_match = list(re.finditer(r'\s+', text[max(0, next_start_raw - 50):next_start_raw]))
            if space_match:
                start = max(0, next_start_raw - 50) + space_match[-1].end()
            else:
                space_match_fwd = re.search(r'\s+', text[next_start_raw:min(text_len, next_start_raw + 50)])
                if space_match_fwd:
                    start = next_start_raw + space_match_fwd.end()
                else:
                    start = next_start_raw
                    
        return chunks

    @staticmethod
    def chunk_text(text: str, document_id: str = "unknown", strategy: str = "semantic", max_chars: int = 800, overlap: int = 150) -> List[Dict[str, Any]]:
        if not text:
            return []
            
        import re
        page_map = []
        clean_text = ""
        last_idx = 0
        
        for match in re.finditer(r'\n*__PAGE_BOUNDARY_(\d+)__\n*', text):
            chunk_part = text[last_idx:match.start()]
            clean_text += chunk_part
            page_map.append((len(clean_text), int(match.group(1))))
            last_idx = match.end()
            
        clean_text += text[last_idx:]
        text = clean_text
            
        text = ChunkingEngine.preprocess_text(text)
        raw_chunks = ChunkingEngine.find_chunk_boundaries(text, max_chars, overlap)
                
        # Generate robust metadata
        chunks_with_meta = []
        for i, (start_idx, chunk_text) in enumerate(raw_chunks):
            if not chunk_text:
                continue
                
            page_num = 1
            for p_idx, p_num in page_map:
                if start_idx >= p_idx:
                    page_num = p_num
                else:
                    break
            char_count = len(chunk_text)
            token_est = char_count // 4
            chunk_hash = hashlib.sha256(chunk_text.encode('utf-8')).hexdigest()
            
            # Extract first and last sentence
            sentences = re.split(r'(?<=[.!?])\s+', chunk_text)
            first_sentence = sentences[0] if sentences else ""
            last_sentence = sentences[-1] if len(sentences) > 0 else ""
            
            chunks_with_meta.append({
                "content": chunk_text,
                "metadata": {
                    "document_id": document_id,
                    "chunk_number": i + 1,
                    "character_count": char_count,
                    "estimated_tokens": token_est,
                    "first_sentence": first_sentence[:150] + "..." if len(first_sentence) > 150 else first_sentence,
                    "last_sentence": last_sentence[:150] + "..." if len(last_sentence) > 150 else last_sentence,
                    "page_number": page_num,
                    "section": None,
                    "heading": None,
                    "hash": chunk_hash,
                    "embedding_status": "pending",
                    "vector_id": None
                }
            })
            
        return chunks_with_meta
