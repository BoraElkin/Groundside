# Database Scripts

## Seed Data

To populate the database with sample data for testing:

```bash
# Using Docker
docker-compose exec backend python scripts/seed_data.py

# Or directly with Python
python backend/scripts/seed_data.py
```

This will create:
- 5 sample customers (Turkish Airlines, Lufthansa, Swissport, Istanbul Airport, Demo)
- API keys for each customer
- 50 sample flights
- 30 turnarounds with activities
- 15 alerts

The script will output API keys that you can use for testing.

## Database Migrations

Create a new migration after model changes:

```bash
docker-compose exec backend alembic revision --autogenerate -m "description of changes"
```

Apply migrations:

```bash
docker-compose exec backend alembic upgrade head
```

Rollback last migration:

```bash
docker-compose exec backend alembic downgrade -1
```

Check current migration version:

```bash
docker-compose exec backend alembic current
```

View migration history:

```bash
docker-compose exec backend alembic history
```
