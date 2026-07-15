import re
from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult

class ConversationIntelligenceStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineResult:
        query = context.normalized_message.lower()
        
        # 1. BOT IDENTITY
        identity_patterns = [
            r'who are you', r'what is your name', r'tell me your name', 
            r'what\'s your name', r'your identity'
        ]
        if any(re.search(p, query) for p in identity_patterns):
            pref_name = context.metadata.get("memory", {}).get("preferred_assistant_name")
            if pref_name:
                response = f"I am {pref_name},\nyour Mobiloitte AI Assistant."
            else:
                response = "I am Mobiloitte AI Assistant."
                
            return PipelineResult(
                stop=True,
                intent="LOOKUP_ASSISTANT_NAME",
                response=response,
                metadata={"Conversation Intelligence": True, "Assistant Name": pref_name or "Mobiloitte AI Assistant"}
            )
            
        # 2. BOT NAME UPDATE
        bot_name_patterns = [
            r'call yourself ([a-z\s]+)', r'i call you ([a-z\s]+)', r'your name is ([a-z\s]+)', 
            r'change your name to ([a-z\s]+)', r'i prefer your name ([a-z\s]+)', 
            r'from today your name is ([a-z\s]+)', r'remember your name ([a-z\s]+)'
        ]
        for p in bot_name_patterns:
            match = re.search(p + r'$', query)
            if match:
                new_name = match.group(1).strip().title()
                actions = [{
                    "type": "UPDATE_MEMORY",
                    "payload": {
                        "preferred_assistant_name": new_name
                    }
                }]
                return PipelineResult(
                    stop=True,
                    intent="UPDATE_ASSISTANT_NAME",
                    response=f"Sure!\nFrom now on you can call me {new_name}.",
                    actions=actions,
                    metadata={"Conversation Intelligence": True, "Memory Updated": True, "Assistant Name": new_name}
                )

        # 3. MEMORY LOOKUP
        lookup_patterns = [
            r'what is my name', r'who am i'
        ]
        if any(re.search(p, query) for p in lookup_patterns):
            user_name = context.metadata.get("memory", {}).get("user_name")
            if user_name:
                response = f"Your name is {user_name}."
            else:
                response = "I don't know your name yet."
            
            return PipelineResult(
                stop=True,
                intent="LOOKUP_USER_NAME",
                response=response,
                metadata={"Conversation Intelligence": True, "User Name": user_name or "Unknown"}
            )
            
        # 4. UPDATE MEMORY (User Name)
        user_name_patterns = [
            r'change my name to ([a-z\s]+)', r'update my name to ([a-z\s]+)', 
            r'actually my name is ([a-z\s]+)', r'correct my name ([a-z\s]+)', 
            r'replace previous name with ([a-z\s]+)', r'modify stored name to ([a-z\s]+)'
        ]
        personal_patterns = [
            r'\bmy name is ([a-z\s]+)', r'\bi\'m ([a-z\s]+)', r'\bi am ([a-z\s]+)', 
            r'\bcall me ([a-z\s]+)', r'\byou can call me ([a-z\s]+)', 
            r'\bremember my name is ([a-z\s]+)', r'\bmy nickname is ([a-z\s]+)', 
            r'\bpreferred name is ([a-z\s]+)'
        ]
        
        all_name_patterns = user_name_patterns + personal_patterns
        # List of generic words to avoid capturing (e.g. "I am looking for...")
        ignore_words = ["looking", "trying", "searching", "wondering", "working", "going", "not sure"]
        
        for p in all_name_patterns:
            match = re.search(p + r'$', query)
            if match:
                new_name = match.group(1).strip().title()
                if any(w in new_name.lower() for w in ignore_words):
                    continue
                
                actions = [{
                    "type": "UPDATE_MEMORY",
                    "payload": {
                        "user_name": new_name
                    }
                }]
                
                is_greeting = "hello" in query or "hi" in query or "good morning" in query
                if is_greeting:
                    response = f"Hi {new_name}!\nNice to meet you."
                else:
                    response = f"Done.\nI'll remember your name is {new_name}."
                    
                return PipelineResult(
                    stop=True,
                    intent="UPDATE_USER_NAME",
                    response=response,
                    actions=actions,
                    metadata={"Conversation Intelligence": True, "Memory Updated": True, "User Name": new_name}
                )

        return PipelineResult(continue_pipeline=True)
