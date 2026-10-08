@echo off
cd /d %~dp0frontend
if not exist node_modules call npm install
npx next dev -p 3030