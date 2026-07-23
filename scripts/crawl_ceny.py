#!/usr/bin/env python3
"""
crawl_ceny.py — automatický zber cien surovín cez crawl4ai do formátu `ceny/*.json`.

Určené primárne pre **GitHub Actions** (`.github/workflows/zber-cien.yml`) —
beží na serveroch GitHubu, kde je otvorená sieť. NEbeží vnútri Claude Code na
webe (sieťová politika blokuje weby obchodov) a netreba ho spúšťať lokálne.
Výstupné `ceny/*.json` workflow zabalí do Pull Requestu, ktorý prejde kontrolou
podľa skillu `.claude/skills/ceny-z-letaku/SKILL.md` (časť C) a potom sa mergne.

Režimy extrakcie (pole `mode` v STORES):
  * kimbino — HLAVNÝ režim: na www.kimbino.sk/<slug>/ nájde najnovší leták,
              stiahne obrázky strán a Gemini vision z nich prečíta názvy + ceny.
              Potrebuje GEMINI_API_KEY (bez kľúča sa preskočí). Podozrivé ceny
              prečíta druhýkrát; nečitateľné sa zahodia (nikdy nula).
  * jsonld  — ZADARMO, bez kľúča: číta schema.org JSON-LD z HTML (e-shopy;
              slovenské reťazce ho ale nemajú — preto kimbino)
  * css     — ZADARMO, ale treba per-web selektory v poli `schema`
  * llm     — Gemini text z HTML stránky (leták-prehliadačky obchodov text
              neobsahujú, preto sa nepoužíva)

Priame weby obchodov (lidl.sk, billa.sk, tesco.sk…) NEfungujú ako zdroj —
ich leták-prehliadačky sú obrázkové appky bez cien v HTML (overené 07/2026).

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
        "kapust", "šalát", "brokolic", "kalerá", "karfiol", "špenát", "avokád", "šampiň",
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
# Všetky obchody idú cez Kimbino (aggregátor letákov): skript na prehľadovej
# stránke obchodu sám nájde najnovší celoštátny leták, stiahne obrázky strán
# a Gemini vision z nich prečíta názvy + ceny. Priame weby obchodov NEfungujú —
# ich leták-prehliadačky neobsahujú ceny v čitateľnej podobe (overené 07/2026).
# Nový obchod = jeden záznam nižšie (slug z www.kimbino.sk/<slug>/).
STORES = {
    "kaufland": {
        "obchod": "Kaufland", "typ": "akciova", "mode": "kimbino",
        "url": "https://www.kimbino.sk/kaufland/", "kimbino_slug": "kaufland",
    },
    "lidl": {
        "obchod": "Lidl", "typ": "akciova", "mode": "kimbino",
        "url": "https://www.kimbino.sk/lidl/", "kimbino_slug": "lidl",
    },
    "tesco": {
        "obchod": "Tesco", "typ": "akciova", "mode": "kimbino",
        "url": "https://www.kimbino.sk/tesco/", "kimbino_slug": "tesco",
    },
    "terno": {
        "obchod": "Terno", "typ": "akciova", "mode": "kimbino",
        "url": "https://www.kimbino.sk/terno/", "kimbino_slug": "terno",
    },
    "billa": {
        "obchod": "BILLA", "typ": "akciova", "mode": "kimbino",
        "url": "https://www.kimbino.sk/billa/", "kimbino_slug": "billa",
    },
    "coop-jednota": {
        "obchod": "COOP Jednota", "typ": "akciova", "mode": "kimbino",
        "url": "https://www.kimbino.sk/coop-jednota/", "kimbino_slug": "coop-jednota",
    },
}

# Koľko strán letáku maximálne spracovať (0 = všetky). Nastavuje --max-pages,
# nech sa dá test kimbino režimu spustiť lacno len na pár stranách.
MAX_PAGES = 0

# Odvodené polia podľa (typ ceny, mode) — do schémy `ceny/`.
def _zdroj(mode: str) -> str:
    return {"jsonld": "crawl4ai (JSON-LD)", "css": "crawl4ai (CSS)",
            "llm": "crawl4ai + Gemini",
            "kimbino": "kimbino + Gemini vision"}.get(mode, "crawl4ai")


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
    if zlavnena is None or zlavnena <= 0:
        return None  # bez ceny (alebo s nulou z nečitateľného obrázka) položka nemá zmysel
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

# Gemini model (multimodálny, lacný). Na jednom mieste — používa ho llm aj kimbino
# režim. Pozor: staršie modely Google priebežne ruší (2.0-flash je už NOT_FOUND).
GEMINI_MODEL = "gemini/gemini-flash-latest"

# Odhad ceny Gemini Flash (USD/1M tokenov; približné, real bill je v Google konzole).
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

# Inštrukcia pre Gemini VISION (číta OBRÁZOK strany letáku) — kimbino režim.
_VISION_INSTRUKCIA = (
    "Toto je jedna strana akciového letáku obchodu (obrázok). Vyextrahuj VŠETKY "
    "potravinové suroviny na varenie, ktoré na strane vidíš, aj s cenami. "
    "Vynechaj alkohol, nápoje, sirupy, snacky, sladkosti, hotové jedlá, drogériu "
    "a nepotraviny. Vráť IBA platné JSON pole (nič iné, žiadny text navyše) v tvare "
    '[{"nazov": "...", "mnozstvo": "...", "povodna_cena": 2.49, "zlava": "-30%", '
    '"zlavnena_cena": 1.69}]. Ceny ako čísla v eurách (1.69, nie \"169\"). '
    "povodna_cena = null ak nie je uvedená, zlava = \"\" ak nie je uvedená, "
    "zlavnena_cena = cena ktorú zákazník zaplatí. Ak na strane nie sú potraviny, "
    "vráť prázdne pole []."
)


def _parse_json_array(txt: str) -> list[dict]:
    """Vytiahne JSON pole z odpovede modelu (aj keď je obalené v ```json ... ```)."""
    if not txt:
        return []
    s = txt.strip()
    if s.startswith("```"):
        s = s.strip("`")
        s = s[s.find("\n") + 1:] if "\n" in s else s
    i, j = s.find("["), s.rfind("]")
    if i == -1 or j == -1 or j < i:
        return []
    try:
        data = json.loads(s[i:j + 1])
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, ValueError):
        return []


def _kimbino_strany(html: str) -> list[str]:
    """Z HTML letáka na Kimbine vytiahne URL plných obrázkov strán (0.jpg, 1.jpg…)."""
    import re as _re
    # pozor: URL obsahuje filters:format(webp):quality(65) — v triede znakov NESMIE
    # byť ')' , inak sa vzor zastaví na zátvorke a nenájde nič. Hranica = úvodzovka/medzera.
    pat = _re.compile(
        r'https://eu\.kimbicdn\.com/thumbor/[^"\'\s]+?/sk/data/\d+/\d+/(\d+)\.jpg[^"\'\s]*')
    seen: dict[int, str] = {}
    for m in pat.finditer(html):
        page = int(m.group(1))
        seen.setdefault(page, m.group(0))
    return [seen[p] for p in sorted(seen)]


async def crawl_kimbino(store: dict, api_key: str | None) -> list[dict]:
    """Kimbino leták (obrázky strán) → Gemini vision prečíta ceny. Vráti surové položky."""
    import base64
    import urllib.request
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        print(f"⏭  {store['obchod']}: kimbino režim potrebuje GEMINI_API_KEY — preskočené.")
        return []

    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
    bconf = BrowserConfig(headless=True, browser_type="chromium",
                          proxy=proxy or None, ignore_https_errors=True)
    async with AsyncWebCrawler(config=bconf) as crawler:
        res = await crawler.arun(url=store["url"], config=CrawlerRunConfig())
        if not res.success:
            print(f"⚠  {store['obchod']}: stránka sa nenačítala — "
                  f"{getattr(res, 'error_message', '?')}")
            return []

        # Ak je zadaný slug, ber store['url'] ako prehľad obchodu a nájdi na ňom
        # NAJNOVŠÍ (prvý) leták: čokoľvek pod /<slug>/ s "letak" v názve — prvý
        # odkaz na prehľade je vždy najnovší. Presný tvar sa medzi obchodmi líši
        # (kaufland-letak-..., ale aj tesco-hypermarket-letak-...), preto voľnejší
        # vzor; prefix /<slug>/ zaručuje, že sa nechytí leták iného obchodu.
        slug = store.get("kimbino_slug")
        if slug:
            import re as _re
            m = _re.search(
                rf'href=["\'](?:https://www\.kimbino\.sk)?(/{slug}/[^"\']*letak[^"\']*?)["\']',
                res.html or "", _re.I)
            if not m:
                print(f"⚠  {store['obchod']}: nenašiel sa odkaz na najnovší leták.")
                return []
            letak_url = "https://www.kimbino.sk" + m.group(1)
            print(f"      {store['obchod']}: najnovší leták → {letak_url}")
            res = await crawler.arun(url=letak_url, config=CrawlerRunConfig())
            if not res.success:
                print(f"⚠  {store['obchod']}: leták sa nenačítal — "
                      f"{getattr(res, 'error_message', '?')}")
                return []

    strany = _kimbino_strany(res.html or "")
    if not strany:
        print(f"⚠  {store['obchod']}: nenašli sa obrázky strán letáku (over URL).")
        return []
    spracuj_n = strany[:MAX_PAGES] if MAX_PAGES else strany
    print(f"      {store['obchod']}: leták má {len(strany)} strán, spracujem {len(spracuj_n)} "
          f"(Gemini vision)")

    import litellm
    out: list[dict] = []
    for idx, url in enumerate(spracuj_n):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            img = urllib.request.urlopen(req, timeout=30).read()
        except Exception as e:
            print(f"      strana {idx}: obrázok sa nestiahol — {e}")
            continue
        b64 = base64.b64encode(img).decode()
        try:
            resp = litellm.completion(
                model=GEMINI_MODEL, api_key=key, temperature=0,
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": _VISION_INSTRUKCIA},
                    {"type": "image_url",
                     "image_url": {"url": f"data:image/webp;base64,{b64}"}},
                ]}])
        except Exception as e:
            print(f"      strana {idx}: Gemini chyba — {e}")
            if idx == 0:  # pri prvej chybe vypíš dostupné modely, nech sa neháda
                try:
                    murl = ("https://generativelanguage.googleapis.com/v1beta/"
                            f"models?key={key}&pageSize=100")
                    md = json.loads(urllib.request.urlopen(murl, timeout=30).read())
                    mods = [m.get("name", "") for m in md.get("models", [])
                            if "generateContent" in m.get("supportedGenerationMethods", [])]
                    print("      DOSTUPNÉ MODELY:", ", ".join(mods) or "(žiadne)")
                except Exception as e2:
                    print(f"      (zoznam modelov sa nepodaril: {e2})")
            continue
        u = getattr(resp, "usage", None)
        if u:
            _COST["in"] += getattr(u, "prompt_tokens", 0) or 0
            _COST["out"] += getattr(u, "completion_tokens", 0) or 0
        prods = _parse_json_array(resp.choices[0].message.content or "")

        # Overovacie kolo: položky s nulovou/nečitateľnou cenou skús prečítať z toho
        # istého obrázka ešte raz, cielene po mene. Čo ani potom nemá kladnú cenu,
        # zahodí normalizuj_polozku (nula sa do ceny/ nikdy nedostane).
        podozrive = [p for p in prods if (_cislo(p.get("zlavnena_cena")) or 0) <= 0]
        if podozrive:
            mena = ", ".join(str(p.get("nazov", "?")) for p in podozrive)
            try:
                resp2 = litellm.completion(
                    model=GEMINI_MODEL, api_key=key, temperature=0,
                    messages=[{"role": "user", "content": [
                        {"type": "text", "text": (
                            "Pozri sa na tento obrázok strany letáku EŠTE RAZ, veľmi "
                            f"pozorne, a nájdi presné ceny týchto produktov: {mena}. "
                            "Ak cena produktu na obrázku naozaj nie je čitateľná, "
                            "produkt úplne vynechaj (nikdy nedávaj 0). "
                            + _VISION_INSTRUKCIA)},
                        {"type": "image_url",
                         "image_url": {"url": f"data:image/webp;base64,{b64}"}},
                    ]}])
                u2 = getattr(resp2, "usage", None)
                if u2:
                    _COST["in"] += getattr(u2, "prompt_tokens", 0) or 0
                    _COST["out"] += getattr(u2, "completion_tokens", 0) or 0
                oprava = {str(p.get("nazov", "")).strip().lower(): p
                          for p in _parse_json_array(resp2.choices[0].message.content or "")}
                opravene = 0
                for p in podozrive:
                    n = oprava.get(str(p.get("nazov", "")).strip().lower())
                    if n and (_cislo(n.get("zlavnena_cena")) or 0) > 0:
                        p.update({k: v for k, v in n.items() if k != "strana"})
                        opravene += 1
                print(f"      strana {idx + 1}: {len(podozrive)} podozrivých cien, "
                      f"po overení opravených {opravene}, zvyšok sa zahodí")
            except Exception as e:
                print(f"      strana {idx + 1}: overovacie kolo zlyhalo — {e}")

        for p in prods:
            p["strana"] = idx + 1
        out.extend(prods)
        print(f"      strana {idx + 1}/{len(spracuj_n)}: {len(prods)} položiek")
    return out


# ── Crawl (importuje crawl4ai až tu, nech testy logiky bežia aj bez neho) ─────
async def crawl(store: dict, api_key: str | None, sample: bool = False) -> list[dict]:
    """Stiahne stránku a vráti surové položky. Bez kľúča: jsonld/css. sample=True uloží vzorku."""
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

    if store["mode"] == "kimbino":
        return await crawl_kimbino(store, api_key)

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
            llm_config=LLMConfig(provider=GEMINI_MODEL, api_token=key),
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
    ap.add_argument("--max-pages", type=int, default=0,
                    help="max. počet strán letáku (kimbino režim); 0 = všetky (lacný test)")
    args = ap.parse_args()

    global MAX_PAGES
    MAX_PAGES = args.max_pages

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
