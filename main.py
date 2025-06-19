from fastapi import FastAPI, Depends, HTTPException
from typing import Optional
from sqlalchemy.orm import Session
from typing import List
import models, schemas
import seed_data
import utils
from database import SessionLocal, engine, get_db
import uuid
import random
from datetime import datetime, timedelta

from schemas import DecorationUsed

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="My Little Grimoire API", version="1.0.0")

# Sample endpoints based on the diagram

@app.get("/")
async def root():
    return {"message": "Welcome to My Little Grimoire API"}

# Playerendpoints
@app.get("/players", response_model=List[schemas.Player])
async def get_all_players(db: Session = Depends(get_db)):
    players = db.query(models.Player).all()
    return players
@app.post("/players/create", response_model=schemas.Player)
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

#Customers
@app.put("/players/{player_id}/customer/{customer_id}", response_model=schemas.Player)
async def set_customer_id(player_id: uuid.UUID, customer_id: int, db: Session = Depends(get_db)):
    player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    player.customer_id = customer_id
    db.commit()
    db.refresh(player)
    return player

#Money
@app.post("/players/{player_id}/money/change", response_model=int)
async def change_player_money(player_id: uuid.UUID, amount: int, db: Session = Depends(get_db)):
    player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    new_money = max(player.money + amount, 0)
    player.money = new_money
    db.commit()
    db.refresh(player)
    return player.money

#Grimoire
@app.get("/players/{player_id}/grimoire", response_model=schemas.Grimoire)
async def get_player_grimoire(player_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get player's grimoire"""
    db_grimoire = db.query(models.Grimoire).filter(models.Grimoire.player_id == player_id).first()
    if not db_grimoire:
        raise HTTPException(status_code=404, detail="Grimoire not found")
    return schemas.Grimoire(unlocked_recipes = [r.id for r in db_grimoire.unlocked_recipes])

@app.post("/players/{player_id}/grimoire/unlock/{recipe_id}", response_model=schemas.Grimoire)
async def unlock_recipe_for_player(player_id: uuid.UUID, recipe_id: int, db: Session = Depends(get_db)):
    """Add recipe to player's grimoire"""
    # Find grimoire for player
    db_grimoire = db.query(models.Grimoire).filter(models.Grimoire.player_id == player_id).first()
    if not db_grimoire:
        raise HTTPException(status_code=404, detail="Grimoire not found")

    # Find recipe by ID (optional)
    recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Check if recipe is already unlocked
    if recipe in db_grimoire.unlocked_recipes:
        raise HTTPException(status_code=404, detail="Recipe is already unlocked")

    # Unlock recipe
    db_grimoire.unlocked_recipes.append(recipe)
    db.commit()
    db.refresh(db_grimoire)

    # Return updated grimoire recipe ids
    return schemas.Grimoire(unlocked_recipes = [r.id for r in db_grimoire.unlocked_recipes])

@app.post("/players/{player_id}/grimoire/lock/{recipe_id}", response_model=schemas.Grimoire)
async def lock_recipe_for_player(player_id: uuid.UUID, recipe_id: int, db: Session = Depends(get_db)):
    """Add recipe to player's grimoire"""
    # Find grimoire for player
    db_grimoire = db.query(models.Grimoire).filter(models.Grimoire.player_id == player_id).first()
    if not db_grimoire:
        raise HTTPException(status_code=404, detail="Grimoire not found")

    # Find recipe by ID (optional)
    recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Check if recipe is already unlocked
    if recipe in db_grimoire.unlocked_recipes:
        db_grimoire.unlocked_recipes.remove(recipe)
        db.commit()
        db.refresh(db_grimoire)
        return schemas.Grimoire(unlocked_recipes=[r.id for r in db_grimoire.unlocked_recipes])

    else:
        raise HTTPException(status_code=404, detail="Recipe has not been unlocked yet")



# Inventory
@app.get("/players/{player_id}/inventory", response_model=schemas.Inventory)
async def get_inventory(player_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get player's recipe by his UUID"""
    player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    inventory = [schemas.InventoryItem(potion_id = item.potion_id, amount=item.amount)
                for item in player.inventory_items
                ]
    return schemas.Inventory(potions=inventory)


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
    inventory = [schemas.InventoryItem(potion_id=item.potion_id, amount=item.amount)
                 for item in player.inventory_items
                 ]
    return schemas.Inventory(potions=inventory)

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
    inventory = [schemas.InventoryItem(potion_id=item.potion_id, amount=item.amount)
                 for item in player.inventory_items
                 ]
    return schemas.Inventory(potions=inventory)


def remove_potion_from_inventory_func(player_id: uuid.UUID, potion_id: int, db: Session):
    player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not player:
       return

    inventory_item = db.query(models.InventoryItem).filter_by(player_id=player_id, potion_id=potion_id).first()
    if not inventory_item:
        return

    if inventory_item.amount > 1:
        inventory_item.amount -= 1
    else:
        db.delete(inventory_item)

    db.commit()
# Decorations

@app.post("/players/{player_id}/decorations/buy/{decoration_id}", response_model=schemas.DecorationInventory)
def buy_decoration(player_id: uuid.UUID, decoration_id: int, db: Session = Depends(get_db)):
    decoration = db.query(models.Decoration).get(decoration_id)
    if not decoration:
        raise HTTPException(404, "Decoration not found")

    player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not player:
        HTTPException(status_code=404, detail="Player not found")

    if player.money < decoration.cost:
        raise HTTPException(400, "Insufficient funds")

    # Check if already owns
    already_owned = db.query(models.DecorationPlayer).filter_by(player_id=player_id, decoration_id=decoration_id).first()
    if already_owned:
        raise HTTPException(400, "Already owned")

    player.money -= decoration.cost
    player_decoration = models.DecorationPlayer(player_id=player_id, decoration_id=decoration_id)
    db.add(player_decoration)
    db.commit()

    inventory_decorations = player.decorations
    return schemas.DecorationInventory(decorations = [schemas.DecorationPlayer(used = d.used, position = d.position, decoration_id = d.decoration_id) for d in inventory_decorations])


#Get decorations
@app.get("/players/{player_id}/decorations", response_model=schemas.DecorationInventory)
def get_player_decorations(player_id: uuid.UUID, db: Session = Depends(get_db)):
    player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    inventory_decorations = player.decorations
    return schemas.DecorationInventory(
        decorations=[schemas.DecorationPlayer(used=d.used, position=d.position, decoration_id=d.decoration_id) for d in
                     inventory_decorations])

@app.post("/players/{player_id}/decorations/place/{decoration_id}")
def place_decoration(player_id: uuid.UUID, decoration_id: int, position: int, db: Session = Depends(get_db)):
    player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    decoration_player = db.query(models.DecorationPlayer).filter_by(player_id=player_id, decoration_id=decoration_id).first()

    if not decoration_player:
        raise HTTPException(status_code=404, detail="Player does not own this decoration")

    decoration = db.query(models.Decoration).filter_by(id=decoration_id).first()
    if not decoration:
        raise HTTPException(status_code=404, detail="Decoration not found")

    # Check allowed position using bitmask
    if not (decoration.allowed_position & (1 << position)):
        raise HTTPException(status_code=400, detail="Invalid position for this decoration")

    other_at_position = (db.query(models.DecorationPlayer)
                        .filter(models.DecorationPlayer.player_id == player_id,
                            models.DecorationPlayer.used == True,
                            models.DecorationPlayer.position == position)
                        .first())
    if other_at_position:
        # Unplace the other decoration
        other_at_position.used = False
        other_at_position.position = None
    decoration_player.used = True
    decoration_player.position = position
    db.commit()
    inventory_decorations = player.decorations
    return schemas.DecorationInventory(
        decorations=[schemas.DecorationPlayer(used=d.used, position=d.position, decoration_id=d.decoration_id) for d in
                     inventory_decorations])

@app.get("/players/{player_id}/decorations/used", response_model=List[schemas.DecorationUsed])
async def get_used_decorations(player_id: uuid.UUID, db: Session = Depends(get_db)):
    player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    used_decorations = db.query(models.DecorationPlayer).filter(
        models.DecorationPlayer.player_id == player_id,
        models.DecorationPlayer.used == True
    ).all()

    return [schemas.DecorationUsed(decoration_id = d.decoration_id, position = d.position) for d in used_decorations]



"""Sessions"""

#create session
@app.post("/session/create", response_model=schemas.SessionInfo)
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

    player_potion_ids = {item.potion_id for item in player.inventory_items}
    required_potion_ids = {p.id for p in recipe.required_potions}
    missing = required_potion_ids - player_potion_ids
    if missing:
         raise HTTPException(status_code=400, detail="Player is missing required potions to start this recipe")

    #Extract flower color_ids from required flowers
    available_colors = available_colors = list({flower.color_id for flower in recipe.required_flowers})

    if not available_colors:
        raise HTTPException(status_code=400, detail="No available colors in recipe")

    assigned_color = available_colors.pop(0)

    join_code = utils.generate_code()

    while db.query(models.Session).filter_by(code=join_code).first():
        join_code = utils.generate_code()

    new_session = models.Session(
        recipe_id=data.recipe_id,
        code=join_code,
        shears_available=available_colors,
        initial_lat=data.initial_lat,
        initial_lng=data.initial_lng,
        initial_player = data.player_id
    )
    db.add(new_session)
    db.flush()

    player.session_id = new_session.session_id
    player.shears_color = assigned_color
    db.commit()

    return schemas.SessionInfo(
        recipe_id = data.recipe_id,
        color_id=assigned_color,
        code=join_code,
        flowers_collected = [],
        players = [schemas.PlayerSessionInfo(player_id = p.player_id, name = p.name, shears_color=p.shears_color, picture = p.profile_picture)  for p in new_session.players],
        status = 0
    )

#Join session
@app.post("/session/join", response_model=schemas.SessionInfo)
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
    if session.status == 1:
        raise HTTPException(status_code=400, detail="Session already in brewing stage")
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

    return schemas.SessionInfo(
        recipe_id=session.recipe_id,
        color_id=assigned_color,
        code=session.code,
        flowers_collected=[f.id for f in session.flowers_collected],
        players=[schemas.PlayerSessionInfo(player_id=p.player_id, name=p.name, shears_color=p.shears_color,
                                           picture=p.profile_picture) for p in session.players],
        status=0
    )


#Leave all sessions
@app.post("/players/{player_id}/leaveSession")
def leave_session(player_id: uuid.UUID, db: Session = Depends(get_db)):
    player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    if not player.session_id:
        raise HTTPException(status_code=404, detail="Player not in any session")
    session = db.query(models.Session).filter(models.Session.session_id == player.session_id).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if player.shears_color:
        session.shears_available.append(player.shears_color)

    player.session_id = None
    player.shears_color = None
    db.commit()
    remaining_players = session.players
    if not remaining_players:
        db.delete(session)
        db.commit()
        return {"message": "Left session successfully"}
    #if initial player leaves during collection, stop session
    if session.initial_player == player.player_id and session.status == 0:
        db.delete(session)
        db.commit()
        return {"message": "Left session successfully. It was initial player, so the session was deleted"}
    return {"message": "Left session successfully"}

#Right now: mocked up with flower_ids
@app.post("/players/{player_id}/session/collect_flower/{flower_id}", response_model=Optional[schemas.SessionInfo])
def collect_flower( flower_id: int, player_id: uuid.UUID, db: Session = Depends(get_db)):
    """Collect flower"""
    #player
    player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not player or not player.session_id:
        raise HTTPException(status_code=404, detail="Player not in a session")

    # get session
    session = db.query(models.Session).filter(models.Session.session_id == player.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status == 1:
        raise HTTPException(status_code=400, detail="Session already in brewing stage")

    flower = db.query(models.Flower).filter(models.Flower.id == flower_id).first()
    if not flower:
        raise HTTPException(status_code=404, detail="Flower not found")

    # Check if flower color matches player's shears
    if flower.color_id != player.shears_color:
        raise HTTPException(status_code=400, detail="Flower color doesn't match your shears color")

    # Add flower to session's collected flowers
    recipe = db.query(models.Recipe).get(session.recipe_id)
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
        for potion in [p.id for p in recipe.required_potions]:
            remove_potion_from_inventory_func(session.initial_player,potion, db)

    db.commit()
    db.refresh(session)
    return schemas.SessionInfo(
        recipe_id=session.recipe_id,
        color_id=player.shears_color,
        code=session.code,
        flowers_collected=[f.id for f in session.flowers_collected],
        players=[schemas.PlayerSessionInfo(player_id=p.player_id, name=p.name, shears_color=p.shears_color,
                                           picture=p.profile_picture) for p in session.players],
        status=session.status
    )


@app.get("/players/{player_id}/session/info", response_model=Optional[schemas.SessionInfo])
def session_info(player_id: uuid.UUID, db: Session = Depends(get_db)):
    """Info about a current session"""
    player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not player or not player.session_id:
        raise HTTPException(status_code=404, detail="Player not in a session")

    # get session
    session = db.query(models.Session).filter(models.Session.session_id == player.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return schemas.SessionInfo(
        recipe_id=session.recipe_id,
        color_id=player.shears_color,
        code=session.code,
        flowers_collected=[f.id for f in session.flowers_collected],
        players=[schemas.PlayerSessionInfo(player_id=p.player_id, name=p.name, shears_color=p.shears_color,
                                           picture=p.profile_picture) for p in session.players],
        status=session.status
    )


#Overall
@app.get("/decorations", response_model=List[schemas.DecorationShop])
def get_all_decorations(db: Session = Depends(get_db)):
    """Get info about all decorations"""
    return db.query(models.Decoration).all()

@app.post("/decorations/add")
async def add_decoration(decoration: schemas.DecorationCreate, db: Session = Depends(get_db)):
    """Add a new decoration"""

    decoration_db = db.query(models.Decoration).filter(models.Decoration.name == decoration.name).first()
    if decoration_db:
        raise HTTPException(status_code=404, detail="Decoration already exists")
    decoration_db =  models.Decoration(name = decoration.name, cost = decoration.cost, allowed_position = decoration.allowed_position)
    db.add(decoration_db)
    db.commit()
    return {"message": "New decoration added!"}


@app.get("/recipes", response_model=List[schemas.Recipe])
async def get_all_recipes(db: Session = Depends(get_db)):
    """Get all recipes"""
    recipes = db.query(models.Recipe).all()
    return [schemas.Recipe(name = r.name, required_flowers=[f.id for f in r.required_flowers], required_potions=[p.id for p in r.required_potions], id = r.id)  for r in recipes]

@app.get("/recipes/{recipe_id}", response_model=schemas.Recipe)
async def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    """Get information about recipe"""
    db_recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if not db_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return schemas.Recipe(name = db_recipe.name, required_flowers=[f.id for f in db_recipe.required_flowers], required_potions=[p.id for p in db_recipe.required_potions], id = db_recipe.id)

@app.post("/recipes/add")
async def add_recipe(recipe: schemas.RecipeCreate, db: Session = Depends(get_db)):
    """Add a new recipe"""

    recipe_db = db.query(models.Recipe).filter(models.Recipe.name == recipe.name).first()
    if recipe_db:
        raise HTTPException(status_code=404, detail="Recipe already exists")

    flowers = []

    for flower_id in recipe.required_flowers:
        flower_db = db.query(models.Flower).get(flower_id)
        if not flower_db:
            raise HTTPException(status_code=404, detail="Flower for recipe not found")
        flowers.append(flower_db)
    potions = []
    for potion_id in recipe.required_potions:
        potion_db = db.query(models.Recipe).get(potion_id)
        if not potion_db:
            raise HTTPException(status_code=404, detail="Potion for recipe not found")
        potions.append(potion_db)


    recipe_db =  models.Recipe(name = recipe.name, required_potions = potions, required_flowers = flowers)
    db.add(recipe_db)
    db.commit()
    return {"message": "New recipe added!"}


@app.get("/flowers", response_model=List[schemas.Flower])
async def get_all_flowers(db: Session = Depends(get_db)):
    """Get all flowers"""
    flowers = db.query(models.Flower).all()
    return flowers
@app.post("/flowers/add")
async def add_flower(color_id: str, db: Session = Depends(get_db)):
    """Add a new flower"""

    flower_db = db.query(models.Flower).filter(models.Flower.color_id == color_id).first()
    if flower_db:
        raise HTTPException(status_code=404, detail="Flower already exists")
    flower_db =  models.Flower(color_id = color_id)
    db.add(flower_db)
    db.commit()
    return {"message": "New flower added!"}


""" Probably unnecessary
@app.get("/potions/{potion_id}", response_model=schemas.PotionBase)
async def get_potion(potion_id: int, db: Session = Depends(get_db)):
    #Get information about potion
    db_recipe = db.query(models.Recipe).filter(models.Recipe.id == potion_id).first()
    if not db_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return db_recipe

@app.get("/potions", response_model=List[schemas.PotionBase])
async def get_all_potions(db: Session = Depends(get_db)):
    recipes = db.query(models.Recipe).all()
    return recipes

"""


#for debug only
@app.post("/debug/reset")
def reset(db: Session = Depends(get_db)):
    """Reset db to initial state"""
    seed_data.reset_and_seed_call()
    return {"message": "Done!"}
#get all sessions (for debugging)
@app.get("/debug/sessions", response_model=List[schemas.DebugSessionInfo])
def get_all_sessions(db: Session = Depends(get_db)):
    """Get all sessions"""
    sessions = db.query(models.Session).all()
    return sessions

#clean sessions (based on creation_time)

@app.post("/debug/clearStaleSessions")
def clear_stale_sessions(db: Session = Depends(get_db)):
    """Remove old sessions"""
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