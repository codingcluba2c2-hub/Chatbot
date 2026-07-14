# backend/steps/conversation_opener_step.py
import re
from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from services.response_service import ResponseService
from core.constants import INTENT_GREETING

class ConversationOpenerStep(PipelineStep):
    def __init__(self):
        # We define a list of common opener tokens. Order by length descending to match longest first if needed.
        self.openers = [
            "good morning", "good evening", "good afternoon",
            "hello", "namaste", "salam", "hey", "hi"
        ]

    def _get_base_opener(self, matched_text: str) -> str:
        matched_text = matched_text.lower()
        if matched_text.startswith('h'):
            if 'e' in matched_text and 'l' in matched_text:
                return 'Hello'
            elif 'e' in matched_text and 'y' in matched_text:
                return 'Hey'
            elif 'i' in matched_text:
                return 'Hi'
        elif matched_text.startswith('n'):
            return 'Namaste'
        elif matched_text.startswith('s'):
            return 'Salam'
        elif matched_text.startswith('g'):
            if 'm' in matched_text:
                return 'Good morning'
            elif 'e' in matched_text:
                return 'Good evening'
            elif 'a' in matched_text:
                return 'Good afternoon'
        return 'Hello'

    def process(self, context: PipelineContext) -> PipelineResult:
        text = context.normalized_message.strip()
        
        # Regex to detect common greetings, including repeated characters (e.g. hiiii, helloooo)
        pattern = re.compile(
            r'\b(h+i+|h+e+l+o+|h+e+y+|n+a+m+a+s+t+e+|s+a+l+a+m+|g+o+o+d+\s+m+o+r+n+i+n+g+|g+o+o+d+\s+e+v+e+n+i+n+g+|g+o+o+d+\s+a+f+t+e+r+n+o+o+n+)\b',
            re.IGNORECASE
        )
        
        match = pattern.search(text)
        
        if match:
            detected_raw = match.group(1)
            base_opener = self._get_base_opener(detected_raw)
            
            context.metadata["greeting_detected"] = True
            context.metadata["greeting_token"] = detected_raw
            
            # Determine prefix format
            prefix = base_opener
            if prefix in ["Hi", "Hello", "Hey", "Namaste", "Salam"]:
                prefix += "!"
            else:
                prefix += "!" # e.g., Good morning!
                
            context.metadata["greeting_prefix"] = prefix
            
            # Remove the detected greeting from the text
            remaining_query = pattern.sub('', text, count=1).strip()
            
            context.metadata["remaining_query"] = remaining_query
            
            if not remaining_query:
                # The user just said "hello"
                final_response = ResponseService.get_sequential_response(
                    context.session_id, 
                    f"greeting_{base_opener.lower()}", 
                    f"{prefix} How can I assist you today?"
                )
                
                context.metadata["routing"] = "Greeting (Empty remaining query)"
                
                return PipelineResult(
                    stop=True,
                    intent=INTENT_GREETING,
                    response=final_response
                )
            else:
                # The user said something like "hi company name" or "dfhkdjf hi kldjfd"
                context.normalized_message = remaining_query
                context.metadata["routing"] = "Greeting + Multi-Intent"
                
                # We continue the pipeline
                return PipelineResult(continue_pipeline=True)
                
        else:
            context.metadata["greeting_detected"] = False
            
        return PipelineResult(continue_pipeline=True)
