#!/usr/bin/env python3
"""
crawl_ceny.py — automatický zber cien surovín cez crawl4ai do formátu `ceny/*.json`.

Určené primárne pre **GitHub Actions** (`.github/workflows/zber-cien.yml`) —
beží na serveroch GitHubu, kde je otvorená sieť. NEbeží vnútri Claude Code na
webe (sieťová politika blokuje weby obchodov) a netreba ho spúšťať lokálne.
Výstupné `ceny/*.json` workflow zabalí do Pull Requestu, ktorý prejde kontrolou
podľa skillu `.claude/skills/ceny-z-letaku/SKILL.md` (časť C) a potom sa mergne.

Režimy extrakcie (pole `mode` v STORES) — primárne FREE, Gemini až keď treba:
  * jsonld — default, ZADARMO, bez kľúča: číta schema.org JSON-LD z HTML
  * css    — ZADARMO, ale treba per-web selektory v poli `schema`
  * llm    — Gemini Flash, potrebuje GEMINI_API_KEY (bez kľúča sa preskočí)

Typ ceny (viď `CLAUDE.md` → Cenová databáza):
  * akciova — z web-letáku obchodu (dočasné akciové ceny)
  * bezna   — z e-shopu obchodu (bežné ceny → doplnia diery pri oceňovaní receptov)

Použitie:
    python scripts/crawl_ceny.py --all                 # všetky obchody (workflow)
    python scripts/crawl_ceny.py --all --sample        # + ulož vzorku stránok
    python scripts/crawl_ceny.py kaufland-letak        # jeden obchod
    python scripts/crawl_ceny.py --all --dry-run       # nič neuloží, len vypíše

Nový obchod = pridaj záznam do STORES nižšie (obchod + typ + mode + url).
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


# ── JSON-LD extrakcia (zadarmo, bez LLM, bez per-web selektorov) ──────────────
# Veľa e-shopov vkladá do stránky schema.org dáta v <script type="application/ld+json">.
# Z nich vieme vytiahnuť názov + cenu bez kľúča aj bez ladenia selektorov.
def _najdi_produkty(uzol, out: list[dict]) -> None:
    """Rekurzívne prejde JSON-LD a nazbiera Product/Offer uzly s cenou."""
    if isinstance(uzol, list):
        for x in uzol:
            _najdi_produkty(x, out)
        return
    if not isinstance(uzol, dict):
        return
    typ = uzol.get("@type", "")
    typy = typ if isinstance(typ, list) else [typ]
    if any(t in ("Product", "Offer") for t in typy) or "offers" in uzol:
        nazov = uzol.get("name") or uzol.get("title")
        offer = uzol.get("offers", uzol)
        if isinstance(offer, list):
            offer = offer[0] if offer else {}
        cena = None
        if isinstance(offer, dict):
            cena = (offer.get("price") or offer.get("lowPrice")
                    or (offer.get("priceSpecification") or {}).get("price"))
        if nazov and cena is not None:
            out.append({"nazov": str(nazov), "zlavnena_cena": cena,
                        "povodna_cena": None, "mnozstvo": ""})
    # zanoríme sa do vnútra (napr. @graph, itemListElement)
    for v in uzol.values():
        if isinstance(v, (list, dict)):
            _najdi_produkty(v, out)


def extrahuj_jsonld(html: str) -> list[dict]:
    """Vytiahne produkty zo všetkých JSON-LD blokov v HTML."""
    import re as _re
    out: list[dict] = []
    for m in _re.finditer(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, _re.S | _re.I,
    ):
        try:
            data = json.loads(m.group(1).strip())
        except (json.JSONDecodeError, ValueError):
            continue
        _najdi_produkty(data, out)
    return out


# ── Konfigurácia obchodov ────────────────────────────────────────────────────
# Každý záznam: obchod, url, typ ("akciova" z letáku / "bezna" z e-shopu), mode.
# mode:
#   "jsonld" — default, ZADARMO, bez kľúča, bez selektorov (schema.org v HTML)
#   "css"    — ZADARMO, ale treba per-web selektory v poli "schema" (záloha)
#   "llm"    — Gemini, potrebuje GEMINI_API_KEY (až keď ho používateľ dodá)
# Kľúč = <obchod>-<typ>, napr. "kaufland-letak", "kaufland-eshop".
#
STORES = {
    # ── PILOT (prieskum): aggregátor letákov ako zdroj pre Kaufland. mode jsonld
    #    = zadarmo, len stiahne a uloží vzorku (--sample), nech vidíme, čo reálny
    #    prehliadač na stránke dostane (text produktov vs. len obrázky, anti-bot). ──
    "kaufland-agg": {
        "obchod": "Kaufland",
        "typ": "akciova",
        "mode": "jsonld",
        "url": "https://www.kimbino.sk/kaufland/",
    },

    # ── FREE teraz: skutočný e-shop s produktovými stránkami (skúsi JSON-LD) ──
    "billa-eshop": {
        "obchod": "BILLA",
        "typ": "bezna",
        "mode": "jsonld",
        "url": "https://www.billa.sk/produkty/",
    },

    # ── Vizuálne letáky/katalógy: štruktúrované ceny nemajú → potrebujú OCR/LLM.
    #    mode "llm" = kým workflow neinjektuje GEMINI_API_KEY, automaticky sa
    #    PRESKOČIA (žiadny Gemini, žiadne náklady). Zapnú sa až keď šporáček
    #    zarába — vtedy stačí vo workflowe odkomentovať GEMINI_API_KEY. ──────────
    "billa-letak": {
        "obchod": "BILLA", "typ": "akciova", "mode": "llm",
        "url": "https://www.billa.sk/letaky-a-akcie",
    },
    "lidl-letak": {
        "obchod": "Lidl", "typ": "akciova", "mode": "llm",
        "url": "https://www.lidl.sk/c/online-letak/s10008489",
    },
    "tesco-hypermarket-letak": {
        "obchod": "Tesco hypermarket", "typ": "akciova", "mode": "llm",
        "url": "https://www.tesco.sk/akciove-ponuky/letaky-a-katalogy/tesco-hypermarket-bratislava-zlate-piesky",
    },
    "tesco-supermarket-letak": {
        "obchod": "Tesco supermarket", "typ": "akciova", "mode": "llm",
        "url": "https://www.tesco.sk/akciove-ponuky/letaky-a-katalogy/tesco-supermarket-zarnovica",
    },
    "terno-letak": {
        "obchod": "Terno", "typ": "akciova", "mode": "llm",
        "url": "https://terno.sk/sekcia/7-akciovy-letak",
    },
    # Pozn.: Lidl a Terno majú LEN letáky (žiadny e-shop) → bežné ceny sa z nich
    # nedajú ťahať. Tesco má aj e-shop potravín (potravinydomov.itesco.sk) —
    # ak budeme chcieť bežné Tesco ceny free, pridá sa ako ďalší 'bezna'/jsonld.
}

# Odvodené polia podľa (typ ceny, mode) — do schémy `ceny/`.
def _zdroj(mode: str) -> str:
    return {"jsonld": "crawl4ai (JSON-LD)", "css": "crawl4ai (CSS)",
            "llm": "crawl4ai + Gemini"}.get(mode, "crawl4ai")


def _store(kluc: str) -> dict:
    """Doplní odvodené polia (zdroj_kontroly, poznamka_default) k STORES záznamu."""
    s = dict(STORES[kluc])
    s.setdefault("mode", "jsonld")
    s["zdroj_kontroly"] = _zdroj(s["mode"])
    s["poznamka_default"] = "bežná cena z e-shopu" if s["typ"] == "bezna" else ""
    return s


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


SAMPLES_DIR = REPO / "scripts" / "_samples"

# Odhad ceny Gemini 2.0 Flash (USD/1M tokenov; približné, real bill je v Google konzole).
GEMINI_FLASH_USD = {"in": 0.10, "out": 0.40}
USD_EUR = 0.92
_COST = {"in": 0, "out": 0}  # kumulatívne tokeny za celý beh


def _zmeraj_cenu(strat) -> None:
    """Prečíta spotrebu tokenov z LLMExtractionStrategy a pripočíta k _COST."""
    tu = getattr(strat, "total_usage", None)
    inp = getattr(tu, "prompt_tokens", 0) or 0
    out = getattr(tu, "completion_tokens", 0) or 0
    if not inp and not out:  # fallback: posčítaj z jednotlivých usages
        for u in getattr(strat, "usages", []) or []:
            inp += getattr(u, "prompt_tokens", 0) or 0
            out += getattr(u, "completion_tokens", 0) or 0
    _COST["in"] += inp
    _COST["out"] += out
    if inp or out:
        eur = (inp / 1e6 * GEMINI_FLASH_USD["in"]
               + out / 1e6 * GEMINI_FLASH_USD["out"]) * USD_EUR
        print(f"      Gemini: {inp} vstup + {out} výstup tokenov ≈ {eur:.4f} €")


def vypis_celkovu_cenu() -> None:
    inp, out = _COST["in"], _COST["out"]
    if not (inp or out):
        return
    eur = (inp / 1e6 * GEMINI_FLASH_USD["in"]
           + out / 1e6 * GEMINI_FLASH_USD["out"]) * USD_EUR
    print(f"\n💶 Gemini spolu: {inp + out} tokenov (~{inp} vstup / {out} výstup) "
          f"≈ {eur:.4f} € (odhad; presný účet je v Google AI Studio).")

# LLM extrakčná schéma + inštrukcia (použije sa len v llm režime).
_LLM_SCHEMA = {
    "type": "array",
    "items": {"type": "object", "properties": {
        "nazov": {"type": "string"},
        "mnozstvo": {"type": "string"},
        "povodna_cena": {"type": ["number", "null"]},
        "zlava": {"type": "string"},
        "zlavnena_cena": {"type": "number"},
    }},
}
_LLM_INSTRUKCIA = (
    "Z web-letáku/e-shopu vyextrahuj VŠETKY potravinové suroviny na varenie. "
    "Vynechaj alkohol, nápoje, sirupy, snacky, sladkosti, hotové jedlá, "
    "drogériu a nepotraviny. Ceny ako čísla v eurách (1.39, nie '139'). "
    "povodna_cena = null ak nie je uvedená. zlavnena_cena = cena, ktorú "
    "zákazník zaplatí."
)


# ── Crawl (importuje crawl4ai až tu, nech testy logiky bežia aj bez neho) ─────
async def crawl(store: dict, api_key: str | None, sample: bool = False) -> list[dict]:
    """Stiahne stránku a vráti surové položky. Bez kľúča: jsonld/css. sample=True uloží vzorku."""
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
    bconf = BrowserConfig(headless=True, browser_type="chromium",
                          proxy=proxy or None, ignore_https_errors=True)

    strat = None
    mode = store["mode"]
    if mode == "css":
        from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
        strat = JsonCssExtractionStrategy(store["schema"])
    elif mode == "llm":
        from crawl4ai import LLMConfig
        from crawl4ai.extraction_strategy import LLMExtractionStrategy
        key = api_key or os.environ.get("GEMINI_API_KEY")
        if not key:
            print(f"⏭  {store['obchod']}: llm režim potrebuje GEMINI_API_KEY — preskočené.")
            return []
        # crawl4ai ≥0.4: provider/api_token sa už nezadávajú priamo, ale cez
        # llm_config=LLMConfig(...). Starý zápis padal na 'provider is deprecated'.
        strat = LLMExtractionStrategy(
            llm_config=LLMConfig(provider="gemini/gemini-2.0-flash", api_token=key),
            schema=_LLM_SCHEMA, extraction_type="schema", instruction=_LLM_INSTRUKCIA)

    run = CrawlerRunConfig(extraction_strategy=strat) if strat else CrawlerRunConfig()
    async with AsyncWebCrawler(config=bconf) as crawler:
        res = await crawler.arun(url=store["url"], config=run)
    if mode == "llm":
        _zmeraj_cenu(strat)
    if not res.success:
        print(f"⚠  {store['obchod']}: crawl zlyhal — {getattr(res, 'error_message', '?')}")
        return []

    if sample:  # ulož vzorku stránky, nech sa dá doladiť extrakcia
        import re as _re
        SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
        html = res.html or ""
        md = res.markdown or ""
        jl = extrahuj_jsonld(html)
        eur = md.count("€")
        imgs = _re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html, _re.I)
        links = _re.findall(r'<a[^>]+href=["\']([^"\']+)["\']', html, _re.I)
        # zaujímavé = obrázky letáku / CDN (nie ikony/ads/loga)
        zaujimave_img = [u for u in imgs if not _re.search(
            r'\.svg|logo|icon|sprite|avatar|googlesyndication|doubleclick', u, _re.I)][:60]
        letak_links = [u for u in links if _re.search(
            r'letak|leaflet|/l/|flyer|akci|katalog', u, _re.I)][:40]
        f = SAMPLES_DIR / f"{store['obchod'].lower()}-{store['typ']}.md"
        f.write_text(
            f"# Vzorka: {store['url']}\n\n"
            f"JSON-LD produktov: {len(jl)} | výskyt '€' v markdowne: {eur} | "
            f"dĺžka markdownu: {len(md)} | <img>: {len(imgs)} | <a>: {len(links)}\n\n"
            f"## Odkazy na leták/katalóg ({len(letak_links)})\n\n"
            + "\n".join(letak_links) + "\n\n"
            f"## Obrázky (bez ikon/log/ads, prvých {len(zaujimave_img)})\n\n"
            + "\n".join(zaujimave_img) + "\n\n"
            f"## Markdown (prvých 15000 znakov)\n\n{md[:15000]}\n\n"
            f"## HTML (prvých 8000 znakov)\n\n```\n{html[:8000]}\n```\n",
            encoding="utf-8")
        print(f"      vzorka → {f.relative_to(REPO)} (JSON-LD: {len(jl)})")

    if mode == "jsonld":
        return extrahuj_jsonld(res.html or "")
    return json.loads(res.extracted_content or "[]")


def spracuj(kluc: str, platnost: str, api_key: str | None,
            dry_run: bool, sample: bool = False) -> bool:
    """Zber jedného obchodu → uloží ceny/<kluc>-<dátum>.json. Vráti True ak sa niečo uložilo."""
    store = _store(kluc)
    if str(store["url"]).startswith("TODO"):
        print(f"⏭  {kluc}: preskočené (nemá URL — doplň link do STORES).")
        return False
    raw = asyncio.run(crawl(store, api_key, sample=sample))
    strany = 0
    polozky = [p for p in (normalizuj_polozku(r, store, platnost) for r in raw) if p]
    if not polozky:
        print(f"⚠  {kluc}: nič sa nevyextrahovalo (over URL / stránku).")
        return False

    data = poskladaj_json(polozky, store, platnost, strany)
    print(f"✓ {kluc}: {len(polozky)} položiek | {store['obchod']} | {store['typ']} | {platnost}")
    for kat in KATEGORIE:
        n = sum(1 for p in polozky if p["kategoria"] == kat)
        if n:
            print(f"      {kat}: {n}")
    if dry_run:
        return False
    zaciatok = platnost.split(" - ")[0]
    out = CENY_DIR / f"{kluc}-{zaciatok}.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"      → {out.relative_to(REPO)}")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Zber cien cez crawl4ai do ceny/*.json")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("store", nargs="?", choices=list(STORES), help="ktorý obchod")
    g.add_argument("--all", action="store_true", help="všetky obchody (pre GitHub Actions)")
    ap.add_argument("--api-key", help="Gemini API kľúč (alebo env GEMINI_API_KEY)")
    ap.add_argument("--platnost", help="'YYYY-MM-DD - YYYY-MM-DD' (inak auto)")
    ap.add_argument("--dry-run", action="store_true", help="neuloží, len vypíše zhrnutie")
    ap.add_argument("--sample", action="store_true",
                    help="ulož vzorku stránky do scripts/_samples/ (na doladenie extrakcie)")
    args = ap.parse_args()

    platnost = args.platnost or tyzden_platnost()
    kluce = list(STORES) if args.all else [args.store]

    ulozene = 0
    for kluc in kluce:
        try:
            ulozene += spracuj(kluc, platnost, args.api_key, args.dry_run, args.sample)
        except SystemExit:
            raise
        except Exception as e:  # jeden obchod nech nezhodí celý beh
            print(f"✗ {kluc}: chyba — {e}")

    vypis_celkovu_cenu()
    if not args.dry_run and ulozene:
        print(f"\nUložených {ulozene} súborov. Ďalej: kontrola podľa skillu "
              "ceny-z-letaku (časť C), potom merge.")


if __name__ == "__main__":
    main()
