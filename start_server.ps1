# Start FastAPI server from project root
# This script automatically navigates to backend directory

Write-Host "Starting FastAPI server..." -ForegroundColor Cyan
Write-Host ""

# Get the script directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendPath = Join-Path $scriptPath "backend"

# Check if backend directory exists
if (Test-Path "$backendPath\app\main.py") {
    Write-Host "Navigating to backend directory..." -ForegroundColor Yellow
    Push-Location $backendPath
    
    # Check for virtual environment
    $python = $null
    if (Test-Path "venv\Scripts\python.exe") {
        $python = "venv\Scripts\python.exe"
    } elseif (Test-Path ".venv\Scripts\python.exe") {
        $python = ".venv\Scripts\python.exe"
    } else {
        Write-Host "Virtual environment not found!" -ForegroundColor Red
        Write-Host "Please activate your virtual environment first." -ForegroundColor Yellow
        Pop-Location
        exit 1
    }
    
    Write-Host "Starting server at http://localhost:8001" -ForegroundColor Green
    Write-Host "API docs at http://localhost:8001/docs" -ForegroundColor Green
    Write-Host "Press CTRL+C to stop the server" -ForegroundColor Yellow
    Write-Host ""
    
    try {
        & $python -m uvicorn app.main:app --reload --port 8001
    } finally {
        Pop-Location
    }
} else {
    Write-Host "Error: backend directory not found at $backendPath" -ForegroundColor Red
    Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow
    exit 1
}

