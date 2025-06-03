from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid


## this is what we are returning
## These are just samples of how stuff can look like, we should definitely reevaluate and refactor them one by one.

# Player Schemas
class Player(BaseModel):
    money: Optional[int] = 0
    player_id: uuid.UUID


# Recipe Schemas
class RecipeBase(BaseModel):
    potion_name: str
    recipe_data: Optional[str] = None
    difficulty_level: Optional[int] = 1

class RecipeCreate(RecipeBase):
    pass

class Recipe(RecipeBase):
    id: int
    recipe_id: uuid.UUID
    
    class Config:
        from_attributes = True

# Session Schemas
class SessionBase(BaseModel):
    is_active: Optional[bool] = True

class SessionCreate(SessionBase):
    player_id: int

class Session(SessionBase):
    id: int
    session_id: uuid.UUID
    player_id: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Grimoire Schemas
class Grimoire(BaseModel):
    recipe_ids: List[str]