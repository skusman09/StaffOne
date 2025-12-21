# Setup Neon PostgreSQL Connection
$neonConnectionString = "postgresql://neondb_owner:npg_1oDGkaSYK3Ex@ep-rapid-meadow-aec4wve4-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

Write-Host "Setting up Neon PostgreSQL connection..." -ForegroundColor Cyan
Write-Host ""

# Update .env file
Write-Host "Updating .env file..." -ForegroundColor Yellow
$envFile = ".env"
$newEnvContent = @"
# Neon PostgreSQL Connection String
DATABASE_URL=$neonConnectionString

# For local SQLite (development), use:
# DATABASE_URL=sqlite:///./checkinout.db

# JWT Settings
SECRET_KEY=your-secret-key-change-in-production-use-a-long-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS Origins (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
"@

$newEnvContent | Out-File -FilePath $envFile -Encoding UTF8
Write-Host ".env file updated successfully!" -ForegroundColor Green
Write-Host ""

# Test connection
Write-Host "Testing Neon database connection..." -ForegroundColor Yellow
if (Test-Path "venv\Scripts\python.exe") {
    $python = "venv\Scripts\python.exe"
} elseif (Test-Path ".venv\Scripts\python.exe") {
    $python = ".venv\Scripts\python.exe"
} else {
    Write-Host "Virtual environment not found!" -ForegroundColor Red
    exit 1
}

& $python test_neon_connection.py
$exitCode = $LASTEXITCODE
if ($exitCode -eq 0) {
    Write-Host ""
    Write-Host "Connection successful! Ready to run migrations." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Run migrations: alembic upgrade head" -ForegroundColor White
    Write-Host "2. Start server: .\start_server.ps1" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "Connection test failed. Please check your connection string." -ForegroundColor Red
}
