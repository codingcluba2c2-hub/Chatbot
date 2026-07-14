import re
from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult

def extract_topic(message: str) -> str:
    cleaned = re.sub(r'[^\w\s\']', '', message).strip()
    stop_words = {"who", "what", "where", "when", "why", "how", "is", "are", "was", "were", "do", "does", "did", "can", "could", "would", "should", "tell", "me", "about", "give", "information", "on", "the", "a", "an", "of", "in", "to", "for", "with", "show"}
    words = cleaned.split()
    filtered = [w for w in words if w.lower() not in stop_words]
    
    if not filtered:
        topic = cleaned
    else:
        topic = " ".join(filtered[:5])
        
    return topic.title()

class FallbackStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineResult:
        if not context.metadata.get("is_meaningful", True):
            return PipelineResult(continue_pipeline=True)
            
        topic = extract_topic(context.original_message)
        
        fallback_msg = f"""⚠️ **Information Not Available**

I couldn't find any information related to **"{topic}"** in my current enterprise knowledge base.

This assistant is designed to answer questions related to Mobiloitte's enterprise services and enterprise business knowledge.

Please ask me questions related to:
• Enterprise AI Systems
• AI Agents
• RAG Solutions
• Blockchain Platforms
• Enterprise Software Development
• Cloud Infrastructure
• Cybersecurity
• Digital Transformation

You may also try one of the suggested topics below."""

        components = [
            {
                "type": "quickReplies",
                "items": ["Enterprise AI Services", "RAG Architecture", "Blockchain Solutions", "Cloud Infrastructure", "Digital Transformation", "Contact Mobiloitte"]
            }
        ]

        return PipelineResult(
            stop=True,
            intent="Fallback",
            response=fallback_msg,
            components=components,
            metadata={"reason": "No match found in FastPath, FAQ, or Knowledge Base", "topic": topic}
        )
