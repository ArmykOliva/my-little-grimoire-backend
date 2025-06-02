from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

## These are just samples of how stuff can look like, we should definitely reevaluate and refactor them one by one.

# Player Schemas
class PlayerBase(BaseModel):
    money: Optional[int] = 0
    level: Optional[int] = 1

class PlayerCreate(PlayerBase):
    pass

class Player(PlayerBase):
    id: int
    player_id: uuid.UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

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

# Flower Schemas
class FlowerBase(BaseModel):
    color_id: str
    name: str
    rarity: Optional[str] = "common"

class FlowerCreate(FlowerBase):
    pass

class Flower(FlowerBase):
    id: int
    flower_id: uuid.UUID
    
    class Config:
        from_attributes = True

# Collected Flower Schemas
class CollectedFlowerBase(BaseModel):
    quantity: Optional[int] = 1

class CollectedFlowerCreate(CollectedFlowerBase):
    session_id: int
    flower_id: int

class CollectedFlower(CollectedFlowerBase):
    id: int
    session_id: int
    flower_id: int
    collected_at: datetime
    
    class Config:
        from_attributes = True

# Inventory Schemas
class InventoryItemBase(BaseModel):
    item_type: str
    item_id: str
    quantity: Optional[int] = 1

class InventoryItemCreate(InventoryItemBase):
    player_id: int

class InventoryItem(InventoryItemBase):
    id: int
    player_id: int
    
    class Config:
        from_attributes = True

# Grimoire Schemas
class GrimoireBase(BaseModel):
    live_recipe_id: Optional[str] = None
    pages_unlocked: Optional[int] = 1

class GrimoireCreate(GrimoireBase):
    player_id: int

class Grimoire(GrimoireBase):
    id: int
    player_id: int
    
    class Config:
        from_attributes = True 