#!/usr/bin/env python3
"""Presentazione Capitolo 16 - server locale per l'aula.

Avvio:  python3 server.py            (apre il browser sul Mac)
        python3 server.py --offline  (senza link pubblico, solo rete Wi-Fi)

- Sul Mac/proiettore:  http://localhost:8016        (vista di chi presenta)
- Sui telefoni:        l'indirizzo /vota mostrato nel QR code
Usa solo la libreria standard di Python. I risultati vengono salvati in risultati.json.
"""
import atexit, json, os, re, secrets, socket, subprocess, sys, tarfile, threading, time, urllib.request, webbrowser, platform, shutil
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PORT = 8016
HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN = secrets.token_urlsafe(16)
LOCK = threading.Lock()

# ---------------- Attività che i telefoni possono ricevere ----------------
ACTS = {
    "intro":  {"type": "poll", "title": "Vi è più utile un voto secco o un commento che vi spiega cosa migliorare?",
               "options": ["Un voto secco", "Un commento"]},
    "forza":  {"type": "poll", "title": "Sapete indicare con precisione i vostri punti di forza e di debolezza prima di una verifica?",
               "options": ["Sì, con precisione", "Solo in parte / no"]},
    "portfolio": {"type": "text", "title": "Cosa mettereste nel vostro e-portfolio di tirocinio?",
               "placeholder": "Es.: il video di un laboratorio"},
    "quiz-0": {"type": "quiz", "title": "Che cos'è l'e-portfolio?",
               "options": ["Un registro dei voti online", "Una raccolta di materiali significativi e di riflessioni personali", "Un test a scelta multipla"]},
    "quiz-1": {"type": "quiz", "title": "Secondo la ricerca, cosa migliora in modo significativo usando l'e-portfolio?",
               "options": ["Il coinvolgimento", "L'autoefficacia", "Il numero di assenze"]},
    "quiz-2": {"type": "quiz", "title": "Cosa significa la sigla del progetto Mosep?",
               "options": ["More Self Esteem with ePortfolios", "Modern School E-Portfolio", "Motivation and Self Evaluation Project"]},
    "voce":   {"type": "poll", "title": "Quale feedback preferite?", "options": ["Lo scritto", "Il vocale"]},
    "ladder": {"type": "ladder", "title": "Commentate il lavoro salendo la Ladder of Feedback",
               "work": "Per spiegare le frazioni in seconda primaria divido una pizza di cartone in 4 parti e chiedo ai bambini quante fette restano se ne mangio una.",
               "options": ["Chiarimento", "Apprezzamento", "Preoccupazione", "Suggerimento"]},
    "badge":  {"type": "poll", "title": "Quale Open Badge vorreste ottenere?",
               "options": ["Peer Reviewer", "Narratore digitale", "Esploratore europeo"]},
    "omp":    {"type": "omp", "title": "One Minute Paper",
               "options": ["Il concetto più importante di oggi", "Lo strumento che vi ha colpito di più", "Un dubbio che vi è rimasto"]},
}

STATE = {"open": None, "rev": 0, "data": {k: {"votes": {}, "texts": []} for k in ACTS}}
URLS = {"lan": None, "public": None, "tunnel": "spento"}
SAVE = os.path.join(HERE, "risultati.json")


def save():
    try:
        out = {}
        for k, d in STATE["data"].items():
            a = ACTS[k]
            out[k] = {"domanda": a["title"],
                      "voti": {o: list(d["votes"].values()).count(i) for i, o in enumerate(a.get("options", []))} if a["type"] in ("poll", "quiz") else None,
                      "risposte": [{"testo": t["text"], **({"tipo": a["options"][t["rung"]]} if t.get("rung") is not None and a.get("options") else {})} for t in d["texts"]]}
        with open(SAVE, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Impossibile salvare i risultati:", e)


def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def admin_view():
    acts = {}
    for k, d in STATE["data"].items():
        a = ACTS[k]
        counts = [0] * len(a.get("options", []))
        for v in d["votes"].values():
            if 0 <= v < len(counts):
                counts[v] += 1
        acts[k] = {"counts": counts, "texts": d["texts"], "people": len(set(d["votes"]) | {t["voter"] for t in d["texts"]})}
    return {"open": STATE["open"], "rev": STATE["rev"], "acts": acts, "urls": URLS}


def phone_view(voter):
    k = STATE["open"]
    if not k:
        return {"open": None, "rev": STATE["rev"]}
    a = ACTS[k]
    d = STATE["data"][k]
    mine = {"vote": d["votes"].get(voter), "sent": sum(1 for t in d["texts"] if t["voter"] == voter)}
    return {"open": dict(a, id=k), "rev": STATE["rev"], "mine": mine}


class H(BaseHTTPRequestHandler):
    server_version = "Cap16"

    def log_message(self, *a):
        pass

    def is_local_presenter(self):
        h = {k.lower() for k in self.headers.keys()}
        if "cf-ray" in h or "cf-connecting-ip" in h or "x-forwarded-for" in h:
            return False
        return self.client_address[0] in ("127.0.0.1", "::1")

    def send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False)
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def file(self, name, token=None):
        with open(os.path.join(HERE, "web", name), encoding="utf-8") as f:
            html = f.read()
        if token:
            html = html.replace('"__ADMIN_TOKEN__"', json.dumps(token))
        self.send(200, html, "text/html; charset=utf-8")

    def body(self):
        n = min(int(self.headers.get("Content-Length") or 0), 10000)
        try:
            return json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return {}

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if u.path == "/":
            if self.is_local_presenter():
                return self.file("index.html", TOKEN)
            self.send_response(302); self.send_header("Location", "/vota"); self.end_headers(); return
        if u.path in ("/vota", "/vota/"):
            return self.file("vota.html")
        if u.path == "/api/state":
            with LOCK:
                return self.send(200, phone_view((q.get("v") or [""])[0][:64]))
        if u.path == "/api/admin":
            if (q.get("t") or [""])[0] != TOKEN:
                return self.send(403, {"error": "non autorizzato"})
            with LOCK:
                return self.send(200, admin_view())
        self.send(404, {"error": "pagina non trovata"})

    def do_POST(self):
        u = urlparse(self.path)
        b = self.body()
        with LOCK:
            if u.path == "/api/vote":
                k, v, opt = STATE["open"], str(b.get("v", ""))[:64], b.get("opt")
                if not k or b.get("act") != k or not v:
                    return self.send(409, {"error": "attività chiusa"})
                a = ACTS[k]
                if a["type"] not in ("poll", "quiz") or not isinstance(opt, int) or not 0 <= opt < len(a["options"]):
                    return self.send(400, {"error": "risposta non valida"})
                STATE["data"][k]["votes"][v] = opt
            elif u.path == "/api/text":
                k, v = STATE["open"], str(b.get("v", ""))[:64]
                text = re.sub(r"\s+", " ", str(b.get("text", ""))).strip()[:280]
                if not k or b.get("act") != k or not v or not text:
                    return self.send(409, {"error": "attività chiusa"})
                a = ACTS[k]
                if a["type"] not in ("text", "ladder", "omp"):
                    return self.send(400, {"error": "risposta non valida"})
                d = STATE["data"][k]
                if sum(1 for t in d["texts"] if t["voter"] == v) >= 6:
                    return self.send(429, {"error": "hai già inviato abbastanza risposte"})
                rung = b.get("rung")
                if a["type"] in ("ladder", "omp") and not (isinstance(rung, int) and 0 <= rung < len(a["options"])):
                    return self.send(400, {"error": "scegli il tipo di risposta"})
                d["texts"].append({"id": secrets.token_hex(4), "voter": v, "text": text, "rung": rung if a["type"] != "text" else None, "t": time.time()})
            elif u.path == "/api/admin":
                if b.get("t") != TOKEN:
                    return self.send(403, {"error": "non autorizzato"})
                cmd, k = b.get("cmd"), b.get("act")
                if cmd == "open" and k in ACTS:
                    STATE["open"] = k
                elif cmd == "close":
                    STATE["open"] = None
                elif cmd == "reset" and k in ACTS:
                    STATE["data"][k] = {"votes": {}, "texts": []}
                elif cmd == "hide" and k in ACTS:
                    STATE["data"][k]["texts"] = [t for t in STATE["data"][k]["texts"] if t["id"] != b.get("id")]
                else:
                    return self.send(400, {"error": "comando sconosciuto"})
            else:
                return self.send(404, {"error": "pagina non trovata"})
            STATE["rev"] += 1
            save()
            return self.send(200, {"ok": True, "rev": STATE["rev"]})


# ---------------- Link pubblico con Cloudflare (facoltativo) ----------------
def cloudflared_path():
    p = shutil.which("cloudflared")
    if p:
        return p
    exe = "cloudflared.exe" if os.name == "nt" else "cloudflared"
    local = os.path.join(HERE, "bin", exe)
    if os.path.exists(local):
        return local
    sysname, arch = platform.system(), platform.machine().lower()
    a = "arm64" if arch in ("arm64", "aarch64") else "amd64"
    if sysname == "Darwin":
        name = f"cloudflared-darwin-{a}.tgz"
    elif sysname == "Windows":
        name = "cloudflared-windows-amd64.exe"
    else:
        name = f"cloudflared-linux-{a}"
    url = "https://github.com/cloudflare/cloudflared/releases/latest/download/" + name
    print("Scarico cloudflared per il link pubblico (solo la prima volta)…")
    os.makedirs(os.path.join(HERE, "bin"), exist_ok=True)
    tmp = os.path.join(HERE, "bin", name)
    urllib.request.urlretrieve(url, tmp)
    if name.endswith(".tgz"):
        with tarfile.open(tmp) as t:
            m = next(m for m in t.getmembers() if m.name.endswith("cloudflared"))
            m.name = exe
            t.extract(m, os.path.join(HERE, "bin"))
        os.remove(tmp)
    elif tmp != local:
        os.replace(tmp, local)
    os.chmod(local, 0o755)
    return local


def tunnel():
    try:
        URLS["tunnel"] = "in avvio"
        exe = cloudflared_path()
        p = subprocess.Popen([exe, "tunnel", "--no-autoupdate", "--url", f"http://localhost:{PORT}"],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        atexit.register(lambda: p.poll() is None and p.terminate())
        for line in p.stdout:
            m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", line)
            if m and not URLS["public"]:
                URLS["public"] = m.group(0)
                URLS["tunnel"] = "attivo"
                print("\n  Link pubblico per i telefoni:", URLS["public"] + "/vota\n")
        URLS["tunnel"] = "chiuso"
    except Exception as e:
        URLS["tunnel"] = "non disponibile"
        print("Link pubblico non disponibile (", e, "). I telefoni possono usare il Wi-Fi:", URLS["lan"])


def main():
    global PORT
    if "--porta" in sys.argv:
        PORT = int(sys.argv[sys.argv.index("--porta") + 1])
    URLS["lan"] = f"http://{lan_ip()}:{PORT}"
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), H)
    print(f"\n  Presentazione pronta.\n  Proiettore:  http://localhost:{PORT}\n  Telefoni (stessa rete Wi-Fi): {URLS['lan']}/vota\n")
    if "--offline" not in sys.argv:
        threading.Thread(target=tunnel, daemon=True).start()
    if "--no-browser" not in sys.argv:
        threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()
    print("  Per chiudere: premi Ctrl+C oppure chiudi questa finestra.\n")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nChiuso. I risultati sono in risultati.json")


if __name__ == "__main__":
    main()
