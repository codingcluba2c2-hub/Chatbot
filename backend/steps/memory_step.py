# backend/steps/memory_step.py
from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from services.fact_extraction_service import FactExtractionService
from services.entity_extraction_service import EntityExtractionService
from services.memory_lookup_service import MemoryLookupService
import time

class MemoryStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineResult:
        # Extract and store facts and entities
        t0 = time.perf_counter()
        facts = FactExtractionService.extract_and_store(context.session_id, context.original_message)
        entities = EntityExtractionService.extract_and_store(context.session_id, context.original_message)
        extraction_time = (time.perf_counter() - t0) * 1000
        
        # Check if the user is asking about a known fact
        t0 = time.perf_counter()
        is_found, matched_key, memory_response = MemoryLookupService.check_memory(context.session_id, context.original_message)
        lookup_time = (time.perf_counter() - t0) * 1000
        
        metadata = {
            "Memory Lookup": True,
            "Found": is_found,
            "Matched Key": matched_key if matched_key else "None",
            "Execution Time": f"{round(lookup_time, 3)}ms",
            "Result": "Memory Response Generated" if is_found else "No Memory Found",
            "Facts Extracted": facts,
            "Entities Extracted": entities
        }
        
        if is_found:
            return PipelineResult(
                stop=True,
                intent="MemoryLookup",
                response=memory_response,
                metadata=metadata
            )
            
        return PipelineResult(
            continue_pipeline=True,
            metadata=metadata
        )
