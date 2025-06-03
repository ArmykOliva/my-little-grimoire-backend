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
async def create_player(player: schemas.Player, db: Session = Depends(get_db)):
    """Create a new player with their grimoire"""
    
    return schemas.Player(
        player_id="123e4567-e89b-12d3-a456-426614174000",
        money=100
    )

@app.get("/players/{player_id}", response_model=schemas.Player)
async def get_player(player_id: str, db: Session = Depends(get_db)):
    """Get player by UUID"""
    return schemas.Player(
        player_id="123e4567-e89b-12d3-a456-426614174000",
        money=100
    )

@app.get("/players/{player_id}/grimoire")
async def get_player_grimoire(player_id: str, db: Session = Depends(get_db)):
    """Get player's grimoire"""
    return schemas.Grimoire(
        recipe_ids=["potion-of-health", "potion-of-strength"]
    )

# Recipe session endpoints
@app.post("/start-recipe-session")
async def start_recipe_session(player_uuid: str, recipe_id: str, db: Session = Depends(get_db)):
    """Start a new recipe session"""
    # for example recipe_name == "health_potion"
    
    return {
        "session_id": "12454567-e89b-12d3-a456-426614174000"
    }