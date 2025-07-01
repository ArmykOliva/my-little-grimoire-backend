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


class PlayerAccount(Base):
    __tablename__ = "playeraccounts"

    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)

    # Relationship to Player
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False, unique=True)
    player = relationship("Player", backref="account", uselist=False)
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

    #Customer
    customer_id = Column(Integer, default = 0)

    """ Other values to consider
    level = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    """

    #session
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.session_id", ondelete="SET NULL"), nullable=True)
    assigned_flower = Column(Integer, nullable=True)

    # Relationships
    session = relationship(
        "Session",
        back_populates="players",
        uselist=False,
        passive_deletes=True,
        foreign_keys=[session_id]
    )
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
    name = Column(String, nullable=False,  default = "SomePotion")
    required_potions = relationship(
        "Recipe",
        secondary=recipe_potions,
        primaryjoin=id == recipe_potions.c.recipe_id,
        secondaryjoin=id == recipe_potions.c.potion_id,
        foreign_keys=[recipe_potions.c.recipe_id, recipe_potions.c.potion_id],
        lazy="joined"
    )
    required_flowers = relationship("Flower", secondary=recipe_flowers)

    #everything else saved only on client side


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
    name = Column(String, default = "Flower Name")
    #Every other info is saved on client side only

class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True)
    session_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True, nullable=False)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    status = Column(Integer, default=0)  # 0 = in progress, 1 = ended
    code = Column(String(5), unique=True, nullable=False)  # 5-letter join code
    flowers_available = Column(MutableList.as_mutable(JSON))  # List of color_ids
    started_at = Column(DateTime, default=datetime.now)
    initial_lat = Column(Float, nullable=True)
    initial_lng = Column(Float, nullable=True)
    initial_player = Column (UUID(as_uuid=True), ForeignKey("players.player_id", ondelete="CASCADE"), nullable=False)
    players = relationship(
        "Player",
        back_populates="session",
        foreign_keys=[Player.session_id]
    )
    recipe = relationship("Recipe")
    flowers_collected = relationship(
        "Flower",
        secondary=session_flower_association
    )


#Decorations
class Decoration(Base):
    __tablename__ = "decorations"
    name = Column(String, nullable=False, default="SomeDecoration")
    id = Column(Integer, primary_key=True)
    allowed_position = Column(Integer, nullable=False)  # bitmask like 0b10101
    cost = Column(Integer, nullable=False)
    #everything else client side

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
