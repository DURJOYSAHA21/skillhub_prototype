@echo off
rem Starts the SkillHub local PostgreSQL cluster (data in .\pgdata, port 5433)
rem Stop with:  "C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe" -D "%~dp0pgdata" stop
set PGBIN=C:\Program Files\PostgreSQL\18\bin
"%PGBIN%\pg_ctl.exe" -D "%~dp0pgdata" -o "-p 5433" -l "%~dp0pgdata\server.log" -w start
echo SkillHub PostgreSQL is running on 127.0.0.1:5433