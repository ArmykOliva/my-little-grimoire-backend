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



#Flowers
#TODO: how the flower recognition function should work and what kind of flower it will return

class Flower (BaseModel):
    id: int
    color_id: str
    flower_name: str
    flower_rarity: Optional[str]
    flower_description: Optional[str]

    class Config:
        orm_mode = True

# Recipe/Potion Schemas
class PotionBase(BaseModel):
    id: int
    potion_name: str
    class Config:
        orm_mode = True



class Recipe (PotionBase):
    required_potions: List['Recipe'] = []
    required_flowers: List[Flower] = []
    # TODO: different sequences to craft (see models)
Recipe.model_rebuild()

# Grimoire Schemas
class Grimoire(BaseModel):
    unlocked_recipes: List[Recipe]
    class Config:
        orm_mode = True


#Inventory
class InventoryItem(BaseModel):
    potion: PotionBase
    amount: int


class Inventory(BaseModel):
    potions: List[InventoryItem]
#Session Schemas
class SessionBase(BaseModel):
    recipe: Recipe
    class Config:
        orm_mode = True

class SessionCreate(BaseModel):
    player_id: uuid.UUID
    initial_lat:str
    initial_lng:str
    recipe_id: int
class SessionJoin(BaseModel):
    player_id: uuid.UUID
    lat:str
    lng:str
    code: str
class SessionJoined(BaseModel):
    #session_id: uuid.UUID
    color_id: str
    #5-letter-string
    code: str

    #TODO: can we allow players to start collecting flowers when not everybody joined?
    # can be done by returning the amount of available colors or so
class SessionInfo(SessionBase):
    flowers_collected: List[Flower]
    status: int
    class Config:
        orm_mode = True


# for debugging
class PlayerSessionInfo(BaseModel):
    player_id: uuid.UUID
    name: str
    shears_color: Optional[str]

    class Config:
        orm_mode = True

class DebugSessionInfo(BaseModel):
    session_id: uuid.UUID
    recipe: Recipe
    status: int
    players: List[PlayerSessionInfo]
    started_at: datetime

    class Config:
        orm_mode = True
