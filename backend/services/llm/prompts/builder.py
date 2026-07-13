from typing import Dict, Any, List

class PromptBuilder:
    @staticmethod
    def build(
        user_message: str, 
        system_instructions: str, 
        rag_context: str, 
        memory_facts: Dict[str, Any], 
        language: str = "en"
    ) -> str:
        
        memory_str = "\n".join([f"- {k}: {v}" for k, v in memory_facts.items()]) if memory_facts else "None"
        
        prompt = f"""
{system_instructions}

---
CONTEXT INFORMATION (RAG):
{rag_context if rag_context else 'None'}

---
CONVERSATION MEMORY:
{memory_str}

---
LANGUAGE: {language}

---
USER QUERY:
{user_message}

---
FORMAT REQUIREMENT:
You must reply ONLY with a valid JSON object matching this schema:
{{
  "response": "The text to show the user",
  "components": [],
  "actions": []
}}
"""
        return prompt.strip()
