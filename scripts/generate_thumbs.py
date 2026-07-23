#!/usr/bin/env python3
"""
generate_thumbs.py — náhľady fotiek receptov pre zoznamy v appke/na webe.

Plné fotky (fotky/*.jpg, 768×1344, ~150–300 KB) sú priveľké na scrollujúci
zoznam — sekal by sa a míňal dáta. Tento skript vygeneruje k náhľadu
docs/fotky-nahlad/<slug>.jpg (šírka 320 px, JPEG q78, ~10–20 KB), ktorý
servíruje GitHub Pages a používa ho API (foto_nahlad_url) aj stránky.

Idempotentné: náhľad sa generuje len ak chýba alebo je starší než originál.
Spustenie:  python3 scripts/generate_thumbs.py     (potrebuje Pillow)
"""
import os, sys, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

try:
    from PIL import Image
except ImportError:
    print("CHYBA: chýba Pillow — nainštaluj `pip install pillow`", file=sys.stderr)
    sys.exit(1)

SRC, DST, WIDTH, QUALITY = "fotky", "docs/fotky-nahlad", 320, 78

os.makedirs(DST, exist_ok=True)
made = skipped = 0
for src in sorted(glob.glob(f"{SRC}/*.jpg")):
    dst = os.path.join(DST, os.path.basename(src))
    if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
        skipped += 1
        continue
    img = Image.open(src).convert("RGB")
    h = round(img.height * WIDTH / img.width)
    img.resize((WIDTH, h), Image.LANCZOS).save(dst, "JPEG", quality=QUALITY, optimize=True)
    made += 1

# uprac náhľady bez originálu (premenovaný/zmazaný recept)
removed = 0
srcs = {os.path.basename(p) for p in glob.glob(f"{SRC}/*.jpg")}
for p in glob.glob(f"{DST}/*.jpg"):
    if os.path.basename(p) not in srcs:
        os.remove(p)
        removed += 1

total_kb = sum(os.path.getsize(p) for p in glob.glob(f"{DST}/*.jpg")) // 1024
print(f"náhľady: {made} nových, {skipped} aktuálnych, {removed} odstránených — spolu {total_kb} KB")
