import random

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime, Text, Table
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from database import Base
import uuid
from datetime import datetime
from sqlalchemy.types import JSON


#TODO: check cascade for all relationships

#Many-to-many table: grimoire <-> recipe
grimoire_recipes = Table(
    "grimoire_recipes",
    Base.metadata,
    Column("grimoire_id", ForeignKey("grimoires.id"), primary_key=True),
    Column("recipe_id", ForeignKey("recipes.id"), primary_key=True)
)
# Many-to-many table: recipe <-> required potions
recipe_potions = Table(
    "recipe_potions",
    Base.metadata,
    Column("recipe_id", ForeignKey("recipes.id"), primary_key=True),
    Column("potion_id", ForeignKey("recipes.id"), primary_key=True),
)

# Many-to-many table: recipe <-> required flowers
recipe_flowers = Table(
    "recipe_flowers",
    Base.metadata,
    Column("recipe_id", ForeignKey("recipes.id"), primary_key=True),
    Column("flower_id", ForeignKey("flowers.id"), primary_key=True),
)

# Many-to-many table: session <-> flowers
session_flower_association = Table(
    "session_flower_association",
    Base.metadata,
    Column("session_id", ForeignKey("sessions.session_id"), primary_key=True),
    Column("flower_id", ForeignKey("flowers.id"), primary_key=True),
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
    money = Column(Integer, default=100)

    """ Other values to consider
    level = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    """

    #session
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.session_id", ondelete="SET NULL"), nullable=True)
    shears_color = Column(String, nullable=True)

    #TODO: either state on client-side or here
    #idea: potions etc. are removed on client-side, but we could pre-safe recipe
    #other option: add potion to player's inventory even before crafting
    # Relationships
    session = relationship("Session", back_populates="players", uselist=False,  passive_deletes=True)
    inventory_items = relationship("InventoryItem", back_populates="player", cascade="all, delete-orphan")
    grimoire = relationship("Grimoire", back_populates="player", uselist=False, cascade="all, delete-orphan")
    decorations = relationship("DecorationPlayer", back_populates="player", cascade="all, delete-orphan")

class Grimoire(Base):
    __tablename__ = "grimoires"
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.player_id"), unique=True)

    # Relationships
    unlocked_recipes = relationship("Recipe", secondary=grimoire_recipes)
    player = relationship("Player", back_populates="grimoire", uselist=False)


#TODO: amount of flowers for recipe?
# (Do we actually need that, because player can just collect the same flower at the same spot, no gameplay difference)
class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True, index=True)
    potion_name = Column(String, nullable=False)

    required_potions = relationship(
        "Recipe",
        secondary=recipe_potions,
        primaryjoin=id == recipe_potions.c.recipe_id,
        secondaryjoin=id == recipe_potions.c.potion_id,
        foreign_keys=[recipe_potions.c.recipe_id, recipe_potions.c.potion_id],
        lazy="joined"
    )
    required_flowers = relationship("Flower", secondary=recipe_flowers)

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
    color_id = Column(String, nullable=False, default = "red")  # Unity color identifier
    flower_name = Column(String, nullable=False, default = "FlowerName")
    flower_rarity = Column(String, default="common")
    flower_description = Column(String, default="Flower description")
    # TODO: Add effects, spawn locations, etc. (if needed), if needed - what potions it can be used for

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    session_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    status = Column(Integer, default=0)  # 0 = in progress, 1 = ended
    code = Column(String(5), unique=True, nullable=False)  # 5-letter join code
    shears_available = Column(MutableList.as_mutable(JSON))  # List of color_ids
    started_at = Column(DateTime, default=datetime.now)
    initial_lat = Column(String, nullable=True)
    initial_lng = Column(String, nullable=True)

    players = relationship("Player", back_populates="session")
    recipe = relationship("Recipe")
    flowers_collected = relationship(
        "Flower",
        secondary=session_flower_association
    )


#Decorations
class Decoration(Base):
    __tablename__ = "decorations"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    allowed_position = Column(Integer, nullable=False)  # bitmask like 0b10101
    cost = Column(Integer, nullable=False)

class DecorationPlayer(Base):
    __tablename__ = "decoraion_player"

    id = Column(Integer, primary_key=True)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.player_id", ondelete="CASCADE"), nullable=False)
    decoration_id = Column(Integer, ForeignKey("decorations.id", ondelete="CASCADE"), nullable=False)

    used = Column(Boolean, default=False)
    position = Column(Integer)

    # Relationships (only back to player, not visible from decoration)
    player = relationship("Player", back_populates="decorations")
    decoration = relationship("Decoration")
