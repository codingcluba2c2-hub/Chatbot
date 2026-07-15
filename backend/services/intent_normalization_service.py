import re
import string
import difflib
from typing import Tuple, Optional, Dict, Any

class IntentNormalizationService:
    def __init__(self):
        # 1. Spelling Correction Dictionary
        self.spelling_dict = {
            "comapny": "company",
            "copmany": "company",
            "compnay": "company",
            "mision": "mission",
            "misison": "mission",
            "misson": "mission",
            "frondend": "frontend",
            "fronted": "frontend",
            "front end": "frontend",
            "back end": "backend",
            "bakend": "backend",
            "leavs": "leave",
            "leve": "leave",
            "horus": "hours",
            "contcat": "contact",
            "rajanarayn": "rajnarayan",
            "managerr": "manager",
            "tell me about yourself": "who are you"
        }

        # 2. Intent Dictionary (Aliases mapped to Canonical Intent)
        self.intents = {
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

        # Precompute flat alias mapping and alias list for fuzzy matching
        self.alias_to_intent = {}
        self.all_aliases = []
        for intent, aliases in self.intents.items():
            for alias in aliases:
                self.alias_to_intent[alias] = intent
                self.all_aliases.append(alias)

    def preprocess_query(self, query: str) -> str:
        """
        Convert lowercase, Remove punctuation, Collapse multiple spaces,
        Normalize unicode, Remove repeated letters.
        """
        # Convert lowercase
        q = query.lower()
        
        # Remove punctuation
        q = q.translate(str.maketrans('', '', string.punctuation))
        
        # Remove repeated letters (3 or more) -> 1 letter
        q = re.sub(r'(.)\1{2,}', r'\1', q)
        
        # Collapse multiple spaces
        q = re.sub(r'\s+', ' ', q).strip()
        return q

    def correct_spelling(self, query: str) -> Tuple[str, Dict[str, str]]:
        """
        Correct spelling mistakes based on the dictionary.
        Returns corrected query and dict of corrected words.
        """
        words = query.split()
        corrected_words_dict = {}
        corrected_query_parts = []
        
        # Multi-word replacements
        temp_query = query
        for typo, correction in self.spelling_dict.items():
            if " " in typo:
                if typo in temp_query:
                    corrected_words_dict[typo] = correction
                    temp_query = temp_query.replace(typo, correction)
        
        # Word by word replacements
        words = temp_query.split()
        final_words = []
        for w in words:
            if w in self.spelling_dict:
                correction = self.spelling_dict[w]
                corrected_words_dict[w] = correction
                final_words.append(correction)
            else:
                final_words.append(w)
                
        corrected_query = " ".join(final_words)
        return corrected_query, corrected_words_dict

    def get_fuzzy_match(self, query: str) -> Tuple[Optional[str], float, Optional[str]]:
        """
        Find best matching alias.
        Returns (Matched Alias, Similarity Score (0-1), Intent)
        """
        best_match = None
        best_score = 0.0
        
        for alias in self.all_aliases:
            score = difflib.SequenceMatcher(None, query, alias).ratio()
            if score > best_score:
                best_score = score
                best_match = alias
                
        if best_score >= 0.85 and best_match:
            intent = self.alias_to_intent[best_match]
            return best_match, best_score, intent
            
        return None, best_score, None

    def process(self, original_query: str) -> Dict[str, Any]:
        """
        Full pipeline:
        1. Preprocess
        2. Spelling Correction
        3. Fuzzy Match
        """
        preprocessed = self.preprocess_query(original_query)
        corrected_query, corrected_words = self.correct_spelling(preprocessed)
        matched_alias, score, intent = self.get_fuzzy_match(corrected_query)
        
        return {
            "original_query": original_query,
            "normalized_query": corrected_query,
            "corrected_words": corrected_words,
            "detected_intent": intent,
            "similarity_score": round(score, 4),
            "matched_alias": matched_alias,
            "confidence_meets_threshold": score >= 0.85
        }
