from fastapi import FastAPI, Depends, HTTPException
from typing import Optional
from sqlalchemy.orm import Session
from typing import List
import models, schemas
import utils
from database import SessionLocal, engine, get_db
import uuid
import random
from datetime import datetime, timedelta

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="My Little Grimoire API", version="1.0.0")

# Sample endpoints based on the diagram

@app.get("/")
async def root():
    return {"message": "Welcome to My Little Grimoire API"}

# Player/Grimoire endpoints

#TODO: evaluate: do we have to return session_id and shears as well?
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
    return db_grimoire

#TODO: evaluate: do we really need grimoire or just save connections by player?
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
    return db_grimoire

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


# Inventory
@app.get("/players/{player_id}/inventory", response_model=schemas.Inventory)
async def get_inventory(player_id: uuid.UUID, db: Session = Depends(get_db)):
    player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # inventory = [
    #     schemas.InventoryItem(
    #         potion_id=item.potion_id,
    #         amount=item.amount
    #     )
    #     for item in player.inventory_items
    # ]
    return schemas.Inventory(potions = player.inventory_items)

@app.post("/players/{player_id}/inventory/add/{potion_id}")
async def add_potion_to_inventory(player_id: uuid.UUID, potion_id: int, db: Session = Depends(get_db)):
    player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    potion = db.query(models.Recipe).filter(models.Recipe.id == potion_id).first()
    if not potion:
        raise HTTPException(status_code=404, detail="Potion does not exist")

    # Check if player already has this potion
    inventory_item = db.query(models.InventoryItem).filter_by(player_id=player_id, potion_id=potion_id).first()

    if inventory_item:
        inventory_item.amount +=1
    else:
        new_item = models.InventoryItem(player_id=player_id, potion_id=potion_id, amount=1)
        db.add(new_item)

    db.commit()
    return {"message": "Potion added to inventory"}

@app.post("/players/{player_id}/inventory/remove/{potion_id}")
async def remove_potion_from_inventory(player_id: uuid.UUID, potion_id: int, db: Session = Depends(get_db)):
    player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    inventory_item = db.query(models.InventoryItem).filter_by(player_id=player_id, potion_id=potion_id).first()
    if not inventory_item:
        raise HTTPException(status_code=404, detail="Potion not found in inventory")

    if inventory_item.amount > 1:
        inventory_item.amount -= 1
    else:
        db.delete(inventory_item)

    db.commit()
    return {"message": "Potion removed from inventory"}

#TODO: evaluate if we need session_id or check it always by session_id from player

#create session
@app.post("/session/create", response_model=schemas.SessionJoined)
def create_session(data: schemas.SessionCreate, db: Session = Depends(get_db)):
    player = db.query(models.Player).filter(models.Player.player_id == data.player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    if player.session_id:
        raise HTTPException(status_code=400, detail="Player already in a session")


    recipe = db.query(models.Recipe).filter(models.Recipe.id == data.recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Check if player has a grimoire
    if not player.grimoire:
        raise HTTPException(status_code=400, detail="Player has no grimoire")

    # Check if the recipe is in the player's unlocked recipes
    if recipe not in player.grimoire.unlocked_recipes:
        raise HTTPException(status_code=403, detail="Recipe is not unlocked by this player")


    #TODO: what do we do, when player who join don't have potions?
    # Should the potions be deleted from player's inventory?
    # Save init player?

    # player_potion_ids = {item.potion_id for item in player.inventory_items}
    # required_potion_ids = {p.id for p in recipe.required_potions}
    # missing = required_potion_ids - player_potion_ids
    # if missing:
    #     raise HTTPException(status_code=400, detail="Player is missing required potions to start this recipe")

    #Extract flower color_ids from required flowers
    available_colors = available_colors = list({flower.color_id for flower in recipe.required_flowers})

    if not available_colors:
        raise HTTPException(status_code=400, detail="No available colors in recipe")

    assigned_color = available_colors.pop(0)

    join_code = utils.generate_code()

    while (db.query(models.Session).filter_by(code=join_code).first()):
        join_code = utils.generate_code()

    new_session = models.Session(
        recipe=recipe,
        code=join_code,
        shears_available=available_colors,
        initial_lat=data.initial_lat,
        initial_lng=data.initial_lng
    )
    db.add(new_session)
    db.flush()

    # TODO: update player on client side?
    player.session_id = new_session.session_id
    player.shears_color = assigned_color

    db.commit()

    return schemas.SessionJoined(
        color_id=assigned_color,
        code=join_code
    )

#Join session
@app.post("/session/join", response_model=schemas.SessionJoined)
def join_session(data: schemas.SessionJoin, db: Session = Depends(get_db)):

    #get player
    player = db.query(models.Player).filter(models.Player.player_id == data.player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    if player.session_id:
        raise HTTPException(status_code=400, detail="Player already in a session")

    #get session
    session = db.query(models.Session).filter(models.Session.code == data.code).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    #TODO: what if players moved? Should we always update with position of first player or let it be like that?
    if not utils.is_within_distance(data.lat, data.lng, session.initial_lat, session.initial_lng):
        raise HTTPException(status_code=400, detail="Too far from session")

    if not session.shears_available:
        raise HTTPException(status_code=400, detail="No shears/colors available")
    assigned_color = session.shears_available[0]
    session.shears_available = session.shears_available[1:]
    player.session_id = session.session_id
    player.shears_color = assigned_color

    db.commit()


    return schemas.SessionJoined(
        color_id=assigned_color,
        code=data.code
    )

#Leave all sessions
@app.post("/players/{player_id}/leave")
def leave_session(player_id: uuid.UUID, db: Session = Depends(get_db)):
    player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    session = db.query(models.Session).filter(models.Session.session_id == player.session_id).first()
    if session and player.shears_color:
        session.shears_available.append(player.shears_color)

    player.session_id = None
    player.shears_color = None

    db.commit()
    return {"message": "Left session successfully"}



#TODO: flower recognition, receiving picture from the client
#Right now: mocked up with flower_ids
@app.post("/session/collect_flower", response_model=Optional[schemas.SessionInfo])
def collect_flower(
    flower_id: int,
    player_id: uuid.UUID,
    db: Session = Depends(get_db)
):

    #player
    player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not player or not player.session_id:
        raise HTTPException(status_code=404, detail="Player not in a session")

    # get session
    session = db.query(models.Session).filter(models.Session.session_id == player.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")


    if session.status == 1:
        player.session_id = None
        player.shears_color = None
        db.commit()
        # Check if any players remain in session
        remaining_players = session.players
        if not remaining_players:
            db.delete(session)
            db.commit()
        return None
    flower = db.query(models.Flower).filter(models.Flower.id == flower_id).first()
    if not flower:
        raise HTTPException(status_code=404, detail="Flower not found")

    # Check if flower color matches player's shears
    if flower.color_id != player.shears_color:
        raise HTTPException(status_code=400, detail="Flower color doesn't match your shears color")

    # Add flower to session's collected flowers
    recipe = session.recipe
    recipe_flower_ids = {f.id for f in recipe.required_flowers}

    if flower.id not in recipe_flower_ids:
        raise HTTPException(status_code=400, detail="This flower is not required for the recipe")

    session.flowers_collected.append(flower)

    # Check if recipe requirements are met
    recipe = session.recipe
    required_ids = {f.id for f in recipe.required_flowers}
    collected_ids = {f.id for f in session.flowers_collected}
    if required_ids.issubset(collected_ids):
        session.status = 1  # Complete
        player.session_id = None
        player.shears_color = None
        db.commit()

        # Check if any players remain in session
        remaining_players = session.players
        if not remaining_players:
            db.delete(session)
            db.commit()
        return None

    db.commit()
    db.refresh(session)
    return session




@app.get("/session/info", response_model=Optional[schemas.SessionInfo])
def session_info(player_id: uuid.UUID, db: Session = Depends(get_db)):
    player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not player or not player.session_id:
        raise HTTPException(status_code=403, detail="Not part of this session")

    # get session
    session = db.query(models.Session).filter(models.Session.session_id == player.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status == 1:
        # Remove player from session
        player.session_id = None
        player.shears_color = None
        db.commit()

        # Check if any players remain in session
        remaining_players = session.players
        if not remaining_players:
            db.delete(session)
            db.commit()
        return None
    return session

#clean sessions (based on creation_time)

def clear_stale_sessions(db: Session = Depends(get_db)):
    cutoff = datetime.now() - timedelta(days=1)

    # Fetch all sessions (you could optimize this by filtering in SQL if needed)
    sessions = db.query(models.Session).all()
    removed_count = 0

    for session in sessions:
        is_old = session.started_at < cutoff
        has_no_players = not session.players or len(session.players) == 0

        if is_old or has_no_players:
            db.delete(session)
            removed_count += 1

    db.commit()
    return removed_count


#get all sessions (for debugging)
@app.get("/debug/sessions", response_model=List[schemas.DebugSessionInfo])
def get_all_sessions(db: Session = Depends(get_db)):
    sessions = db.query(models.Session).all()
    return sessions
