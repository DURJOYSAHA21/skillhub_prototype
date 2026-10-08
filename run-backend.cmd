@echo off
cd /d %~dp0backend
if not exist .venv python -m venv .venv
if not exist .venv\Scripts\uvicorn.exe .venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m uvicorn app.main:app --port 8030 --reload