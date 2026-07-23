"""Regresné testy jadra build_databaza.py — parsovanie množstiev, balení,
párovanie a formát receptov. Presne tu sa kedysi skrývala chyba
"1 lyžica = 1 liter", preto je parsovanie pod testami natrvalo.

Spustenie:  python3 -m pytest tests/ -q
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from build_databaza import (parse_recipe_qty, parse_package, parse_platnost,
                            slugify, norm, Matcher, check_format,
                            LYZICA_G, LYZICKA_G, STIPKA_G, PODLA_CHUTI_G)


# ---------- množstvá v recepte ----------
def q(text, hint="g"):
    return parse_recipe_qty(text, hint)

def test_gramy_a_kila():
    assert q("300 g") == {"qty": 300, "unit": "g"}
    assert q("1,5 kg") == {"qty": 1500, "unit": "g"}
    assert q("200 ml", "ml") == {"qty": 200, "unit": "ml"}
    assert q("1 l", "ml") == {"qty": 1000, "unit": "ml"}

def test_kusy_a_strucik():
    assert q("1 ks") == {"qty": 1, "unit": "ks"}
    assert q("2 strúčiky") == {"qty": 2, "unit": "ks"}

def test_lyzica_nie_je_liter():
    # REGRESIA: "1 lyžica" sa kedysi parsovala ako 1 liter (l zo slova Lyžica)
    r = q("1 lyžica", "ml")
    assert r["qty"] == LYZICA_G and r["unit"] == "ml" and r["approx"]
    r = q("2 lyžice", "g")
    assert r["qty"] == 2 * LYZICA_G and r["unit"] == "g"
    r = q("1 lyžička")
    assert r["qty"] == LYZICKA_G

def test_pl_cl():
    assert q("3 PL", "ml")["qty"] == 3 * LYZICA_G
    assert q("1 ČL")["qty"] == LYZICKA_G

def test_unicode_zlomky():
    assert q("½ ČL")["qty"] == 0.5 * LYZICKA_G
    assert q("½ ks")["qty"] == 0.5
    assert q("¼ ks (šťava)")["qty"] == 0.25

def test_slovne_mnozstva():
    assert q("štipka")["qty"] == STIPKA_G
    assert q("podľa chuti")["qty"] == PODLA_CHUTI_G
    assert q("—")["qty"] == PODLA_CHUTI_G
    assert q("pár vetvičiek")["qty"] == 5
    assert q("2 vetvičky")["qty"] == 4
    assert q("pár lístkov")["qty"] == 2
    assert q("4 plátky")["qty"] == 60
    assert q("kúsok (~2 cm)")["qty"] == 10
    assert q("1 zväzok")["qty"] == 30
    assert q("na vyprážanie", "ml")["qty"] == 30

def test_neparsovatelne():
    assert q("") is None
    assert q(None) is None


# ---------- balenia z letáku ----------
def test_balenie_zaklad():
    assert parse_package("500 g") == {"qty": 500, "unit": "g"}
    assert parse_package("1 l") == {"qty": 1000, "unit": "ml"}
    assert parse_package("cena za 1 kg") == {"qty": 1000, "unit": "g"}

def test_balenie_multipack():
    # REGRESIA: "4 × 100 g" sa parsovalo ako 100 g (Lagris ryža 12,9 €/kg)
    assert parse_package("4 × 100 g, varné vrecká (1 kg = 2,23)") == {"qty": 400, "unit": "g"}
    assert parse_package("2 x 250 ml") == {"qty": 500, "unit": "ml"}


# ---------- platnosť ----------
def test_platnost():
    assert parse_platnost("2026-07-13 - 2026-07-19") == ("2026-07-13", "2026-07-19")
    assert parse_platnost(None) == (None, None)


# ---------- párovanie ----------
def _matcher():
    suroviny = [
        {"id": "muka", "_alias_all": ["múka", "múka hladká"], "_vyluc": ["mandlova", "kokosova"]},
        {"id": "kuracie-prsia", "_alias_all": ["kuracie prsia", "kuracie rezne"], "_vyluc": []},
        {"id": "mlieko", "_alias_all": ["mlieko"], "_vyluc": []},
        {"id": "kokosove-mlieko", "_alias_all": ["kokosové mlieko"], "_vyluc": []},
    ]
    return Matcher(suroviny)

def test_matcher_alias():
    m = _matcher()
    assert m.match("Kuracie rezne Domäsko") == "kuracie-prsia"

def test_matcher_vyluc():
    # REGRESIA: mandľová múka (16 €/kg) sa párovala na obyčajnú múku
    m = _matcher()
    assert m.match("Racionella mandľová múka") is None
    assert m.match("Múka hladká špeciál") == "muka"

def test_matcher_najdlhsi_vyhrava():
    # kokosové mlieko sa nesmie chytiť ako mlieko
    m = _matcher()
    assert m.match("Asia Time kokosové mlieko") == "kokosove-mlieko"


# ---------- formát receptu ----------
def test_format_ok():
    t = ("# Recept\n\n**slug:** x\n**porcie:** 2\n**čas prípravy:** 30 minút\n"
         "**foto_url:** fotky/x.jpg\n\n## Foto prompt\np\n\n## Suroviny (pre 2 osoby)\n"
         "|a|b|\n\n## Nutričné hodnoty (na porciu, odhad)\n|x|y|\n\n## Postup\n1. krok\n\n## Tagy\n`#obed`\n")
    assert check_format("x.md", t) == []

def test_format_frontmatter_zakazany():
    assert any("frontmatter" in p for p in check_format("x.md", "---\nid: x\n---\n# R\n"))


# ---------- normalizácia ----------
def test_norm():
    assert norm("Bezjadierková červená dyňa") == "bezjadierkova cervena dyna"
    assert norm("Jogurt 3,5 %") == "jogurt"
    assert slugify("bujón (kocka)") == "bujon"
