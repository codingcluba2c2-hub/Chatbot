import re
from typing import Dict, Any, List

class LocalMarkdownFormatter:
    """
    Enterprise Local Response Builder that formats raw retrieved chunks 
    into a beautiful Markdown response when all LLM providers fail.
    """
    
    def generate_response(self, chunks: List[Dict[str, Any]], context_text: str) -> Dict[str, Any]:
        """
        Generate local fallback Markdown.
        Never show internal properties: Section, Subsection, Chunk ID, Block Type, Embedding, Document ID, Metadata, Similarity, Parent, Node.
        """
        if not chunks and not context_text:
            return {"success": False, "response": "No information found.", "error": "No context"}
            
        # If rag.py already built a nice context_text, we can use it as the base
        response = "### Enterprise Fallback Response\n\n"
        
        if context_text:
            # Clean out any system leakage just in case
            cleaned = self._clean_system_metadata(context_text)
            response += cleaned
        else:
            # Fallback to formatting raw chunks if context_text is somehow missing
            for c in chunks:
                text = c.get("text", "")
                if text:
                    response += self._clean_system_metadata(text) + "\n\n"
                    
        return {"success": True, "response": response.strip(), "error": None}
        
    def _clean_system_metadata(self, text: str) -> str:
        # Remove patterns like "Chunk ID: 123", "Document ID: xyz", etc.
        patterns = [
            r"(?i)^.*(chunk id|document id|block type|embedding|similarity|metadata|node|parent).*?:.*$\n?",
            r"(?i)^.*(section|subsection)\s*:\s*.*$\n?",
        ]
        cleaned = text
        for p in patterns:
            cleaned = re.sub(p, "", cleaned, flags=re.MULTILINE)
        return cleaned.strip()
