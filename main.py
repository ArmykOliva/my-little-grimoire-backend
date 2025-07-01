from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
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
import base64
import openai
import os
from olingo_llm_parser import parse_template_and_schema

from schemas import DecorationUsed

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="My Little Grimoire API", version="1.0.0")

# Sample endpoints based on the diagram

@app.get("/")
async def root():
    return {"message": "Welcome to My Little Grimoire API"}

#login endpoints
@app.post("/register", response_model=schemas.Player)
async def register_player(reg_data: schemas.PlayerRegister, db: Session = Depends(get_db)):
    existing = db.query(models.PlayerAccount).filter(models.PlayerAccount.user_name == reg_data.user_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken.")

    # Create Player
    new_player = models.Player()
    db.add(new_player)
    db.flush()  #

    # Create Account
    account = models.PlayerAccount(
        user_name=reg_data.user_name,
        password_hash=utils.hash_password(reg_data.password),
        player_id=new_player.id
    )
    db.add(account)
    db.commit()

    db_grimoire = models.Grimoire(player=new_player)
    db.add(db_grimoire)
    db.commit()
    db.refresh(new_player)
    return new_player

@app.post("/login", response_model=schemas.Player)
async def login_player(login_data: schemas.PlayerLogin, db: Session = Depends(get_db)):
    account = db.query(models.PlayerAccount).filter(models.PlayerAccount.user_name == login_data.user_name).first()
    if not account or not utils.verify_password(login_data.password, account.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    player = db.query(models.Player).filter(models.Player.id == account.player_id).first()
    return player

# Playerendpoints
@app.get("/players", response_model=List[schemas.Player])
async def get_all_players(db: Session = Depends(get_db)):
    players = db.query(models.Player).all()
    return players
@app.post("/players/create_noAcc", response_model=schemas.Player)
async def create_player_noAcc(player: schemas.PlayerCreate, db: Session = Depends(get_db)):
    """Create a new player with their grimoire. Created without link to account"""

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

@app.post("/players/{player_id}/updateData", response_model=schemas.Player)
async def update_player_data(player_id: uuid.UUID, player_data: schemas.PlayerBase, db: Session = Depends(get_db)):
    """Use this when just registered or if player changes his data"""
    db_player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not db_player:
        raise HTTPException(status_code=404, detail="Player not found.")

    if player_data.name:
        db_player.name = player_data.name
    if player_data.picture is not None:
        db_player.profile_picture = player_data.picture

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
#update location
@app.put("/players/{player_id}/session/update_loc", response_model=schemas.SessionInfo)
def update_loc_session(player_id: uuid.UUID, data: schemas.PlayerLocation, db: Session = Depends(get_db)):
    player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    if not player.session_id:
        raise HTTPException(status_code=400, detail="Player not in a session")
    session = db.query(models.Session).filter(models.Session.session_id == player.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if player_id != session.initial_player:
        raise HTTPException(status_code=400, detail="Player is not initial player in this session")
    session.initial_lat = data.initial_lat
    session.initial_lng = data.initial_lng
    db.commit()
    db.refresh(session)
    return schemas.SessionInfo(
        recipe_id=session.recipe_id,
        flower_id=player.assigned_flower,
        code=session.code,
        initial_player=session.initial_player,
        flowers_collected=[f.id for f in session.flowers_collected],
        players=[schemas.PlayerSessionInfo(player_id=p.player_id, name=p.name, assigned_flower=p.assigned_flower,
                                           picture=p.profile_picture) for p in session.players],
        status=session.status
    )

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
    available_flowers = list({flower.id for flower in recipe.required_flowers})

    if not available_flowers:
        raise HTTPException(status_code=400, detail="No available colors in recipe")

    assigned_flower = available_flowers.pop(0)

    join_code = utils.generate_code()

    while db.query(models.Session).filter_by(code=join_code).first():
        join_code = utils.generate_code()
    status = 0

    #change status to collecting
    if not available_flowers:
        status = 1

    new_session = models.Session(
        recipe_id=data.recipe_id,
        code=join_code,
        flowers_available=available_flowers,
        initial_lat=data.initial_lat,
        initial_lng=data.initial_lng,
        initial_player = data.player_id,
        status = status
    )
    db.add(new_session)
    db.flush()

    player.session_id = new_session.session_id
    player.assigned_flower = assigned_flower
    db.commit()

    return schemas.SessionInfo(
        recipe_id = data.recipe_id,
        flower_id=assigned_flower,
        code=join_code,
        flowers_collected = [],
        initial_player = new_session.initial_player,
        players = [schemas.PlayerSessionInfo(player_id = p.player_id, name = p.name, assigned_flower=p.assigned_flower, picture = p.profile_picture)  for p in new_session.players],
        status = new_session.status
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
    if session.status == 1 or session.status == 2:
        raise HTTPException(status_code=400, detail="Session already in collecting or brewing stage")
    #ambiguous
    if not session.flowers_available:
        raise HTTPException(status_code=400, detail="No flowers available")
    #TODO: what if players moved? Should we always update with position of first player or let it be like that?
    if not utils.is_within_distance(data.lat, data.lng, session.initial_lat, session.initial_lng):
        raise HTTPException(status_code=400, detail="Too far from session")



    assigned_flower = session.flowers_available[0]
    session.flowers_available = session.flowers_available[1:]
    player.session_id = session.session_id
    player.assigned_flower = assigned_flower


    #change to collecting
    if not session.flowers_available:
        session.status = 1
    db.commit()
    db.refresh(session)

    return schemas.SessionInfo(
        recipe_id=session.recipe_id,
        flower_id=assigned_flower,
        initial_player = session.initial_player,
        code=session.code,
        flowers_collected=[f.id for f in session.flowers_collected],
        players=[schemas.PlayerSessionInfo(player_id=p.player_id, name=p.name, assigned_flower=p.assigned_flower,
                                           picture=p.profile_picture) for p in session.players],
        status=session.status
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
    if player.assigned_flower:
        session.flowers_available.append(player.assigned_flower)

    player.session_id = None
    player.assigned_flower = None
    db.commit()
    remaining_players = session.players
    if not remaining_players:
        db.delete(session)
        db.commit()
        return {"message": "Left session successfully"}
    #if initial player leaves during collection, stop session
    if session.initial_player == player.player_id and (session.status == 0 or session.status == 1):
        db.delete(session)
        db.commit()
        return {"message": "Left session successfully. It was initial player, so the session was deleted"}
    if session.status == 1:
        session.status = 0
        db.commit()
        return {"message": "Player left. Other player will return to lobby"}
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

    if session.status == 0:
        raise HTTPException(status_code=400, detail="Waiting for other players")

    if session.status == 2:
        raise HTTPException(status_code=400, detail="Session already in brewing stage")

    flower = db.query(models.Flower).filter(models.Flower.id == flower_id).first()
    if not flower:
        raise HTTPException(status_code=404, detail="Flower not found")

    # Check if flower color matches player's shears
    if flower_id != player.assigned_flower:
        raise HTTPException(status_code=400, detail="You cannot collect this flower!")

    # Add flower to session's collected flowers
    recipe = db.query(models.Recipe).get(session.recipe_id)
    recipe_flower_ids = {f.id for f in recipe.required_flowers}

    if flower_id not in recipe_flower_ids:
        raise HTTPException(status_code=400, detail="This flower is not required for the recipe")

    session.flowers_collected.append(flower)

    # Check if recipe requirements are met
    recipe = session.recipe
    required_ids = {f.id for f in recipe.required_flowers}
    collected_ids = {f.id for f in session.flowers_collected}
    if required_ids.issubset(collected_ids):
        session.status = 2  # Complete
        for potion in [p.id for p in recipe.required_potions]:
            remove_potion_from_inventory_func(session.initial_player,potion, db)

    db.commit()
    db.refresh(session)
    return schemas.SessionInfo(
        recipe_id=session.recipe_id,
        flower_id=player.assigned_flower,
        code=session.code,
        initial_player=session.initial_player,
        flowers_collected=[f.id for f in session.flowers_collected],
        players=[schemas.PlayerSessionInfo(player_id=p.player_id, name=p.name, assigned_flower=p.assigned_flower,
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
        flower_id=player.assigned_flower,
        code=session.code,
        initial_player = session.initial_player,
        flowers_collected=[f.id for f in session.flowers_collected],
        players=[schemas.PlayerSessionInfo(player_id=p.player_id, name=p.name, assigned_flower=p.assigned_flower,
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
async def add_flower(color_id: str, name:str, db: Session = Depends(get_db)):
    """Add a new flower"""

    flower_db = db.query(models.Flower).filter(models.Flower.color_id == color_id).first()
    if flower_db:
        raise HTTPException(status_code=404, detail="Flower with this color already exists")
    flower_db =  models.Flower(color_id = color_id, name = name)
    db.add(flower_db)
    db.commit()
    return {"message": "New flower added!"}

@app.post("/flowers/identify", response_model=schemas.FlowerIdentificationResponse)
async def identify_flower(image: UploadFile = File(...), db: Session = Depends(get_db)):
    """Identify flower color from an uploaded image using AI vision"""

    # Validate that the uploaded file is an image
    if not image.content_type or not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        # Read the image file
        image_bytes = await image.read()

        # Convert image to base64 for OpenAI API
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')

        # Get valid colors dynamically from the database
        flowers = db.query(models.Flower).all()
        valid_colors = list(set(flower.color_id for flower in flowers))

        if not valid_colors:
            raise HTTPException(status_code=500, detail="No flower colors found in database")

        # Parse template and schema
        messages, response_format = parse_template_and_schema(
            template="flower_identification_prompt.jinja",
            schema="flower_identification_schema.json",
            variables={"valid_colors": valid_colors}
        )

        # Add the image to the user message
        user_message = messages[-1]  # Last message should be the user message
        user_message["content"] = [
            {
                "type": "text",
                "text": user_message["content"]
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{image.content_type};base64,{image_base64}"
                }
            }
        ]

        # Get OpenAI API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("!!!!!!!!!!!!!!!!OpenAI API key not configured")
            return schemas.FlowerIdentificationResponse(
                color_id="red"
            )

        # Initialize OpenAI client
        client = openai.OpenAI(api_key=api_key)

        # Call OpenAI API with vision capabilities
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            response_format=response_format,
            max_tokens=300
        )

        # Parse the response
        result = response.choices[0].message.content

        # The response should be JSON thanks to the structured output
        import json
        parsed_result = json.loads(result)

        if parsed_result.get("error") and parsed_result.get("error") != "":
            raise HTTPException(status_code=400, detail=parsed_result.get("error"))

        return schemas.FlowerIdentificationResponse(
            color_id=parsed_result.get("color_id")
        )

    except openai.APIError as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


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