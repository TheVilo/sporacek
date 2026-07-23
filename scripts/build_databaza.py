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
    # multibalenie "4 × 100 g" = 400 g (nie 100!)
    m = re.search(r"(\d+)\s*[×x]\s*(\d+[.,]?\d*)\s*(kg|g|ml|l|ks)\b", s)
    if m:
        n = int(m.group(1))
        qty = float(m.group(2).replace(",", ".")) * n
        unit = m.group(3)
    else:
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
# presné definície kuchynských mier a slovných množstiev (gramy, ak nie je
# uvedené inak; pri PL/ČL a pod. sa jednotka g/ml preberá z cieľového balenia)
LYZICA_G = 15      # 1 PL / polievková lyžica
LYZICKA_G = 5      # 1 ČL / čajová lyžička
STIPKA_G = 0.5     # štipka
PODLA_CHUTI_G = 2  # "podľa chuti" / "—" (soľ, korenie…) — nominálny odhad
VETVICKA_G = 2     # 1 vetvička bylinky ("pár vetvičiek" = 5 g)
PAR_LISTKOV_G = 2  # "pár lístkov" (bazalka…)
PLATOK_G = 15      # 1 plátok (syr, citrón…)
ZVAZOK_G = 30      # 1 zväzok byliniek
HRST_G = 30        # 1 hrsť
KVAPKY_G = 1       # "pár kvapiek"
NA_VYPRAZANIE_G = 30   # "na vyprážanie" (olej)
NA_POSYP_G = 5     # "na posyp/podsypanie/ozdobu/podávanie"
CM_G = 5           # 1 cm koreňa (zázvor) ~ 5 g; "kúsok" bez rozmeru ~ 10 g

def parse_recipe_qty(mnozstvo, pkg_unit_hint):
    if not mnozstvo:
        return None
    s = mnozstvo.lower().strip()
    # unicode zlomky -> desatinné čísla (½ ČL, ¼ ks…)
    for frac, dec in (("½", "0.5"), ("¼", "0.25"), ("¾", "0.75"),
                      ("⅓", "0.33"), ("⅔", "0.67"), ("⅛", "0.125")):
        s = s.replace(frac, dec)
    hint_unit = "ml" if pkg_unit_hint == "ml" else "g"

    # POZOR: lyžica/lyžička kontroluj PRED generickými jednotkami — inak by
    # „1 lyžica" chytilo „l" (liter) zo slova lyžica. PL/ČL = objemový odhad.
    m = re.search(r"(\d+[.,]?\d*)\s*(čl|čajov\w*\s*lyžičk\w*|lyžičk\w*)\b", s)
    if m:
        return {"qty": float(m.group(1).replace(",", ".")) * LYZICKA_G,
                "unit": hint_unit, "approx": True}
    m = re.search(r"(\d+[.,]?\d*)\s*(pl|polievkov\w*\s*lyžic\w*|lyžic\w*)\b", s)
    if m:
        return {"qty": float(m.group(1).replace(",", ".")) * LYZICA_G,
                "unit": hint_unit, "approx": True}
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

    # slovné množstvá (vždy odhad)
    def approx(qty, unit="g"):
        return {"qty": qty, "unit": unit, "approx": True}
    if "štipka" in s:
        return approx(STIPKA_G)
    if "podľa chuti" in s or s in ("—", "-", "–"):
        return approx(PODLA_CHUTI_G)
    if "vyprážanie" in s or "vypráž" in s:
        return approx(NA_VYPRAZANIE_G, hint_unit)
    if "posyp" in s or "podsypanie" in s or "ozdob" in s or "podávanie" in s:
        return approx(NA_POSYP_G)
    if "kvapiek" in s or "kvapky" in s:
        return approx(KVAPKY_G, hint_unit)
    m = re.search(r"(\d+[.,]?\d*)\s*plát", s)
    if m:
        return approx(float(m.group(1).replace(",", ".")) * PLATOK_G)
    m = re.search(r"(\d+[.,]?\d*)\s*vetvičk", s)
    if m:
        return approx(float(m.group(1).replace(",", ".")) * VETVICKA_G)
    if "vetvičiek" in s or "vetvičk" in s:
        return approx(5)  # "pár vetvičiek"
    if "lístk" in s:
        return approx(PAR_LISTKOV_G)
    m = re.search(r"(\d+[.,]?\d*)\s*zväz", s)
    if m:
        return approx(float(m.group(1).replace(",", ".")) * ZVAZOK_G)
    if "zväzok" in s:
        return approx(ZVAZOK_G)
    if "hrsť" in s or "hrst" in s:
        return approx(HRST_G)
    m = re.search(r"kúsok[^\d]*(\d+[.,]?\d*)\s*cm", s)
    if m:
        return approx(float(m.group(1).replace(",", ".")) * CM_G)
    if "kúsok" in s:
        return approx(10)
    return None

# ---------- matcher: názov (leták/recept) -> id suroviny ----------
class Matcher:
    def __init__(self, suroviny):
        # exact index: normovaný alias -> id ; + zoznam (aliasKey,id) na substring
        self.exact = {}
        self.phrases = []  # (alias_norm, id) zoradené od najdlhšieho
        self.vyluc = {}    # id -> [norm. podreťazce, pri ktorých sa id NEsmie použiť]
        for s in suroviny:
            self.vyluc[s["id"]] = [norm(v) for v in s.get("_vyluc", [])]
            for a in s["_alias_all"]:
                k = norm(a)
                if len(k) < 3:
                    continue
                self.exact.setdefault(k, s["id"])
                self.phrases.append((k, s["id"]))
        self.phrases.sort(key=lambda x: -len(x[0]))

    def _blocked(self, iid, k):
        return any(v and v in k for v in self.vyluc.get(iid, []))

    def match(self, nazov):
        k = norm(nazov)
        if len(k) < 3:
            return None
        if k in self.exact and not self._blocked(self.exact[k], k):
            return self.exact[k]
        # substring: alias sa nachádza v názve (najdlhší alias vyhráva)
        for ak, iid in self.phrases:
            if ak in k and not self._blocked(iid, k):
                return iid
        # obrátene: názov je súčasťou aliasu (kratší recept. názov)
        best, bd = None, 1e9
        for ak, iid in self.phrases:
            if k in ak and not self._blocked(iid, k):
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
        # bežná cena mimo akcie (fallback pre suroviny, čo nebývajú v letáku —
        # soľ, korenie, múka… User ich väčšinou má doma, ale recept s nimi
        # musí počítať, inak nikdy nedostane úplnú cenu.)
        bezna = None
        if isinstance(extra.get("bezna_cena"), (int, float)) and extra.get("bezne_balenie"):
            bpkg = parse_package(extra["bezne_balenie"])
            if bpkg and bpkg.get("qty"):
                bezna = {"cena": extra["bezna_cena"], "balenie": extra["bezne_balenie"],
                         "qty": bpkg["qty"], "unit": bpkg["unit"]}
        s = {"id": c["id"], "nazov": c["nazov"], "kategoria": c["kategoria"],
             "jednotka": unit, "trvanlivost": trv,
             "gramy_za_ks": extra.get("gramy_za_ks"),  # priem. hmotnosť 1 ks (na prepočet a špajžu)
             "spotreba_dni": spotreba,                 # odhad "spotrebuj do X dní" (pre špajžu)
             "alergeny": list(extra.get("alergeny", [])),
             "sezona": extra.get("sezona"),            # mesiace sezóny (ovocie/zelenina)
             "bezna_cena": extra.get("bezna_cena"),
             "bezne_balenie": extra.get("bezne_balenie"),
             "_bezna": bezna,
             "_vyluc": list(extra.get("vyluc", [])),
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
                # normalizovaný názov produktu (bez diakritiky) — nech appka
                # vie deterministicky matchovať sledované produkty ("rajo
                # maslo") naprieč týždňami bez vlastného porovnávania reťazcov
                "nazov_norm": norm(p["nazov"]),
                # jednotková cena (€ za 1 g/ml/ks) — nech appka neprepočítava
                "jednotkova_cena": (round(p["zlavnena_cena"] / pkg["qty"], 5)
                                    if pkg and pkg.get("qty") and isinstance(p.get("zlavnena_cena"), (int, float))
                                    else None),
            }
            id_index[iid]["ceny"].append(rec)
            all_records.append((letak_od, iid, rec))

    # na cenenie receptov len najnovší leták per obchod
    catalog_by_store = {}  # obchod -> id -> [polozky z najnovšieho letáku]
    current_by_iid = {}    # id -> [aktuálne položky zo všetkých obchodov]
    for letak_od, iid, rec in all_records:
        if letak_od == letak_od_by_store.get(rec["obchod"]):
            catalog_by_store.setdefault(rec["obchod"], {}).setdefault(iid, []).append(rec)
            current_by_iid.setdefault(iid, []).append(rec)

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
        # kde je surovina PRÁVE TERAZ najlacnejšia (len aktuálne letáky) —
        # pre watchlist, špajzu aj "kde kúpiť" bez počítania v appke
        best_now = None
        for c in current_by_iid.get(s["id"], []):
            if c["jednotkova_cena"] is None or c["balenie_jednotka"] != s["jednotka"]:
                continue
            if best_now is None or c["jednotkova_cena"] < best_now["jednotkova_cena"]:
                best_now = c
        s["aktualne_najlacnejsie"] = ({
            "obchod": best_now["obchod"], "nazov_v_letaku": best_now["nazov_v_letaku"],
            "zlavnena_cena": best_now["zlavnena_cena"], "mnozstvo": best_now["mnozstvo"],
            "jednotkova_cena": best_now["jednotkova_cena"], "zlava": best_now["zlava"],
            "podmienka": best_now["podmienka"], "platnost_do": best_now["platnost_do"],
        } if best_now else None)

    # ---- recepty -> id + cena za porciu per obchod ----
    recepty, format_warnings = parse_recipes()
    unmatched_ingr = {}
    stores = sorted(catalog_by_store.keys())

    def best_price_for(iid, obchod):
        """Najlepšie oceniteľné balenie danej suroviny v obchode (najnižšia jedn. cena).
        Balenie "za kus" (šalát, citróny…) sa prepočíta na gramy cez gramy_za_ks,
        nech vie oceniť aj recepty s množstvom v gramoch."""
        gpk = id_index[iid].get("gramy_za_ks")
        best = None
        for rec in catalog_by_store.get(obchod, {}).get(iid, []):
            if not isinstance(rec["zlavnena_cena"], (int, float)):
                continue
            if not rec["balenie_qty"]:
                continue
            qty, unit = rec["balenie_qty"], rec["balenie_jednotka"]
            if unit == "ks" and gpk:
                qty, unit = qty * gpk, "g"
            ppu = rec["zlavnena_cena"] / qty
            if best is None or ppu < best["_ppu"]:
                best = {**rec, "balenie_qty": qty, "balenie_jednotka": unit, "_ppu": ppu}
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
        # sezónne suroviny receptu — appka/social z toho vie "v júli má tento
        # recept marhule v sezóne" (mesiace sú nadčasové, nezastarajú)
        r["sezonne_suroviny"] = [
            {"id": ing["id"], "mesiace": id_index[ing["id"]]["sezona"]}
            for ing in r["suroviny"]
            if ing.get("id") and id_index[ing["id"]].get("sezona")
        ]

        # cena za porciu per obchod
        ceny_za_porciu = []
        total = len(r["suroviny"])
        for obchod in stores:
            spolu, usetri, priced = 0.0, 0.0, 0
            z_letaku, odhadom = 0, 0
            plat_od, plat_do = None, None
            nakup = []  # konkrétny produkt na kúpu (so značkou) — pre nákupný zoznam
            for ing in r["suroviny"]:
                iid = ing.get("id")
                if not iid:
                    continue
                bp = best_price_for(iid, obchod)
                if not bp and id_index[iid]["_bezna"]:
                    # fallback: bežná cena mimo akcie (soľ, korenie, múka…) —
                    # nie je v letáku, ale recept s ňou musí počítať
                    b = id_index[iid]["_bezna"]
                    bp = {"nazov_v_letaku": None, "mnozstvo": b["balenie"],
                          "balenie_qty": b["qty"], "balenie_jednotka": b["unit"],
                          "zlavnena_cena": b["cena"], "povodna_cena": None,
                          "zlava": None, "podmienka": None,
                          "platnost_od": None, "platnost_do": None,
                          "zdroj_ceny": "bezna"}
                if not bp:
                    continue
                zdroj = bp.get("zdroj_ceny", "letak")
                item = {
                    "id": iid,
                    "surovina": id_index[iid]["nazov"],
                    "kupit": bp["nazov_v_letaku"],   # konkrétny produkt/značka z letáku (None pri bežnej cene)
                    "zdroj_ceny": zdroj,             # "letak" | "bezna" (odhad mimo akcie)
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
                    if zdroj == "letak":
                        z_letaku += 1
                    else:
                        odhadom += 1
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
            # spoľahlivosť: aspoň polovica surovín ocenená A ZÁROVEŇ ocenené
            # suroviny pokrývajú >= 80 % známej hmotnosti receptu — inak by
            # lacné základy (soľ, korenie s bežnou cenou) "pretlačili" recept
            # aj keď hlavná surovina (mäso) cenu nemá
            known_g = sum(i["mnozstvo_g"] for i in r["suroviny"]
                          if i.get("id") and i.get("mnozstvo_g"))
            priced_ids = {it["id"] for it in nakup if it["cena_v_recepte"] is not None}
            priced_g = sum(i["mnozstvo_g"] for i in r["suroviny"]
                           if i.get("id") in priced_ids and i.get("mnozstvo_g"))
            weight_ok = (known_g == 0) or (priced_g / known_g >= 0.8)
            spolahlive = priced >= max(1, (total + 1) // 2) and weight_ok
            ceny_za_porciu.append({
                "obchod": obchod,
                "cena_za_porciu": round(spolu / max(1, r["porcie"]), 2),
                "usetris_za_porciu": round(usetri / max(1, r["porcie"]), 2),
                "napar_surovin": priced,
                "z_letaku": z_letaku,     # koľko surovín má cenu z aktuálneho letáku
                "odhadom": odhadom,       # koľko z bežnej ceny (odhad mimo akcie)
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
    # História cien v databaza.json sa drží len ~12 týždňov dozadu (plná
    # história ostáva v ceny/*.json) — inak by súbor rástol donekonečna.
    # Štatistiky (bezna_jednotkova_cena) sú už spočítané z PLNEJ histórie.
    newest = max(letak_od_by_store.values(), default=None)
    cutoff = None
    if newest:
        from datetime import date, timedelta
        y, m, dd = map(int, newest.split("-"))
        cutoff = (date(y, m, dd) - timedelta(days=90)).isoformat()
    for s in suroviny:
        del s["_alias_all"]
        del s["_bezna"]
        del s["_vyluc"]
        if cutoff:
            s["ceny"] = [c for c in s["ceny"] if (c.get("platnost_od") or newest) >= cutoff]
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
        # kompaktný JSON — súbor číta appka, nie človek; gzip na GitHub Pages
        # ho zrazí na zlomok. Na čítanie schémy je docs/data/SCHEMA.md.
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))

    # ---- statické API v1 pre appky (docs/api/v1/) ----
    # API kontrakt je to jediné, na čo sa appky (Android/iOS) natvrdo viažu.
    # Dnes ho servíruje GitHub Pages ako statické JSON-y; budúci backend má
    # dodržať rovnaké tvary a cesty — potom sa v appke mení len base URL.
    # URL na fotky sú v odpovediach ABSOLÚTNE — appka si nikdy neskladá cesty
    # sama, takže hosting fotiek sa dá kedykoľvek presunúť bez zmeny appky.
    PAGES = "https://recepty.sporacek.sk"
    RAW = "https://raw.githubusercontent.com/TheVilo/sporacek/main"

    def foto_urls(r):
        slug = r["slug"]
        return (f"{RAW}/fotky/{slug}.jpg", f"{PAGES}/fotky-nahlad/{slug}.jpg")

    api = "docs/api/v1"
    import shutil
    shutil.rmtree(api, ignore_errors=True)  # čistý rebuild — žiadne siroty po premenovaní
    os.makedirs(f"{api}/recepty", exist_ok=True)
    os.makedirs(f"{api}/suroviny", exist_ok=True)

    def dump(path, obj):
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, ensure_ascii=False, separators=(",", ":"))

    dump(f"{api}/meta.json", out["meta"])

    # zoznam receptov — ľahký (na scrollujúci zoznam), detail sa ťahá zvlášť
    recepty_index = []
    for r in recepty:
        foto, nahlad = foto_urls(r)
        recepty_index.append({
            "slug": r["slug"], "nazov": r["nazov"], "porcie": r["porcie"],
            "cas_pripravy": r["cas_pripravy"], "tagy": r["tagy"],
            "foto_url": foto, "foto_nahlad_url": nahlad,
            "kcal": r["nutricne"]["kcal"],
            "pocet_surovin": len(r["suroviny"]),
            "alergeny": r["alergeny"],
            "vegetarianske": r["vegetarianske"], "veganske": r["veganske"],
            "najlacnejsie": r["najlacnejsie"],
        })
    dump(f"{api}/recepty/index.json", {"meta": {"pocet": len(recepty_index)}, "recepty": recepty_index})

    for r in recepty:
        foto, nahlad = foto_urls(r)
        detail = {**r, "foto_url": foto, "foto_nahlad_url": nahlad}
        dump(f"{api}/recepty/{r['slug']}.json", detail)

    # suroviny — index ľahký (watchlist/špajza výber), detail s históriou cien
    sur_index = [{
        "id": s["id"], "nazov": s["nazov"], "kategoria": s["kategoria"],
        "jednotka": s["jednotka"], "trvanlivost": s["trvanlivost"],
        "alergeny": s["alergeny"], "sezona": s["sezona"],
        "aktualne_najlacnejsie": s["aktualne_najlacnejsie"],
    } for s in suroviny]
    dump(f"{api}/suroviny/index.json", {"meta": {"pocet": len(sur_index)}, "suroviny": sur_index})
    for s in suroviny:
        dump(f"{api}/suroviny/{s['id']}.json", s)

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
    # sanity-check: podozrivé ceny (chyba parsovania sa prejaví ako extrém —
    # presne tak sa kedysi našla chyba "1 lyžica = 1 liter")
    sus = []
    for r in recepty:
        for c in r["ceny_za_porciu"]:
            if c["spolahlive"] and c["cena_za_porciu"] > 8:
                sus.append(f"{r['slug']} @ {c['obchod']}: {c['cena_za_porciu']} €/porcia")
    for s in suroviny:
        st = s.get("statistiky")
        if not st:
            continue
        for c in s["ceny"]:
            # porovnávaj len rovnaké jednotky (kus vs. gram nie je porovnateľné)
            if c["balenie_jednotka"] != s["jednotka"]:
                continue
            if c["jednotkova_cena"] and st["bezna_jednotkova_cena"] and \
               c["jednotkova_cena"] > 5 * st["bezna_jednotkova_cena"]:
                sus.append(f"{s['id']}: {c['nazov_v_letaku']} ({c['obchod']}) jednotková {c['jednotkova_cena']} vs bežná {st['bezna_jednotkova_cena']}")
    if sus:
        print("\n⚠ PODOZRIVÉ CENY (over ručne — môže ísť o chybu parsovania):")
        for x in sus[:15]:
            print("  •", x)
    # konzistencia fotiek: každý recept má mať fotku a každá fotka recept
    bez_fotky = [r["slug"] for r in recepty
                 if not r["foto_url"] or not os.path.exists(r["foto_url"])]
    if bez_fotky:
        print(f"\n⚠ RECEPTY BEZ FOTKY ({len(bez_fotky)}) — vygeneruj cez .claude/skills/generovanie-fotiek:")
        for x in bez_fotky:
            print("  •", x)
    bez_nahladu = [r["slug"] for r in recepty
                   if os.path.exists(r["foto_url"] or "")
                   and not os.path.exists(f"docs/fotky-nahlad/{r['slug']}.jpg")]
    if bez_nahladu:
        print(f"\n⚠ FOTKY BEZ NÁHĽADU ({len(bez_nahladu)}) — spusti: python3 scripts/generate_thumbs.py")
    n_api = len(glob.glob("docs/api/v1/recepty/*.json")) + len(glob.glob("docs/api/v1/suroviny/*.json")) + 1
    print(f"API v1 (docs/api/v1/):       {n_api} súborov")
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
