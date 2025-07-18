
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
            {"name":"Cat moon painting orange yellow", "allowed_position": 0b001, "cost": 1000},
            {"name":"Cat moon painting red blue","allowed_position": 0b001, "cost": 1000},
            {"name":"Grimeow bed green yellow","allowed_position": 0b010, "cost": 600},
            {"name":"Grimeow bed Jade green yellow","allowed_position": 0b010, "cost": 400},
            {"name":"Grimeow bed purple green","allowed_position": 0b010, "cost": 400},
            {"name": "Grimeow bed purple jade green", "allowed_position": 0b010, "cost": 500},
            {"name": "Grimeow bed purple yellow", "allowed_position": 0b010, "cost": 500},
            {"name": "Grimeow bed red black", "allowed_position": 0b010, "cost": 300},
            {"name": "Grimeow bed red yellow", "allowed_position": 0b010, "cost": 200},
            {"name": "Hanging rack", "allowed_position": 0b100, "cost": 800},
            {"name":"Moon landscape painting","allowed_position": 0b001, "cost": 500},
            {"name": "Sunrise landscape painting", "allowed_position": 0b001, "cost": 600},
            {"name": "Vase green yellow", "allowed_position": 0b100, "cost": 200},
            {"name": "Vase Jade yellow", "allowed_position": 0b100, "cost": 100},
            {"name": "Vase purple Jade", "allowed_position": 0b100, "cost": 150},
            {"name": "Vase purple yellow", "allowed_position": 0b100, "cost": 125},
            {"name": "Vase red yellow", "allowed_position": 0b100, "cost": 250},
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
            {"color_id": "black", "name": "Vesperthorn"},
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

        # Sleep Potion
        sleep_potion = models.Recipe(
            name="Sleep Potion",
            required_flowers=[flower_map["blue"]],
            required_potions=[]
        )
        db.add(sleep_potion)
        db.commit()

        # Death Potion
        death_potion = models.Recipe(
            name="Death Potion",
            required_flowers=[flower_map["white"], flower_map["black"]],
            required_potions=[]
        )
        db.add(death_potion)
        db.commit()

        # Beauty Potion
        beauty_potion = models.Recipe(
            name="Beauty Potion",
            required_flowers=[flower_map["white"], flower_map["pink"]],
            required_potions=[]
        )
        db.add(beauty_potion)
        db.commit()

        # Eternal Wealth
        eternal_wealth = models.Recipe(
            name="Eternal Wealth",
            required_flowers=[flower_map["yellow"], flower_map["orange"], flower_map["blue"]],
            required_potions=[]
        )
        db.add(eternal_wealth)
        db.commit()

        # Eternal Health
        eternal_health = models.Recipe(
            name="Eternal Health",
            required_flowers=[flower_map["red"], flower_map["lilac"]],
            required_potions=[death_potion]
        )
        db.add(eternal_health)
        db.commit()

        # Eternal Happiness
        eternal_happiness = models.Recipe(
            name="Eternal Happiness",
            required_flowers=[flower_map["yellow"], flower_map["white"]],
            required_potions=[eternal_health, beauty_potion, eternal_wealth]
        )
        db.add(eternal_happiness)
        db.commit()

        # Love Potion
        love_potion = models.Recipe(
            name="Love Potion",
            required_flowers=[flower_map["red"], flower_map["pink"], flower_map["white"], flower_map["orange"]],
            required_potions=[beauty_potion]
        )
        db.add(love_potion)
        db.commit()

        # Painless Death = Death Potion
        painless_death = models.Recipe(
            name="Painless Death",
            required_flowers=[flower_map["blue"], flower_map["black"], flower_map["white"]],
            required_potions=[death_potion]
        )
        db.add(painless_death)
        db.commit()

        # Wolf
        wolf = models.Recipe(
            name="Wolf",
            required_flowers=[flower_map["blue"], flower_map["yellow"], flower_map["lilac"]],
            required_potions=[sleep_potion]
        )
        db.add(wolf)
        db.commit()

        print ("Potions added!")
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
        create_seed_trades(db, death_potion, eternal_health, sleep_potion)
        
    except Exception as e:
        print(f"Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

def create_seed_trades(db: Session, death_potion, eternal_health, sleep_potion):
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
        # Player 1 gets death potions
        sleep_potion_inventory = models.InventoryItem(
            player_id=player1.player_id,
            potion_id=sleep_potion.id,
            amount=3
        )
        db.add(sleep_potion_inventory)
        
        # Player 2 gets death_potion
        death_potion_inventory = models.InventoryItem(
            player_id=player2.player_id,
            potion_id=death_potion.id,
            amount=2
        )
        db.add(death_potion_inventory)
        
        # Player 3 gets legendary elixir
        eternal_health_inventory = models.InventoryItem(
            player_id=player3.player_id,
            potion_id=eternal_health.id,
            amount=1
        )
        db.add(eternal_health)
        
        # Give players more money for trading
        player1.money = 200
        player2.money = 150
        player3.money = 500
        
        db.commit()
        
        # Simple sale listings

        # Player 1 gets 3 Sleep Potions
        sleep_potion_inventory = models.InventoryItem(
            player_id=player1.player_id,
            potion_id=sleep_potion.id,
            amount=3
        )
        db.add(sleep_potion_inventory)

        # Player 2 gets 2 Death Potions
        death_potion_inventory = models.InventoryItem(
            player_id=player2.player_id,
            potion_id=death_potion.id,
            amount=2
        )
        db.add(death_potion_inventory)

        # Player 3 gets 1 Eternal Health potion (legendary)
        eternal_health_inventory = models.InventoryItem(
            player_id=player3.player_id,
            potion_id=eternal_health.id,
            amount=1
        )
        db.add(eternal_health_inventory)

        # Add some money to players for trading
        player1.money = 200
        player2.money = 150
        player3.money = 500

        db.commit()

        # Create trade listings

        # Sale 1: Sleep Potion for 50 coins (available)
        sale1 = models.Trade(
            seller_id=player1.player_id,
            item_id=sleep_potion.id,
            item_amount=1,
            price=50,
            status="available"
        )
        db.add(sale1)

        # Sale 2: Death Potion for 75 coins (available)
        sale2 = models.Trade(
            seller_id=player2.player_id,
            item_id=death_potion.id,
            item_amount=1,
            price=75,
            status="available"
        )
        db.add(sale2)

        # Sale 3: Eternal Health for 300 coins (available)
        sale3 = models.Trade(
            seller_id=player3.player_id,
            item_id=eternal_health.id,
            item_amount=1,
            price=300,
            status="available"
        )
        db.add(sale3)

        # Sale 4: Another Eternal Health for 40 coins (cheaper))
        sale4 = models.Trade(
            seller_id=player1.player_id,
            item_id=eternal_health.id,
            item_amount=1,
            price=40,
            status="available"
        )
        db.add(sale4)

        # Sale 5: A previously sold Death Potion for 65 coins
        sale5 = models.Trade(
            seller_id=player2.player_id,
            item_id=death_potion.id,
            item_amount=1,
            price=65,
            status="sold"
        )
        db.add(sale5)

        db.commit()

        # Output summary
        print("\n🏪 Sample sales created successfully!")
        print(f"💤 Sale 1: {player1.name} selling Sleep Potion for 50 coins")
        print(f"💀 Sale 2: {player2.name} selling Death Potion for 75 coins")
        print(f"🧬 Sale 3: {player3.name} selling Eternal Health for 300 coins")
        print(f"💸 Sale 4: {player1.name} selling Eternal Health for 40 coins (cheap!)")
        print(f"✅ Sale 5: {player2.name} already sold Death Potion for 65 coins")

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

