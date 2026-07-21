# backend/agents/orchestrator.py
from typing import Dict, Any, Generator, Optional
import os
import json
from agno.agent import Agent
from agno.models.google import Gemini
from .tools import search_knowledge_base, query_sql_database
from core.logger import get_logger
from core.config import DEVELOPER_MODE

logger = get_logger(__name__)

class AgentOrchestrator:
    def __init__(self):
        # We try to initialize Groq first, then fallback to Gemini.
        self.groq_key = os.environ.get("GROQ_API_KEY", "")
        self.gemini_key = os.environ.get("GEMINI_API_KEY", "")
        
        if self.groq_key:
            from agno.models.groq import Groq
            self.model = Groq(id="llama-3.3-70b-versatile", api_key=self.groq_key)
        elif self.gemini_key:
            self.model = Gemini(id="gemini-1.5-flash", api_key=self.gemini_key)
        else:
            self.model = None
        
        self.formatting_agent = Agent(
            model=self.model,
            description="You are a professional Enterprise AI Assistant formatting responses in clean markdown.",
            instructions=[
                "Respond accurately using only the provided context.",
                "Use bullet points, bold terms, and headings where appropriate to make the answer enterprise-grade.",
                "If the user query is just a keyword or job title, summarize the available details from the context.",
                "If the context is empty, politely inform the user that you don't have that information."
            ]
        )
        
    def stream_response(self, context: Any, retrieved_context: str) -> Generator[Dict[str, Any], None, None]:
        """
        Takes the linear pipeline context, merges it, and streams the response token-by-token.
        """
        system_prompt = f"""
You are the final Enterprise AI Assistant. 
Here is the context retrieved from the enterprise knowledge base:
{retrieved_context}

User's exact query (resolved with conversation context): {context.normalized_message}
"""
        try:
            if not self.model:
                raise ValueError("No API keys available for external LLM models.")
                
            context.metadata["gemini_used"] = True
            context.metadata["fallback_used"] = False
            
            # Stream the response via Agno Agent
            run_response = self.formatting_agent.run(system_prompt, stream=True)
            
            for chunk in run_response:
                if chunk.content:
                    yield {"type": "stream", "chunk": chunk.content}
                    
        except Exception as e:
            logger.warning(f"FormattingAgent failed or unavailable: {e}. Falling back to local summarizer.")
            yield from self._fallback_stream(context, retrieved_context)

    def _fallback_stream(self, context: Any, retrieved_context: str) -> Generator[Dict[str, Any], None, None]:
        """
        Fallback formatter that uses AnswerCompressor to provide a readable response 
        without calling an external LLM.
        """
        from services.rag.answer_compressor import AnswerCompressor
        
        context.metadata["fallback_used"] = True
        context.metadata["gemini_used"] = False
        
        # We need to construct dummy chunk dicts since AnswerCompressor expects them
        dummy_chunks = [{"text": p} for p in retrieved_context.split("\n") if p.strip()]
        
        if not dummy_chunks:
            yield {"type": "stream", "chunk": "I'm sorry, I couldn't find any relevant information regarding your request."}
            return
            
        compression_result = AnswerCompressor.compress(context.original_message, dummy_chunks, max_sentences=6)
        sentences = compression_result["sentences"]
        
        if not sentences:
            yield {"type": "stream", "chunk": "I'm sorry, I couldn't find any relevant information regarding your request."}
            return
            
        intro = "📍 **Enterprise Knowledge (Fallback Mode)**\n\n"
        yield {"type": "stream", "chunk": intro}
        
        for s in sentences:
            yield {"type": "stream", "chunk": f"• {s}\n\n"}
