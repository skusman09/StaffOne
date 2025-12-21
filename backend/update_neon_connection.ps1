# Script to update .env file with Neon connection string
$neonConnectionString = "postgresql://neondb_owner:npg_1oDGkaSYK3Ex@ep-rapid-meadow-aec4wve4-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

Write-Host "Updating .env file with Neon connection string..." -ForegroundColor Cyan

# Read current .env file if it exists
$envContent = @()
if (Test-Path ".env") {
    $envContent = Get-Content ".env"
}

# Create new content
$newContent = @()
$databaseUrlFound = $false

foreach ($line in $envContent) {
    if ($line -match "^DATABASE_URL=") {
        $newContent += "# Neon PostgreSQL Connection String"
        $newContent += "DATABASE_URL=$neonConnectionString"
        $newContent += ""
        $newContent += "# For local SQLite (development), use:"
        $newContent += "# DATABASE_URL=sqlite:///./checkinout.db"
        $databaseUrlFound = $true
    } elseif (-not $databaseUrlFound -and $line -match "^#.*DATABASE_URL") {
        # Skip comment lines about DATABASE_URL if we haven't found the actual DATABASE_URL yet
        continue
    } else {
        $newContent += $line
    }
}

# If DATABASE_URL wasn't found, add it at the beginning
if (-not $databaseUrlFound) {
    $newContent = @(
        "# Neon PostgreSQL Connection String",
        "DATABASE_URL=$neonConnectionString",
        "",
        "# For local SQLite (development), use:",
        "# DATABASE_URL=sqlite:///./checkinout.db",
        ""
    ) + $newContent
}

# Write to .env file
$newContent | Set-Content ".env" -Encoding UTF8

Write-Host "✓ .env file updated successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Testing connection to Neon database..." -ForegroundColor Cyan

# Test connection
if (Test-Path "venv\Scripts\python.exe") {
    $python = "venv\Scripts\python.exe"
} elseif (Test-Path ".venv\Scripts\python.exe") {
    $python = ".venv\Scripts\python.exe"
} else {
    Write-Host "Virtual environment not found!" -ForegroundColor Red
    exit 1
}

try {
    $testScript = "from app.database import engine; conn = engine.connect(); print('Successfully connected to Neon PostgreSQL!'); conn.close()"
    & $python -c $testScript
    Write-Host ""
    Write-Host "Connection successful! Ready to run migrations." -ForegroundColor Green
} catch {
    Write-Host "Connection test failed. Please check your connection string." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Yellow
}

