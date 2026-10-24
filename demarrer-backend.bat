@echo off
chcp 65001 >nul
title Lycée Ambohitromby - Backend (Django)
cd /d "%~dp0backend"
where python >nul 2>nul || (echo Python n'est pas reconnu. Installez Python 3.12 en cochant "Add python.exe to PATH". & pause & exit /b 1)
if not exist venv (
  echo Creation de l'environnement virtuel...
  python -m venv venv || (pause & exit /b 1)
  call venv\Scripts\activate
  python -m pip install --upgrade pip
  pip install -r requirements.txt || (echo Echec de l'installation des dependances. & pause & exit /b 1)
) else (
  call venv\Scripts\activate
)
echo Application des migrations (MySQL XAMPP doit etre demarre)...
python manage.py migrate || (echo Echec : verifiez que MySQL est demarre dans XAMPP et que la base lycee_ambohitromby existe. & pause & exit /b 1)
python manage.py initialiser_etablissement
echo.
echo API disponible sur http://127.0.0.1:8000/api/
python manage.py runserver 127.0.0.1:8000
pause
