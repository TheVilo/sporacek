# šporáček — mozog systému

Toto je centrálny súbor. Prečítaj si ho vždy na začiatku práce.

## Čo je šporáček

Značka (a pripravovaná appka), ktorá pomáha ľuďom **nakupovať rozumnejšie, variť jednoduchšie a míňať menej peňazí na jedlo**.

Heslo: **Čo kúpiť. Čo navariť. Koľko ušetríš.**

Princíp: nezačíname receptom, ale rozhodnutím — čo sa dnes oplatí kúpiť a čo z toho navariť.

Aktuálna fáza: **budovanie povedomia cez sociálne siete.** Appka ešte nie je spustená. Paralelne budujeme databázu receptov, ktorú neskôr prevezme web aj appka.

## Tón (dôležité)

- Sme: priateľský, praktický, rozumný, úprimný, pozitívny pomocník.
- Nie sme: korporátni, poučujúci, elitárski, komplikovaní, technologickí.
- **Nikdy sa neposmievame** a nepoučujeme. Pomáhame.
- Konkrétne ceny a príklady, nie všeobecné frázy.

Podrobnosti: `znalostna-baza/brand-manual.md`, `znalostna-baza/strategia.md`

---

## Súbory v repe

| Súbor / priečinok | Na čo je |
|---|---|
| `CLAUDE.md` | tento súbor — pravidlá jadra, vždy sa načíta |
| `.claude/skills/` | workflow postupy, načítajú sa len keď sú potrebné |
| `znalostna-baza/` | brand manuál, obsahová stratégia |
| `suroviny.md` | **číselník surovín** — jednotné názvy (kritické!) |
| `recepty/` | jeden súbor = jeden recept |
| `fotky/` | fotky receptov, pomenované podľa id (napr. `kremove-kuracie-rizoto-sampinony.jpg`) |
| `tydne/` | výstup týždňa (leták → recepty → nákup → úspora) |

Fotky **sú v repe** (priečinok `fotky/`) — nech sa cez GitHub/git pull sync automaticky ukladajú aj lokálne. Recept v `foto_url` drží relatívnu cestu (napr. `fotky/kremove-kuracie-rizoto-sampinony.jpg`).

---

## Pravidlá pre recepty

### id (technické, večné)
- Slug z opisného názvu, obsahuje kľúčové suroviny.
  Príklad: „Krémové kuracie rizoto so šampiňónmi" → `kremove-kuracie-rizoto-sampinony`
- Bez diakritiky, malé písmená, pomlčky.
- **id sa nikdy nemení**, aj keď sa zmení názov (inak prestane sedieť fotka).
- Pred vytvorením **skontroluj `recepty/`**:
  - ak existuje rovnaký recept → **neduplikuj**, upozorni používateľa
  - ak je podobný, ale iný → nájdi rozdiel a premietni ho do id (napr. `...-sampinony` vs `...-hrasok`), prípadne pridaj `-02`

### názov (pre ľudí)
- Kuchársky, lákavý, opisný. Nie „kuracie rizoto", ale „Krémové kuracie rizoto so šampiňónmi".
- Môže sa neskôr zmeniť. id ostáva.

### suroviny
- **Vždy z číselníka `suroviny.md`.** Ak surovina chýba, pridaj ju tam (jednotný názov).
- Nikdy nepoužívaj synonymá (vždy „paradajky", nikdy „rajčiny").
- Toto je kľúč k rýchlemu skladaniu receptov z akciových surovín.

### tagy (na rýchle vyhľadávanie)
Používaj len tieto skupiny, nevymýšľaj nové hodnoty:

- **typ:** obed, večera, polievka, šalát, jednohrnec
- **surovina:** kura, bravčové, hovädzie, ryba, bezmäsité, strukoviny
- **výživa:** vegetariánske, vysoký-proteín, ľahké, sýte
- **náročnosť:** do-20-minút, do-rúry, jednohrnec
- **cena:** lacné (pod 1 €/porcia), stredné

Recept má viac tagov naraz.

### cena za porciu
- Je to **snapshot** — počítaná z cien v danom týždni.
- Trvalé sú suroviny a množstvá; cenu vieme kedykoľvek prepočítať podľa aktuálneho letáku.

### nutričné hodnoty
- **Odhad**, nie lekársky presné údaje. Vždy uvádzať ako približné.

### fotka
- Súbor sa volá podľa **id** (napr. `kremove-kuracie-rizoto-sampinony.jpg`) a ukladá sa do `fotky/`.
- Recept obsahuje `foto_prompt` (zadanie pre generátor) a `foto_url` (relatívna cesta k hotovej fotke, napr. `fotky/kremove-kuracie-rizoto-sampinony.jpg`).
- Presná šablóna promptu je v skille `.claude/skills/tyzdenny-vystup/SKILL.md`, presný postup generovania (Gemini/nanobanana) je v `.claude/skills/generovanie-fotiek/SKILL.md`.

---

## Čo je dobrý šporáček recept

1. **Jednoduchý** — málo krokov, bežné vybavenie kuchyne.
2. **Lacný** — základ tvoria akciové suroviny.
3. **Chutný a zdravý** — lacné nesmie znamenať zlé.
4. **Prekrývajúce sa suroviny** — v rámci týždňa sa suroviny opakujú, nič sa nevyhodí.
5. **Realistický** — jedlo, ktoré si bežný človek naozaj uvarí.

---

## Kedy siahnuť po skille

- Spracovanie týždenného letáku (recepty, nákupný zoznam, ceny, stories) → `.claude/skills/tyzdenny-vystup/SKILL.md`. Nenačítavaj ho, ak práve neriešiš týždenný výstup — šetrí to kontext.
- Generovanie fotky k receptu (foto_url) → `.claude/skills/generovanie-fotiek/SKILL.md`. Obsahuje presný funkčný postup (SDK, nie curl) aj časté chyby, nech sa nezisťuje nanovo v každej session.
- Pridanie nového receptu mimo týždenného letáku → `.claude/skills/novy-recept/SKILL.md`. Recepty sa hľadajú na internete (nevymýšľajú sa) a píšu prirodzenou slovenčinou.

---

## Artifacty (vizuálne prehľady)

**Zdroj pravdy je vždy repo** (`recepty/`, `fotky/`, `tydne/`). Artifacty sú len jeho zobrazenie — nikdy nežijú vlastným životom. Ak sa artifact rozchádza s repom, repo vyhráva a artifact sa prepíše podľa neho.

Pred vytvorením nového artifactu **vždy over `Artifact list`**, či už niečo podobné neexistuje. Ak áno, **rozšír/aktualizuj ten istý** (rovnaká URL), nevytváraj duplicitu. Pri úprave existujúceho artifactu si najprv over jeho aktuálny obsah proti repu, nie len podľa pamäte z konverzácie.

Rozlišuj dva odlišné spôsoby zobrazenia, nemiešaj ich:

1. **Databáza receptov** — **NIE JE artifact.** Je to živá stránka `docs/index.html` (GitHub Pages), ktorá si dáta (recepty, fotky, tagy) ťahá naživo priamo z repa cez GitHub API pri každom otvorení/obnovení. **Nikdy sa neprepublikovúva** — stačí pushnúť nový recept/fotku do `recepty/`/`fotky/` a stránka ho ukáže sama po F5. Má vyhľadávanie a filtrovanie podľa tagov.
   **URL:** https://thevilo.github.io/sporacek/ (po zapnutí GitHub Pages v Settings)
   Starý artifact „šporáček — databáza receptov" (https://claude.ai/code/artifact/4a74dccc-333b-40d5-ac90-2c43f4bcd1bf) je **zastaraný, nepoužívaj ho** — nahradený touto stránkou.
2. **Týždenný "social" flow** — zatiaľ prepojené artifacty (🛒 Katalóg → 🍽️ Recepty týždňa → 📋 Nákupný zoznam), naviazané na *jeden konkrétny* leták/týždeň (`tydne/<týždeň>/`). Ukazuje len recepty skutočne vybrané pre daný týždeň, nie celú databázu. Cieľ je zlúčiť to do **jedného** artifactu na týždeň (zatiaľ nedokončené). Každý nový týždeň dostáva vlastné nové URL, zapísané do `tydne/<týždeň>/OVERVIEW.md`.

---

## Dôležité upozornenia

- **Leták je len dočasný vstup.** Automatický zber akciových produktov stavia programátor — my ho tu neriešime a neukladáme dlhodobo.
- **Trvalá hodnota = databáza receptov.** Tá sa nesmie robiť dvakrát. Preto zapisuj dôsledne a konzistentne.
- Pri každom novom recepte **over duplicity** a **konzistenciu názvov surovín**. Toto je jediná vec, ktorá môže systém rozbiť.
