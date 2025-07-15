
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
            {"color_id": "blue", "name": "Mystic Azurea"},
            {"color_id": "coral", "name": "Coralia Blossom"},
            {"color_id": "lilac", "name": "Moonbell"},
            {"color_id": "orange", "name": "Cinderflare"},
            {"color_id": "pink", "name": "Feypetal"},
            {"color_id": "purple", "name": "Vesperthorn"},
            {"color_id": "red", "name": "Sanguine Rose"},
            {"color_id": "white", "name": "Angelbud"},
            {"color_id": "yellow", "name": "Solaria's Crown"},
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

        healing_potion = models.Recipe(name = "Healing Potion", required_flowers=[flower_map["red"], flower_map["lilac"]])
        db.add(healing_potion)
        db.commit()
        mana_potion = models.Recipe(name = "Mana Potion", required_flowers=[flower_map["white"], flower_map["purple"]])
        db.add(mana_potion)
        db.commit()
        legendary_elixir = models.Recipe(
            name="Legendary Elixir",
            required_flowers=[flower_map["yellow"]],
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

        # Create seed trades
        create_seed_trades(db, healing_potion, mana_potion, legendary_elixir)
        
    except Exception as e:
        print(f"Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

def create_seed_trades(db: Session, healing_potion, mana_potion, legendary_elixir):
    """Create sample simple sale listings"""
    try:
        # Get players
        players = db.query(models.Player).all()
        if len(players) < 2:
            print("Not enough players to create trades")
            return
            
        player1, player2 = players[0], players[1]
        player3 = players[2] if len(players) > 2 else player1
        
        # Give players some inventory for trading
        # Player 1 gets healing potions
        healing_inventory = models.InventoryItem(
            player_id=player1.player_id,
            potion_id=healing_potion.id,
            amount=3
        )
        db.add(healing_inventory)
        
        # Player 2 gets mana potions
        mana_inventory = models.InventoryItem(
            player_id=player2.player_id,
            potion_id=mana_potion.id,
            amount=2
        )
        db.add(mana_inventory)
        
        # Player 3 gets legendary elixir
        legendary_inventory = models.InventoryItem(
            player_id=player3.player_id,
            potion_id=legendary_elixir.id,
            amount=1
        )
        db.add(legendary_inventory)
        
        # Give players more money for trading
        player1.money = 200
        player2.money = 150
        player3.money = 500
        
        db.commit()
        
        # Simple sale listings
        
        # Sale 1: Healing Potion for 50 coins (available)
        sale1 = models.Trade(
            seller_id=player1.player_id,
            item_id=healing_potion.id,
            item_amount=1,
            price=50,
            status="available"
        )
        db.add(sale1)
        
        # Sale 2: Mana Potion for 75 coins (available)
        sale2 = models.Trade(
            seller_id=player2.player_id,
            item_id=mana_potion.id,
            item_amount=1,
            price=75,
            status="available"
        )
        db.add(sale2)
        
        # Sale 3: Legendary Elixir for 300 coins (available)
        sale3 = models.Trade(
            seller_id=player3.player_id,
            item_id=legendary_elixir.id,
            item_amount=1,
            price=300,
            status="available"
        )
        db.add(sale3)
        
        # Sale 4: Another Healing Potion for cheaper (available)
        sale4 = models.Trade(
            seller_id=player1.player_id,
            item_id=healing_potion.id,
            item_amount=1,
            price=40,
            status="available"
        )
        db.add(sale4)
        
        # Sale 5: Sold example (for history)
        sale5 = models.Trade(
            seller_id=player2.player_id,
            item_id=mana_potion.id,
            item_amount=1,
            price=65,
            status="sold"
        )
        db.add(sale5)
        
        db.commit()
        
        print("\n🏪 Sample sales created successfully!")
        print(f"💰 Sale 1: {player1.name} selling Healing Potion for 50 coins")
        print(f"💰 Sale 2: {player2.name} selling Mana Potion for 75 coins")
        print(f"💰 Sale 3: {player3.name} selling Legendary Elixir for 300 coins")
        print(f"💰 Sale 4: {player1.name} selling Healing Potion for 40 coins (cheaper!)")
        print(f"✅ Sale 5: {player2.name} already sold Mana Potion for 65 coins")
        
    except Exception as e:
        print(f"Error creating seed trades: {e}")
        db.rollback()

def reset_db():
    db = SessionLocal()
    try:
        db.execute(text("""
                        TRUNCATE TABLE
                            trades,
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
                        flowers,
                        player_followers,
                        playeraccounts
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

