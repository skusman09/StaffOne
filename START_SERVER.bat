@echo off
echo Starting FastAPI Server...
echo.
cd backend
if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8001
) else if exist venv\Scripts\python.exe (
    venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8001
) else (
    echo Virtual environment not found!
    echo Please activate your virtual environment first.
    pause
    exit /b 1
)
