from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from database import Base
import uuid
from datetime import datetime

## These are just samples of how stuff can look like, we should definitely reevaluate and refactor them one by one.

class Player(Base):
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    money = Column(Integer, default=0)
    level = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # TODO: Add player stats, experience, etc.
    
    # Relationships
    sessions = relationship("Session", back_populates="player")
    inventory_items = relationship("InventoryItem", back_populates="player")
    grimoire = relationship("Grimoire", back_populates="player", uselist=False)

class Recipe(Base):
    __tablename__ = "recipes"
    
    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    potion_name = Column(String, nullable=False)
    recipe_data = Column(Text)  # JSON string of recipe components
    difficulty_level = Column(Integer, default=1)
    
    # TODO: Add recipe ingredients, effects, brewing time, etc.
    
    # Relationships
    session_recipes = relationship("SessionRecipe", back_populates="recipe")

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"))
    is_active = Column(Boolean, default=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    
    # TODO: Add session state, progress tracking, etc.
    
    # Relationships
    player = relationship("Player", back_populates="sessions")
    collected_flowers = relationship("CollectedFlower", back_populates="session")
    session_recipes = relationship("SessionRecipe", back_populates="session")

class Flower(Base):
    __tablename__ = "flowers"
    
    id = Column(Integer, primary_key=True, index=True)
    flower_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    color_id = Column(String, nullable=False)  # Unity color identifier
    name = Column(String, nullable=False)
    rarity = Column(String, default="common")
    
    # TODO: Add flower properties, effects, spawn locations, etc.
    
    # Relationships
    collected_instances = relationship("CollectedFlower", back_populates="flower")

class CollectedFlower(Base):
    __tablename__ = "collected_flowers"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    flower_id = Column(Integer, ForeignKey("flowers.id"))
    collected_at = Column(DateTime, default=datetime.utcnow)
    quantity = Column(Integer, default=1)
    
    # TODO: Add flower condition, preservation status, etc.
    
    # Relationships
    session = relationship("Session", back_populates="collected_flowers")
    flower = relationship("Flower", back_populates="collected_instances")

class InventoryItem(Base):
    __tablename__ = "inventory_items"
    
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"))
    item_type = Column(String, nullable=False)  # "potion", "ingredient", "tool", etc.
    item_id = Column(String, nullable=False)  # Reference to specific item
    quantity = Column(Integer, default=1)
    
    # TODO: Add item properties, durability, enchantments, etc.
    
    # Relationships
    player = relationship("Player", back_populates="inventory_items")

class Grimoire(Base):
    __tablename__ = "grimoires"
    
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), unique=True)
    live_recipe_id = Column(String, nullable=True)  # Currently active recipe
    pages_unlocked = Column(Integer, default=1)
    
    # TODO: Add discovered recipes, research progress, spell components, etc.
    
    # Relationships
    player = relationship("Player", back_populates="grimoire")

class SessionRecipe(Base):
    __tablename__ = "session_recipes"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    progress = Column(Float, default=0.0)  # 0.0 to 1.0
    is_completed = Column(Boolean, default=False)
    
    # TODO: Add brewing steps, time remaining, success rate, etc.
    
    # Relationships
    session = relationship("Session", back_populates="session_recipes")
    recipe = relationship("Recipe", back_populates="session_recipes") 