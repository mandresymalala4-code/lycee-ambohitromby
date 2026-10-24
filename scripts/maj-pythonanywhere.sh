#!/bin/bash
# Mise à jour du site sur PythonAnywhere après un "git push" : à lancer dans la console Bash de PythonAnywhere.
#   bash ~/lycee/scripts/maj-pythonanywhere.sh
set -e
cd ~/lycee
git pull
source ~/.virtualenvs/lycee-env/bin/activate
cd backend
pip install -r requirements-pythonanywhere.txt
python manage.py migrate
touch /var/www/${USER}_pythonanywhere_com_wsgi.py   # recharge l'application
echo "Mise à jour terminée."
