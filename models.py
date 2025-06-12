import random

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime, Text, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from database import Base
import uuid
from datetime import datetime

#define many-to-many relationship
grimoire_recipes = Table(
    "grimoire_recipes",
    Base.metadata,
    Column("grimoire_id", ForeignKey("grimoires.id"), primary_key=True),
    Column("recipe_id", ForeignKey("recipes.id"), primary_key=True)
)

def random_name():
    return random.choice(["Alex", "Krystof", "Ben", "Maxi", "Heloisa"])

class Player(Base):
    __tablename__ = "players"

    # Player info
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True, nullable=False)
    name = Column(String, default=lambda: random_name())

    #We will use some pre-defined pictures
    profile_picture = Column(Integer, default=0)

    # Player stats
    money = Column(Integer, default=0)

    """ Other values to consider
    level = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    """
    # Relationships
    #sessions = relationship("Session", back_populates="player", uselist=False)
    inventory_items = relationship("InventoryItem", back_populates="player", cascade="all, delete-orphan")
    grimoire = relationship("Grimoire", back_populates="player", uselist=False, cascade="all, delete-orphan")

class Grimoire(Base):
    __tablename__ = "grimoires"
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.player_id"), unique=True)

    # Relationships
    unlocked_recipes = relationship("Recipe", secondary=grimoire_recipes)
    player = relationship("Player", back_populates="grimoire", uselist=False)

class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True, index=True)
    potion_name = Column(String, nullable=False)
    potion_picture = Column(String, default="default_potion.png")
    #TODO
    #Question: do we want to have two separate lists for flowers + potions that are needed?
    #What do we do, when the player doesn't have all potions for recipe? Should he have them in advance before staring this new recipe?
    #My idea would be: player goes with recipe to the ministry box, and it automatically gets the potions needed from inventory
    #Therefore we have 2 lists: one for flowers and one for potions
    recipe_data = Column(Text)  # JSON string of recipe components

    # TODO: suggestion
    # Rather than defining how to craft potion in DB, randomise it in Unity
    # Otherwise I would define like 3-4 sequences -> every potion has one of them defined

    """ Other values to consider
        difficulty_level = Column(Integer, default=1)
        created_at = Column(DateTime, default=datetime.utcnow)
    """


class InventoryItem(Base):
    __tablename__ = "inventory_items"
    id = Column(Integer, primary_key=True, index=True)

    player_id = Column(UUID(as_uuid=True), ForeignKey("players.player_id"), nullable=False)
    potion_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    amount = Column(Integer, nullable=False, default=0)

    player = relationship("Player", back_populates="inventory_items")
    potion = relationship("Recipe")


class Flower(Base):
    __tablename__ = "flowers"

    id = Column(Integer, primary_key=True, index=True)

    #TODO: string or int ids?
    color_id = Column(String, nullable=False)  # Unity color identifier
    flower_name = Column(String, nullable=False)

    # TODO: Add flower properties, effects, spawn locations, etc.
    flower_rarity = Column(String, default="common")
    flower_description = Column(String, default="Flower description")


# class Session(Base):
#     __tablename__ = "sessions"
#
#     id = Column(Integer, primary_key=True, index=True)
#     session_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
#     player_id = Column(Integer, ForeignKey("players.id"))
#     is_active = Column(Boolean, default=True)
#
#
#     # TODO: Add session state, progress tracking, etc.
#
#     """ Other values to consider
#         started_at = Column(DateTime, default=datetime.now)
#         ended_at = Column(DateTime, nullable=True)
#     """
#     # Relationships
#     player = relationship("Player", back_populates="sessions")
#     collected_flowers = relationship("CollectedFlower", back_populates="session")
#     session_recipes = relationship("SessionRecipe", back_populates="session")


#
# class CollectedFlower(Base):
#     __tablename__ = "collected_flowers"
#
#     id = Column(Integer, primary_key=True, index=True)
#     session_id = Column(Integer, ForeignKey("sessions.id"))
#     flower_id = Column(Integer, ForeignKey("flowers.id"))
#     collected_at = Column(DateTime, default=datetime.utcnow)
#     quantity = Column(Integer, default=1)
#
#     # TODO: Add flower condition, preservation status, etc.
#
#     # Relationships
#     session = relationship("Session", back_populates="collected_flowers")
#     flower = relationship("Flower", back_populates="collected_instances")
#
# class SessionRecipe(Base):
#     __tablename__ = "session_recipes"
#
#     id = Column(Integer, primary_key=True, index=True)
#     session_id = Column(Integer, ForeignKey("sessions.id"))
#     recipe_id = Column(Integer, ForeignKey("recipes.id"))
#     progress = Column(Float, default=0.0)  # 0.0 to 1.0
#     is_completed = Column(Boolean, default=False)
#
#     # TODO: Add brewing steps, time remaining, success rate, etc.
#
#     # Relationships
#     session = relationship("Session", back_populates="session_recipes")
#     recipe = relationship("Recipe", back_populates="session_recipes")

