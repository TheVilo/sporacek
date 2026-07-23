---
name: udrzba-databazy
description: Použi na údržbu hlavnej databázy (docs/data/databaza.json) — dopĺňanie aliasov podľa nespárovaných letákových názvov, bežných cien, riešenie varovaní z build reportu (podozrivé ceny, chýbajúce fotky, formát receptov). Trigger frázy - "doplň aliasy", "prečo recept nemá cenu", "over databázu", "nespárované suroviny", "podozrivá cena", po importe nového letáku do ceny/.
---

# Údržba hlavnej databázy

Celá architektúra je v `CLAUDE.md` (sekcia „Hlavná databáza pre appku") a schéma výstupu v `docs/data/SCHEMA.md`. Tento skill je pracovný postup pre opakovanú údržbu.

## Základný cyklus

```
python3 scripts/build_databaza.py     # build + report
python3 -m pytest tests/ -q           # regresné testy parsovania (16+)
```

Report na konci buildu je kontrolný zoznam údržby — cieľ je build **bez varovaní** a rastúce pokrytie. Na `main` beží build aj automaticky (GitHub Action `.github/workflows/build-databaza.yml`).

## 1. Nespárované letákové názvy → aliasy

`scripts/.nesparovane.json` (gitom ignorovaný) drží zoznam letákových názvov bez páru, zoradený podľa početnosti. Postup:

- Alias dopĺňaj **len keď ide o surovinu, ktorá JE v `suroviny.md`** — väčšina nespárovaných je legitímne mimo záber (značkové výrobky, sladkosti, nátierky, mäsové rezy mimo číselníka).
- Alias píš normalizovane (malé písmená, bez diakritiky), **nie príliš všeobecný** (samotné „kuracie" by chytalo párky aj polievkové zmesi).
- Keď všeobecnejší alias chytá nesprávne produkty (napr. „muka" ⊂ „mandľová múka" — 16 €/kg by kazilo ceny), pridaj do suroviny `vyluc`: zoznam podreťazcov, pri ktorých sa párovanie zakáže.

## 2. Recept nemá spoľahlivú cenu — prečo?

`spolahlive` = ocenená aspoň polovica surovín **a** ≥ 80 % známej hmotnosti receptu. Keď recept cenu nemá, príčiny v poradí častosti:

1. **Hlavná surovina nie je v žiadnom aktuálnom letáku** a nemá `bezna_cena` — pri základoch (múka, korenie, mliečne) doplň `bezna_cena` + `bezne_balenie` do `aliasy.json`; pri mäse to **nechaj tak** (recept má byť lákavý vtedy, keď je mäso v akcii — bežnú cenu mäsu zámerne nedávame).
2. **Chýba `gramy_za_ks`** — recept uvádza kusy, leták predáva na kg.
3. **Chýba alias** — surovina v letáku je, ale pod iným názvom (pozri bod 1).

## 3. Varovania reportu

- **⚠ PODOZRIVÉ CENY** — cena za porciu > 8 € alebo jednotková cena 5× nad bežnou. Skoro vždy chyba parsovania (multibalenia, jednotky) alebo zlý match — over záznam v `ceny/*.json` a oprav parser/alias/vyluc. Nikdy neignoruj bez overenia.
- **⚠ RECEPTY BEZ FOTKY** — vygeneruj cez `.claude/skills/generovanie-fotiek/SKILL.md` (pozor na 429 spending cap — vie ho zdvihnúť len používateľ).
- **⚠ RECEPTY MIMO ŠTANDARDNÉHO FORMÁTU** — oprav na šablónu z `.claude/skills/novy-recept/SKILL.md`; nikdy nenechávaj recepty v dvoch formátoch.
- **Nespárované suroviny receptu** (okrem „voda") — surovina chýba v `suroviny.md`: doplň ju tam + obohať `aliasy.json` (checklist v `novy-recept/SKILL.md`, krok 4).

## 4. Kedy meniť build skript

`scripts/build_databaza.py` meň len pri novej logike (nová jednotka, nový formát letáku). **Každú zmenu parsera sprevádzaj testom** v `tests/test_build.py` — regresie v parsovaní bývajú tiché a drahé (viď test „1 lyžica ≠ 1 liter"). Kuchynské miery (PL=15 g, ČL=5 g, štipka=0,5 g, „podľa chuti"=2 g…) sú konštanty na začiatku skriptu.

## 5. Čo do databázy NEpatrí

Užívateľské dáta (špajza, watchlist, obľúbené, história nákupov) — tie žijú v appke a prepájajú sa cez `id` / `nazov_norm`. Databáza je read-only obsah: suroviny + ceny + recepty.
