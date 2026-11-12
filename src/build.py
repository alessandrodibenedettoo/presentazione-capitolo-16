#!/usr/bin/env python3
"""Ricrea web/index.html da src/template.html + illustrazioni + libreria QR.
Uso (dalla cartella principale):  python3 src/build.py"""
import os
H = os.path.dirname(os.path.abspath(__file__))
rd = lambda n: open(os.path.join(H, n), encoding="utf-8").read()
t, icons, qr = rd("template.html"), rd("icons.json"), rd("qrcode.js")
assert "</script" not in icons.lower() and "</script" not in qr.lower()
out = t.replace("/*ICONS*/", icons, 1).replace("/*QRLIB*/", qr, 1)
dst = os.path.join(H, "..", "web", "index.html")
open(dst, "w", encoding="utf-8").write(out)
print(len(out) // 1024, "KB ->", os.path.normpath(dst))
