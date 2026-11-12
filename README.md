# Presentazione Capitolo 16

Tecnologie per la riflessione e l'autovalutazione. E-portfolio, feedback, open badge.
Presentazione interattiva a slide con server locale: i compagni rispondono dal telefono.

| Percorso | Cosa contiene |
|---|---|
| `Avvia presentazione.command` | avvio su Mac: fa `git pull` e poi parte il server |
| `server.py` | server locale (solo libreria standard di Python), link pubblico con Cloudflare |
| `web/index.html` | le slide (generate, non modificare a mano) |
| `web/vota.html` | la pagina per i telefoni |
| `src/` | sorgenti: `python3 src/build.py` ricrea `web/index.html` |

Le risposte della classe vengono salvate in `risultati.json`, che resta solo sul Mac.
