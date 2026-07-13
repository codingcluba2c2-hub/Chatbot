from typing import List, Dict, Any

class RAGResponseBuilder:
    @staticmethod
    def build_fallback() -> str:
        return "I don't have enough information regarding this topic."

    @staticmethod
    def build_response(accepted_chunks: List[Dict[str, Any]]) -> str:
        if not accepted_chunks:
            return RAGResponseBuilder.build_fallback()
            
        # Normally this would be fed to an LLM. Since we CANNOT use an LLM,
        # we will deterministically return a concatenation of the top retrieved text.
        
        # We ensure no hallucination by strictly returning the exact chunk text.
        text_responses = []
        for hit in accepted_chunks:
            payload = hit["payload"]
            text_responses.append(payload.get("content", ""))
            
        merged_text = "\n\n".join(text_responses)
        return f"Based on the knowledge base:\n\n{merged_text}"
        
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
