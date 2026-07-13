# backend/services/fastpath_service.py
from repositories.registry import fastpath_repo

class FastPathService:
    @staticmethod
    def get_response(fastpath_key: str) -> str:
        paths = fastpath_repo.get_all(limit=1000)
        for path in paths:
            if not path.enabled:
                continue
            if fastpath_key.lower() == path.trigger.lower() or fastpath_key.lower() in [a.lower() for a in path.aliases]:
                return path.response
                
        return "FastPath triggered but response not found."
