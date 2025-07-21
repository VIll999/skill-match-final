# Skill-Match API

## Database Setup

### Prerequisites
- PostgreSQL database running (via docker-compose)
- Python environment with dependencies installed

### Initial Setup

1. Start the PostgreSQL database:
```bash
docker-compose up -d db
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database with sample data:
```bash
python init_db.py
```

### Database Migrations

1. Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

2. Apply migrations:
```bash
alembic upgrade head
```

3. Rollback migrations:
```bash
alembic downgrade -1
```

### API Endpoints

- `GET /api/health` - Health check
- `GET /api/v1/db-test` - Database connection test
- `GET /api/v1/jobs` - List job postings
- `POST /api/v1/jobs` - Create job posting
- `GET /api/v1/jobs/{id}` - Get specific job posting
- `GET /api/v1/skills` - List skills
- `POST /api/v1/skills` - Create skill
- `GET /api/v1/skills/categories` - List skill categories
- `POST /api/v1/skills/categories` - Create skill category

### Running the API

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Or with Docker:
```bash
docker-compose up api
```