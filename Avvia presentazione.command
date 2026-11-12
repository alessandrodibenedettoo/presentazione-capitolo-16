#!/bin/bash
cd "$(dirname "$0")"
if [ -d .git ]; then
  echo "Cerco aggiornamenti della presentazione…"
  if git pull --ff-only --quiet; then
    echo "Presentazione aggiornata all'ultima versione."
  else
    echo "Aggiornamento non riuscito (nessuna connessione?): uso la versione già presente."
  fi
fi
python3 server.py
