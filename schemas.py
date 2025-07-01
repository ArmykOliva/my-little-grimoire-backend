

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
    money: Optional[int] = 100
    customer_id: int
    class Config:
        orm_mode = True
class PlayerCreate(PlayerBase):
    pass
class PlayerLog(BaseModel):
    name: str
    password: str


#Flowers
#TODO: how the flower recognition function should work and what kind of flower it will return

class Flower (BaseModel):
    id: int
    color_id: str
    name: str
    class Config:
        orm_mode = True

# Recipe/Potion Schemas
class PotionBase(BaseModel):
    id: int
    class Config:
        orm_mode = True
class RecipeCreate (BaseModel):
    name: Optional[str]
    required_potions: List[int] = []
    required_flowers: List[int] = []
    class Config:
        orm_mode = True
class Recipe (RecipeCreate):
    id: int

class RecipeDebug(BaseModel):
    name: Optional[str]
    required_potions: List['RecipeDebug']
    required_flowers: List[Flower]

    class Config:
        orm_mode = True
RecipeDebug.model_rebuild()
# Grimoire Schemas
class Grimoire(BaseModel):
    unlocked_recipes: List[int]
    class Config:
        orm_mode = True
#Inventory
class InventoryItem(BaseModel):
    potion_id: int
    amount: int
    class Config:
        orm_mode = True

class Inventory(BaseModel):
    potions: List[InventoryItem]
    class Config:
        orm_mode = True
#Session Schemas
class SessionBase(BaseModel):
    recipe_id: int
    class Config:
        orm_mode = True

class SessionCreate(BaseModel):
    player_id: uuid.UUID
    initial_lat: float
    initial_lng: float
    recipe_id: int
    class Config:
        orm_mode = True
class SessionJoin(BaseModel):
    player_id: uuid.UUID
    lat: float
    lng: float
    code: str
    class Config:
        orm_mode = True


# for debugging
class PlayerSessionInfo(BaseModel):
    player_id: uuid.UUID
    name: str
    picture: Optional[int] = 0
    assigned_flower: int
    class Config:
        orm_mode = True
class SessionInfo(BaseModel):
    recipe_id: int
    flower_id: Optional[int]
    #5-letter-string
    code: str
    initial_player: uuid.UUID
    players: List[PlayerSessionInfo] =[]
    flowers_collected: List[int]
    status: int
    class Config:
        orm_mode = True

class DebugSessionInfo(BaseModel):
    code: str
    recipe: RecipeDebug
    status: int
    flowers_collected: List[Flower]
    initial_player: uuid.UUID
    players: List[PlayerSessionInfo]
    started_at: datetime
    class Config:
        orm_mode = True

# Decorations

# Shop decorations
class DecorationCreate(BaseModel):
    name: Optional[str]
    cost: int
    allowed_position: int

class DecorationShop(BaseModel):
    name: Optional[str]
    id: int
    cost: int
    class Config:
        orm_mode = True

# Player's owned decoration
class DecorationPlayer(BaseModel):
    decoration_id: int
    used: bool
    position: Optional[int] = None  # Position from 0 to 4
    class Config:
        orm_mode = True


# Player's entire decoration inventory
class DecorationInventory(BaseModel):
    decorations: List[DecorationPlayer]
    class Config:
        orm_mode = True

#idk if we need that, but this is for the case we visit other player's shop
class DecorationUsed(BaseModel):
    decoration_id: int
    position: int
    class Config:
        orm_mode = True

# Flower Identification Schemas
class FlowerIdentificationResponse(BaseModel):
    color_id: Optional[str] = None
    error: Optional[str] = None
    
    class Config:
        orm_mode = True