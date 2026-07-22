---
name: ceny-z-letaku
description: Použi keď treba spracovať leták obchodu do cenovej databázy (ceny/) — či už z priloženého JSON-u z Gemini na overenie, z PDF letáku, alebo z automatického zberu cez crawl4ai (scripts/crawl_ceny.py). Trigger frázy - "over tento json", "pridaj leták do cien", "skontroluj cenový json z gemini", "spracuj tento leták do ceny", "crawl4ai", "automatický zber cien", priloženie cenového JSON + PDF letáku. Obsahuje hotový Gemini prompt aj postup na kontrolu a import.
---

# Spracovanie letáku do cenovej databázy (`ceny/`)

Pravidlá cenovej databázy sú v koreňovom `CLAUDE.md` (sekcia „Cenová databáza `ceny/`"). Tento skill dopĺňa: **(A)** hotový prompt pre Gemini, ktorý dáva používateľ, a **(B)** môj postup na kontrolu a import JSON-u do `ceny/`.

Používateľ typicky spraví JSON z letáku cez **Gemini** (v inej appke) a prinesie ho sem s PDF na overenie. Gemini nemá „skilly" — dáva sa mu iba **prompt** (časť A).

---

## A) Prompt pre Gemini (skopíruj používateľovi, keď oň požiada)

> Si extraktor cien z letáku obchodu. Z priložených obrázkov/PDF letáku vyextrahuj VŠETKY potravinové suroviny na varenie a vráť IBA validný JSON (žiadny text navyše) presne v tomto tvare:
>
> ```json
> {
>   "obchod": "<Lidl / Kaufland / Tesco supermarket / Tesco hypermarket / COOP / BILLA / Terno ...>",
>   "platnost_tyzdenna_default": "YYYY-MM-DD - YYYY-MM-DD",
>   "pocet_stran_v_katalogu": 0,
>   "pocet_potravinovych_polozok": 0,
>   "poznamka_metodika": "<1 veta, ako si extrahoval>",
>   "polozky": [
>     {
>       "strana": 1,
>       "nazov": "<názov produktu>",
>       "mnozstvo": "<napr. '1 kg', '250 g', 'cena za 100 g'>",
>       "povodna_cena": null,
>       "zlava": "<'-30%' ak je uvedená; inak '' alebo štítok z letáku napr. 'SUPER CENA'>",
>       "zlavnena_cena": 0.00,
>       "platnost": "YYYY-MM-DD - YYYY-MM-DD",
>       "poznamka": "<voliteľné: 'pultový predaj', 'Clubcard', 'víkendová akcia'...>",
>       "obchod": "<rovnaké ako hore>",
>       "zdroj_kontroly": "Gemini OCR",
>       "kategoria": "<PRESNE jedna zo 6 kategórií nižšie>"
>     }
>   ]
> }
> ```
>
> PRAVIDLÁ:
> 1. `kategoria` musí byť PRESNE jedna z týchto šiestich (nič iné, nevymýšľaj, nekombinuj ako „Trvanlivé a ryby/základ"):
>    `Mäso a ryby` · `Ovocie a zelenina` · `Mliečne a vajcia` · `Trvanlivé a základ` · `Orechy a sladkosti` · `Pečivo a pekáreň`
> 2. Ceny sú ČÍSLA s desatinnou bodkou v eurách (`0.75`, nie `"075"` ani `"0,75"`). `povodna_cena` je číslo **alebo `null`** — NIKDY prázdny reťazec `""`.
> 3. Ak leták neuvádza pôvodnú cenu (len akciovú + %), daj `povodna_cena: null` a do `zlava` daj to % alebo štítok z letáku.
> 4. `zlavnena_cena` je vždy povinná — akciová cena, ktorú zákazník zaplatí (za balenie/kus/kg podľa `mnozstvo`).
> 5. ZBIERAJ IBA skutočné suroviny na varenie. VYNECHAJ (vôbec nedávaj do JSON):
>    alkohol; VŠETKY nápoje (minerálka, sýtené, 100% šťava, **sirup**, ľadový čaj, káva, čaj, energetické); chipsy a slané snacky; žuvačky, cukríky, čokolády, sušienky, oblátky, zmrzliny, hotové dezerty; sladké pečivo (croissanty, koláče, donuty, buchty, bábovky); mrazené hotové jedlá (pizza, obaľované/vyprážané polotovary, hotové menu); drogéria, kozmetika, čistiace prostriedky, domáce potreby, papierové výrobky; krmivo, detská výživa/plienky, proteínové doplnky/tyčinky; kvety, záhrada, hračky, elektronika, oblečenie.
>    (Naopak DNU patria: múka, cukor, olej, ryža, cestoviny, konzervovaná zelenina/strukoviny, kokosové mlieko, koreniny, kečup/horčica/omáčky na varenie, orechy a semienka.)
> 6. Ak akcia platí len víkend/pár dní, daj tej položke správnu `platnost` (napr. `2026-07-17 - 2026-07-19`).
> 7. Ak obchod má viac formátov (Tesco supermarket vs hypermarket, COOP bežný vs XXL), spracuj každý leták zvlášť a do `obchod` daj konkrétny formát.
>
> Platnosť letáku: **<doplň dátumy z letáku>**

---

## B) Kontrola a import JSON-u (robím ja)

### 1. Vnútorná kontrola (bez PDF, lacné)
Skriptom (Python) preveď a skontroluj:
- **kategórie** — každá musí byť v pevnej šestke; nič iné (chytí „Trvanlivé a ryby/základ" a pod.).
- **`povodna_cena`** — žiadny `""` (má byť `null` alebo číslo). Priebežne oprav `"" → null`.
- **`zlavnena_cena`** — nikde `null`; nikde akc > pôvodná.
- **zľava %** — tam, kde je pôvodná cena číslo a `zlava` v tvare `-NN%`, over, či sedí s vypočítaným z cien (tolerancia ~2 %).
- **scope** — hľadaj podozrivé kľúčové slová (`sirup`, `šťava`, `pivo`, `víno`, `čip`, `šampón`, `prací`...) → nápoje/nepotraviny odstráň.

### 2. Náhodná kontrola proti PDF (dôležité — používateľ to ocení)
- Text z PDF vytiahni cez **PyMuPDF** (`fitz`), nie cez obrázky (šetrí tokeny). Väčšina letákov má čitateľný text.
- Ceny sú v texte často **spojené číslice** (`075` = 0,75; `139` = 1,39) alebo `1 kg = X` jednotkové ceny.
- Vyber **náhodnú vzorku** (napr. 7–8 položiek) cez `random.sample`, nájdi ich v texte a porovnaj `zlavnena_cena` (a % ak je pôvodná). Nájdenie zlyháva len kvôli medzerám/diakritike — skús aj prvé 1–2 slová názvu.
- Nahlás výsledok tabuľkou; jasne oddeľ **cenu** (kritická, musí sedieť) od **%** (často drobná OCR chyba, keď obchod neuvádza pôvodnú cenu — netreba to preháňať).

### 3. Import do repa
- Normalizuj poradie koreňových polí ako v ostatných súboroch: `obchod`, `platnost_tyzdenna_default`, `pocet_stran_v_katalogu` (skutočný počet strán PDF z `fitz`), `pocet_potravinovych_polozok`, `poznamka_metodika`, `polozky`.
- Ulož do **`ceny/<obchod>-<dátum-začiatku>.json`** (obchod malými písmenami, bez diakritiky). Pri viacerých formátoch odlíš názov aj `obchod`: `tesco-supermarket-...` / `tesco-hypermarket-...`, `coop-...` / `coop-xxl-...`.
- Pri importe **oprav zjavné chyby** (prázdne ceny → null, chybná kategória, nápoje/nepotraviny von) a v odpovedi to **zhrň**, čo si zmenil.
- Nezabudni, že PDF letáky sú len **pracovný vstup** — do repa ide `ceny/…json`, PDF sa dlhodobo neukladá.

### 4. Commit a push
- Commitni `ceny/<súbor>.json`. **Push robí používateľ** (má na to prístup, my z tohto prostredia nepushujeme). V zhrnutí uveď, koľko commitov čaká.
- V zhrnutí ukáž aj stav databázy (počet obchodov, spolu cien, koľko surovín je porovnateľných naprieč obchodmi).

---

## C) Automatický zber cez crawl4ai (GitHub Actions)

Namiesto ručného Gemini kroku (časť A) sa vstupný JSON generuje automaticky cez **crawl4ai** (`scripts/crawl_ceny.py`) — LLM-friendly crawler, ktorý stránku obchodu prevedie na štruktúrovaný JSON priamo v `ceny/` schéme.

**Kde beží:** na **serveroch GitHubu** cez workflow `.github/workflows/zber-cien.yml` (týždenne v štvrtok + tlačidlo „Run workflow"). **NEbeží vnútri Claude Code na webe** (sieťová politika blokuje weby obchodov, `403` na CONNECT) ani lokálne u používateľa. Workflow výstup **nezapisuje rovno do main**, ale otvorí **Pull Request** (`ceny/*.json`) — ten prejde kontrolou z časti B a až potom sa mergne. V súlade s `CLAUDE.md` (*„automatický zber stavia programátor"*).

**Typ ceny** (pole `typ` v `STORES` v skripte):
- `akciova` — z **web-letáku** (dočasné akciové ceny).
- `bezna` — z **e-shopu** (bežné needzľavnené ceny) → doplnia diery pri oceňovaní receptov vo `vyber.html`. V schéme len cena bez zľavy (`zlava: ""`, `povodna_cena: null`), odlíšená cez `zdroj_kontroly`/`poznamka` — netreba meniť schému ani `ceny.html`.

Extrakcia ide cez **Gemini Flash** pre oboje (netreba ladiť CSS selektory, len URL). Nový obchod = pridať záznam do `STORES` (obchod + typ + url). Workflow potrebuje GitHub secret **`GEMINI_API_KEY`**.

**Moja rola pri PR z workflowu:** obsah PR (aj keď vznikol automaticky) **nikdy nemergujem naslepo** — prejde rovnakou kontrolou ako Gemini JSON: vnútorná kontrola (B.1), náhodná kontrola vzorky proti zdroju (B.2), oprava zjavných chýb (B.3). Heuristická kategorizácia a scope filter v skripte kontrolu **nenahrádzajú**, len uľahčujú. Po kontrole PR mergnem (alebo doň pushnem opravy).
