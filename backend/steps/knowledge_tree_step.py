# backend/steps/knowledge_tree_step.py
from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from utils.detectors import detect_knowledge_tree
from services.response_service import ResponseService
from core.constants import INTENT_KNOWLEDGE_TREE

class KnowledgeTreeStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineResult:
        is_matched, matched_node, conf, response_md, node_id = detect_knowledge_tree(context.normalized_message)
        
        if is_matched:
            context.entities["knowledge_node"] = matched_node
            
            final_response = ResponseService.get_sequential_response(
                context.session_id,
                f"knowledge_tree_{matched_node}",
                response_md
            )
            greeting_prefix = context.metadata.get("greeting_prefix", "")
            if greeting_prefix:
                final_response = f"{greeting_prefix}\n\n{final_response}"
                
            # Fetch nodes to build children and breadcrumbs
            from repositories.registry import knowledge_node_repo
            all_nodes = knowledge_node_repo.get_all(limit=1000)
            
            # Build Breadcrumb
            path = []
            current_id = node_id
            while current_id:
                current_node = next((n for n in all_nodes if n.id == current_id or n.title == current_id), None)
                if current_node:
                    path.insert(0, current_node.title)
                    current_id = getattr(current_node, "parent_id", None)
                    if not current_id or str(current_id).lower() == "none":
                        break
                else:
                    break
            
            if len(path) > 1:
                breadcrumb = " ➔ ".join(f"{p}" for p in path)
                final_response = f"📍 **{breadcrumb}**\n\n{final_response}"
                
            children = [n.title for n in all_nodes if (getattr(n, "parent_id", "") == node_id or getattr(n, "parent_id", "") == matched_node) and getattr(n, "status", "active") == "active" and n.title]
            
            components = []
            if children:
                components.append({
                    "type": "quickReplies",
                    "items": children
                })
                
            return PipelineResult(
                stop=True,
                intent=INTENT_KNOWLEDGE_TREE,
                response=final_response,
                components=components,
                metadata={
                    "matched_node": matched_node, 
                    "confidence": conf, 
                    "node_id": node_id,
                    "topic": matched_node,
                    "knowledge_node": matched_node
                }
            )
            
        return PipelineResult(continue_pipeline=True)
