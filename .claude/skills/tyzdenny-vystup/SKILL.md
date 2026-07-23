---
name: tyzdenny-vystup
description: Použi pri spracovaní týždenného letáku (akciové produkty) na recepty, nákupný zoznam, ceny a obsah pre Stories. Trigger frázy - "leták", "týždenný výstup", "priprav recepty na tento týždeň", priloženie PDF/screenshotu letáku, alebo žiadosť o nákupný zoznam/úsporu na týždeň.
---

# Spracovanie týždenného letáku

Pravidlá pre recepty (id, suroviny, tagy, tón) sú v `CLAUDE.md` (kritické invarianty) a detailne v `znalostna-baza/architektura.md` — načítaj si ich, ak ešte nie sú v kontexte.

## Viacero obchodov naraz

Ak dostaneš katalógy z viacerých obchodov (Lidl, Kaufland, Tesco...) naraz alebo v krátkom čase, **spracuj ich oddelene** — každý obchod má vlastný priečinok, vlastných 5 receptov, vlastný nákupný zoznam aj social obsah. Nemiešaj suroviny/recepty naprieč obchodmi do jedného výstupu (zodpovedá to reálnemu nákupu v jednom obchode aj brandu "toto bolo dnes v akcii v X").

## Priečinok týždňa

Formát: `tydne/<rok>-W<týždeň>-<obchod>/` (napr. `tydne/2026-W29-lidl/`, `tydne/2026-W29-kaufland/`). Obchod malými písmenami bez diakritiky.

## Rýchly výber bez letáku

Niekedy nie je k dispozícii aktuálny leták, ale treba rýchlo social obsah (Stories) na budovanie povedomia — napr. na vetu "priprav 5 receptov a stories na tento týždeň" bez priloženého letáku. V tom prípade:

1. Vyber 5 receptov priamo z `recepty/` (živé vyhľadávanie cez `docs/index.html`), nie z letáku.
   - Uprednostni rozmanitosť: mix typov (obed/večera/šalát/polievka), nie 5× to isté.
   - Skontroluj priečinky v `tydne/`, ktoré recepty sa použili nedávno, a vyhni sa ich opakovaniu.
2. **Nevymýšľaj úsporu ani akciové ceny.** Bez reálneho letáku nemáme čo porovnávať — tvrdenie o úspore by bolo nepravdivé. Cena za porciu sa berie z `cena_za_porciu` v recepte (je to stále platný snapshot z minulého výpočtu).
3. Priprav Stories rovnako ako pri letáku (názov jedla + cena za porciu), len bez "akcia/úspora" rámca — napr. namiesto "ušetríš X €" použi tón typu "chutné a lacné, X €/porcia".
4. Zapíš do `tydne/<rok>-W<týždeň>-vyber/` (namiesto názvu obchodu `vyber`):
   - rovnaká štruktúra `data.json` ako pri letáku, ale `katalog_zvyraznenia`, `nakupny_zoznam` a `suhrn.uspora` **vynechaj** (prázdne pole / `null`) — `docs/tyzden.html` tieto sekcie pri chýbajúcich dátach automaticky skryje.
   - `obchod` v `data.json` nastav na `"Výber z databázy"`.

## Postup

1. **Prečítaj leták** (PDF/screenshot/text) → vypíš akciové produkty s cenami.
2. **Zisti, ktoré recepty sa majú použiť:**
   - **Ak používateľ prišiel s výberom z `docs/vyber.html`** (skopírovaný zoznam receptov s ID) — použi presne tie, over si ich v `recepty/`, netreba znova prehľadávať celú databázu.
   - **Inak prehľadaj celú `recepty/`** (najrýchlejšie cez živé vyhľadávanie na `docs/index.html`, prípadne rovno cez `docs/vyber.html` pre daný obchod) → toto je hlavný krok, nie formalita. Databáza receptov časom rastie a jej zmyslom je práve to, aby sa dala takto prehľadávať — nový týždeň sa má primárne **skladať z toho, čo už existuje** a sedí na aktuálnu akciu, nie z rovno vymyslených nových receptov.
3. **Navrhni 5 obedov (Po–Pi), vždy pre 2 osoby**, podľa pravidiel z CLAUDE.md.
   - prednostne použi existujúce recepty z databázy, ak sedia na akciu
   - nové recepty vytvor len ak sa v databáze nenájde nič vhodné (alebo ak si o to používateľ vyslovene povie)
4. **Prepočítaj:**
   - cenu za porciu pre každé jedlo — recept sám cenu neobsahuje (viď CLAUDE.md), takže ju vždy dopočítaš teraz: vezmi jeho suroviny + množstvá a oceň ich podľa tohto letáku (akciová cena, ak je surovina v akcii; bežná odhadovaná cena, ak nie je)
   - kompletný nákupný zoznam s cenami
   - celkovú cenu nákupu
   - úsporu oproti bežným cenám
   - vypočítanú cenu za porciu zapíš **len do `tydne/<týždeň>/` výstupu** (`data.json` pole `recepty[].cena`, `OVERVIEW.md`, `NAKUPNY-ZOZNAM.md`, `SOCIAL-PLAN.md`) — **nikdy späť do `recepty/<slug>.md`**
5. **Ku každému novému receptu daj `foto_prompt`** (šablóna nižšie) a vygeneruj fotku (`.claude/skills/generovanie-fotiek/SKILL.md`). Existujúce recepty nefotografuj znova.
6. **Priprav texty do Stories** (názov jedla + cena za porciu) a feed posty.
7. **Zapíš do `tydne/<rok>-W<týždeň>-<obchod>/`:**
   - `OVERVIEW.md` — prehľad letáku + vybraných 5 receptov (pre človeka)
   - `NAKUPNY-ZOZNAM.md` — nákupný zoznam (pre človeka)
   - `SOCIAL-PLAN.md` — Stories a feed texty (pre človeka)
   - `data.json` — **strojovo čitateľná verzia** pre `docs/tyzden.html` (živá stránka), presná štruktúra nižšie. Bez tohto súboru sa týždeň na stránke nezobrazí.
   - nové recepty do `recepty/`, nové suroviny do `suroviny.md`

## Recepty sú zdroj pravdy — `tydne/` je len odvodený pohľad

`OVERVIEW.md`, `NAKUPNY-ZOZNAM.md`, `SOCIAL-PLAN.md` aj `data.json` sú **výstup vypočítaný z aktuálneho stavu `recepty/`** v momente písania, nie samostatne udržiavaný obsah. Ak sa neskôr recept použitý v už publikovanom týždni zmení (iné suroviny, iná cena — napr. pri prerábaní na chutnejšiu verziu), staré čísla v `tydne/<ten-týždeň>/` sa tým pádom rozídu s realitou. Keď si to všimneš (alebo ťa na to upozorní používateľ), **prepočítaj celý dotknutý týždeň nanovo** z aktuálnych receptov — neopravuj len jedno číslo, cena/suroviny sa menia v celom nákupnom zozname aj súhrne naraz.

## Štruktúra `data.json`

```json
{
  "obchod": "Lidl",
  "tyzden": "29/2026",
  "platnost": "2026-07-13 - 2026-07-19",
  "katalog_zvyraznenia": [
    {"nazov": "Marhule", "stara_cena": 4.49, "akciova_cena": 1.99, "zlava": "-55%", "kategoria": "Ovocie a zelenina", "flag": ""}
  ],
  "recepty": [
    {"den": "Pondelok 13. 7.", "slug": "plnena-cuketa-mlete-maso", "cena": 0.94}
  ],
  "nakupny_zoznam": {
    "skupiny": [
      {"nazov": "Zelenina a ovocie (akciové)", "polozky": [{"nazov": "cuketa", "mnozstvo": "1 ks", "cena": 0.49}]}
    ],
    "poznamka": "..."
  },
  "social": {
    "stories": [
      {"den": "Pondelok 13. 7.", "recept": "🥒 Plnená cuketa", "slide1": "...", "slide2": "...", "cta": "..."}
    ],
    "feed_posty": [
      {"nazov": "Food Waste fakt (streda)", "text": "..."}
    ]
  },
  "suhrn": {"plan_spolu": 6.16, "uspora": 7.59, "priemer_porcia": 0.62}
}
```

`recepty[].slug` musí presne sedieť s id v `recepty/<slug>.md` — stránka si fotku aj postup dotiahne odtiaľ naživo, netreba ich duplikovať do `data.json`.

## Šablóna foto promptu (pre nanobanana)

Presný 2-krokový proces (analýza receptu → anglický opis jedla → jedna z 10 kompozičných šablón "Modern Editorial & Elevated Lifestyle") je v `.claude/skills/generovanie-fotiek/SKILL.md`, sekcia "Foto prompt — 2-krokový proces". Použi ho vždy, aj pre nové recepty vzniknuté z týždenného letáku — nedrž si tu vlastnú kópiu šablóny, nech sa časom nerozíde s aktuálnou verziou.
