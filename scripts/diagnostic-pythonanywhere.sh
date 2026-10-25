#!/bin/bash
# Diagnostic en cas de page « Something went wrong » sur PythonAnywhere.
# Console Bash :  bash ~/lycee/scripts/diagnostic-pythonanywhere.sh   (puis copiez-collez le résultat si besoin d'aide)
echo "== 1. Dossier du projet =="
cd ~/lycee/backend 2>/dev/null || { echo "ERREUR : ~/lycee/backend introuvable. Refaites : cd ~ && git clone https://github.com/VOTRE_COMPTE/lycee-ambohitromby.git lycee"; exit 1; }
pwd
echo; echo "== 2. Environnement virtuel =="
if [ -f ~/.virtualenvs/lycee-env/bin/activate ]; then source ~/.virtualenvs/lycee-env/bin/activate; which python; python --version
else echo "ERREUR : environnement ~/.virtualenvs/lycee-env introuvable. Faites : mkvirtualenv --python=python3.12 lycee-env"; fi
echo; echo "== 3. Fichier .env (clé masquée) =="
if [ -f .env ]; then sed -E 's/^(SECRET_KEY=).*/\1***masquée***/' .env; else echo "ERREUR : .env MANQUANT. Faites : cp .env.production.example .env  puis  nano .env"; fi
echo; echo "== 4. Paquets installés =="
pip list 2>/dev/null | grep -iE "^(django|djangorestframework|djangorestframework-simplejwt|django-cors-headers|pillow|reportlab|python-dotenv) " || echo "ERREUR : paquets absents. Faites : pip install -r requirements-pythonanywhere.txt"
echo; echo "== 5. Vérification Django =="
python manage.py check 2>&1 | tail -n 6
echo; echo "== 6. Migrations non appliquées (doit afficher 0) =="
python manage.py showmigrations 2>/dev/null | grep -c "\[ \]"
echo; echo "== 7. Fichier WSGI =="
W=/var/www/${USER}_pythonanywhere_com_wsgi.py
[ -f "$W" ] && grep -nE "sys.path|DJANGO_SETTINGS_MODULE|chemin|path =" "$W" || echo "Fichier WSGI introuvable : $W"
echo; echo "== 8. 25 dernières lignes du journal d'erreurs =="
tail -n 25 /var/log/${USER}.pythonanywhere.com.error.log 2>/dev/null || echo "(journal introuvable)"
