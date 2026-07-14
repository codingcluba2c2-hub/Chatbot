from typing import List, Dict, Any

class RAGResponseBuilder:
    @staticmethod
    def build_fallback() -> str:
        return "I don't have enough information regarding this topic."

    @staticmethod
    def build_context(accepted_chunks: List[Dict[str, Any]]) -> str:
        if not accepted_chunks:
            return ""
            
        context_parts = []
        for i, hit in enumerate(accepted_chunks):
            payload = hit["payload"]
            content = payload.get("content", "")
            doc_id = payload.get("document_id", "Unknown")
            heading = payload.get("heading", "")
            
            header = f"--- Document: {doc_id} "
            if heading:
                header += f"| Section: {heading} "
            header += "---"
            
            context_parts.append(f"{header}\n{content}\n")
            
        return "\n".join(context_parts)

class ContextResponseBuilder:
    @staticmethod
    def build_concise_fallback(chunks: List[Dict[str, Any]]) -> str:
        """
        Extracts 1-3 most relevant sentences across all chunks.
        Max 80 words. Deduplicates sentences.
        Does not dump raw chunks.
        """
        if not chunks:
            return "I found related information in the knowledge base, but couldn't confidently extract a concise answer."
            
        import re
        unique_sentences = set()
        ordered_sentences = []
        
        for chunk in chunks:
            text = chunk.get("text", "")
            # Split into roughly sentence-like chunks
            # We use a simple regex split on punctuation, keeping the punctuation
            raw_sentences = re.split(r'(?<=[.!?])\s+', text)
            
            for sentence in raw_sentences:
                line = sentence.strip()
                if not line:
                    continue
                    
                line_lower = line.lower()
                # Remove common artifacts
                if re.match(r'^page\s+\d+$', line_lower) or re.match(r'^pg\.?\s+\d+$', line_lower):
                    continue
                if re.match(r'^chunk\s+#?\d+$', line_lower):
                    continue
                if line_lower.startswith('source:') or line_lower.startswith('document:'):
                    continue
                    
                # Clean up multiple spaces
                clean_line = re.sub(r'\s+', ' ', line)
                
                # Deduplicate
                if clean_line not in unique_sentences and len(clean_line) > 10:
                    unique_sentences.add(clean_line)
                    ordered_sentences.append(clean_line)
                    
        if not ordered_sentences:
            return "I found related information in the knowledge base, but couldn't confidently extract a concise answer."
            
        # Extract 1-3 most relevant sentences (we just take the first 3 for simplicity, which are highest ranked due to retrieval score)
        final_sentences = ordered_sentences[:3]
        final_text = " ".join(final_sentences)
        
        # Enforce 80 words maximum
        words = final_text.split()
        if len(words) > 80:
            final_text = " ".join(words[:80]) + "..."
            
        return final_text
        
    @staticmethod
    def build_citations(accepted_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        components = []
        for i, hit in enumerate(accepted_chunks):
            payload = hit["payload"]
            score = round(hit["score"] * 100, 1)
            doc_name = payload.get("doc_name", "Unknown Document")
            
            # Use dynamic UI components for citations
            components.append({
                "type": "card",
                "props": {
                    "title": f"Source {i+1}: {doc_name}",
                    "subtitle": f"Similarity: {score}%",
                    "description": payload.get("content", "")[:100] + "..."
                }
            })
        return components
