@echo off
echo Starting FastAPI server...
echo Server will be available at http://localhost:8001
echo API docs at http://localhost:8001/docs
echo Press CTRL+C to stop the server
echo.

venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8001

