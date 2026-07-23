import re
from typing import Tuple, Dict, Any, List

class EntityDetector:
    """
    Lightweight deterministic entity detector for enterprise keywords.
    """
    
    # Categorized entity keywords (lowercase for matching)
    ENTITIES = {
        "job_roles": {"designer", "developer", "engineer", "manager", "lead", "architect", "analyst", "director", "intern", "ceo", "cto", "hr", "recruiter"},
        "departments": {"hr", "human resources", "engineering", "sales", "marketing", "finance", "admin", "it", "support", "management"},
        "company": {"mobiloitte", "company", "firm", "enterprise", "organization", "workplace", "startup"},
        "services": {"services", "integration", "blockchain", "app development", "web development", "cloud", "devops", "consulting", "design"},
        "policies": {"leave", "policy", "policies", "payroll", "hours", "timing", "salary", "holiday", "vacation", "benefits", "insurance"},
        "employees": {"employee", "staff", "team", "internship", "interns", "colleagues", "workers"},
        "technologies": {"react", "web3", "unreal engine", "python", "node", "aws", "azure", "gcp", "docker", "kubernetes", "flutter", "ios", "android"},
        "products": {"product", "app", "software", "solution", "platform", "dashboard", "portal"},
        "office": {"office", "building", "headquarters", "hq", "branch", "work", "desk", "facility"},
        "contact": {"contact", "email", "phone", "support", "help", "address", "number"},
        "locations": {"delhi", "pune", "boston", "singapore", "london", "india", "uk", "usa"}
    }
    
    @classmethod
    def evaluate(cls, text: str) -> Tuple[bool, Dict[str, List[str]]]:
        """
        Check if any predefined enterprise entities are present in the text.
        Returns (has_entity, matched_entities_dict)
        """
        text_lower = text.lower()
        
        # Fast substring and exact word check
        found_entities = {}
        has_entity = False
        
        for category, keywords in cls.ENTITIES.items():
            matches = []
            for kw in keywords:
                # If keyword is multiple words, substring check is usually safe
                if " " in kw:
                    if kw in text_lower:
                        matches.append(kw)
                else:
                    # Single word - check with word boundaries to avoid partial matches
                    if re.search(rf'\b{re.escape(kw)}\b', text_lower):
                        matches.append(kw)
            
            if matches:
                found_entities[category] = matches
                has_entity = True
                
        return has_entity, found_entities
