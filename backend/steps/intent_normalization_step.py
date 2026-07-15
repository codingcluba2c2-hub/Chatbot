from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from services.intent_normalization_service import IntentNormalizationService

class IntentNormalizationStep(PipelineStep):
    def __init__(self):
        self.normalization_service = IntentNormalizationService()

    def process(self, context: PipelineContext) -> PipelineResult:
        original = context.original_message.strip()
        
        # Run normalization service
        result = self.normalization_service.process(original)
        
        # Extract variables
        normalized_query = result["normalized_query"]
        corrected_words = result["corrected_words"]
        detected_intent = result["detected_intent"]
        similarity_score = result["similarity_score"]
        matched_alias = result["matched_alias"]
        confidence_meets_threshold = result["confidence_meets_threshold"]
        
        # Apply logic based on confidence
        if confidence_meets_threshold and matched_alias:
            context.normalized_message = matched_alias
            if detected_intent:
                context.entities["normalized_intent"] = detected_intent
        else:
            context.normalized_message = normalized_query
            
        # Ensure we keep the numeric check from NormalizeStep just in case it's useful
        is_numeric = context.normalized_message.replace(" ", "").isdigit()
        context.is_numeric = is_numeric

        # Add developer trace metadata
        metadata = {
            "Original Query": original,
            "Normalized Query": normalized_query,
            "Corrected Words": corrected_words,
            "Detected Intent": detected_intent,
            "Similarity Score": similarity_score,
            "Matched Alias": matched_alias
        }
        context.metadata.update({"intent_normalization_trace": metadata})
        
        return PipelineResult(
            continue_pipeline=True,
            metadata=metadata
        )
