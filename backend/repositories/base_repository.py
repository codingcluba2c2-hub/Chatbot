# backend/repositories/base_repository.py
from typing import TypeVar, Generic, Type, List, Optional, Dict, Any
from pydantic import BaseModel
import time
from sqlalchemy import or_, desc, asc
from core.database import SessionLocal

T = TypeVar("T", bound=BaseModel)
D = TypeVar("D") # DB Model

class BaseRepository(Generic[T, D]):
    def __init__(self, pydantic_model: Type[T], db_model: Type[D] = None):
        self.model = pydantic_model
        self.db_model = db_model
        
    def _to_pydantic(self, db_obj: Any) -> T:
        if not db_obj:
            return None
        # Convert SQLAlchemy object to dictionary, then to Pydantic
        obj_dict = {}
        for prop in self.db_model.__mapper__.column_attrs:
            attr_name = prop.key
            col_name = prop.columns[0].name
            obj_dict[col_name] = getattr(db_obj, attr_name)
        return self.model(**obj_dict)

    def _invalidate_cache(self):
        if hasattr(self, "_cache"):
            self._cache.clear()
            self._cache_times.clear()

    def get_all(self, skip: int = 0, limit: int = 100, sort_by: str = "created_at", descending: bool = True, query: str = None) -> List[T]:
        if not self.db_model:
            return []
            
        cache_key = f"get_all_{skip}_{limit}_{sort_by}_{descending}_{query}"
        
        if not hasattr(self, "_cache"):
            self._cache = {}
            self._cache_times = {}
            
        now = time.time()
        if cache_key in self._cache and (now - self._cache_times.get(cache_key, 0)) < 3600:
            return self._cache[cache_key]
            
        from sqlalchemy.exc import OperationalError
        
        max_retries = 2
        for attempt in range(max_retries):
            try:
                with SessionLocal() as session:
                    stmt = session.query(self.db_model)
                    
                    if query:
                        # Basic search on string columns
                        query_lower = f"%{query.lower()}%"
                        string_columns = [c for c in self.db_model.__table__.columns if c.type.python_type is str]
                        if string_columns:
                            filters = [c.ilike(query_lower) for c in string_columns]
                            if filters:
                                stmt = stmt.filter(or_(*filters))
                                
                    if hasattr(self.db_model, sort_by):
                        sort_col = getattr(self.db_model, sort_by)
                        if descending:
                            stmt = stmt.order_by(desc(sort_col))
                        else:
                            stmt = stmt.order_by(asc(sort_col))
                    else:
                        if hasattr(self.db_model, "created_at"):
                            stmt = stmt.order_by(desc(self.db_model.created_at))
                            
                    stmt = stmt.offset(skip).limit(limit)
                    db_items = stmt.all()
                    
                    results = [self._to_pydantic(item) for item in db_items if item is not None]
                    
                    self._cache[cache_key] = results
                    self._cache_times[cache_key] = now
                    
                    return results
            except OperationalError:
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    raise
        return []
    def get_by_id(self, item_id: str) -> Optional[T]:
        if not self.db_model:
            return None
            
        with SessionLocal() as session:
            db_item = session.query(self.db_model).filter(self.db_model.id == item_id).first()
            return self._to_pydantic(db_item)
        
    def create(self, item: BaseModel) -> T:
        if not self.db_model:
            # Fallback if db_model is missing
            return self.model(**item.model_dump())
            
        db_item = self.model(**item.model_dump())
        item_dict = db_item.model_dump()
        
        db_obj = self.db_model(**item_dict)
        
        with SessionLocal() as session:
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
            self._invalidate_cache()
            return self._to_pydantic(db_obj)
        
    def update(self, item_id: str, update_data: BaseModel) -> Optional[T]:
        if not self.db_model:
            return None
            
        with SessionLocal() as session:
            db_obj = session.query(self.db_model).filter(self.db_model.id == item_id).first()
            if not db_obj:
                return None
                
            update_dict = update_data.model_dump(exclude_unset=True)
            for key, value in update_dict.items():
                if hasattr(db_obj, key) and key not in ["id", "created_at"]:
                    setattr(db_obj, key, value)
                    
            if hasattr(db_obj, "updated_at"):
                db_obj.updated_at = time.time()
                
            session.commit()
            session.refresh(db_obj)
            self._invalidate_cache()
            return self._to_pydantic(db_obj)
        
    def delete(self, item_id: str) -> bool:
        if not self.db_model:
            return False
            
        with SessionLocal() as session:
            db_obj = session.query(self.db_model).filter(self.db_model.id == item_id).first()
            if db_obj:
                session.delete(db_obj)
                session.commit()
                self._invalidate_cache()
                return True
            return False

    def count(self) -> int:
        if not self.db_model:
            return 0
            
        with SessionLocal() as session:
            return session.query(self.db_model).count()
