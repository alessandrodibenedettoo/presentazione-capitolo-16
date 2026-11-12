#!/usr/bin/env python3
"""Ricrea web/index.html da src/template.html + illustrazioni + libreria QR.
Uso (dalla cartella principale):  python3 src/build.py"""
import os
H = os.path.dirname(os.path.abspath(__file__))
rd = lambda n: open(os.path.join(H, n), encoding="utf-8").read()
t, icons, qr = rd("template.html"), rd("icons.json"), rd("qrcode.js")
assert "</script" not in icons.lower() and "</script" not in qr.lower()
out = t.replace("/*ICONS*/", icons, 1).replace("/*QRLIB*/", qr, 1)
import base64, re
def img(m):
    data = open(os.path.join(H, m.group(1) + ".jpg"), "rb").read()
    return "data:image/jpeg;base64," + base64.b64encode(data).decode()
out = re.sub(r"IMG:([a-z0-9_-]+)", img, out)
dst = os.path.join(H, "..", "web", "index.html")
open(dst, "w", encoding="utf-8").write(out)
print(len(out) // 1024, "KB ->", os.path.normpath(dst))
