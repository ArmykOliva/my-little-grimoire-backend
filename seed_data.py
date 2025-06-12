"""
Seed script to populate the database with sample data for testing
Run this after the database is up to have some initial data to work with
"""
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models

def create_sample_data():
    db = SessionLocal()
    
    try:
        # Create sample flowers
        # sample_flowers = [
        #     {"color_id": "red", "name": "Crimson Rose", "rarity": "common"},
        #     {"color_id": "blue", "name": "Azure Lily", "rarity": "uncommon"},
        #     {"color_id": "purple", "name": "Mystic Violet", "rarity": "rare"},
        #     {"color_id": "gold", "name": "Golden Sunflower", "rarity": "legendary"},
        #     {"color_id": "green", "name": "Forest Herb", "rarity": "common"},
        # ]
        
        # for flower_data in sample_flowers:
        #     # Check if flower already exists
        #     existing = db.query(models.Flower).filter(
        #         models.Flower.color_id == flower_data["color_id"]
        #     ).first()
        #
        #     if not existing:
        #         flower = models.Flower(**flower_data)
        #         db.add(flower)
        #         print(f"Created flower: {flower_data['name']}")
        #
        # Create sample recipes
        sample_recipes = [
            {
                "potion_name": "Healing Potion",
                "recipe_data": '{"ingredients": ["red", "green"], "steps": ["mix", "boil"]}',
            },
            {
                "potion_name": "Mana Potion",
                "recipe_data": '{"ingredients": ["blue", "purple"], "steps": ["distill", "enchant"]}',
            },
            {
                "potion_name": "Legendary Elixir",
                "recipe_data": '{"ingredients": ["gold", "purple", "blue"], "steps": ["prepare", "mix", "concentrate", "finalize"]}',
            },
        ]
        
        for recipe_data in sample_recipes:
            # Check if recipe already exists
            existing = db.query(models.Recipe).filter(
                models.Recipe.potion_name == recipe_data["potion_name"]
            ).first()
            
            if not existing:
                recipe = models.Recipe(**recipe_data)
                db.add(recipe)
                print(f"Created recipe: {recipe_data['potion_name']}")
        
        # Create a sample player
        existing_player = db.query(models.Player).first()
        if not existing_player:
            player = models.Player(name="Player")
            db.add(player)
            db.flush()

            # Create grimoire for the player
            grimoire = models.Grimoire(player=player)
            db.add(grimoire)
            # Add some sample inventory items
            # sample_items = [
            #     {"item_type": "potion", "item_id": "healing_potion_basic", "quantity": 2},
            #     {"item_type": "ingredient", "item_id": "dried_herbs", "quantity": 5},
            #     {"item_type": "tool", "item_id": "mortar_pestle", "quantity": 1},
            # ]
            #
            # for item_data in sample_items:
            #     item = models.InventoryItem(player_id=player.id, **item_data)
            #     db.add(item)

            db.commit()
            db.refresh(player)
            print(f"Created sample player with UUID: {player.player_id}")
        db.commit()
        print("Sample data creation completed!")
        
        # Print summary
        # flower_count = db.query(models.Flower).count()
        recipe_count = db.query(models.Recipe).count()
        player_count = db.query(models.Player).count()
        grimoire_count = db.query(models.Grimoire).count()

        print(f"\nDatabase summary:")
        #print(f"Flowers: {flower_count}")
        print(f"Recipes: {recipe_count}")
        print(f"Players: {player_count}")
        print(f"Grimoire: {grimoire_count}")

        grimoire = db.query(models.Grimoire).first()
        if grimoire:
            grimoire_player = grimoire.player_id
            print("Player UUID:", grimoire_player)
        else:
            print("No grimoire found.")
        # Show sample player UUID for testing
        sample_player = db.query(models.Player).first()
        if sample_player:
            print(f"\nSample player UUID for testing: {sample_player.player_id}")
            print("You can use this UUID to test the endpoints!")
        
    except Exception as e:
        print(f"Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

def reset_db():
    db = SessionLocal()
    try:
        db.execute(text("TRUNCATE TABLE grimoires, players, recipes RESTART IDENTITY CASCADE;"))
        db.commit()
    except Exception as e:
        db.rollback()
        print("Error:", e)
    finally:
        db.close()
if __name__ == "__main__":
    # Create tables if they don't exist
    reset_db()
    models.Base.metadata.create_all(bind=engine)
    create_sample_data() 