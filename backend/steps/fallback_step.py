import re
from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from repositories.registry import fastpath_repo, faq_repo

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
        
        fallback_msg = f"""I couldn't find information about
"{context.original_message}" in the current knowledge base.

You may try one of these instead:"""

        # Generate suggestions dynamically or use defaults requested by user
        default_topics = [
            "Office Timings", 
            "Career", 
            "Our Services", 
            "Contact Us", 
            "Company About", 
            "Projects Completed"
        ]
        
        # We can still add fastpaths/faqs if we want, but user requested these specifically.
        # Let's just use the exact 6 requested to make a perfect 2x3 grid.
        suggestions = default_topics

        components = [
            {
                "type": "quickReplies",
                "items": suggestions
            }
        ]

        return PipelineResult(
            stop=True,
            intent="Fallback",
            response=fallback_msg,
            components=components,
            metadata={
                "reason": "No Relevant Chunks", 
                "topic": topic,
                "Suggestions Generated": len(suggestions),
                "Suggestion Source": "FastPath + FAQ + Knowledge Base"
            }
        )
