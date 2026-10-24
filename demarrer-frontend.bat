@echo off
chcp 65001 >nul
title Lycée Ambohitromby - Frontend (React)
cd /d "%~dp0frontend"
where npm >nul 2>nul || (echo Node.js n'est pas reconnu. Installez Node.js LTS. & pause & exit /b 1)
if not exist node_modules (
  echo Installation des dependances...
  call npm install || (pause & exit /b 1)
)
echo Application disponible sur http://localhost:5173
call npm run dev
pause
