#!/usr/bin/env python3
"""
build_databaza.py — postaví hlavnú databázu pre appku (a živé stránky).

Zdroje pravdy (nič sa v nich nemení, len sa z nich číta):
  - suroviny.md                     kanonický zoznam surovín (názvy + kategórie)
  - znalostna-baza/aliasy.json      kurátorované aliasy + jednotky (rastie v čase)
  - ceny/*.json                     cenníky z letákov (cena, platnosť, podmienky)
  - recepty/*.md                    recepty (suroviny + množstvá, NIKDY cena)

Výstup (generovaný, needituj ručne — vždy sa prepíše týmto skriptom):
  - docs/data/databaza.json         hlavná databáza pre appku aj stránky

Princíp: každá surovina má stabilné id. Cez id sa deterministicky spája
recept -> surovina -> cena (platnosť od-do, podmienka). Žiadne fuzzy hádanie
za behu — párovanie letáku na surovinu drží kurátorovaná alias-vrstva.

Spustenie:  python3 scripts/build_databaza.py
"""
import re, json, glob, os, sys, unicodedata
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

# ---------- normalizácia názvov (rovnaká logika ako docs/vyber.html) ----------
def strip_dia(s):
    return "".join(c for c in unicodedata.normalize("NFD", s or "")
                   if unicodedata.category(c) != "Mn")

def norm(s):
    s = strip_dia((s or "").lower())
    s = re.sub(r"\([^)]*\)", " ", s)          # (konzervovaná), (kocka) ...
    s = re.sub(r"\b\d+([.,]\d+)?\s*%", " ", s) # 3,5 %
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return s

# ---------- kanonické suroviny zo suroviny.md ----------
DEFAULT_UNIT_BY_CAT = {
    "Mäso a ryby": "g", "Zelenina": "g", "Ovocie": "g",
    "Orechy a semienka": "g", "Strukoviny a obilniny": "g",
    "Mliečne a vajcia": "g", "Základy a koreniny": "g",
}

# trvanlivosť: "cerstve" (kúpiť čerstvé na tento týždeň) vs "trvanlive"
# (odkladá sa do špajze, kúpi sa raz a vydrží). Základ podľa kategórie,
# výnimky (konzervy, skladovateľná zelenina, pečivo…) v aliasy.json.
DEFAULT_TRV_BY_CAT = {
    "Mäso a ryby": "cerstve", "Zelenina": "cerstve", "Ovocie": "cerstve",
    "Mliečne a vajcia": "cerstve",
    "Orechy a semienka": "trvanlive", "Strukoviny a obilniny": "trvanlive",
    "Základy a koreniny": "trvanlive",
}

# odhad trvanlivosti ČERSTVEJ suroviny v dňoch (pre špajzu: "spotrebuj do X").
# Základ podľa kategórie, presnejšie hodnoty per surovina v aliasy.json
# (spotreba_dni). Trvanlivé suroviny nemajú default (v horizonte plánovania
# nevypršia) — ale override v aliasy.json ich môže doplniť.
DEFAULT_SPOTREBA_BY_CAT = {
    "Mäso a ryby": 2, "Mliečne a vajcia": 7,
    "Zelenina": 7, "Ovocie": 6,
}

def slugify(nazov):
    s = strip_dia(nazov.lower())
    s = re.sub(r"\([^)]*\)", " ", s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s

def load_canonical():
    """Vráti zoznam surovín zo suroviny.md: {id, nazov, kategoria}."""
    out, cat = [], None
    for line in open("suroviny.md", encoding="utf-8"):
        line = line.rstrip("\n")
        h = re.match(r"^##\s+(.+)$", line.strip())
        if h:
            cat = h.group(1).strip()
            continue
        if line.strip().startswith("- "):
            nazov = line.strip()[2:].strip()
            out.append({"id": slugify(nazov), "nazov": nazov, "kategoria": cat})
    return out

# ---------- kurátorovaná alias-vrstva ----------
def load_aliasy():
    p = "znalostna-baza/aliasy.json"
    if not os.path.exists(p):
        return {}
    return json.load(open(p, encoding="utf-8")).get("suroviny", {})

# ---------- cenníky ----------
def parse_platnost(s):
    """'2026-07-13 - 2026-07-19' -> ('2026-07-13','2026-07-19')."""
    if not s:
        return (None, None)
    m = re.findall(r"(\d{4}-\d{2}-\d{2})", s)
    if len(m) >= 2:
        return (m[0], m[1])
    if len(m) == 1:
        return (m[0], m[0])
    return (None, None)

def parse_package(mnozstvo):
    """Veľkosť balenia z letáku -> {qty, unit} v základnej jednotke (g/ml/ks)."""
    if not mnozstvo:
        return None
    s = mnozstvo.lower()
    if re.search(r"cena\s*za\s*1\s*kg", s):
        return {"qty": 1000, "unit": "g"}
    if re.search(r"cena\s*za\s*1\s*l\b", s):
        return {"qty": 1000, "unit": "ml"}
    m = re.search(r"(\d+[.,]?\d*)\s*(kg|g|ml|l|ks)\b", s)
    if not m:
        return None
    qty = float(m.group(1).replace(",", "."))
    unit = m.group(2)
    if unit == "kg":
        return {"qty": qty * 1000, "unit": "g"}
    if unit == "l":
        return {"qty": qty * 1000, "unit": "ml"}
    return {"qty": qty, "unit": unit}

# ---------- množstvo v recepte (rovnaká logika ako docs/vyber.html) ----------
def parse_recipe_qty(mnozstvo, pkg_unit_hint):
    if not mnozstvo:
        return None
    s = mnozstvo.lower()
    # POZOR: lyžica/lyžička kontroluj PRED generickými jednotkami — inak by
    # „1 lyžica" chytilo „l" (liter) zo slova lyžica. PL/ČL = objemový odhad.
    m = re.search(r"(\d+[.,]?\d*)\s*(čl|čajov\w*\s*lyžičk\w*|lyžičk\w*)\b", s)
    if m:
        qty = float(m.group(1).replace(",", "."))
        unit = "ml" if pkg_unit_hint == "ml" else "g"
        return {"qty": qty * 5, "unit": unit, "approx": True}
    m = re.search(r"(\d+[.,]?\d*)\s*(pl|polievkov\w*\s*lyžic\w*|lyžic\w*)\b", s)
    if m:
        qty = float(m.group(1).replace(",", "."))
        unit = "ml" if pkg_unit_hint == "ml" else "g"
        return {"qty": qty * 15, "unit": unit, "approx": True}
    # generické jednotky — \b zabráni, aby „l" chytilo začiatok iného slova
    m = re.search(r"(\d+[.,]?\d*)\s*(kg|g|ml|l|ks|strúčik\w*|balen\w*)\b", s)
    if m:
        qty = float(m.group(1).replace(",", "."))
        unit = m.group(2)
        if unit.startswith("strúčik") or unit.startswith("balen"):
            unit = "ks"
        if unit == "kg":
            return {"qty": qty * 1000, "unit": "g"}
        if unit == "l":
            return {"qty": qty * 1000, "unit": "ml"}
        return {"qty": qty, "unit": unit}
    return None

# ---------- matcher: názov (leták/recept) -> id suroviny ----------
class Matcher:
    def __init__(self, suroviny):
        # exact index: normovaný alias -> id ; + zoznam (aliasKey,id) na substring
        self.exact = {}
        self.phrases = []  # (alias_norm, id) zoradené od najdlhšieho
        for s in suroviny:
            for a in s["_alias_all"]:
                k = norm(a)
                if len(k) < 3:
                    continue
                self.exact.setdefault(k, s["id"])
                self.phrases.append((k, s["id"]))
        self.phrases.sort(key=lambda x: -len(x[0]))

    def match(self, nazov):
        k = norm(nazov)
        if len(k) < 3:
            return None
        if k in self.exact:
            return self.exact[k]
        # substring: alias sa nachádza v názve (najdlhší alias vyhráva)
        for ak, iid in self.phrases:
            if ak in k:
                return iid
        # obrátene: názov je súčasťou aliasu (kratší recept. názov)
        best, bd = None, 1e9
        for ak, iid in self.phrases:
            if k in ak:
                d = len(ak) - len(k)
                if d < bd:
                    best, bd = iid, d
        return best

# ---------- recepty ----------
# povinné časti štandardného receptu — všetky recepty musia byť rovnaké
REQUIRED_SECTIONS = ["## Foto prompt", "## Suroviny", "## Nutričné hodnoty",
                     "## Postup", "## Tagy"]

def check_format(fname, t):
    """Vráti zoznam odchýlok od štandardného formátu receptu (prázdny = OK)."""
    problems = []
    if t.lstrip().startswith("---"):
        problems.append("začína YAML frontmatterom (---) namiesto '# Názov'")
    if not re.match(r"^#\s+\S", t.lstrip()):
        problems.append("nezačína názvom '# ...'")
    for field in ["**slug:**", "**porcie:**", "**čas prípravy:**", "**foto_url:**"]:
        if field not in t:
            problems.append(f"chýba pole {field}")
    for sec in REQUIRED_SECTIONS:
        if sec not in t:
            problems.append(f"chýba sekcia {sec}")
    return problems

def parse_recipes():
    out = []
    format_warnings = []
    for f in sorted(glob.glob("recepty/*.md")):
        t = open(f, encoding="utf-8").read()
        probs = check_format(f, t)
        if probs:
            format_warnings.append((os.path.basename(f), probs))
        # recepty existujú v dvoch formátoch: (a) markdown s **bold** poľami a
        # ## Tagy, (b) YAML frontmatter (---). Každé pole skúsime oboma spôsobmi.
        def first(*pats, cast=None, default=None):
            for p in pats:
                m = re.search(p, t, re.M)
                if m:
                    v = m.group(1).strip().strip('"')
                    return cast(v) if cast else v
            return default

        slug = first(r"\*\*slug:\*\*\s*(\S+)", r"^id:\s*(\S+)",
                     default=os.path.basename(f)[:-3])
        nazov = first(r"^nazov:\s*(.+)$", r"^#\s+(.+)$", default=slug)
        porcie = first(r"\*\*porcie:\*\*\s*(\d+)", r"^pocet_porcii:\s*(\d+)",
                       r"## Suroviny\s*\((?:pre\s*)?(\d+)", cast=int, default=1)
        foto = first(r"foto_url:\**\s*\"?([^\"\n]+?)\"?\s*$")
        cas = first(r"\*\*čas prípravy:\*\*\s*([^\n]+)", r"^cas_pripravy:\s*(.+)$")

        # tagy: buď `#tag` (markdown), alebo frontmatter blok tagy:
        tagy = re.findall(r"`#([^`]+)`", t)
        if not tagy:
            fmTagy = re.search(r"^tagy:\s*\n((?:\s+\w+:.*\n?)+)", t, re.M)
            if fmTagy:
                for grp in re.findall(r"\[(.*?)\]", fmTagy.group(1)):
                    tagy += [x.strip() for x in grp.split(",") if x.strip()]

        secM = re.search(r"## Suroviny[^\n]*\n(.+?)(?=\n---|\n## |$)", t, re.S)
        ingr = []
        if secM:
            for line in secM.group(1).splitlines():
                line = line.strip()
                if not line.startswith("|") or set(line) <= set("|-: "):
                    continue
                cells = [c.strip() for c in line.strip("|").split("|")]
                if len(cells) < 2 or cells[0].lower() in ("surovina", ""):
                    continue
                ingr.append({"nazov": cells[0], "mnozstvo": cells[1]})

        # postup (kroky)
        postup = []
        pM = re.search(r"## Postup\s*\n(.+?)(?=\n---|\n## |$)", t, re.S)
        if pM:
            for line in pM.group(1).splitlines():
                m = re.match(r"^\s*\d+\.\s*(.+)$", line)
                if m:
                    postup.append(m.group(1).strip())

        # nutričné hodnoty (na porciu, odhad) — tabuľka alebo frontmatter
        def num(*pats):
            for p in pats:
                m = re.search(p, t, re.M)
                if m:
                    return int(m.group(1))
            return None
        nutricne = {
            "kcal": num(r"Energia\s*\|\s*~?(\d+)\s*kcal", r"^\s*kcal:\s*(\d+)"),
            "bielkoviny_g": num(r"Bielkoviny\s*\|\s*~?(\d+)\s*g", r"^\s*bielkoviny_g:\s*(\d+)"),
            "sacharidy_g": num(r"Sacharidy\s*\|\s*~?(\d+)\s*g", r"^\s*sacharidy_g:\s*(\d+)"),
            "tuky_g": num(r"Tuky\s*\|\s*~?(\d+)\s*g", r"^\s*tuky_g:\s*(\d+)"),
        }

        out.append({"slug": slug, "nazov": nazov, "porcie": porcie,
                    "cas_pripravy": cas, "foto_url": foto, "tagy": tagy,
                    "suroviny": ingr, "postup": postup, "nutricne": nutricne})
    return out, format_warnings

# ======================================================================
def main():
    canonical = load_canonical()
    aliasy = load_aliasy()

    # zostav suroviny s aliasmi + jednotkou
    suroviny = []
    id_index = {}
    for c in canonical:
        extra = aliasy.get(c["id"], {})
        unit = extra.get("jednotka") or DEFAULT_UNIT_BY_CAT.get(c["kategoria"], "g")
        trv = extra.get("trvanlivost") or DEFAULT_TRV_BY_CAT.get(c["kategoria"], "trvanlive")
        spotreba = extra.get("spotreba_dni")
        if spotreba is None and trv == "cerstve":
            spotreba = DEFAULT_SPOTREBA_BY_CAT.get(c["kategoria"])
        alias_all = [c["nazov"]] + list(extra.get("aliasy", []))
        s = {"id": c["id"], "nazov": c["nazov"], "kategoria": c["kategoria"],
             "jednotka": unit, "trvanlivost": trv,
             "gramy_za_ks": extra.get("gramy_za_ks"),  # priem. hmotnosť 1 ks (na prepočet a špajžu)
             "spotreba_dni": spotreba,                 # odhad "spotrebuj do X dní" (pre špajžu)
             "alergeny": list(extra.get("alergeny", [])),
             "_alias_all": alias_all, "ceny": []}
        suroviny.append(s)
        id_index[c["id"]] = s

    matcher = Matcher(suroviny)

    # ---- cenníky -> ceny k surovinám ----
    # História cien (suroviny[].ceny[]) drží VŠETKY letáky (aj staré) — na grafy
    # a štatistiky. Ale ceny receptov sa počítajú LEN z najnovšieho letáku
    # každého obchodu — inak by sa po pridaní ďalšieho týždňa miešali staré
    # (už neplatné) zľavy s novými.
    unmatched_catalog = {}
    all_records = []          # (letak_od, rec) — všetko, aj história
    letak_od_by_store = {}    # obchod -> najnovší dátum začiatku letáku
    for f in sorted(glob.glob("ceny/*.json")):
        d = json.load(open(f, encoding="utf-8"))
        obchod = d.get("obchod", "?")
        default_platnost = d.get("platnost_tyzdenna_default")
        letak_od = (parse_platnost(default_platnost)[0]
                    or (re.search(r"(\d{4}-\d{2}-\d{2})", f) or [None, ""])[1])
        if letak_od > letak_od_by_store.get(obchod, ""):
            letak_od_by_store[obchod] = letak_od
        for p in d.get("polozky", []):
            iid = matcher.match(p["nazov"])
            if not iid:
                unmatched_catalog[p["nazov"]] = unmatched_catalog.get(p["nazov"], 0) + 1
                continue
            od, do = parse_platnost(p.get("platnost") or default_platnost)
            pkg = parse_package(p.get("mnozstvo"))
            rec = {
                "obchod": obchod,
                "nazov_v_letaku": p["nazov"],
                "mnozstvo": p.get("mnozstvo"),
                "balenie_qty": pkg["qty"] if pkg else None,
                "balenie_jednotka": pkg["unit"] if pkg else None,
                "povodna_cena": p.get("povodna_cena"),
                "zlavnena_cena": p.get("zlavnena_cena"),
                "zlava": p.get("zlava"),
                "platnost_od": od,
                "platnost_do": do,
                "podmienka": p.get("poznamka") or None,
                "kategoria_letak": p.get("kategoria"),
                # jednotková cena (€ za 1 g/ml/ks) — nech appka neprepočítava
                "jednotkova_cena": (round(p["zlavnena_cena"] / pkg["qty"], 5)
                                    if pkg and pkg.get("qty") and isinstance(p.get("zlavnena_cena"), (int, float))
                                    else None),
            }
            id_index[iid]["ceny"].append(rec)
            all_records.append((letak_od, iid, rec))

    # na cenenie receptov len najnovší leták per obchod
    catalog_by_store = {}  # obchod -> id -> [polozky z najnovšieho letáku]
    for letak_od, iid, rec in all_records:
        if letak_od == letak_od_by_store.get(rec["obchod"]):
            catalog_by_store.setdefault(rec["obchod"], {}).setdefault(iid, []).append(rec)

    # ---- štatistiky per surovina (bežná cena z celej histórie) ----
    # bežná jednotková cena = medián z pôvodných (nezľavnených) cien; kde
    # pôvodná chýba, berie sa zľavnená. Slúži na "zlacnelo o X %" v appke
    # aj na social fakty ("o 55 % lacnejšie ako priemer").
    for s in suroviny:
        unit_prices = []
        for c in s["ceny"]:
            if not c["balenie_qty"] or c["balenie_jednotka"] != s["jednotka"]:
                continue
            base = c["povodna_cena"] if isinstance(c["povodna_cena"], (int, float)) else c["zlavnena_cena"]
            if isinstance(base, (int, float)):
                unit_prices.append(base / c["balenie_qty"])
        if unit_prices:
            unit_prices.sort()
            n = len(unit_prices)
            med = unit_prices[n // 2] if n % 2 else (unit_prices[n // 2 - 1] + unit_prices[n // 2]) / 2
            s["statistiky"] = {
                "bezna_jednotkova_cena": round(med, 5),
                "min_jednotkova_cena": round(unit_prices[0], 5),
                "pocet_zaznamov": n,
            }
        else:
            s["statistiky"] = None

    # ---- recepty -> id + cena za porciu per obchod ----
    recepty, format_warnings = parse_recipes()
    unmatched_ingr = {}
    stores = sorted(catalog_by_store.keys())

    def best_price_for(iid, obchod):
        """Najlepšie oceniteľné balenie danej suroviny v obchode (najnižšia jedn. cena)."""
        best = None
        for rec in catalog_by_store.get(obchod, {}).get(iid, []):
            if not isinstance(rec["zlavnena_cena"], (int, float)):
                continue
            if not rec["balenie_qty"]:
                continue
            ppu = rec["zlavnena_cena"] / rec["balenie_qty"]
            if best is None or ppu < best["_ppu"]:
                best = {**rec, "_ppu": ppu}
        return best

    for r in recepty:
        # napáruj suroviny receptu na id
        for ing in r["suroviny"]:
            iid = matcher.match(ing["nazov"])
            if not iid and "," in ing["nazov"]:
                iid = matcher.match(ing["nazov"].split(",")[0])
            ing["id"] = iid
            if not iid:
                unmatched_ingr[ing["nazov"]] = unmatched_ingr.get(ing["nazov"], 0) + 1

        # normalizované množstvo priamo na surovine receptu — nech appka vie
        # škálovať porcie a zlučovať nákup z viacerých receptov bez parsovania
        # slovenských textov ("300 g (na rezance)" -> qty=300, jednotka=g).
        # mnozstvo_g = množstvo v g/ml (pri ks prepočet cez gramy_za_ks).
        for ing in r["suroviny"]:
            iid = ing.get("id")
            hint = id_index[iid]["jednotka"] if iid else "g"
            rq = parse_recipe_qty(ing["mnozstvo"], hint)
            ing["qty"] = rq["qty"] if rq else None
            ing["jednotka"] = rq["unit"] if rq else None
            g = None
            if rq:
                if rq["unit"] in ("g", "ml"):
                    g = rq["qty"]
                elif rq["unit"] == "ks" and iid and id_index[iid].get("gramy_za_ks"):
                    g = rq["qty"] * id_index[iid]["gramy_za_ks"]
            ing["mnozstvo_g"] = round(g) if g is not None else None

        # alergény a diétne príznaky receptu — odvodené zo surovín
        rec_alerg = set()
        vegetarianske = True
        veganske = True
        for ing in r["suroviny"]:
            iid = ing.get("id")
            if not iid:
                continue
            s = id_index[iid]
            rec_alerg.update(s["alergeny"])
            if s["kategoria"] == "Mäso a ryby":
                vegetarianske = False
            if s["kategoria"] in ("Mäso a ryby", "Mliečne a vajcia") or iid == "med" \
               or "laktoza" in s["alergeny"] or "vajcia" in s["alergeny"]:
                veganske = False
        r["alergeny"] = sorted(rec_alerg)
        r["vegetarianske"] = vegetarianske
        r["veganske"] = veganske

        # cena za porciu per obchod
        ceny_za_porciu = []
        total = len(r["suroviny"])
        for obchod in stores:
            spolu, usetri, priced = 0.0, 0.0, 0
            plat_od, plat_do = None, None
            nakup = []  # konkrétny produkt na kúpu (so značkou) — pre nákupný zoznam
            for ing in r["suroviny"]:
                iid = ing.get("id")
                if not iid:
                    continue
                bp = best_price_for(iid, obchod)
                if not bp:
                    continue
                item = {
                    "id": iid,
                    "surovina": id_index[iid]["nazov"],
                    "kupit": bp["nazov_v_letaku"],   # konkrétny produkt/značka z letáku
                    "balenie": bp["mnozstvo"],
                    "balenie_qty": bp["balenie_qty"],           # číselne (napr. 500)
                    "balenie_jednotka": bp["balenie_jednotka"], # g / ml / ks
                    "cena_balenia": bp["zlavnena_cena"],
                    "povodna_cena": bp["povodna_cena"],
                    "akcia": bool(bp["zlava"]),
                    "podmienka": bp["podmienka"],
                    "trvanlivost": id_index[iid]["trvanlivost"],
                    "cena_v_recepte": None,
                    "usetris_v_recepte": None,
                }
                rq = parse_recipe_qty(ing["mnozstvo"], bp["balenie_jednotka"])
                # koľko z balenia (v jeho jednotke) recept spotrebuje
                qty_pkg = None
                gpk = id_index[iid].get("gramy_za_ks")
                if rq and bp["balenie_qty"]:
                    if rq["unit"] == bp["balenie_jednotka"]:
                        qty_pkg = rq["qty"]
                    elif rq["unit"] == "ks" and bp["balenie_jednotka"] == "g" and gpk:
                        qty_pkg = rq["qty"] * gpk  # ks -> gramy cez priemernú hmotnosť
                if qty_pkg is not None:
                    cost = (bp["zlavnena_cena"] / bp["balenie_qty"]) * qty_pkg
                    spolu += cost
                    priced += 1
                    item["cena_v_recepte"] = round(cost, 2)
                    item["mnozstvo_g"] = round(qty_pkg) if bp["balenie_jednotka"] in ("g", "ml") else None
                    # úspora = rozdiel oproti pôvodnej (nezľavnenej) cene,
                    # prepočítaný na množstvo, ktoré recept reálne použije
                    if isinstance(bp["povodna_cena"], (int, float)) and bp["povodna_cena"] > bp["zlavnena_cena"]:
                        sav = ((bp["povodna_cena"] - bp["zlavnena_cena"]) / bp["balenie_qty"]) * qty_pkg
                        item["usetris_v_recepte"] = round(sav, 2)
                        usetri += sav
                    # najneskoršie od / najskoršie do pre spoločnú platnosť
                    if bp["platnost_od"]:
                        plat_od = max(plat_od, bp["platnost_od"]) if plat_od else bp["platnost_od"]
                    if bp["platnost_do"]:
                        plat_do = min(plat_do, bp["platnost_do"]) if plat_do else bp["platnost_do"]
                nakup.append(item)
            if priced == 0:
                continue
            spolahlive = priced >= max(1, (total + 1) // 2)  # aspoň polovica surovín
            ceny_za_porciu.append({
                "obchod": obchod,
                "cena_za_porciu": round(spolu / max(1, r["porcie"]), 2),
                "usetris_za_porciu": round(usetri / max(1, r["porcie"]), 2),
                "napar_surovin": priced,
                "spolu_surovin": total,
                "spolahlive": spolahlive,
                "platnost_od": plat_od,
                "platnost_do": plat_do,
                "nakup": nakup,
            })
        ceny_za_porciu.sort(key=lambda x: (not x["spolahlive"], x["cena_za_porciu"]))
        r["ceny_za_porciu"] = ceny_za_porciu
        # súhrn pre karty ("Najlacnejšie v Lidl · ušetríš €0,75")
        best = next((c for c in ceny_za_porciu if c["spolahlive"]), None)
        r["najlacnejsie"] = ({"obchod": best["obchod"],
                              "cena_za_porciu": best["cena_za_porciu"],
                              "usetris_za_porciu": best["usetris_za_porciu"]}
                             if best else None)
        # vyčisti interné
        for ing in r["suroviny"]:
            ing.setdefault("id", None)

    # ---- zapíš databázu ----
    for s in suroviny:
        del s["_alias_all"]
        # zoraď ceny podľa obchodu a dátumu
        s["ceny"].sort(key=lambda c: (c["obchod"], c.get("platnost_od") or ""))

    out = {
        "meta": {
            "schema_verzia": 2,
            "generovane": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "zdroj": "scripts/build_databaza.py — generované, needituj ručne",
            "pocet_surovin": len(suroviny),
            "pocet_receptov": len(recepty),
            "obchody": stores,
            # ceny receptov sú z najnovšieho letáku každého obchodu — appka
            # podľa toho vie, či sú dáta aktuálne alebo už po platnosti
            "aktualny_letak_od": letak_od_by_store,
        },
        "suroviny": suroviny,
        "recepty": recepty,
    }
    os.makedirs("docs/data", exist_ok=True)
    with open("docs/data/databaza.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)

    # ---- report pokrytia ----
    sur_s_cenou = sum(1 for s in suroviny if s["ceny"])
    ingr_total = sum(len(r["suroviny"]) for r in recepty)
    ingr_mapped = sum(1 for r in recepty for i in r["suroviny"] if i.get("id"))
    recepty_ocenene = sum(1 for r in recepty if any(c["spolahlive"] for c in r["ceny_za_porciu"]))
    print("=" * 60)
    print("DATABÁZA VYGENEROVANÁ -> docs/data/databaza.json")
    print("=" * 60)
    print(f"suroviny (kanonické):        {len(suroviny)}")
    print(f"  z toho s aspoň 1 cenou:    {sur_s_cenou}")
    print(f"recepty:                     {len(recepty)}")
    print(f"  spoľahlivo ocenené (≥1 obchod): {recepty_ocenene}")
    print(f"suroviny v receptoch:        {ingr_total}")
    print(f"  napárované na id:          {ingr_mapped} ({100*ingr_mapped//max(1,ingr_total)} %)")
    print(f"letákové názvy nespárované:  {len(unmatched_catalog)} (z rôznych obchodov)")
    if format_warnings:
        print()
        print("⚠ RECEPTY MIMO ŠTANDARDNÉHO FORMÁTU (všetky recepty musia byť rovnaké):")
        for name, probs in format_warnings:
            print(f"  • {name}: {'; '.join(probs)}")
    else:
        print("formát receptov:            ✓ všetkých", len(recepty), "v štandardnom formáte")
    print()
    # ulož nespárované pre kuráciu aliasov
    dbg = "scripts/.nesparovane.json"
    json.dump({
        "letak_nesparovane": dict(sorted(unmatched_catalog.items(), key=lambda x: -x[1])),
        "recept_ingr_nesparovane": dict(sorted(unmatched_ingr.items(), key=lambda x: -x[1])),
    }, open(dbg, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"(nespárované názvy pre kuráciu -> {dbg})")

if __name__ == "__main__":
    main()
