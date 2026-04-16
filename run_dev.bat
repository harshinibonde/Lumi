@echo off
echo Starting LumiAI Services...

echo Starting FastAPI Backend...
start cmd /k "cd /d "%~dp0backend" && ..\.venv\Scripts\activate && uvicorn main:app --reload"

echo Starting Next.js Frontend...
start cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo Both services are starting up in separate windows!
