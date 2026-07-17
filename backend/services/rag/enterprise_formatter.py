import re
from typing import List

class EnterpriseFormatter:
    @staticmethod
    def detect_type(query: str) -> str:
        query_lower = query.lower()
        if any(w in query_lower for w in ["address", "where", "location", "office", "headquarter"]):
            return "location"
        if any(w in query_lower for w in ["phone", "contact", "call"]):
            return "phone"
        if any(w in query_lower for w in ["email"]):
            return "email"
        if any(w in query_lower for w in ["working hours", "timing", "time", "shift"]):
            return "working_hours"
        if any(w in query_lower for w in ["founder", "ceo", "who started"]):
            return "founder"
        if any(w in query_lower for w in ["leave", "holiday", "vacation"]):
            return "leave"
        if any(w in query_lower for w in ["tech", "stack", "technology", "framework"]):
            return "technology"
        if any(w in query_lower for w in ["policy", "rules"]):
            return "policy"
        if any(w in query_lower for w in ["mission", "vision"]):
            return "mission"
            
        return "general"

    @staticmethod
    def format_response(query: str, sentences: List[str]) -> str:
        ans_type = EnterpriseFormatter.detect_type(query)
        text = "\n".join(sentences)
        
        if ans_type in ["location", "phone"]:
            address_part = []
            phone_part = []
            for s in sentences:
                if "phone" in s.lower() or re.search(r'\b\+?\d{8,}\b', s):
                    s_clean = re.sub(r'(?i)phone:\s*', '', s).strip()
                    phone_part.append(s_clean)
                else:
                    address_part.append(s)
            
            output = ""
            if "singapore" in query.lower():
                output += "Singapore Office\n\n"
            elif "uae" in query.lower() or "dubai" in query.lower():
                output += "UAE Office\n\n"
            elif "india" in query.lower() or "delhi" in query.lower():
                output += "India Office\n\n"
                
            if address_part:
                output += "📍 Address\n" + "\n".join(address_part) + "\n\n"
            if phone_part:
                output += "📞 Phone\n" + "\n".join(phone_part) + "\n"
            
            if output.strip():
                return output.strip()
                
        elif ans_type == "founder":
            return f"👤 Founder\n\n{text}"
            
        elif ans_type == "working_hours":
            return f"🕒 Working Hours\n\n{text}"
            
        elif ans_type == "leave":
            return f"🏖 Leave Policy\n\n{text}"
            
        elif ans_type == "technology":
            lines = []
            for line in text.split('\n'):
                line = re.sub(r'^[\-\•\*\d\.]+\s*', '', line.strip())
                if line:
                    lines.append(f"• {line}")
            return "Technology Stack\n\n" + "\n".join(lines)
            
        # General formatting
        if len(sentences) == 1:
            return sentences[0]
            
        return text
