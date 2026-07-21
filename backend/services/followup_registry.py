# backend/services/followup_registry.py
from typing import Dict, Any, Optional

class FollowupPatternRegistry:
    def __init__(self):
        # keyword -> (rewrite_template, priority)
        self.patterns: Dict[str, Dict[str, Any]] = {
            "name": {
                "template": "What is my preferred name?",
                "priority": 10
            },
            "salary": {
                "template": "What is the salary for {last_entity}?",
                "priority": 10
            },
            "price": {
                "template": "What is the price of {last_entity}?",
                "priority": 10
            },
            "pricing": {
                "template": "What is the pricing for {last_entity}?",
                "priority": 10
            },
            "address": {
                "template": "What is the address of {last_entity}?",
                "priority": 10
            },
            "phone": {
                "template": "What is the phone number of {last_entity}?",
                "priority": 10
            },
            "contact": {
                "template": "What is the contact information for {last_entity}?",
                "priority": 10
            },
            "timing": {
                "template": "What are the timings for {last_entity}?",
                "priority": 10
            },
            "location": {
                "template": "What is the location of {last_entity}?",
                "priority": 10
            },
            "email": {
                "template": "What is the email address for {last_entity}?",
                "priority": 10
            },
            "website": {
                "template": "What is the website for {last_entity}?",
                "priority": 10
            },
            "owner": {
                "template": "Who is the owner of {last_entity}?",
                "priority": 10
            },
            "ceo": {
                "template": "Who is the CEO of {last_entity}?",
                "priority": 10
            },
            "founder": {
                "template": "Who is the founder of {last_entity}?",
                "priority": 10
            },
            "services": {
                "template": "What services does {last_entity} offer?",
                "priority": 10
            },
            "leave": {
                "template": "What is the leave policy for {last_entity}?",
                "priority": 10
            },
            "policy": {
                "template": "What is the policy regarding {last_entity}?",
                "priority": 10
            }
        }

    def get_pattern(self, keyword: str) -> Optional[Dict[str, Any]]:
        return self.patterns.get(keyword.lower().strip())

    def add_pattern(self, keyword: str, template: str, priority: int = 10):
        self.patterns[keyword.lower().strip()] = {
            "template": template,
            "priority": priority
        }

followup_registry = FollowupPatternRegistry()
