#!/bin/bash
cd "$(dirname "$0")"
if [ -d .git ]; then
  echo "Cerco aggiornamenti della presentazione…"
  git checkout -- web/index.html 2>/dev/null
  if git pull --ff-only --quiet; then
    echo "Presentazione aggiornata all'ultima versione."
    python3 src/build.py >/dev/null 2>&1 || echo "Attenzione: non riesco a ricostruire le slide, uso l'ultima versione funzionante."
  else
    echo "Aggiornamento non riuscito (nessuna connessione?): uso la versione già presente."
  fi
fi
python3 server.py
