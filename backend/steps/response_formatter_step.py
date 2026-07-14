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
                    
        # Question type formatting
        query_lower = context.normalized_message.lower()
        formatted_output = ""
        
        if "leave policy" in query_lower or "leaves" in query_lower or "list" in query_lower:
            formatted_output = "Here is the information requested:\n"
            for sent in ordered_sentences[:5]:
                formatted_output += f"- {sent}\n"
                
        elif "hour" in query_lower or "time" in query_lower:
            formatted_output = "Working Hours:\n"
            for sent in ordered_sentences[:3]:
                if "am" in sent.lower() or "pm" in sent.lower() or "hour" in sent.lower():
                    formatted_output += f"{sent}\n"
            if formatted_output == "Working Hours:\n":
                formatted_output += ordered_sentences[0] if ordered_sentences else ""
                
        elif "address" in query_lower or "location" in query_lower:
            address_lines = [s for s in ordered_sentences if any(k in s.lower() for k in ["address", "street", "city", "country", "pin", "code"])]
            if address_lines:
                formatted_output = "Address:\n" + "\n".join(address_lines[:2])
            else:
                formatted_output = ordered_sentences[0] if ordered_sentences else ""
                
        elif "email" in query_lower or "contact" in query_lower:
            email_lines = [s for s in ordered_sentences if "@" in s or "contact" in s.lower()]
            if email_lines:
                formatted_output = "Contact Information:\n" + "\n".join(email_lines[:3])
            else:
                formatted_output = ordered_sentences[0] if ordered_sentences else ""
                
        else:
            # Fact / General
            formatted_output = " ".join(ordered_sentences[:3]) # Limit to 3 sentences for conciseness
            
        if not formatted_output.strip():
            formatted_output = "I don't have enough information regarding this topic."
            
        context.metadata["formatted_rag_response"] = formatted_output.strip()
        context.metadata["response_formatter_used"] = True
        
        return PipelineResult(continue_pipeline=True)
