from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid



## this is what we are returning
## These are just samples of how stuff can look like, we should definitely reevaluate and refactor them one by one.

# Player Schemas

class PlayerBase(BaseModel):
    name: Optional[str] = None
    picture: Optional[int] = 0

class Player(PlayerBase):
    player_id: uuid.UUID
    money: Optional[int] = 0
    class Config:
        orm_mode = True
class PlayerCreate(PlayerBase):
    pass

# Grimoire Schemas
class Grimoire(BaseModel):
    recipe_ids: List[int]
    class Config:
        orm_mode = True

# Recipe/Potion Schemas
class PotionBase(BaseModel):
    id: int
    potion_name: str
    potion_picture: Optional[str]
    class Config:
        orm_mode = True



class Recipe (PotionBase):
    # TODO: maybe 2 references to flowers and potions (see models)
    recipe_data: Optional[str] = None
    # TODO: different sequences to craft (see models)

#Inventory
class InventoryItem(BaseModel):
    potion_id: int
    amount: int


class Inventory(BaseModel):
    potions: List[InventoryItem]
#Session Schemas
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

