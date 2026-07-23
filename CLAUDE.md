# šporáček — mozog systému

Centrálny súbor — pravidlá jadra a rozcestník. Načíta sa pri každej session, preto je **zámerne krátky**. Detail býva v skilloch (workflow) a v `znalostna-baza/architektura.md` (dátový model) — načítaj ich len keď ich reálne potrebuješ, nemíňaj kontext dopredu.

## Čo je šporáček

Značka (a pripravovaná appka), ktorá pomáha ľuďom **nakupovať rozumnejšie, variť jednoduchšie a míňať menej peňazí na jedlo**. Heslo: **Čo kúpiť. Čo navariť. Koľko ušetríš.** Princíp: nezačíname receptom, ale rozhodnutím — čo sa dnes oplatí kúpiť a čo z toho navariť.

Aktuálna fáza: **budovanie povedomia cez sociálne siete.** Appka ešte nie je spustená. Paralelne budujeme databázu receptov, ktorú neskôr prevezme web aj appka.

## Tón (dôležité)

- Sme: priateľský, praktický, rozumný, úprimný, pozitívny pomocník.
- Nie sme: korporátni, poučujúci, elitárski, komplikovaní, technologickí.
- **Nikdy sa neposmievame** a nepoučujeme. Pomáhame. Konkrétne ceny a príklady, nie všeobecné frázy.

Podrobnosti: `znalostna-baza/brand-manual.md`, `znalostna-baza/strategia.md`

## Súbory v repe

| Súbor / priečinok | Na čo je |
|---|---|
| `CLAUDE.md` | tento súbor — pravidlá jadra + rozcestník, vždy sa načíta |
| `znalostna-baza/architektura.md` | **detailná referencia** dátového modelu (ceny, databáza, social, stránky, formát receptu) — číta sa len keď treba |
| `.claude/skills/` | workflow postupy, načítajú sa len keď sú potrebné |
| `znalostna-baza/` | brand manuál, obsahová stratégia |
| `suroviny.md` | **číselník surovín** — jednotné názvy (kritické!) |
| `znalostna-baza/aliasy.json` | kurátorovaná alias-vrstva (leták↔surovina), jednotky, bežné ceny — jediná ručne udržiavaná vec párovania |
| `scripts/build_databaza.py` | build skript: `suroviny.md` + `aliasy.json` + `ceny/` + `recepty/` → `docs/data/databaza.json` |
| `docs/data/databaza.json` | **generovaná** hlavná databáza pre appku (needituj ručne, ani nečítaj do kontextu — má 2,6 MB) |
| `docs/data/SCHEMA.md` | dátový kontrakt pre programátora appky (API v1 endpointy + schéma databázy) |
| `docs/api/v1/` | **generované** statické API pre appky (Android/iOS) — needituj ručne, robí ho build |
| `docs/fotky-nahlad/` | **generované** 320 px náhľady fotiek pre zoznamy (`scripts/generate_thumbs.py`) |
| `docs/app/` | dizajnové tokeny appky (`tokens.json` + web/Compose témy) a style guide — detail `docs/app/README.md` |
| `docs/app/design-handoff/` | **kompletný design handoff MVP appky** — 24 schválených obrazoviek (`App*.dc.html`), `UI Kit.dc.html`, hotové PNG screenshoty (`screenshots/`), `README.md` s tabuľkou obrazoviek a tokenmi. Zdroj pravdy pre presné hodnoty pri fáze 3 appky (a neskôr). Pôvodne z Claude Design (beta) — ak treba znova exportovať, cez "Export → Project HTML" tam. |
| `znalostna-baza/plan-appky.md` | **záväzný plán vývoja appky** (fázy, architektúra, čo je rozhodnuté) — čítaj pred každou prácou na appke |
| `recepty/` | jeden súbor = jeden recept (nikdy neobsahuje cenu) |
| `fotky/` | fotky receptov, pomenované podľa id (sú v repe) |
| `tydne/` | výstup týždňa (leták → recepty → nákup → úspora) |
| `ceny/` | cenová databáza — celý zoznam potravín z každého letáku |
| `katalogy/` | vstupné PDF letákov (pracovný vstup, nie zdroj pravdy) |
| `social/` | evergreen social obsah (`tipy.json`, `brand.json`) |

## Kritické invarianty (toto rozbije systém, ak sa poruší)

1. **Recept nikdy neobsahuje cenu** ani väzbu na konkrétny týždeň/obchod/dátum. Cena vzniká až pri použití (týždenný výstup / build) — nikdy v `recepty/<slug>.md`. Recepty sú navždy nezastarateľná databáza (suroviny + množstvá + postup + fotka + tagy).
2. **Suroviny vždy z číselníka `suroviny.md`**, jednotné názvy, žiadne synonymá („paradajky", nikdy „rajčiny"). Každá surovina použitá v recepte **musí byť v `suroviny.md`**.
3. **Pri novom recepte over duplicity** (skontroluj `recepty/`) a konzistenciu názvov. `id` je slug bez diakritiky a **nikdy sa nemení** (inak prestane sedieť fotka).
4. **Po každej zmene `ceny/`, `recepty/`, `suroviny.md` alebo `aliasy.json` prebuild-ni databázu:** `python3 scripts/build_databaza.py` (na `main` to spraví aj Action, ale lokálny rebuild ukáže report pokrytia a formátové varovania hneď). `databaza.json` je **generovaný** — needituj ho ručne a nečítaj ho do kontextu (2,6 MB); keď potrebuješ dáta, čítaj zdroje (`recepty/`, `ceny/`, `suroviny.md`) alebo `docs/data/SCHEMA.md`.
5. **Recept = poriadne, chutné jedlo**, ktoré sa len postaví na akciových surovinách. Akciové ≠ chudobné. Najprv dobrý recept (inšpirovaný reálnymi z netu), až potom lacnejšie suroviny.

## Kedy siahnuť po skille

- **Týždenný leták** (recepty, nákupný zoznam, ceny, stories) → `.claude/skills/tyzdenny-vystup/SKILL.md`
- **Nový recept** mimo letáku → `.claude/skills/novy-recept/SKILL.md`
- **Fotka k receptu** (`foto_url`) → `.claude/skills/generovanie-fotiek/SKILL.md`
- **Leták do `ceny/`** (overenie JSON z Gemini / import z PDF / crawl) → `.claude/skills/ceny-z-letaku/SKILL.md`
- **Údržba databázy** (aliasy, bežné ceny, riešenie varovaní z buildu, „prečo recept nemá cenu") → `.claude/skills/udrzba-databazy/SKILL.md`

Nenačítavaj skill, ak práve nerobíš daný workflow — šetrí to kontext.

## Detailná referencia

Dátový model a jeho pravidlá (cenová databáza `ceny/`, generovanie `databaza.json`, alergény/diéty, `trvanlivost`, `gramy_za_ks`, špajža, social obsah, formát receptu, taxonómia tagov, živé stránky a ich URL, viacero obchodov) → **`znalostna-baza/architektura.md`**. Číta sa len keď reálne pracuješ s daným podsystémom.

## Šetrenie tokenov (dôležité, čítaj vždy)

- **`docs/data/databaza.json` nikdy nečítaj do kontextu** (2,6 MB ≈ 660-tisíc tokenov) — pozri invariant 4 vyššie.
- **`ceny/` čítaj len pre obchod, ktorý práve riešiš** (napr. `ceny/lidl-*.json`), nikdy všetkých 8 súborov naraz „pre istotu" — to je ~85-tisíc tokenov. Ak treba porovnanie naprieč obchodmi, over si najprv, či to nevie priamo stránka `docs/ceny.html` (počíta to naživo v prehliadači).
- **Pri hromadných operáciách na receptoch** (napr. „skontroluj všetky recepty na X") **nečítaj všetkých 117 súborov naraz** — buď to zúž (konkrétne tagy/suroviny cez `grep`), alebo deleguj cez `Agent`/`Explore`, nech sa surové súbory nehromadia v hlavnom kontexte.
- **Model:** na bežnú prácu (recept, leták, aliasy, fotka) stačí štandardný model — nepoužívaj drahší model „pre istotu". Nová/samostatná úloha → radšej nová session než dlhé naťahovanie jednej konverzácie (kontext sa platí znova pri každej odpovedi).

## Dôležité upozornenia

- **Leták je len dočasný vstup.** Trvalá hodnota = databáza receptov — nesmie sa robiť dvakrát, preto zapisuj dôsledne a konzistentne.
- **Zdroj pravdy je vždy repo.** Živé stránky (GitHub Pages, doména `recepty.sporacek.sk`) sú len jeho zobrazenie — pushni zmenu, stránka ju ukáže po F5. Claude Artifacty pre šporáček už nepoužívaj (staré URL ignoruj).
