from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models, schemas
from database import SessionLocal, engine, get_db
import uuid
from datetime import datetime
# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="My Little Grimoire API", version="1.0.0")

# Sample endpoints based on the diagram

@app.get("/")
async def root():
    return {"message": "Welcome to My Little Grimoire API"}

# Player/Grimoire endpoints
@app.post("/players/", response_model=schemas.Player)
async def create_player(player: schemas.PlayerCreate, db: Session = Depends(get_db)):
    """Create a new player with their grimoire"""

    db_player = models.Player(
        name=player.name,
        profile_picture=player.picture
    )
    db.add(db_player)
    db.flush()
    db_grimoire = models.Grimoire(player=db_player)
    db.add(db_grimoire)
    db.commit()
    db.refresh(db_player)

    return db_player

@app.get("/players/{player_id}", response_model=schemas.Player)
async def get_player(player_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get player by UUID"""
    db_player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not db_player:
        raise HTTPException(status_code=404, detail="Player not found")
    return db_player

@app.get("/players/{player_id}/grimoire", response_model=schemas.Grimoire)
async def get_player_grimoire(player_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get player's grimoire"""
    db_grimoire = db.query(models.Grimoire).filter(models.Grimoire.player_id == player_id).first()
    if not db_grimoire:
        raise HTTPException(status_code=404, detail="Grimoire not found")
    return schemas.Grimoire(recipe_ids=[r.id for r in db_grimoire.unlocked_recipes])

@app.get("/recipes/{recipe_id}", response_model=schemas.Recipe)
async def get_recipes(recipe_id: int, db: Session = Depends(get_db)):
    """Get information about recipe"""
    db_recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if not db_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return db_recipe

@app.get("/recipes", response_model=List[schemas.Recipe])
async def get_all_recipes(db: Session = Depends(get_db)):
    recipes = db.query(models.Recipe).all()
    return recipes

@app.get("/potions/{potion_id}", response_model=schemas.PotionBase)
async def get_potion(potion_id: int, db: Session = Depends(get_db)):
    """Get information about recipe"""
    db_recipe = db.query(models.Recipe).filter(models.Recipe.id == potion_id).first()
    if not db_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return db_recipe

@app.get("/potions", response_model=List[schemas.PotionBase])
async def get_all_potions(db: Session = Depends(get_db)):
    recipes = db.query(models.Recipe).all()
    return recipes

#TODO: do we add recipe to player or to grimoire?
@app.post("/players/{player_id}/grimoire/unlock/{recipe_id}", response_model=schemas.Grimoire)
async def unlock_recipe_for_player(player_id: uuid.UUID, recipe_id: int, db: Session = Depends(get_db)):
    # Find grimoire for player
    db_grimoire = db.query(models.Grimoire).filter(models.Grimoire.player_id == player_id).first()
    if not db_grimoire:
        raise HTTPException(status_code=404, detail="Grimoire not found")

    # Find recipe by ID
    recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Check if recipe is already unlocked
    if recipe in db_grimoire.unlocked_recipes:
        return {"message": "Recipe already unlocked"}

    # Unlock recipe
    db_grimoire.unlocked_recipes.append(recipe)
    db.commit()
    db.refresh(db_grimoire)

    # Return updated grimoire recipe ids
    return schemas.Grimoire(recipe_ids=[r.id for r in db_grimoire.unlocked_recipes])

# Recipe session endpoints
@app.post("/start-recipe-session")
async def start_recipe_session(player_uuid: str, recipe_id: str, db: Session = Depends(get_db)):
    """Start a new recipe session"""
    # for example recipe_name == "health_potion"

    #TODO


    #TODO: check whether player has all potions needed

    #TODO: create list of shears needed

    #TODO: create 5-letter-cide for later connection

    #TODO: return session_id + shear color
    #Questin: what if all shears are used? just random? (or don't allow to connect?)
    return {
        "session_id": "12454567-e89b-12d3-a456-426614174000"
    }

@app.get("/players/{player_id}/inventory", response_model=schemas.Inventory)
async def get_inventory(player_id: uuid.UUID, db: Session = Depends(get_db)):
    player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    inventory = [
        schemas.InventoryItem(
            potion_id=item.potion_id,
            amount=item.amount
        )
        for item in player.inventory_items
    ]
    return schemas.Inventory(potions=inventory)

@app.post("/players/{player_id}/inventory/add/{potion_id}")
async def add_potion_to_inventory(player_id: uuid.UUID, potion_id: int, db: Session = Depends(get_db)):
    player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    """ Optional 
    potion = db.query(models.Recipe).filter(models.Recipe.id == potion_id).first()
    if not potion:
        raise HTTPException(status_code=404, detail="Potion does not exist")
    """
    # Check if player already has this potion
    inventory_item = db.query(models.InventoryItem).filter_by(player_id=player_id, potion_id=potion_id).first()

    if inventory_item:
        inventory_item.amount +=1
    else:
        new_item = models.InventoryItem(player_id=player_id, potion_id=potion_id, amount=1)
        db.add(new_item)

    db.commit()
    return {"message": "Potion added to inventory"}

#TODO: use item from inventory

#TODO: join session

#TODO: get session information