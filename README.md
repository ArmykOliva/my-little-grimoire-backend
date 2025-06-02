# My Little Grimoire Backend

A FastAPI backend for a potion crafting game with session management, player inventory, and recipe system.

## Tech Stack

- **FastAPI**: Modern Python web framework
- **PostgreSQL**: Database for persistent storage
- **SQLAlchemy**: ORM for database interactions
- **Docker & Docker Compose**: Containerization
- **Alembic**: Database migrations (TODO)

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Setup

2. **Start the application**
   ```bash
   docker-compose up --build
   ```

3. **Access the API**
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - Database: localhost:5432

## Docker Commands

```bash
# Start everything
docker-compose up --build

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop everything
docker-compose down

# Reset database
docker-compose down -v
docker-compose up --build
```