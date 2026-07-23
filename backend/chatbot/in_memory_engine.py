import re
from typing import Dict, List, Tuple, Any, Optional
from core.logger import get_logger

logger = get_logger("in_memory_engine")

class InMemoryEngine:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(InMemoryEngine, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        if self._initialized:
            return
            
        self.is_loaded = False
        
        # Greetings
        self.greeting_phrases: List[Tuple[str, str, str]] = []
        
        # FAQs
        self.faq_exact_map: Dict[str, Tuple[str, Any]] = {}
        self.faq_rapidfuzz_choices: List[str] = []
        self.faq_children_map: Dict[str, List[Any]] = {}
        
        # Aliases
        self.alias_map: Dict[str, str] = {}
        self.all_aliases: List[str] = []
        self.spelling_dict: Dict[str, str] = {}
        
        # Compiled Regex
        self.compiled_regex: Dict[str, re.Pattern] = {}
        
        # Gibberish Engine 
        self.english_dictionary: set = set()
        self.false_positive_allowlist: set = set()
        
        self._initialized = True

    def load_all(self):
        logger.info("Loading deterministic data into RAM...")
        from core.database import greeting_repo, faq_repo
        
        self.english_dictionary.clear()
        self.false_positive_allowlist.clear()
        
        # 1. Load Greetings
        try:
            greetings = greeting_repo.get_all(limit=1000)
            phrases = []
            for g in greetings:
                if getattr(g, "enabled", True):
                    name = getattr(g, "name", "")
                    if name:
                        phrases.append((name.lower(), name, getattr(g, "response", "")))
                    for alias in getattr(g, "alias", []):
                        if alias:
                            phrases.append((alias.lower(), alias, getattr(g, "response", "")))
            phrases.sort(key=lambda x: len(x[0]), reverse=True)
            self.greeting_phrases = phrases
        except Exception as e:
            logger.error(f"Error loading greetings: {e}")

        # 2. Load FAQs
        try:
            faqs = faq_repo.get_all(limit=5000)
            exact_map = {}
            choices = []
            children_map = {}
            
            # Map children
            for f in faqs:
                if getattr(f, "status", "active") == "active":
                    parent_id = getattr(f, "parent_id", None)
                    if parent_id:
                        if parent_id not in children_map:
                            children_map[parent_id] = []
                        children_map[parent_id].append(f)
                        
            # Sort children
            for pid in children_map:
                children_map[pid].sort(key=lambda x: getattr(x, "created_at", 0))
            self.faq_children_map = children_map

            # Map titles & aliases
            for f in faqs:
                if getattr(f, "status", "active") == "active":
                    q = getattr(f, "title", "")
                    if q:
                        ql = q.lower()
                        if ql not in exact_map:
                            exact_map[ql] = (q, f)
                        choices.append(ql)
                        # Dynamically add to dictionary
                        for w in ql.split():
                            w_clean = re.sub(r'[^a-z]', '', w)
                            if w_clean:
                                self.english_dictionary.add(w_clean)
                                
                    for alias in getattr(f, "aliases", []):
                        if alias:
                            al = alias.lower()
                            if al not in exact_map:
                                exact_map[al] = (alias, f)
                            choices.append(al)
                            # Dynamically add to dictionary
                            for w in al.split():
                                w_clean = re.sub(r'[^a-z]', '', w)
                                if w_clean:
                                    self.english_dictionary.add(w_clean)
            
            self.faq_exact_map = exact_map
            self.faq_rapidfuzz_choices = sorted(list(set(choices)), key=len, reverse=True)
        except Exception as e:
            logger.error(f"Error loading FAQs: {e}")
            
        # 3. Load Aliases and Spelling
        self.spelling_dict = {
            "comapny": "company", "copmany": "company", "compnay": "company",
            "mision": "mission", "misison": "mission", "misson": "mission",
            "frondend": "frontend", "fronted": "frontend", "front end": "frontend",
            "back end": "backend", "bakend": "backend",
            "leavs": "leave", "leve": "leave", "horus": "hours",
            "contcat": "contact", "rajanarayn": "rajnarayan",
            "managerr": "manager", "tell me about yourself": "who are you"
        }
        
        intents = {
            "COMPANY_INFORMATION": [
                "company", "company name", "company details", "about company",
                "company information", "organization", "firm", "enterprise", "corporate profile"
            ],
            "COMPANY_MISSION": [
                "mission", "vision", "goal", "objective", "purpose",
                "company mission", "company vision", "corporate mission"
            ],
            "CONTACT_INFORMATION": [
                "contact", "phone", "email", "support", "hr contact",
                "sales contact", "reach company", "mobile", "reach us"
            ],
            "WORKING_HOURS": [
                "timing", "office timing", "working hours", "office hours",
                "shift timing", "business hours"
            ],
            "LEAVE_POLICY": [
                "leave", "holiday", "earned leave", "casual leave",
                "leave policy", "vacation", "time off"
            ],
            "SERVICES": [
                "services", "offerings", "products", "solutions", "what do you do"
            ],
            "TECHNOLOGY": [
                "tech stack", "technology", "framework", "backend", "frontend",
                "react", "vite", "node"
            ]
        }
        
        alias_map = {}
        all_aliases = []
        for intent, aliases in intents.items():
            for alias in aliases:
                alias_map[alias] = intent
                all_aliases.append(alias)
        self.alias_map = alias_map
        self.all_aliases = all_aliases
        
        # 4. Gibberish Engine Setup
        self.false_positive_allowlist.update({
            "api", "sql", "python", "react", "nodejs", "mobiloitte", "openai", "chatgpt", "gpt", 
            "bca", "mern", "iot", "ai", "blockchain", "rag", "llm", "fastapi", "next.js"
        })
        self.english_dictionary.update({
            "hello", "hi", "hey", "good", "morning", "afternoon", "evening", "night", "thanks", "thank",
            "you", "company", "name", "leave", "policy", "contact", "salary", "what", "is", "who", "ceo",
            "our", "services", "cloud", "blockchain", "mobiloitte", "openai", "where", "how", "why", "when",
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "about"
        })
        
        # 5. Scope Detector Setup
        self.scope_keywords = {
            "company", "services", "products", "careers", "employees", "office",
            "policies", "departments", "contact", "technology", "projects", "training",
            "documents", "leave", "timing", "hr", "it", "salary", "vision", "mission", "ceo"
        }
        
        # Merge scope keywords into allowlist and dictionary so they are never flagged as gibberish
        self.false_positive_allowlist.update(self.scope_keywords)
        self.english_dictionary.update(self.scope_keywords)
        
        # 6. Pre-compile Regex
        self.compiled_regex = {
            "symbols_only": re.compile(r'^[^\w\s]+$'),
            "digits_only": re.compile(r'^\d+$'),
            "alphanumeric_only": re.compile(r'^[a-z0-9]+$'),
            "repeated_char": re.compile(r'(.)\1{4,}'),
            "repeated_pattern": re.compile(r'(.{2,})\1{3,}'),
            "only_letters": re.compile(r'[^a-z]'),
            "has_vowels": re.compile(r'[aeiouy]'),
            "consonant_cluster": re.compile(r'[bcdfghjklmnpqrstvwxz]{3,}'),
            "five_consonant_cluster": re.compile(r'[bcdfghjklmnpqrstvwxz]{5,}'),
            "collapse_spaces": re.compile(r'\s+'),
            "three_plus_letters": re.compile(r'(.)\1{2,}'),
            "unicode_noise": re.compile(r'[^\x00-\x7F]+')
        }
        
        self.is_loaded = True
        logger.info("RAM preload complete.")

engine = InMemoryEngine()
