#!/bin/bash
# Sauvegarde de la base SQLite et des photos (console PythonAnywhere) : bash ~/lycee/scripts/sauvegarde-pythonanywhere.sh
set -e
mkdir -p ~/sauvegardes
d=$(date +%F)
cp ~/lycee/backend/db.sqlite3 ~/sauvegardes/db-$d.sqlite3
tar -czf ~/sauvegardes/media-$d.tar.gz -C ~/lycee/backend media 2>/dev/null || true
ls -lh ~/sauvegardes
echo "Sauvegarde terminée (téléchargeable depuis l'onglet Files)."
