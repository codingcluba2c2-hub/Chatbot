import os
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any, List

app = FastAPI(title="Enterprise AI Engine")

class RAGRequest(BaseModel):
    query: str
    metadata: Dict[str, Any]

class RAGResponse(BaseModel):
    response: str
    chunks: List[Dict[str, Any]]
    intent: str

@app.on_event("startup")
async def load_models():
    print("Loading AI Models (Gemini)...")
    from chatbot.llm import initialize_llm_provider
    try:
        initialize_llm_provider()
    except Exception as e:
        print(f"LLM init warning: {e}")
    print("AI Models Loaded. Engine Ready on port 8002.")

@app.post("/rag", response_model=RAGResponse)
async def generate_rag_response(req: RAGRequest):
    from chatbot.llm import get_llm_provider
    provider = get_llm_provider()
    
    rag_context = req.metadata.get("rag_context", "")
    
    system_prompt = (
        "You are an enterprise knowledge assistant.\n"
        "Answer ONLY using the provided context. Your goal is to make the answer readable, professional and conversational.\n"
        "Generate rich, structured responses using Markdown formatting. Use headings (#, ##), bold (**), bullet lists (•), numbered lists, and short paragraphs.\n"
        "Do not expose metadata, chunk IDs, similarity scores, or payload fields.\n"
        "Convert the retrieved information into a well-formatted markdown response. Preserve headings, lists, and hierarchy when available in the context.\n"
        "Do NOT invent headings or create fake sections. If the chunk contains a single paragraph, return a single paragraph.\n"
        "Never merge everything into one paragraph. Keep paragraph separation.\n"
        "Never invent information. Do not hallucinate. Do not use external knowledge.\n"
        "Do not remove important information or aggressively summarize. Preserve useful details.\n"
        "Choose response length dynamically: small question -> short answer (2-4 lines), broad question -> comprehensive response (150-300 words).\n"
        "If the user asks about a specific topic (e.g., 'What is salary?'), return ONLY that information. Do not include unrelated info.\n"
        "If the user asks a broad topic (e.g., 'Tell me about Product Designer'), return a full overview (Overview, Skills, Experience, Education, Salary) if present.\n"
        "The context may contain noisy text from PDFs. Ignore noise and extract ONLY what matches the query.\n"
        "Only say you couldn't find the information if the query is TRULY not mentioned anywhere."
    )
    
    prompt = f"User Query: {req.query}\n\nContext:\n{rag_context}\n\nPlease provide a helpful, richly formatted markdown response based ONLY on the context."
    config = {
        "system_prompt": system_prompt,
        "temperature": 0.2
    }
    
    try:
        result = provider.generate(prompt, config)
        import json
        try:
            res_data = json.loads(result.text)
            final_response = res_data.get("response", result.text)
        except:
            final_response = result.text
            
        return RAGResponse(
            response=final_response,
            chunks=[],
            intent="Knowledge"
        )
    except Exception as e:
        print(f"LLM Generation Error: {e}")
        return RAGResponse(
            response=rag_context, # Fallback to context
            chunks=[],
            intent="Knowledge"
        )

if __name__ == "__main__":
    uvicorn.run("ai_engine:app", host="0.0.0.0", port=8002, reload=False)
