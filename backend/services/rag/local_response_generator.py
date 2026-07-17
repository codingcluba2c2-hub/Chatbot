import time
from typing import List, Dict, Any
from .response_builder import ContextResponseBuilder, RAGResponseBuilder
from .answer_compressor import AnswerCompressor

class LocalResponseGenerator:
    @staticmethod
    def generate(query: str, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        t0 = time.time()
        
        # 1. Answer Compression
        compression_result = AnswerCompressor.compress(query, chunks, max_sentences=6)
        sentences = compression_result["sentences"]
        metrics = compression_result["metrics"]
        
        # 2. Formatting
        if not sentences:
            formatted_response = "I couldn't find enough relevant information in the knowledge base to answer that."
        else:
            formatted_response = "\n".join(sentences)
            
        t1 = time.time()
        processing_time_ms = int((t1 - t0) * 1000)
        
        return {
            "response": formatted_response,
            "metadata": {
                "Response Source": "Local Generator (Enterprise Mode)",
                "Fallback Used": True,
                "Sentences Selected": len(sentences),
                "Compression Ratio": f"{metrics['compressed_length']} / {metrics['original_length']} chars",
                "Processing Time": f"{processing_time_ms} ms"
            }
        }
