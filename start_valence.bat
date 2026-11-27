@echo off
title VALENCE — Voice-to-Rights Civic Shield
echo Starting VALENCE Backend + Frontend on http://127.0.0.1:8000 ...
cd /d "%~dp0backend"
start "" "http://127.0.0.1:8000"
python -m uvicorn main:app --host 127.0.0.1 --port 8000
pause
