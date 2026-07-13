from typing import List, Dict, Any

class ComponentBuilder:
    @staticmethod
    def quick_replies(items: List[str]) -> Dict[str, Any]:
        return {
            "type": "quickReplies",
            "items": items
        }

    @staticmethod
    def action_buttons(buttons: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        buttons = [{"text": "Apply Leave", "action": "leave_start"}]
        """
        return {
            "type": "buttons",
            "buttons": buttons
        }

    @staticmethod
    def form(fields: List[Dict[str, Any]], submit_action: str = "form_submit") -> Dict[str, Any]:
        """
        fields = [{"name": "leave_type", "type": "dropdown", "options": ["Sick", "Casual", "Earned"], "required": True}]
        """
        return {
            "type": "form",
            "fields": fields,
            "submit_action": submit_action
        }

    @staticmethod
    def card(title: str, description: str, subtitle: str = None, image_url: str = None, buttons: List[Dict[str, str]] = None) -> Dict[str, Any]:
        return {
            "type": "card",
            "title": title,
            "subtitle": subtitle,
            "description": description,
            "image_url": image_url,
            "buttons": buttons or []
        }
    
    @staticmethod
    def table(columns: List[str], rows: List[List[Any]]) -> Dict[str, Any]:
        return {
            "type": "table",
            "columns": columns,
            "rows": rows
        }

    @staticmethod
    def carousel(cards: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "type": "carousel",
            "items": cards
        }
