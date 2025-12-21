# Start the FastAPI server using Python module (more reliable)
Write-Host "Starting FastAPI server..." -ForegroundColor Green
Write-Host "Server will be available at http://localhost:8001" -ForegroundColor Cyan
Write-Host "API docs at http://localhost:8001/docs" -ForegroundColor Cyan
Write-Host "Press CTRL+C to stop the server" -ForegroundColor Yellow
Write-Host ""

.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8001

