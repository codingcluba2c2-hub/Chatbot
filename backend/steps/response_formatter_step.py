import re
from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult

class ResponseFormatterStep(PipelineStep):
    def __init__(self):
        pass
        
    def process(self, context: PipelineContext) -> PipelineResult:
        if context.current_intent != "Knowledge":
            return PipelineResult(continue_pipeline=True)
            
        chunks = context.metadata.get("rag_chunks", [])
        if not chunks:
            return PipelineResult(continue_pipeline=True)
            
        # Extract and clean text
        unique_sentences = set()
        ordered_sentences = []
        
        for chunk in chunks:
            text = chunk.get("text", "")
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            for line in lines:
                line_lower = line.lower()
                
                # Remove artifacts
                if re.match(r'^page\s+\d+$', line_lower) or re.match(r'^pg\.?\s+\d+$', line_lower):
                    continue
                if re.match(r'^chunk\s+#?\d+$', line_lower):
                    continue
                if line_lower.startswith('source:') or line_lower.startswith('document:'):
                    continue
                if 'confidential' in line_lower:
                    continue
                    
                clean_line = re.sub(r'\s+', ' ', line)
                
                if clean_line not in unique_sentences and len(clean_line) > 10:
                    unique_sentences.add(clean_line)
                    ordered_sentences.append(clean_line)
                    
        # Extractive Summarization Algorithm
        query_words = set([w for w in context.normalized_message.lower().split() if len(w) > 3 and w not in ["what", "when", "where", "how", "who", "why", "the", "and", "for", "that"]])
        if not query_words:
            # Fallback if no substantial query words, use first few sentences
            query_words = set(context.normalized_message.lower().split())

        selected_sentences = []
        for i, sent in enumerate(ordered_sentences):
            sent_lower = sent.lower()
            if any(qw in sent_lower for qw in query_words):
                # Add surrounding sentences (1 before, 1 after)
                if i > 0:
                    selected_sentences.append(ordered_sentences[i-1])
                selected_sentences.append(sent)
                if i < len(ordered_sentences) - 1:
                    selected_sentences.append(ordered_sentences[i+1])
                    
        # Remove duplicates while preserving order
        final_sentences = []
        for s in selected_sentences:
            if s not in final_sentences:
                final_sentences.append(s)
                
        # If no keywords matched, just take the first 3 lines
        if not final_sentences:
            final_sentences = ordered_sentences[:3]
            
        # Maximum 5 lines
        final_sentences = final_sentences[:5]
        
        # Format output
        formatted_output = ""
        for s in final_sentences:
            # Format list items nicely if they look like bullet points
            if "leave:" in s.lower() or "days" in s.lower():
                formatted_output += f"{s}\n\n"
            else:
                formatted_output += f"{s}\n"
                
        if not formatted_output.strip():
            formatted_output = "I don't have enough information regarding this topic."
            
        context.metadata["formatted_rag_response"] = formatted_output.strip()
        context.metadata["Summary Mode"] = True
        context.metadata["response_formatter_used"] = True
        
        return PipelineResult(continue_pipeline=True)
