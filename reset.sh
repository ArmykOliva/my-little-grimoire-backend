#!/bin/bash

echo "🔄 Starting full reset process..."
echo

# Step 1: Git pull latest changes
echo "📥 Pulling latest changes from git..."
git pull
if [ $? -ne 0 ]; then
    echo "❌ Git pull failed!"
    exit 1
fi
echo "✅ Git pull completed"
echo

# Step 2: Bring down containers and remove volumes
echo "🔻 Bringing down Docker containers and removing volumes..."
docker compose down -v
if [ $? -ne 0 ]; then
    echo "❌ Docker compose down failed!"
    exit 1
fi
echo "✅ Containers and volumes removed"
echo

# Step 3: Build and start containers
echo "🔧 Building and starting Docker containers..."
docker compose up --build -d
if [ $? -ne 0 ]; then
    echo "❌ Docker compose up failed!"
    exit 1
fi
echo "✅ Containers built and started"
echo

# Step 4: Wait for services to be ready
echo "⏳ Waiting 30 seconds for services to initialize..."
sleep 30
echo "✅ Wait completed"
echo

# Step 5: Run seed data script
echo "🌱 Running database seed script..."
docker compose exec web python seed_data.py
if [ $? -ne 0 ]; then
    echo "❌ Seed data script failed!"
    exit 1
fi
echo "✅ Database seeded successfully"
echo

# Success message
echo "🎉 RESET COMPLETED SUCCESSFULLY! 🎉"
echo
echo "📋 Summary:"
echo "  ✅ Git repository updated"
echo "  ✅ Docker containers rebuilt"
echo "  ✅ Database reset and seeded"
echo "  ✅ API server running at http://localhost:8000"
echo "  ✅ Database ready with sample data"
echo
echo "🚀 Your development environment is ready!" 