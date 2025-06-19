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
            {"name":"A", "allowed_position": 0b11111, "cost": 50},
            {"name":"B","allowed_position": 0b00100, "cost": 10},
            {"name":"C","allowed_position": 0b11000, "cost": 150},
            {"name":"D","allowed_position": 0b00011, "cost": 10},
            {"name":"E","allowed_position": 0b10101, "cost": 10},
        ]

        for decoration_data in sample_decorations:
            decoration = models.Decoration(**decoration_data)
            db.add(decoration)

        db.commit()
        print("Sample decorations added successfully")
        # Create sample flowers
        sample_flowers = [
            {"color_id": "red"},
            {"color_id": "blue"},
            {"color_id": "purple"},
            {"color_id": "gold"},
            {"color_id": "green"}
        ]

        flower_map = {}
        for flower_data in sample_flowers:
            flower = db.query(models.Flower).filter(models.Flower.color_id == flower_data["color_id"]).first()
            if not flower:
                flower = models.Flower(**flower_data)
                db.add(flower)
                db.commit()
            flower_map[flower_data["color_id"]] = flower
        print("Flowers added!")
        # Create sample recipes

        healing_potion = models.Recipe(name = "Healing Potion", required_flowers=[flower_map["red"], flower_map["green"]])
        db.add(healing_potion)
        db.commit()
        mana_potion = models.Recipe(name = "Mana Potion", required_flowers=[flower_map["blue"], flower_map["purple"]])
        db.add(mana_potion)
        db.commit()
        legendary_elixir = models.Recipe(
            name="Legendary Elixir",
            required_flowers=[flower_map["gold"]],
            required_potions=[healing_potion, mana_potion])
        db.add(legendary_elixir)
        db.commit()

        print ("Flowers added!")
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
        flower_count = db.query(models.Flower).count()
        recipe_count = db.query(models.Recipe).count()
        player_count = db.query(models.Player).count()
        grimoire_count = db.query(models.Grimoire).count()

        print(f"\nDatabase summary:")
        print(f"Flowers: {flower_count}")
        print(f"Recipes: {recipe_count}")
        print(f"Players: {player_count}")
        print(f"Grimoire: {grimoire_count}")
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
        db.execute(text("""
                        TRUNCATE TABLE
                            decoraion_player,
                        inventory_items,
                        grimoires,
                        players,
                        session_flower_association,
                        sessions,
                        recipe_flowers,
                        recipe_potions,
                        grimoire_recipes,
                        recipes,
                        decorations,
                        flowers
                    RESTART IDENTITY CASCADE;
                        """))
        db.commit()
        db.commit()
    except Exception as e:
        db.rollback()
        print("Error:", e)
    finally:
        db.close()
def reset_and_seed_call():
    reset_db()
    models.Base.metadata.create_all(bind=engine)
    create_sample_data()
if __name__ == "__main__":
    reset_and_seed_call()

