# backend/steps/meaningful_validator_step.py
from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult

class MeaningfulValidatorStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineResult:
        if context.is_numeric:
            context.metadata["is_meaningful"] = False
            context.metadata["meaningful_score"] = "0.0%"
            context.metadata["dictionary_match"] = "0.0%"
            context.metadata["validation_reason"] = "numeric_only"
            context.metadata["business_keyword_match"] = "NO"
            return PipelineResult(continue_pipeline=True)
            
        from utils.detectors import validate_query
        
        validation = validate_query(context.normalized_message)
        
        # Attach routing decisions for developer mode
        context.metadata["meaningful_score"] = f"{validation['metrics']['meaningful_score']}%"
        context.metadata["dictionary_match"] = f"{validation['metrics']['dictionary_match']}%"
        context.metadata["is_meaningful"] = validation["isMeaningful"]
        context.metadata["validation_reason"] = validation["reason"]
        
        if "Business Keyword" in validation["reason"]:
            context.metadata["business_keyword_match"] = "YES"
        else:
            context.metadata["business_keyword_match"] = "NO"
        
        return PipelineResult(continue_pipeline=True)
