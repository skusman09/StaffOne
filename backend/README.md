# Backend API - Check-In/Check-Out System

FastAPI backend for the attendance tracking system.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your configuration.

3. **Run the server:**
   ```bash
   uvicorn app.main:app --reload --port 8001
   ```

4. **Access API documentation:**
   - Swagger UI: http://localhost:8001/docs
   - ReDoc: http://localhost:8001/redoc

## API Endpoints

See the main README.md for complete API documentation.

## Database Migrations

To create a new migration:
```bash
alembic revision --autogenerate -m "description"
```

To apply migrations:
```bash
alembic upgrade head
```

