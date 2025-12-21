# PowerShell script to run Alembic migrations
# Usage: .\run_migrations.ps1 [command] [options]

param(
    [string]$Command = "upgrade",
    [string]$Target = "head",
    [string]$Message = ""
)

Write-Host "Alembic Migration Tool" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Green
    & .\venv\Scripts\Activate.ps1
} elseif (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Green
    & .\.venv\Scripts\Activate.ps1
} else {
    Write-Host "Virtual environment not found!" -ForegroundColor Red
    exit 1
}

Write-Host ""

switch ($Command.ToLower()) {
    "upgrade" {
        Write-Host "Applying migrations up to: $Target" -ForegroundColor Yellow
        alembic upgrade $Target
    }
    "downgrade" {
        Write-Host "Rolling back migrations to: $Target" -ForegroundColor Yellow
        alembic downgrade $Target
    }
    "create" {
        if ($Message -eq "") {
            Write-Host "Error: Message required for creating migration" -ForegroundColor Red
            Write-Host "Usage: .\run_migrations.ps1 -Command create -Message 'Your message'" -ForegroundColor Yellow
            exit 1
        }
        Write-Host "Creating new migration: $Message" -ForegroundColor Yellow
        alembic revision --autogenerate -m $Message
    }
    "current" {
        Write-Host "Current migration status:" -ForegroundColor Yellow
        alembic current
    }
    "history" {
        Write-Host "Migration history:" -ForegroundColor Yellow
        alembic history
    }
    default {
        Write-Host "Available commands:" -ForegroundColor Cyan
        Write-Host "  upgrade   - Apply migrations (default: head)"
        Write-Host "  downgrade - Rollback migrations"
        Write-Host "  create    - Create new migration (requires -Message)"
        Write-Host "  current   - Show current migration"
        Write-Host "  history   - Show migration history"
        Write-Host ""
        Write-Host "Examples:" -ForegroundColor Yellow
        Write-Host "  .\run_migrations.ps1"
        Write-Host "  .\run_migrations.ps1 -Command upgrade -Target head"
        Write-Host "  .\run_migrations.ps1 -Command create -Message 'Add new field'"
        Write-Host "  .\run_migrations.ps1 -Command current"
    }
}

