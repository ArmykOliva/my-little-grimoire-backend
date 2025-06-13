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
        sample_decorations = [
            {"id": 1, "name": "Wooden Fence", "allowed_position": 0b11111, "cost": 50},
            {"id": 2, "name": "Crystal Fountain", "allowed_position": 0b00100, "cost": 10},
            {"id": 3, "name": "Enchanted Tree", "allowed_position": 0b11000, "cost": 150},
            {"id": 4, "name": "Mystic Stone", "allowed_position": 0b00011, "cost": 10},
            {"id": 5, "name": "Golden Bench", "allowed_position": 0b10101, "cost": 10},
        ]

        for decoration_data in sample_decorations:
            decoration = models.Decoration(**decoration_data)
            db.add(decoration)

        db.commit()
        print("Sample decorations added successfully")
        # Create sample flowers
        sample_flowers = [
            {"color_id": "red", "flower_name": "Crimson Rose", "flower_rarity": "common"},
            {"color_id": "blue", "flower_name": "Azure Lily", "flower_rarity": "uncommon"},
            {"color_id": "purple", "flower_name": "Mystic Violet", "flower_rarity": "rare"},
            {"color_id": "gold", "flower_name": "Golden Sunflower", "flower_rarity": "legendary"},
            {"color_id": "green", "flower_name": "Forest Herb", "flower_rarity": "common"},
        ]

        flower_map = {}
        for flower_data in sample_flowers:
            flower = db.query(models.Flower).filter_by(flower_name=flower_data["flower_name"]).first()
            if not flower:
                flower = models.Flower(**flower_data)
                db.add(flower)
                db.commit()
            flower_map[flower_data["flower_name"]] = flower
        # Create sample recipes

        healing_potion = db.query(models.Recipe).filter_by(potion_name="Healing Potion").first()
        if not healing_potion:
            healing_potion = models.Recipe(
                potion_name="Healing Potion",
                required_flowers=[
                    flower_map["Crimson Rose"],
                    flower_map["Forest Herb"]
                ]
            )
            db.add(healing_potion)
            db.commit()

        mana_potion = db.query(models.Recipe).filter_by(potion_name="Mana Potion").first()
        if not mana_potion:
            mana_potion = models.Recipe(
                potion_name="Mana Potion",
                required_flowers=[
                    flower_map["Azure Lily"],
                    flower_map["Mystic Violet"]
                ]
            )
            db.add(mana_potion)
            db.commit()

        legendary_elixir = db.query(models.Recipe).filter_by(potion_name="Legendary Elixir").first()
        if not legendary_elixir:
            legendary_elixir = models.Recipe(
                potion_name="Legendary Elixir",
                required_flowers=[
                    flower_map["Golden Sunflower"]
                ],
                required_potions=[
                    healing_potion,
                    mana_potion
                ]
            )
            db.add(legendary_elixir)
            db.commit()
        
        # Create a sample player
        existing_player = db.query(models.Player).filter(models.Player.name == "Player").first()
        if not existing_player:
            player = models.Player(name="Player")
            db.add(player)
            db.flush()

            # Create grimoire for the player
            grimoire = models.Grimoire(player=player)
            db.add(grimoire)


            db.commit()
            db.refresh(player)
            print(f"Created sample player with UUID: {player.player_id}")
        existing_player = db.query(models.Player).filter(models.Player.name == "Alex").first()
        if not existing_player:
            player = models.Player(name="Alex")
            db.add(player)
            db.flush()

            # Create grimoire for the player
            grimoire = models.Grimoire(player=player)
            db.add(grimoire)

            db.commit()
            db.refresh(player)
            print(f"Created sample player with UUID: {player.player_id}")

            existing_player = db.query(models.Player).filter(models.Player.name == "Krystof").first()
            if not existing_player:
                player = models.Player(name="Krystof")
                db.add(player)
                db.flush()

                # Create grimoire for the player
                grimoire = models.Grimoire(player=player)
                db.add(grimoire)

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
            print("You can use this UUID to test the endpoints!")
            print(f"\nSample player UUID for testing: {sample_player.player_id}")
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