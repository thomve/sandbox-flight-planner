@echo off
cd /d "%~dp0"

echo Starting Flight Planner API...
start "Flight API" cmd /k "uv sync && uv run flight-api"

echo Starting Angular frontend...
start "Angular UI" cmd /k "cd frontend && npm start"

echo.
echo Services starting up:
echo   API      -^> http://localhost:8000
echo   Frontend -^> http://localhost:4200
echo.
echo Close the two console windows to stop.
