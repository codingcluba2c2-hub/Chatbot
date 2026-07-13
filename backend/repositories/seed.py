# backend/repositories/seed.py
from repositories.registry import greeting_repo, fastpath_repo
from schemas.admin import Greeting, FastPath
from utils.responses import GREETING_RESPONSES, FASTPATH_RESPONSES

def seed_data():
    if greeting_repo.count() == 0:
        for g in GREETING_RESPONSES:
            greeting_repo.create(Greeting(name="Default Greeting", response=g))
            
    if fastpath_repo.count() == 0:
        for key, text in FASTPATH_RESPONSES.items():
            fastpath_repo.create(FastPath(
                trigger=key.replace("_", " ").title(),
                aliases=[key, key.replace("_", "")],
                response=text
            ))

# Seed data will be called from app.py during startup
