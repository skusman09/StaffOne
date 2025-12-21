# Script to migrate base models to Neon DB
Write-Host "Migrating Base Models to Neon PostgreSQL..." -ForegroundColor Cyan
Write-Host "=" * 50
Write-Host ""

# Check if virtual environment exists
if (Test-Path "venv\Scripts\python.exe") {
    $python = "venv\Scripts\python.exe"
} elseif (Test-Path ".venv\Scripts\python.exe") {
    $python = ".venv\Scripts\python.exe"
} else {
    Write-Host "Virtual environment not found!" -ForegroundColor Red
    exit 1
}

# Step 1: Check current migration status
Write-Host "1. Checking current migration status..." -ForegroundColor Yellow
& $python -m alembic current
Write-Host ""

# Step 2: Show migration history
Write-Host "2. Migration history:" -ForegroundColor Yellow
& $python -m alembic history
Write-Host ""

# Step 3: Apply migrations
Write-Host "3. Applying migrations to Neon DB..." -ForegroundColor Yellow
& $python -m alembic upgrade head
Write-Host ""

# Step 4: Verify tables exist
Write-Host "4. Verifying tables in Neon DB..." -ForegroundColor Yellow
& $python -c "from app.database import engine; from sqlalchemy import text; conn = engine.connect(); result = conn.execute(text('SELECT table_name FROM information_schema.tables WHERE table_schema = ''public'' ORDER BY table_name')); tables = [row[0] for row in result]; print(f'Found {len(tables)} tables: {', '.join(tables)}'); conn.close()"
Write-Host ""

Write-Host "=" * 50
Write-Host "Migration complete!" -ForegroundColor Green
Write-Host "Your base models are now migrated to Neon PostgreSQL." -ForegroundColor Green

