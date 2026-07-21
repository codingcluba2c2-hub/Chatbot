import time
from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from services.llm import get_llm_provider
from services.rag.local_response_generator import LocalResponseGenerator
from core.logger import get_logger

logger = get_logger(__name__)

class ResponseGeneratorStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineResult:
        if getattr(self, 'stop', False):
            return PipelineResult(continue_pipeline=False)
            
        t0 = time.perf_counter()
        
        # Determine if we should generate a response
        decision = context.metadata.get("knowledge_search_decision", "SKIPPED")
        if decision.startswith("REJECTED") or decision == "SKIPPED (Gibberish)":
            t1 = time.perf_counter()
            context.metadata["llm_latency_ms"] = int((t1 - t0) * 1000)
            context.metadata["fallback_used"] = True
            context.metadata["gemini_used"] = False
            
            context.current_intent = "Fallback"
            
            # Sub-ms deterministic suggestion engine
            text_lower = context.normalized_message.lower()
            suggestions = []
            
            if "salary" in text_lower or "pay" in text_lower or "hr" in text_lower or "leave" in text_lower:
                suggestions = ["Leave Policy", "Attendance", "HR Contact", "Employee Benefits"]
            elif "tech" in text_lower or "software" in text_lower or "react" in text_lower or "node" in text_lower:
                suggestions = ["AI Services", "React", "Node.js", "Cloud", "Projects"]
            elif "company" in text_lower or "about" in text_lower or "founder" in text_lower:
                suggestions = ["Founder", "Mission", "Vision", "Services", "Contact", "company about"]
            else:
                suggestions = ["Overview", "Office Timings", "Leave Policy", "Contact", "Services", "Career", "Help"]
                
            from components.factory import ComponentBuilder
            fallback_component = ComponentBuilder.fallback(context.normalized_message, suggestions)
            
            # Keep string response empty, let frontend render the component
            final_response = ""
            
            # Developer mode metrics
            context.metadata["fallback_trigger"] = decision
            context.metadata["suggestions_generated"] = len(suggestions)
            context.metadata["response_source"] = "Fallback"
                
            return PipelineResult(
                continue_pipeline=False,
                stop=True,
                intent="Fallback",
                response=final_response,
                components=[fallback_component]
            )
            
        # We have chunks, let's filter and compress them first!
        rag_context = context.metadata.get("rag_context", "")
        chunks = context.metadata.get("rag_chunks", [])
        
        from services.rag.answer_compressor import AnswerCompressor
        compression_result = AnswerCompressor.compress(context.normalized_message, chunks, max_sentences=6)
        filtered_sentences = compression_result["sentences"]
        metrics = compression_result["metrics"]
        
        # Override the rag_context with ONLY the highly relevant filtered sentences
        filtered_context = "\n".join(filtered_sentences)
        context.metadata["compression_ratio"] = f"{metrics['compressed_length']} / {metrics['original_length']} chars"
        context.metadata["sentences_kept"] = f"{metrics['kept_sentences']} / {metrics['total_sentences']}"
        
        provider = get_llm_provider()
        gemini_success = False
        final_response = ""
        final_intent = ""
        
        if provider:
            system_prompt = (
                "You are Mobiloitte's Enterprise AI Assistant. "
                "CRITICAL INSTRUCTION: Answer the user's query using ONLY the provided filtered sentences below. "
                "Do NOT use any outside knowledge, assumptions, or external internet data under any circumstances. "
                "If the exact answer is not explicitly written in the provided sentences, you MUST say 'I couldn't find enough relevant information in the knowledge base to answer that.' "
                "If the user's query is just a keyword or job title (like 'Product Designer'), summarize the available details (e.g., Role, Salary, Experience) about it from the context. "
                "FORMATTING RULES:\n"
                "- If Location/Address, format as: 📍 Address\\n[address]\n"
                "- If Phone, format as: 📞 Phone\\n[phone]\n"
                "- If Working Hours, format as: 🕒 Working Hours\\n[hours]\n"
                "- If Leave Policy, format as: 🏖 Leave Policy\\n[policy]\n"
                "- If Founder/Person, format as: 👤 Founder\\n[name]\n"
                "- Use clean bullet points for lists. Never dump long paragraphs."
            )
            
            try:
                prompt = f"User Question: {context.normalized_message}\n\nContext Data:\n{filtered_context}"
                config = {
                    "system_prompt": system_prompt,
                    "temperature": 0.2
                }
                
                result = provider.generate(prompt, config)
                
                import json
                try:
                    res_data = json.loads(result.text)
                    final_response = res_data.get("response", result.text)
                except:
                    final_response = result.text
                final_intent = "Knowledge"
                gemini_success = True
                
                context.metadata["gemini_used"] = True
                context.metadata["fallback_used"] = False
                
            except Exception as e:
                logger.error(f"Gemini generation failed: {e}. Switching to Local Response Generator.")
                gemini_success = False
                
        # If Gemini failed (e.g. 429 quota, timeout), use local fallback
        if not gemini_success:
            logger.info("Using LocalResponseGenerator fallback.")
            local_gen = LocalResponseGenerator()
            local_res = local_gen.generate(context.normalized_message, chunks)
            final_response = local_res["response"]
            final_intent = "Knowledge (Fallback)"
            
            context.metadata["gemini_used"] = False
            context.metadata["fallback_used"] = True
            context.metadata["response_formatter_used"] = True
            if "metadata" in local_res:
                context.metadata.update(local_res["metadata"])
            
        t1 = time.perf_counter()
        context.metadata["llm_latency_ms"] = int((t1 - t0) * 1000)
        context.current_intent = final_intent
        
        # If the LLM explicitly states it couldn't find the answer in the chunks, convert it to a structured fallback!
        if "couldn't find enough relevant information" in final_response.lower() or "do not know" in final_response.lower():
            text_lower = context.normalized_message.lower()
            suggestions = []
            if "salary" in text_lower or "pay" in text_lower or "hr" in text_lower or "leave" in text_lower:
                suggestions = ["Leave Policy", "Attendance", "HR Contact", "Employee Benefits"]
            elif "tech" in text_lower or "software" in text_lower or "react" in text_lower or "node" in text_lower:
                suggestions = ["AI Services", "React", "Node.js", "Cloud", "Projects"]
            elif "company" in text_lower or "about" in text_lower or "founder" in text_lower:
                suggestions = ["Founder", "Mission", "Vision", "Services", "Contact"]
            else:
                suggestions = ["Overview", "Office Timings", "Leave Policy", "Contact", "Services", "Career", "Help"]
                
            from components.factory import ComponentBuilder
            fallback_component = ComponentBuilder.fallback(context.normalized_message, suggestions)
            
            context.metadata["fallback_used"] = True
            context.metadata["response_source"] = "LLM Rejected (Fallback Triggered)"
            
            return PipelineResult(
                continue_pipeline=False,
                stop=True,
                intent="Fallback",
                response="",
                components=[fallback_component]
            )
        
        # Prepend greeting if present
        greeting_prefix = context.metadata.get("greeting_prefix", "")
        if greeting_prefix:
            final_response = f"{greeting_prefix}\n\n{final_response}"
            
        return PipelineResult(
            continue_pipeline=False,
            stop=True,
            intent=final_intent,
            response=final_response
        )
