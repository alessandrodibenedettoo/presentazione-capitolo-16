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

## Come modificare le slide (per tutto il gruppo)

1. Su github.com apri `src/template.html` e premi la matita (Modifica).
2. Con Ctrl+F (⌘F su Mac) trova la frase da cambiare e modifica **solo il testo** tra i tag, senza toccare `<` `>` e le parti in inglese.
3. In basso premi **Commit changes**.

Al prossimo avvio di `Avvia presentazione.command` il Mac scarica la modifica e ricostruisce le slide da solo.
Per cambiamenti più grandi (nuove slide, animazioni) chiedete ad Alessandro.
