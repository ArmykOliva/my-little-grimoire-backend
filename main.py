from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models, schemas
from database import SessionLocal, engine, get_db
import uuid

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
    # TODO: Implement proper player creation logic
    db_player = models.Player(**player.dict())
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    
    # Create grimoire for the player
    # TODO: Initialize grimoire with starting recipes
    grimoire = models.Grimoire(player_id=db_player.id)
    db.add(grimoire)
    db.commit()
    
    return db_player

@app.get("/players/{player_id}", response_model=schemas.Player)
async def get_player(player_id: str, db: Session = Depends(get_db)):
    """Get player by UUID"""
    # TODO: Add proper error handling and validation
    db_player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if db_player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return db_player

# Recipe session endpoints
@app.post("/start-recipe-session")
async def start_recipe_session(player_uuid: str, recipe_name: str, db: Session = Depends(get_db)):
    """Start a new recipe session"""
    # TODO: Implement session validation and recipe lookup
    player = db.query(models.Player).filter(models.Player.player_id == player_uuid).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Check if player has an active session
    active_session = db.query(models.Session).filter(
        models.Session.player_id == player.id,
        models.Session.is_active == True
    ).first()
    
    if active_session:
        return {
            "status": "error",
            "message": "Player already has an active session",
            "session_id": str(active_session.session_id)
        }
    
    # Create new session
    # TODO: Add recipe validation and session initialization
    new_session = models.Session(player_id=player.id)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return {
        "status": "success",
        "player_id": str(player.player_id),
        "session_id": str(new_session.session_id),
        "recipe": recipe_name
    }

@app.post("/reconnect-to-session")
async def reconnect_to_session(player_uuid: str, db: Session = Depends(get_db)):
    """Reconnect player to their current session"""
    # TODO: Implement proper session reconnection logic
    player = db.query(models.Player).filter(models.Player.player_id == player_uuid).first()
    if not player:
        return {"status": "error", "message": "Player not found"}
    
    current_session = db.query(models.Session).filter(
        models.Session.player_id == player.id,
        models.Session.is_active == True
    ).first()
    
    if current_session is None:
        return {"status": "no_session", "message": "No active session found"}
    
    return {
        "status": "success",
        "session_id": str(current_session.session_id),
        "started_at": current_session.started_at.isoformat()
    }

# Plant/Flower collection endpoints
@app.post("/collect-plant")
async def collect_plant(session_id: str, flower_color: str, db: Session = Depends(get_db)):
    """Collect a plant/flower during a session"""
    # TODO: Implement proper flower collection logic with validation
    session = db.query(models.Session).filter(models.Session.session_id == session_id).first()
    if not session or not session.is_active:
        raise HTTPException(status_code=404, detail="Active session not found")
    
    # Find or create flower
    flower = db.query(models.Flower).filter(models.Flower.color_id == flower_color).first()
    if not flower:
        # TODO: Add proper flower creation with properties
        flower = models.Flower(color_id=flower_color, name=f"Flower_{flower_color}")
        db.add(flower)
        db.commit()
        db.refresh(flower)
    
    # Collect the flower
    # TODO: Add collection validation, rarity checks, etc.
    collected = models.CollectedFlower(
        session_id=session.id,
        flower_id=flower.id
    )
    db.add(collected)
    db.commit()
    
    return {
        "status": "success",
        "player_id": str(session.player.player_id),
        "flower": flower.name,
        "color": flower.color_id
    }

@app.get("/collected-flowers-in-session/{session_id}")
async def get_collected_flowers_in_session(session_id: str, db: Session = Depends(get_db)):
    """Get all flowers collected in a session"""
    # TODO: Add proper session validation and flower data formatting
    session = db.query(models.Session).filter(models.Session.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    collected_flowers = db.query(models.CollectedFlower).filter(
        models.CollectedFlower.session_id == session.id
    ).all()
    
    # TODO: Format response with flower details, quantities, etc.
    return {
        "session_id": session_id,
        "player_id": str(session.player.player_id),
        "collected_flowers": [
            {
                "flower_name": cf.flower.name,
                "color_id": cf.flower.color_id,
                "collected_at": cf.collected_at.isoformat(),
                "quantity": cf.quantity
            }
            for cf in collected_flowers
        ]
    }

@app.post("/fix-recipe-session")
async def fix_recipe_session(session_id: str, db: Session = Depends(get_db)):
    """Fix/end a recipe session"""
    # TODO: Implement session completion logic
    session = db.query(models.Session).filter(models.Session.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.is_active:
        return {
            "status": "already_ended",
            "message": "Session is already ended",
            "ended": True
        }
    
    # TODO: Add recipe completion validation, rewards calculation, etc.
    from datetime import datetime
    session.is_active = False
    session.ended_at = datetime.utcnow()
    db.commit()
    
    return {
        "status": "success",
        "ended": True,
        "session_id": session_id
    }

# Player inventory endpoints
@app.get("/players/{player_id}/inventory")
async def get_player_inventory(player_id: str, db: Session = Depends(get_db)):
    """Get player's inventory (list of potions and items)"""
    # TODO: Implement proper inventory system with item details
    player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    inventory = db.query(models.InventoryItem).filter(
        models.InventoryItem.player_id == player.id
    ).all()
    
    # TODO: Group by item type, add item descriptions, etc.
    return {
        "player_id": player_id,
        "inventory": [
            {
                "item_type": item.item_type,
                "item_id": item.item_id,
                "quantity": item.quantity
            }
            for item in inventory
        ]
    }

# Recipe endpoints
@app.get("/recipes/", response_model=List[schemas.Recipe])
async def get_recipes(db: Session = Depends(get_db)):
    """Get all available recipes"""
    # TODO: Add filtering, pagination, player-specific recipes
    recipes = db.query(models.Recipe).all()
    return recipes

@app.post("/recipes/", response_model=schemas.Recipe)
async def create_recipe(recipe: schemas.RecipeCreate, db: Session = Depends(get_db)):
    """Create a new recipe"""
    # TODO: Add recipe validation, ingredient checking, etc.
    db_recipe = models.Recipe(**recipe.dict())
    db.add(db_recipe)
    db.commit()
    db.refresh(db_recipe)
    return db_recipe

# Flower endpoints
@app.get("/flowers/", response_model=List[schemas.Flower])
async def get_flowers(db: Session = Depends(get_db)):
    """Get all available flowers"""
    # TODO: Add filtering by rarity, location, etc.
    flowers = db.query(models.Flower).all()
    return flowers

@app.post("/flowers/", response_model=schemas.Flower)
async def create_flower(flower: schemas.FlowerCreate, db: Session = Depends(get_db)):
    """Create a new flower type"""
    # TODO: Add flower validation, rarity system, etc.
    db_flower = models.Flower(**flower.dict())
    db.add(db_flower)
    db.commit()
    db.refresh(db_flower)
    return db_flower

# Health check
@app.get("/health")
async def health_check():
    """API health check"""
    return {"status": "healthy", "service": "My Little Grimoire API"} 