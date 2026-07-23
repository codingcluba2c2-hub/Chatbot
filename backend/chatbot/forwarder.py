import urllib.request
import urllib.parse
import json
import logging
from typing import Any
from chatbot.pipeline import PipelineStep, PipelineContext, PipelineResult

logger = logging.getLogger(__name__)

class AIEngineForwarderStep(PipelineStep):
    """
    Forwards RAG requests to the EnterpriseAIEngine running on port 8002.
    Uses standard library urllib to avoid heavy dependencies like httpx.
    """
    def process(self, context: PipelineContext) -> PipelineResult:
        url = f"{os.getenv('AI_ENGINE_URL', 'http://127.0.0.1:8002')}/rag"
        data = {
            "query": context.normalized_message or context.original_message,
            "metadata": dict(context.metadata)
        }
        
        req = urllib.request.Request(
            url, 
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result_json = json.loads(response.read().decode('utf-8'))
                
                context.metadata["rag_chunks"] = result_json.get("chunks", [])
                
                return PipelineResult(
                    stop=True,
                    intent=result_json.get("intent", "RAG"),
                    response=result_json.get("response", "AI Engine Error"),
                    metadata={"forwarder_status": "success"}
                )
        except Exception as e:
            logger.error(f"[AI ENGINE FAILURE] Technical error during forwarder execution: {e}")
            
            fallback_msg = "I couldn't find information related to your question in the current enterprise knowledge base."
            
            return PipelineResult(
                stop=True,
                intent="Fallback",
                response=fallback_msg,
                components=[{
                    "type": "fallback",
                    "prefix": "I couldn't find information related to",
                    "query": context.original_message,
                    "suffix": "in the current enterprise knowledge base. Please try asking about one of the topics below.",
                    "suggestions": ["Company Information", "Office Timings", "Leave Policy", "Contact", "Services", "Careers", "Employees"]
                }],
                metadata={"forwarder_status": "error_handled"}
            )
