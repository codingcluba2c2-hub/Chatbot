from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from rapidfuzz import process, fuzz

class SpellCorrectionStep(PipelineStep):
    def __init__(self):
        super().__init__()
        self.dictionary = [
            "company", "leave", "holiday", "salary", "attendance", "contact", 
            "owner", "mission", "vision", "technology", "react", "vite", 
            "mongodb", "postgres", "frontend", "backend", "location", "address", 
            "email", "phone", "services", "projects", "career", "jobs", "policy", 
            "hr", "founder", "framework", "working", "hours", "total", "mobiloitte"
        ]
        
    def process(self, context: PipelineContext) -> PipelineResult:
        words = context.normalized_message.split()
        corrected_words = []
        corrections_made = 0
        
        for word in words:
            # We only correct words that are alphabetical and at least 4 characters
            if word.isalpha() and len(word) >= 4:
                # Find the best match in the dictionary
                result = process.extractOne(word.lower(), self.dictionary, scorer=fuzz.ratio)
                if result:
                    match, score, index = result
                    if score >= 80 and word.lower() != match:
                        # Keep original casing if possible (simplified here)
                        corrected_words.append(match)
                        corrections_made += 1
                        continue
            
            corrected_words.append(word)
            
        if corrections_made > 0:
            new_message = " ".join(corrected_words)
            context.metadata["spell_correction"] = {
                "original": context.normalized_message,
                "corrected": new_message,
                "corrections_count": corrections_made
            }
            context.normalized_message = new_message
            
        return PipelineResult(continue_pipeline=True)
