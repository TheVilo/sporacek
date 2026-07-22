#!/usr/bin/env python3
"""
crawl_ceny.py — automatický zber cien surovín cez crawl4ai do formátu `ceny/*.json`.

POZOR: tento skript beží LOKÁLNE u teba (alebo na serveri s otvorenou sieťou),
NIE vnútri Claude Code na webe — tam sieťová politika blokuje weby obchodov.
Výstupný `ceny/<...>.json` sa potom commitne do repa a prejde kontrolou podľa
skillu `.claude/skills/ceny-z-letaku/SKILL.md` (časť C).

Dva režimy podľa toho, čo ťaháme (viď `CLAUDE.md` → Cenová databáza):

  * css  — z e-shopu obchodu, kde je cena priamo v HTML. NEPOUŽÍVA LLM = zadarmo.
           Typicky BEŽNÉ (needzľavnené) ceny → doplnia diery pri oceňovaní receptov.
  * llm  — z vizuálneho web-letáku, kde treba OCR/porozumenie. Používa Gemini Flash
           (najlacnejší), fallback keď css nestačí. Typicky AKCIOVÉ ceny.

Použitie:
    # najprv jednorazovo (lokálne):
    pip install -r scripts/requirements-crawl.txt
    playwright install chromium

    # potom:
    python scripts/crawl_ceny.py kaufland-eshop            # css režim (zadarmo)
    python scripts/crawl_ceny.py kaufland-letak            # llm režim (Gemini)
    python scripts/crawl_ceny.py kaufland-eshop --dry-run  # neuloží, len vypíše

LLM režim potrebuje kľúč:  export GEMINI_API_KEY=...   (alebo --api-key)

Nová konfigurácia obchodu = pridaj záznam do STORES nižšie. Selektory pre css
režim si over v prehliadači (F12 → Inspect) na konkrétnom e-shope — každý web
je iný a bez živého prístupu ich nevieme uhádnuť za teba.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CENY_DIR = REPO / "ceny"

# ── Pevná sada kategórií (musí sedieť s CLAUDE.md, nevymýšľaj nové) ──────────
KATEGORIE = [
    "Mäso a ryby",
    "Ovocie a zelenina",
    "Mliečne a vajcia",
    "Trvanlivé a základ",
    "Orechy a sladkosti",
    "Pečivo a pekáreň",
]

# Kľúčové slová → kategória (heuristika; jednoduchá, po zbere ešte prejde kontrola).
KATEGORIA_KEYWORDS = {
    "Mäso a ryby": [
        "kur", "morč", "brav", "hovädz", "mäso", "rezeň", "rezn", "steak", "šunk",
        "slanin", "klobás", "párk", "saláma", "ryb", "losos", "tuniak", "krevet",
        "filé", "stehno", "krídl", "mleté", "kačic", "hus",
    ],
    "Ovocie a zelenina": [
        "jablk", "hrušk", "marhul", "broskyn", "slivk", "čeres", "višn", "hrozn",
        "melón", "banán", "pomaranč", "citrón", "jahod", "malin", "čučoried",
        "paradajk", "uhork", "papri", "cibuľ", "cesnak", "zemiak", "mrkv",
        "kapust", "šalát", "brokolic", "kalerá", "špenát", "avokád", "šampiň",
        "hrášok", "fazuľk", "cuket", "baklažán", "reďkov", "petržlen",
    ],
    "Mliečne a vajcia": [
        "mliek", "mlieko", "smotan", "jogurt", "syr", "tvaroh", "maslo", "vajc",
        "vajíčk", "kefír", "cmar", "žervé", "mascarpone", "mozzarella", "parmez",
        "eidam", "niva", "cottage", "acidko",
    ],
    "Trvanlivé a základ": [
        "múk", "cukor", "olej", "ryž", "cestovin", "špaget", "kečup", "horčic",
        "omáčk", "konzerv", "fazuľ", "šošovic", "cícer", "kokosov", "paradajkov pretl",
        "pretlak", "ocot", "kváskov", "droždie", "korenie", "soľ", "med", "sirup javor",
        "polievk", "vývar", "strúhank", "krupic", "vločk", "musli",
    ],
    "Orechy a sladkosti": [
        "orech", "mandľ", "kešu", "lieskov", "para orech", "pistác", "semienk",
        "slnečnic", "tekvicov", "chia", "ľanov", "sezam", "kakao", "čokoláda na varenie",
        "hrozienk", "datle", "sušené ovocie",
    ],
    "Pečivo a pekáreň": [
        "chlieb", "rožk", "bageta", "pečivo", "toast", "žemľ", "tortilla", "lavash",
    ],
}

# Scope filter — čo NIKDY nezbierame (viď CLAUDE.md / ceny-z-letaku prompt).
VYNECHAT_KEYWORDS = [
    "pivo", "víno", "vodka", "rum", "whisky", "gin", "likér", "sekt", "prosecco",
    "minerálk", "sýten", "malinovk", "kofol", "cola", "džús", "šťava", "nektár",
    "sirup", "ľadový čaj", "energetick", "red bull", "káva", "espresso", "čaj ",
    "čip", "chips", "snack", "tyčink", "žuvačk", "cukrík", "bonbón", "lízatk",
    "sušienk", "oblátk", "keks", "napolitánk", "zmrzlin", "nanuk", "dezert",
    "croissant", "koláč", "donut", "šiška", "bábovk", "muffin", "torta",
    "pizza", "vyprážan", "obaľovan", "hotové jedlo", "instantn",
    "šampón", "sprchov", "mydlo", "prací", "aviváž", "čistiac", "wc ", "toaletn",
    "krmiv", "granul", "plienk", "detská výživa", "protein", "proteín",
    "kvet", "hračk", "elektronik", "oblečen", "záhrad",
]


def kategorizuj(nazov: str) -> str:
    n = nazov.lower()
    for kat, kws in KATEGORIA_KEYWORDS.items():
        if any(kw in n for kw in kws):
            return kat
    return "Trvanlivé a základ"  # bezpečný default; kontrola to ešte doladí


def je_v_scope(nazov: str) -> bool:
    n = nazov.lower()
    return not any(kw in n for kw in VYNECHAT_KEYWORDS)


def _cislo(x) -> float | None:
    """'1,39 €' / '139' / 1.39 → 1.39 ; nečitateľné → None."""
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return round(float(x), 2)
    s = str(x).strip().replace("€", "").replace("\xa0", " ").strip()
    s = s.replace(",", ".")
    s = "".join(ch for ch in s if ch.isdigit() or ch == ".")
    if not s or s == ".":
        return None
    try:
        return round(float(s), 2)
    except ValueError:
        return None


# ── Konfigurácia obchodov ────────────────────────────────────────────────────
# Selektory sú ILUSTRAČNÉ — over si ich v prehliadači na konkrétnom e-shope.
# schema.fields: name = kľúč vo výstupe, selector = CSS, type = "text"/"attribute".
STORES = {
    "kaufland-eshop": {
        "obchod": "Kaufland",
        "mode": "css",
        "url": "https://www.kaufland.sk/aktualne-ponuky.html",  # over reálnu URL
        "zdroj_kontroly": "crawl4ai e-shop (CSS)",
        "poznamka_default": "bežná cena z e-shopu",
        "schema": {
            "name": "produkty",
            "baseSelector": "article.product, div.product-tile",  # kontajner produktu
            "fields": [
                {"name": "nazov", "selector": ".product-title, h3", "type": "text"},
                {"name": "zlavnena_cena", "selector": ".price, .product-price", "type": "text"},
                {"name": "povodna_cena", "selector": ".price--old, .strikethrough", "type": "text"},
                {"name": "mnozstvo", "selector": ".product-unit, .base-price", "type": "text"},
            ],
        },
    },
    "kaufland-letak": {
        "obchod": "Kaufland",
        "mode": "llm",
        "url": "https://www.kaufland.sk/prospekt.html",  # over reálnu URL web-letáku
        "zdroj_kontroly": "crawl4ai + Gemini (web-leták)",
        "poznamka_default": "",
    },
}


def normalizuj_polozku(raw: dict, store: dict, platnost: str) -> dict | None:
    """Surový záznam z crawlu → položka presne v schéme `ceny/`."""
    nazov = (raw.get("nazov") or "").strip()
    if not nazov or not je_v_scope(nazov):
        return None
    zlavnena = _cislo(raw.get("zlavnena_cena"))
    if zlavnena is None:
        return None  # bez ceny, ktorú zákazník zaplatí, položka nemá zmysel
    povodna = _cislo(raw.get("povodna_cena"))
    zlava = (raw.get("zlava") or "").strip()
    if not zlava and povodna and povodna > zlavnena:
        zlava = f"-{round((1 - zlavnena / povodna) * 100)}%"
    return {
        "strana": raw.get("strana"),  # e-shop nemá stranu → None
        "nazov": nazov,
        "mnozstvo": (raw.get("mnozstvo") or "").strip(),
        "povodna_cena": povodna,
        "zlava": zlava,
        "zlavnena_cena": zlavnena,
        "platnost": platnost,
        "poznamka": (raw.get("poznamka") or store.get("poznamka_default", "")).strip(),
        "obchod": store["obchod"],
        "zdroj_kontroly": store["zdroj_kontroly"],
        "kategoria": kategorizuj(nazov),
    }


def poskladaj_json(polozky: list[dict], store: dict, platnost: str, strany: int) -> dict:
    """Koreň v presnom poradí polí ako ostatné `ceny/*.json`."""
    return {
        "obchod": store["obchod"],
        "platnost_tyzdenna_default": platnost,
        "pocet_stran_v_katalogu": strany,
        "pocet_potravinovych_polozok": len(polozky),
        "poznamka_metodika": (
            f"Automatický zber cez crawl4ai ({store['mode']} režim) z {store['url']}. "
            "Len skutočné suroviny na varenie (alkohol, nápoje, snacky, drogéria a "
            "nepotraviny vynechané). Kategórie priradené heuristicky podľa názvu. "
            "Výstup pred importom prejde kontrolou podľa skillu ceny-z-letaku."
        ),
        "polozky": polozky,
    }


def tyzden_platnost(dnes: date | None = None) -> str:
    """Default platnosť: štvrtok–streda okolo dneška (typický cyklus letákov)."""
    d = dnes or date.today()
    zaciatok = d - timedelta(days=(d.weekday() - 3) % 7)  # najbližší minulý štvrtok
    koniec = zaciatok + timedelta(days=6)
    return f"{zaciatok.isoformat()} - {koniec.isoformat()}"


# ── Crawl (importuje crawl4ai až tu, nech testy logiky bežia aj bez neho) ─────
async def crawl(store: dict, api_key: str | None) -> tuple[list[dict], int]:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
    bconf = BrowserConfig(headless=True, browser_type="chromium",
                          proxy=proxy or None, ignore_https_errors=True)

    if store["mode"] == "css":
        from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
        strat = JsonCssExtractionStrategy(store["schema"])
    else:
        from crawl4ai.extraction_strategy import LLMExtractionStrategy
        key = api_key or os.environ.get("GEMINI_API_KEY")
        if not key:
            sys.exit("LLM režim potrebuje GEMINI_API_KEY (alebo --api-key).")
        strat = LLMExtractionStrategy(
            provider="gemini/gemini-2.0-flash",  # najlacnejší; zmeň podľa potreby
            api_token=key,
            schema={
                "type": "array",
                "items": {"type": "object", "properties": {
                    "nazov": {"type": "string"},
                    "mnozstvo": {"type": "string"},
                    "povodna_cena": {"type": ["number", "null"]},
                    "zlava": {"type": "string"},
                    "zlavnena_cena": {"type": "number"},
                }},
            },
            extraction_type="schema",
            instruction=(
                "Z web-letáku vyextrahuj VŠETKY potravinové suroviny na varenie. "
                "Vynechaj alkohol, nápoje, sirupy, snacky, sladkosti, hotové jedlá, "
                "drogériu a nepotraviny. Ceny ako čísla v eurách (1.39, nie '139'). "
                "povodna_cena = null ak nie je uvedená. zlavnena_cena = cena, ktorú "
                "zákazník zaplatí."
            ),
        )

    run = CrawlerRunConfig(extraction_strategy=strat)
    async with AsyncWebCrawler(config=bconf) as crawler:
        res = await crawler.arun(url=store["url"], config=run)
    if not res.success:
        sys.exit(f"Crawl zlyhal: {getattr(res, 'error_message', 'neznáma chyba')}")
    raw = json.loads(res.extracted_content or "[]")
    return raw, 0


def main() -> None:
    ap = argparse.ArgumentParser(description="Zber cien cez crawl4ai do ceny/*.json")
    ap.add_argument("store", choices=list(STORES), help="ktorý obchod/režim")
    ap.add_argument("--api-key", help="Gemini API kľúč (alebo env GEMINI_API_KEY)")
    ap.add_argument("--platnost", help="'YYYY-MM-DD - YYYY-MM-DD' (inak auto)")
    ap.add_argument("--out", help="cesta k výstupu (inak ceny/<store>-<dátum>.json)")
    ap.add_argument("--dry-run", action="store_true", help="neuloží, len vypíše zhrnutie")
    args = ap.parse_args()

    store = STORES[args.store]
    platnost = args.platnost or tyzden_platnost()

    raw, strany = asyncio.run(crawl(store, args.api_key))
    polozky = [p for p in (normalizuj_polozku(r, store, platnost) for r in raw) if p]
    if not polozky:
        sys.exit("Nič sa nevyextrahovalo — over URL a selektory pre tento obchod.")

    data = poskladaj_json(polozky, store, platnost, strany)
    print(f"✓ {len(polozky)} položiek | {store['obchod']} | {store['mode']} | {platnost}")
    for kat in KATEGORIE:
        n = sum(1 for p in polozky if p["kategoria"] == kat)
        if n:
            print(f"    {kat}: {n}")

    if args.dry_run:
        print("\n(dry-run — neukladám)")
        return

    zaciatok = platnost.split(" - ")[0]
    out = Path(args.out) if args.out else CENY_DIR / f"{args.store}-{zaciatok}.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n→ uložené: {out.relative_to(REPO)}")
    print("  Ďalej: skontroluj podľa skillu ceny-z-letaku (časť C) a commitni.")


if __name__ == "__main__":
    main()
