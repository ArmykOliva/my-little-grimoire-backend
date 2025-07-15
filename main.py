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
@app.post("/register", response_model=schemas.Player, tags=["Account"])
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

@app.post("/login", response_model=schemas.Player, tags=["Account"])
async def login_player(login_data: schemas.PlayerLogin, db: Session = Depends(get_db)):
    account = db.query(models.PlayerAccount).filter(models.PlayerAccount.user_name == login_data.user_name).first()
    if not account or not utils.verify_password(login_data.password, account.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    player = db.query(models.Player).filter(models.Player.id == account.player_id).first()
    return player

# Playerendpoints
@app.get("/players", response_model=List[schemas.Player], tags=["Player"])
async def get_all_players(db: Session = Depends(get_db)):
    players = db.query(models.Player).all()
    return players
@app.post("/players/create_noAcc", response_model=schemas.Player, tags = ["Debug", "Player"])
async def create_player_noAcc(player: schemas.PlayerCreate, db: Session = Depends(get_db)):
    """Create a new player with their grimoire. Created without link to account"""

    db_player = models.Player(
        name=player.name,
        profile_picture=player.profile_picture
    )
    db.add(db_player)
    db.flush()
    db_grimoire = models.Grimoire(player=db_player)
    db.add(db_grimoire)
    db.commit()
    db.refresh(db_player)
    return db_player

@app.post("/players/{player_id}/updateData", response_model=schemas.Player, tags = ["Player"])
async def update_player_data(player_id: uuid.UUID, player_data: schemas.PlayerBase, db: Session = Depends(get_db)):
    """Use this when just registered or if player changes his data"""
    db_player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not db_player:
        raise HTTPException(status_code=404, detail="Player not found.")

    if player_data.name:
        db_player.name = player_data.name
    db_player.profile_picture = player_data.profile_picture

    db.commit()
    db.refresh(db_player)
    return db_player
@app.get("/players/{player_id}", response_model=schemas.Player, tags = ["Player"])
async def get_player(player_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get player by UUID"""
    db_player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not db_player:
        raise HTTPException(status_code=404, detail="Player not found")
    return db_player


@app.post("/players/{player_id}/follow/{followed_id}", tags = ["Followers"])
async def follow_player(player_id: uuid.UUID, followed_id: uuid.UUID, db: Session = Depends(get_db)):

    if player_id == followed_id:
        raise HTTPException(status_code=404, detail="Cannot follow yourself")
    follower = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    followed = db.query(models.Player).filter(models.Player.player_id ==followed_id).first()

    if not follower or not followed:
        raise HTTPException(status_code=404, detail="Player(s) not found")

    existing = db.query(models.PlayerFollower).filter_by(
        follower_id=follower.id,
        followed_id=followed.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already following this player")

    follow = models.PlayerFollower(
        follower_id=follower.id,
        followed_id=followed.id
    )
    db.add(follow)
    db.commit()
    return {"message": "Followed successfully"}


@app.post("/players/{player_id}/unfollow/{followed_id}", tags = ["Followers"])
async def unfollow_player(player_id: uuid.UUID, followed_id: uuid.UUID, db: Session = Depends(get_db)):
    follower = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    followed = db.query(models.Player).filter(models.Player.player_id == followed_id).first()

    if not follower or not followed:
        raise HTTPException(status_code=404, detail="Player(s) not found")

    deleted = db.query(models.PlayerFollower).filter_by(
        follower_id=follower.id,
        followed_id=followed.id
    ).delete()

    if not deleted:
        raise HTTPException(status_code=400, detail="Not following this player")

    db.commit()
    return {"message": "Unfollowed successfully"}

@app.get("/players/{player_id}/followers", response_model=List[schemas.Player], tags = ["Followers"])
async def get_followers(player_id: uuid.UUID, db: Session = Depends(get_db)):
    player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    followers = (
        db.query(models.Player)
        .join(models.PlayerFollower, models.Player.id == models.PlayerFollower.follower_id)
        .filter(models.PlayerFollower.followed_id == player.id)
        .all()
    )
    return followers

@app.get("/players/{player_id}/following", response_model=List[schemas.Player], tags = ["Followers"])
async def get_following(player_id: uuid.UUID, db: Session = Depends(get_db)):
    player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    following = (
        db.query(models.Player)
        .join(models.PlayerFollower, models.Player.id == models.PlayerFollower.followed_id)
        .filter(models.PlayerFollower.follower_id == player.id)
        .all()
    )
    return following

#Customers
@app.put("/players/{player_id}/customer/{customer_id}", response_model=schemas.Player, tags = ["Customers"])
async def set_customer_id(player_id: uuid.UUID, customer_id: int, db: Session = Depends(get_db)):
    player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    player.customer_id = customer_id
    db.commit()
    db.refresh(player)
    return player

@app.post("/players/{player_id}/customer_post/{customer_id}", response_model=schemas.Player, tags = ["Customers", "Debug"])
async def set_customer_id_post(player_id: uuid.UUID, customer_id: int, db: Session = Depends(get_db)):
    player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    player.customer_id = customer_id
    db.commit()
    db.refresh(player)
    return player

#Money
@app.post("/players/{player_id}/money/change", response_model=int, tags = ["Money"])
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

def _format_grimoire(grimoire: models.Grimoire, db: Session) -> schemas.Grimoire:
    """Format grimoire"""
    return schemas.Grimoire(unlocked_recipes=[r.id for r in grimoire.unlocked_recipes])

@app.get("/players/{player_id}/grimoire", response_model=schemas.Grimoire, tags = ["Grimoire"])
async def get_player_grimoire(player_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get player's grimoire"""
    db_grimoire = db.query(models.Grimoire).filter(models.Grimoire.player_id == player_id).first()
    if not db_grimoire:
        raise HTTPException(status_code=404, detail="Grimoire not found")
    return _format_grimoire(db_grimoire, db)


@app.post("/players/{player_id}/grimoire/unlock/{recipe_id}", response_model=schemas.Grimoire, tags = ["Grimoire"])
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
    return _format_grimoire(db_grimoire, db)

#TODO: maybe change to remove
@app.post("/players/{player_id}/grimoire/lock/{recipe_id}", response_model=schemas.Grimoire, tags = ["Grimoire"])
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
        return _format_grimoire(db_grimoire, db)

    else:
        raise HTTPException(status_code=404, detail="Recipe has not been unlocked yet")


def _format_inventory(inventory_items: List[models.InventoryItem], db: Session) -> schemas.Inventory:
    """Format inventory"""
    return schemas.Inventory(potions = [schemas.InventoryItem(potion_id = item.potion_id, amount=item.amount)
                for item in inventory_items
                ])


# Inventory
@app.get("/players/{player_id}/inventory", response_model=schemas.Inventory, tags = ["Inventory"])
async def get_inventory(player_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get player's recipe by his UUID"""
    player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    return _format_inventory(player.inventory_items, db)


@app.post("/players/{player_id}/inventory/add/{potion_id}", response_model=schemas.Inventory, tags = ["Inventory"])
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
    return _format_inventory(player.inventory_items, db)


#TODO: maybe choose from psot to remove (-> notify Maxi later)
@app.post("/players/{player_id}/inventory/remove/{potion_id}", response_model=schemas.Inventory, tags = ["Inventory"])
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
    return _format_inventory(player.inventory_items, db)


#TODO: ideally merge into previous
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

def _format_decorations(inventory_decorations: List[models.DecorationPlayer], db: Session) -> schemas.DecorationInventory:
    """Format decorations"""
    return schemas.DecorationInventory(decorations = [schemas.DecorationPlayer(used = d.used, position = d.position, decoration_id = d.decoration_id) for d in inventory_decorations])

@app.post("/players/{player_id}/decorations/buy/{decoration_id}", response_model=schemas.DecorationInventory, tags = ["Decorations"])
async def buy_decoration(player_id: uuid.UUID, decoration_id: int, db: Session = Depends(get_db)):
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

    return _format_decorations (player.decorations, db)


#Get decorations
@app.get("/players/{player_id}/decorations", response_model=schemas.DecorationInventory, tags = ["Decorations"])
async def get_player_decorations(player_id: uuid.UUID, db: Session = Depends(get_db)):
    player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return _format_decorations (player.decorations, db)

@app.post("/players/{player_id}/decorations/place/{decoration_id}", response_model=schemas.DecorationInventory, tags = ["Decorations"])
async def place_decoration(player_id: uuid.UUID, decoration_id: int, position: int, db: Session = Depends(get_db)):
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
    if position < 0 or not (decoration.allowed_position & (1 << position)):
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
    return _format_decorations (player.decorations, db)

@app.post("/players/{player_id}/decorations/unplace/{decoration_id}", response_model=schemas.DecorationInventory, tags = ["Decorations"])
async def unplace_decoration(player_id: uuid.UUID, decoration_id: int, db: Session = Depends(get_db)):
    # Get player
    player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Check if player owns the decoration
    decoration_player = db.query(models.DecorationPlayer).filter_by(player_id=player_id, decoration_id=decoration_id
    ).first()

    if not decoration_player:
        raise HTTPException(status_code=404, detail="Player does not own this decoration")

    # Check if it is placed
    if not decoration_player.used:
        raise HTTPException(status_code=400, detail="Decoration is not placed")

    # Unplace it
    decoration_player.used = False
    decoration_player.position = None
    db.commit()

    return _format_decorations(player.decorations, db)
@app.get("/players/{player_id}/decorations/used", response_model=List[schemas.DecorationUsed], tags = ["Decorations"])
async def get_used_decorations(player_id: uuid.UUID, db: Session = Depends(get_db)):
    player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    used_decorations = db.query(models.DecorationPlayer).filter(
        models.DecorationPlayer.player_id == player_id,
        models.DecorationPlayer.used == True
    ).all()

    return [schemas.DecorationUsed(decoration_id = d.decoration_id, position = d.position) for d in used_decorations]



def _format_player_session_info(players: List[models.Player], db: Session) -> List[schemas.PlayerSessionInfo]:
    """Format player session info"""
    return [schemas.PlayerSessionInfo(player_id=p.player_id, name=p.name, assigned_flower=p.assigned_flower,
                                           profile_picture=p.profile_picture) for p in players]

def _format_flowers(flowers: List[models.Flower], db: Session) -> List[int]:
    """Format flower to return id only"""
    return [f.id for f in flowers]
def _format_session_info(session: models.Session, flower: int, db: Session) -> schemas.SessionInfo:
    """Format session info"""
    return schemas.SessionInfo(
        recipe_id=session.recipe_id,
        flower_id=flower,
        code=session.code,
        initial_player=session.initial_player,
        flowers_collected=_format_flowers(session.flowers_collected, db),
        players=_format_player_session_info(session.players, db),
        status=session.status
    )

"""Sessions"""
#update location
@app.put("/players/{player_id}/session/update_loc", response_model=schemas.SessionInfo, tags = ["Session"])
async def update_loc_session(player_id: uuid.UUID, data: schemas.PlayerLocation, db: Session = Depends(get_db)):
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
    return _format_session_info(session, player.assigned_flower, db)

@app.post("/players/{player_id}/session/update_loc_post", response_model=schemas.SessionInfo, tags = ["Session"])
async def update_loc_session_post(player_id: uuid.UUID, data: schemas.PlayerLocation, db: Session = Depends(get_db)):
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
    return _format_session_info(session, player.assigned_flower, db)

#create session
@app.post("/session/create", response_model=schemas.SessionInfo, tags = ["Session"])
async def create_session(data: schemas.SessionCreate, db: Session = Depends(get_db)):
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

    # #change status to collecting
    # if not available_flowers:
    #     status = 1

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

    return _format_session_info(new_session, assigned_flower, db)


#start session
@app.post("/players/{player_id}/session/start", response_model=schemas.SessionInfo, tags = ["Session"])
async def start_session(player_id: uuid.UUID, db: Session = Depends(get_db)):
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
    if session.status !=0:
        raise HTTPException(status_code=400, detail="Session already started")
    if not session.flowers_available:
        session.status = 1
    else:
        raise HTTPException(status_code=400, detail="Not enough players")
    db.commit()
    db.refresh(session)
    return _format_session_info(session, player.assigned_flower, db)

#Join session
@app.post("/session/join", response_model=schemas.SessionInfo, tags = ["Session"])
async def join_session(data: schemas.SessionJoin, db: Session = Depends(get_db)):
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

    if not utils.is_within_distance(data.lat, data.lng, session.initial_lat, session.initial_lng):
        raise HTTPException(status_code=400, detail="Too far from session")



    assigned_flower = session.flowers_available[0]
    session.flowers_available = session.flowers_available[1:]
    player.session_id = session.session_id
    player.assigned_flower = assigned_flower


    # #change to collecting
    # if not session.flowers_available:
    #     session.status = 1
    db.commit()
    db.refresh(session)

    return _format_session_info(session, assigned_flower, db)


#Leave all sessions
@app.post("/players/{player_id}/leaveSession", tags = ["Session"])
async def leave_session(player_id: uuid.UUID, db: Session = Depends(get_db)):
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


@app.post("/players/{player_id}/session/collect_flower", response_model=Optional[schemas.SessionInfo], tags = ["Session"])
async def collect_flower(player_id: uuid.UUID, image: UploadFile = File(...), db: Session = Depends(get_db)):
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

    flower_response = await identify_flower(image, db)

    if flower_response.error:
        raise HTTPException(status_code=404, detail=flower_response.error)

    flower = db.query(models.Flower).filter(models.Flower.color_id == flower_response.color_id).first()

    if not flower:
        raise HTTPException(status_code=404, detail="Flower not found")

    # Check if flower color matches player's shears
    if flower.id != player.assigned_flower:
        raise HTTPException(status_code=400, detail="You cannot collect this flower!")

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
        session.status = 2  # Complete
        for potion in [p.id for p in recipe.required_potions]:
            remove_potion_from_inventory_func(session.initial_player,potion, db)

    db.commit()
    db.refresh(session)
    return _format_session_info(session, player.assigned_flower, db)

async def identify_flower(image:UploadFile, db:Session):
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

@app.get("/players/{player_id}/session/info", response_model=Optional[schemas.SessionInfo], tags = ["Session"])
async def session_info(player_id: uuid.UUID, db: Session = Depends(get_db)):
    """Info about a current session"""
    player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not player or not player.session_id:
        raise HTTPException(status_code=404, detail="Player not in a session")

    # get session
    session = db.query(models.Session).filter(models.Session.session_id == player.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return _format_session_info(session, player.assigned_flower, db)


#Overall
@app.get("/decorations", response_model=List[schemas.DecorationShop], tags = ["Decorations"])
async def get_all_decorations(db: Session = Depends(get_db)):
    """Get info about all decorations"""
    return db.query(models.Decoration).all()

@app.post("/decorations/add", tags = ["Decorations"])
async def add_decoration(decoration: schemas.DecorationCreate, db: Session = Depends(get_db)):
    """Add a new decoration"""

    decoration_db = db.query(models.Decoration).filter(models.Decoration.name == decoration.name).first()
    if decoration_db:
        raise HTTPException(status_code=404, detail="Decoration already exists")
    decoration_db =  models.Decoration(name = decoration.name, cost = decoration.cost, allowed_position = decoration.allowed_position)
    db.add(decoration_db)
    db.commit()
    return {"message": "New decoration added!"}

def _format_recipe_id(recipes: List[models.Recipe], db: Session) -> List[int]:
    """Format recipe to return id only"""
    return [r.id for r in recipes]

def _format_recipe (r: models.Recipe, db: Session) -> schemas.Recipe:
    """Format recipes to return id only"""
    return schemas.Recipe(name=r.name, required_flowers=_format_flowers(r.required_flowers, db),
                          required_potions=_format_recipe_id(r.required_potions, db), id=r.id)
def _format_recipes(recipes: List[models.Recipe], db: Session) -> List[schemas.Recipe]:
    """Format recipe info to return id only"""
    return [_format_recipe(r, db) for r in recipes]
@app.get("/recipes", response_model=List[schemas.Recipe], tags = ["Recipe"])
async def get_all_recipes(db: Session = Depends(get_db)):
    """Get all recipes"""
    recipes = db.query(models.Recipe).all()
    return _format_recipes(recipes, db)

@app.get("/recipes/{recipe_id}", response_model=schemas.Recipe, tags = ["Recipe"])
async def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    """Get information about recipe"""
    db_recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if not db_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return _format_recipe(db_recipe, db)

@app.post("/recipes/add", tags = ["Recipe"])
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


@app.get("/flowers", response_model=List[schemas.Flower], tags = ["Flower"])
async def get_all_flowers(db: Session = Depends(get_db)):
    """Get all flowers"""
    flowers = db.query(models.Flower).all()
    return flowers
@app.post("/flowers/add", tags = ["Flower"])
async def add_flower(color_id: str, name:str, db: Session = Depends(get_db)):
    """Add a new flower"""

    flower_db = db.query(models.Flower).filter(models.Flower.color_id == color_id).first()
    if flower_db:
        raise HTTPException(status_code=404, detail="Flower with this color already exists")
    flower_db =  models.Flower(color_id = color_id, name = name)
    db.add(flower_db)
    db.commit()
    return {"message": "New flower added!"}


# Trading System - Simple Buy/Sell Marketplace

@app.post("/trading/create", response_model=schemas.TradeResponse, tags=["Trading"])
async def create_sale(trade: schemas.TradeCreate, seller_id: uuid.UUID, db: Session = Depends(get_db)):
    """Create a sale listing - put a potion up for sale at a fixed price"""
    
    # Verify seller exists
    seller = db.query(models.Player).filter(models.Player.player_id == seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    
    # Verify seller has the item to sell
    inventory_item = db.query(models.InventoryItem).filter_by(
        player_id=seller_id, 
        potion_id=trade.item_id
    ).first()
    if not inventory_item or inventory_item.amount < trade.item_amount:
        raise HTTPException(status_code=400, detail="Insufficient items in inventory")
    
    # Verify the potion exists
    potion = db.query(models.Recipe).filter(models.Recipe.id == trade.item_id).first()
    if not potion:
        raise HTTPException(status_code=404, detail="Potion not found")
    
    # Create the sale listing
    new_trade = models.Trade(
        seller_id=seller_id,
        item_id=trade.item_id,
        item_amount=trade.item_amount,
        price=trade.price
    )
    db.add(new_trade)
    db.commit()
    db.refresh(new_trade)
    
    return _format_trade_response(new_trade, db)


@app.get("/trading/board", response_model=schemas.TradeBoardResponse, tags=["Trading"])
async def get_trading_board(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Get all available items for sale"""
    
    trades = db.query(models.Trade).filter(
        models.Trade.status == "available"
    ).offset(skip).limit(limit).all()
    
    total_count = db.query(models.Trade).filter(
        models.Trade.status == "available"
    ).count()
    
    trade_responses = [_format_trade_response(trade, db) for trade in trades]
    
    return schemas.TradeBoardResponse(
        trades=trade_responses,
        total_count=total_count
    )


@app.post("/trading/{trade_id}/buy", response_model=schemas.TradeResponse, tags=["Trading"])
async def buy_item(trade_id: int, buyer_id: uuid.UUID, db: Session = Depends(get_db)):
    """Buy an item from a sale listing"""
    
    # Get the trade
    trade = db.query(models.Trade).filter(models.Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    if trade.status != "available":
        raise HTTPException(status_code=400, detail="Item is no longer available")
    
    # Verify buyer exists and is not the seller
    buyer = db.query(models.Player).filter(models.Player.player_id == buyer_id).first()
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    
    if buyer_id == trade.seller_id:
        raise HTTPException(status_code=400, detail="Cannot buy your own item")
    
    # Verify buyer has enough money
    if buyer.money < trade.price:
        raise HTTPException(status_code=400, detail="Insufficient money")
    
    # Verify seller still has the item
    seller_inventory = db.query(models.InventoryItem).filter_by(
        player_id=trade.seller_id,
        potion_id=trade.item_id
    ).first()
    if not seller_inventory or seller_inventory.amount < trade.item_amount:
        raise HTTPException(status_code=400, detail="Seller no longer has the item")
    
    # Execute the trade
    seller = trade.seller
    
    # Transfer money
    buyer.money -= trade.price
    seller.money += trade.price
    
    # Transfer the item from seller to buyer
    if seller_inventory.amount > trade.item_amount:
        seller_inventory.amount -= trade.item_amount
    else:
        db.delete(seller_inventory)
    
    # Add item to buyer
    buyer_item = db.query(models.InventoryItem).filter_by(
        player_id=buyer_id,
        potion_id=trade.item_id
    ).first()
    
    if buyer_item:
        buyer_item.amount += trade.item_amount
    else:
        new_item = models.InventoryItem(
            player_id=buyer_id,
            potion_id=trade.item_id,
            amount=trade.item_amount
        )
        db.add(new_item)
    
    # Mark trade as sold
    trade.status = "sold"
    
    db.commit()
    db.refresh(trade)
    
    return _format_trade_response(trade, db)


@app.delete("/trading/{trade_id}/cancel", tags=["Trading"])
async def cancel_sale(trade_id: int, seller_id: uuid.UUID, db: Session = Depends(get_db)):
    """Cancel a sale listing (only the seller can cancel)"""
    
    trade = db.query(models.Trade).filter(models.Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    if trade.seller_id != seller_id:
        raise HTTPException(status_code=403, detail="Only the seller can cancel the sale")
    
    if trade.status != "available":
        raise HTTPException(status_code=400, detail="Can only cancel available sales")
    
    trade.status = "cancelled"
    
    db.commit()
    
    return {"message": "Sale cancelled successfully"}


@app.get("/players/{player_id}/trades/selling", response_model=List[schemas.TradeResponse], tags=["Trading"])
async def get_player_sales(player_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get all sales by a player"""
    
    trades = db.query(models.Trade).filter(models.Trade.seller_id == player_id).all()
    return [_format_trade_response(trade, db) for trade in trades]


# Helper function for trading
def _format_trade_response(trade: models.Trade, db: Session) -> schemas.TradeResponse:
    """Format a trade for response"""
    
    return schemas.TradeResponse(
        id=trade.id,
        seller_id=trade.seller_id,
        seller_name=trade.seller.name,
        item_id=trade.item_id,
        item_name=trade.item.name,
        item_amount=trade.item_amount,
        price=trade.price,
        status=trade.status,
        created_at=trade.created_at
    )


#for debug only
@app.post("/debug/reset", tags = ["Debug"])
async def reset(db: Session = Depends(get_db)):
    """Reset db to initial state"""
    seed_data.reset_and_seed_call()
    return {"message": "Done!"}
#get all sessions (for debugging)
@app.get("/debug/sessions", response_model=List[schemas.DebugSessionInfo], tags = ["Debug"])
async def get_all_sessions(db: Session = Depends(get_db)):
    """Get all sessions"""
    sessions = db.query(models.Session).all()
    return sessions

#clean sessions (based on creation_time)

@app.post("/debug/clearStaleSessions", tags = ["Debug"])
async def clear_stale_sessions(db: Session = Depends(get_db)):
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

#Right now: mocked up with flower_ids
@app.post("/players/{player_id}/session/collect_flower_old/{flower_id}", response_model=Optional[schemas.SessionInfo], tags = ["Debug"])
async def collect_flower_old( flower_id: int, player_id: uuid.UUID, db: Session = Depends(get_db)):
    """Collect flower with flower_id, if identifying doesn't work"""
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
    return _format_session_info(session, player.assigned_flower, db)

@app.post("/debug/identify", tags = ["Debug"])
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