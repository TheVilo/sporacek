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
| `ceny/` | **cenová databáza** — celý zoznam potravinových surovín z každého spracovaného letáku, s cenou, dátumom, obchodom (pozri nižšie) |
| `katalogy/` | vstupné PDF letákov + surové/pracovné extrakcie (pracovný vstup, nie zdroj pravdy — tým je `ceny/`) |
| `social/` | **všeobecný social obsah** — evergreen tipy a brand posty, nie viazané na recept/leták/týždeň (pozri nižšie) |

Fotky **sú v repe** (priečinok `fotky/`) — nech sa cez GitHub/git pull sync automaticky ukladajú aj lokálne. Recept v `foto_url` drží relatívnu cestu (napr. `fotky/kremove-kuracie-rizoto-sampinony.jpg`).

---

## Cenová databáza (`ceny/`)

**Účel:** dlhodobý dátový základ pre porovnávanie cien naprieč časom a obchodmi (napr. "marhule boli v júli o 55 % lacnejšie ako v priemere"). Iný účel než `tydne/` — `tydne/` má len úzky výber receptov/highlightov pre daný týždeň, `ceny/` má **celý** zoznam potravinových položiek z letáku, nech sa dá spätne dotazovať.

**Pravidlo:** pri každom spracovanom letáku (nezávisle od toho, či sa z neho robí aj týždenný recept-výstup) ulož **celý zoznam potravinových surovín** do `ceny/<obchod>-<dátum-začiatku-platnosti>.json`, napr. `ceny/kaufland-2026-07-16.json`. Jeden leták = jeden nový súbor (neprepisuje sa, história sa hromadí).

**Schéma** (JSON): koreň `{ obchod, platnost_tyzdenna_default, pocet_stran_v_katalogu, pocet_potravinovych_polozok, poznamka_metodika, polozky[] }`; každá položka `{ strana, nazov, mnozstvo, povodna_cena, zlava, zlavnena_cena, platnost, poznamka, obchod, zdroj_kontroly, kategoria }`. Kategórie (pevná sada, nevymýšľaj nové): `Mäso a ryby`, `Ovocie a zelenina`, `Mliečne a vajcia`, `Trvanlivé a základ`, `Orechy a sladkosti`, `Pečivo a pekáreň`.

**Scope — len skutočné suroviny na varenie.** Vynechaj alkohol, nápoje, chipsy/snacky, žuvačky, hotové sladkosti/zmrzliny, sladké hotové pečivo, kozmetiku/drogériu, domáce potreby, krmivo, detskú výživu/plienky, proteínové doplnky, elektroniku/odevy/záhradu. Platí rovnako naprieč obchodmi.

**Vzťah k `suroviny.md`:** `ceny/` je širší než číselník receptov — obsahuje všetko z letáku, aj veci, čo (zatiaľ) nie sú v žiadnom recepte. Do `suroviny.md` pridávaj surovinu až keď sa reálne použije v recepte.

---

## Social obsah (`social/`)

**Účel:** `docs/social.html` je databáza pripraveného social obsahu — hotový text a grafika na Instagram/Facebook na priame stiahnutie. Štyri zdroje:

1. **Fakty o cenách** — počítané **naživo v prehliadači** priamo z `ceny/*.json` (najväčšie aktuálne zľavy + cenové porovnanie tej istej suroviny naprieč obchodmi tento týždeň). Nič sa nezapisuje, rastie to samo s každým novým letákom. Položky s podmienkou v `poznamka` (kupón, vernostná karta, min. nákup) sa buď vynechajú z rebríčka, alebo sa podmienka pridá do textu — nikdy sa nesmie ukázať zľava bez tejto podmienky, bola by zavádzajúca.
2. **Recepty** — naživo z `recepty/` + `fotky/` (rovnaký zdroj ako `docs/index.html`). Jedna karta na recept, foto je vždy vlastná fotka receptu (nie náhodná).
3. **Tipy na nákup** — evergreen, `social/tipy.json`. Nie viazané na konkrétny leták/týždeň/recept (na to je `tydne/`).
4. **Brand/misia posty** — evergreen, `social/brand.json`. Princíp, tón, engagement — v duchu `znalostna-baza/brand-manual.md` (banka claimov, tón hlasu).

**Schéma** oboch JSON súborov (`tipy.json`, `brand.json`): koreň `{ kategoria, poznamka, polozky[] }`, každá položka `{ id, hook, caption }` — `hook` je krátky text na grafiku (max ~12 slov), `caption` je dlhší text na skopírovanie k postu.

**Pravidlo pri pridávaní tipov/brand postov:** rešpektuj `znalostna-baza/brand-manual.md` tón hlasu aj "NIKDY nehovoríme" pravidlá (žiadna appka/sťahovanie/čakacia listina vo fáze 1, žiadne moralizovanie o šetrení, žiadne "kríza/drahota", vždy konkrétne, nie abstraktné rady).

**Grafika sa negeneruje cez AI ani neukladá do repa** — `docs/social.html` ju vyrenderuje priamo v prehliadači (canvas) pri kliknutí na "Story"/"Post" a rovno spustí stiahnutie. Toto je zámerne iný mechanizmus než `foto_url` fotky jedla (tie *sú* generované cez Gemini a *sú* v repe, pozri `generovanie-fotiek/SKILL.md`) — tu ide o kompozíciu z existujúcej fotky + textu, AI image model by presný text nevykreslil spoľahlivo.

**6 striedajúcich sa dizajnových šablón** (nie jeden univerzálny vzhľad) — `fullbleed` (fotka na celú plochu + gradient, text zarovnaný vľavo), `colorblock` (fotka hore ~60 %, farebný blok dole s textom), `bignum` (bez fotky, obrovské číslo/percento ako hlavný prvok — pre jednu zľavu), `split` (diagonálne rozdelenie na dve farby, cena vs. cena — len pre medziobchodné porovnanie), `polaroid` (fotka orámovaná bielym okrajom, popis pod rámom), `badge` (kruhový fotka-odznak v rohu + veľký nadpis). Šablóna sa vyberá deterministicky podľa `id` karty (rovnaký post = vždy rovnaká šablóna), rozdelené podľa vhodnosti: `fakt` (zľava) → bignum/fullbleed, `fakt` (porovnanie) → vždy split, `recept` → colorblock/polaroid, `tip`/`brand` → fullbleed/colorblock/badge.

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

- **typ:** obed, večera, raňajky, desiata, olovrant, dezert, polievka, šalát, jednohrnec, predjedlo, príloha, nápoj, pečivo
- **surovina:** kura, bravčové, hovädzie, ryba, morčacie, morské-plody, bezmäsité, strukoviny
- **výživa:** vegetariánske, vysoký-proteín, ľahké, sýte
- **náročnosť:** do-20-minút, do-rúry, jednohrnec

Recept má viac tagov naraz. (Cenová kategória zámerne nie je tag — pozri nižšie.) Taxonómia sa dá časom rozšíriť, keď pribudne typ jedla, ktorý do žiadnej skupiny nesedí — priebežne, nie dopredu "pre istotu".

### recept nikdy neobsahuje cenu ani väzbu na konkrétny týždeň/obchod
- Recept má **len suroviny a množstvá**, nikdy cenu (ani za surovinu, ani za porciu, ani "Celkom"). Cena akejkoľvek suroviny sa mení každý týždeň — keby bola napísaná v recepte, zastarala by hneď a niekto by ju musel ručne opravovať naprieč desiatkami receptov.
- Cena sa počíta **až v momente použitia** — pri spracovaní týždenného letáku (`.claude/skills/tyzdenny-vystup/SKILL.md`, tam ide do `tydne/<týždeň>/`) alebo pri akomkoľvek inom custom požiadavke ("Lidl, talianske recepty pre 2 na 2 dni, len raňajky a večere") — presne to, čo neskôr bude robiť appka automaticky.
- To isté platí pre čokoľvek iné viazané na konkrétny obchod/dátum — pole "týždeň", tag `#akcia-lidl`, poznámka "platí len v utorok" a podobne. **Toto všetko patrí výhradne do `tydne/<týždeň>/`, nikdy do `recepty/<slug>.md`** — aj keď recept práve vznikol z konkrétneho letáku, časom ho použijeme v mnohých ďalších týždňoch aj obchodoch.
- Recepty samotné (`recepty/`) sú tak **navždy nezastarateľná databáza**: suroviny + množstvá + postup + fotka + tagy z taxonómie. Ničím časovo ani obchodovo podmieneným.

### nutričné hodnoty
- **Odhad**, nie lekársky presné údaje. Vždy uvádzať ako približné.

### fotka
- Súbor sa volá podľa **id** (napr. `kremove-kuracie-rizoto-sampinony.jpg`) a ukladá sa do `fotky/`.
- Recept obsahuje `foto_prompt` (zadanie pre generátor) a `foto_url` (relatívna cesta k hotovej fotke, napr. `fotky/kremove-kuracie-rizoto-sampinony.jpg`).
- Presná šablóna promptu je v skille `.claude/skills/tyzdenny-vystup/SKILL.md`, presný postup generovania (Gemini/nanobanana) je v `.claude/skills/generovanie-fotiek/SKILL.md`.

---

## Čo je dobrý šporáček recept

1. **Jednoduchý** — málo krokov, bežné vybavenie kuchyne.
2. **Z akciových surovín** — základ tvoria suroviny, ktoré sú práve v akcii. Ale **akciové ≠ chudobné.** Šporáček nie je "jedlo pre chudobných" — je to chutné jedlo postavené na tom, čo je práve výhodné kúpiť, prispôsobené tomu, čo si človek vyberie (napr. "fitness" → vysoký proteín/ľahšie, "rodinné" → sýte a vydatné). Nikdy nerob recept zámerne chudobný/nudný len preto, že je lacný.
   **Poradie myslenia:** najprv poriadny, chutný recept (aký by si našiel na dobrom kuchárskom webe) — až potom sa pozri, ktoré jeho suroviny sú v akcii a dajú sa tak uvariť lacnejšie. Nikdy nie naopak ("čo je najlacnejšie, to hodím na tanier a nazvem to jedlom" — napr. mäso + krajec chleba, len aby to bolo pod 1 €). Šporáček učí ľudí variť dobre **a zároveň** šetriť — nie variť chudobne.
3. **Chutný a zdravý** — recept musí byť taký, že by si ho človek naozaj chcel navariť a zjesť, nielen taký, čo "stačí". Inšpiruj sa **reálnymi receptami z netu** (rovnako ako pri `.claude/skills/novy-recept/SKILL.md`), neskladaj kroky nazlepšie od stola.
4. **Prekrývajúce sa suroviny** — v rámci týždňa sa suroviny opakujú, nič sa nevyhodí.
5. **Realistický** — jedlo, ktoré si bežný človek naozaj uvarí.

---

## Kedy siahnuť po skille

- Spracovanie týždenného letáku (recepty, nákupný zoznam, ceny, stories) → `.claude/skills/tyzdenny-vystup/SKILL.md`. Nenačítavaj ho, ak práve neriešiš týždenný výstup — šetrí to kontext.
- Generovanie fotky k receptu (foto_url) → `.claude/skills/generovanie-fotiek/SKILL.md`. Obsahuje presný funkčný postup (SDK, nie curl) aj časté chyby, nech sa nezisťuje nanovo v každej session.
- Pridanie nového receptu mimo týždenného letáku → `.claude/skills/novy-recept/SKILL.md`. Recepty sa hľadajú na internete (nevymýšľajú sa) a píšu prirodzenou slovenčinou.

---

## Živé stránky (GitHub Pages, nie artifacty)

**Zdroj pravdy je vždy repo** (`recepty/`, `fotky/`, `tydne/`, `ceny/`, `social/`, `suroviny.md`). Všetky stránky nižšie sú len jeho živé zobrazenie — nikdy neobsahujú dáta, ktoré nie sú v repe, a nikdy sa neprepublikovávajú ručne. Stačí pushnúť zmenu do repa, stránka ju ukáže po obnovení (F5).

Stránky bežia cez GitHub Pages na **custom doméne `recepty.sporacek.sk`** (`docs/CNAME`). Pages servuje z priečinka `docs/` na `main`.

**Claude Artifacty pre šporáček viac nepoužívaj** (staré URL z predošlej fázy sú zastarané a ignoruj ich) — všetko nahradili týchto päť stránok v `docs/`:

1. **`docs/index.html` — databáza receptov.** Prehľad *všetkých* receptov (fotka, suroviny, tagy, postup — bez ceny, tá sa počíta len na úrovni týždňa), naživo z `recepty/` a `fotky/`. Má vyhľadávanie podľa názvu a filtrovanie podľa tagov. Toto je tá trvalá databáza, z ktorej sa recepty párujú s akciovými surovinami.
   **URL:** https://recepty.sporacek.sk/
2. **`docs/tyzden.html` — týždenný "social" výstup.** Naviazaný na *konkrétny* leták/obchod/týždeň. Číta `tydne/<rok>-W<týždeň>-<obchod>/data.json` a k receptom naživo dotiahne fotku/postup z `recepty/`. Má prepínač týždňov/obchodov hore (chip pre každý priečinok v `tydne/`).
   **URL:** https://recepty.sporacek.sk/tyzden.html
   **Bez `data.json` sa týždeň na stránke nezobrazí** — presná štruktúra je v `.claude/skills/tyzdenny-vystup/SKILL.md`.
3. **`docs/ceny.html` — cenová databáza.** Prehľad cien surovín naprieč obchodmi a časom, naživo zo všetkých `ceny/*.json`. Tabuľka (filter podľa obchodu/kategórie/hľadania, čo je v akcii) + graf vývoja ceny po kliknutí na surovinu. Rastie automaticky s každým novým súborom v `ceny/`.
   **URL:** https://recepty.sporacek.sk/ceny.html
4. **`docs/vyber.html` — zostav týždeň.** Interaktívny nástroj na výber receptov pre týždenný výstup — vyberieš obchod, stránka pri každom recepte naživo prepočíta, koľko jeho surovín je práve v akcii (porovnaním `recepty/*.md` surovín s `ceny/<obchod>-*.json`), zoradí podľa zhody a dá vyfiltrovať podľa tagov. Zaškrtneš recepty, tlačidlo "Skopírovať výber" skopíruje zoznam do schránky — ten sa potom pošle v chate a z neho sa spracuje `tydne/<týždeň>/` presne podľa `.claude/skills/tyzdenny-vystup/SKILL.md` (táto stránka nič sama neukladá, je to len pomôcka na výber, nie generátor výstupu — GitHub Pages nevie zapisovať do repa).
   **URL:** https://recepty.sporacek.sk/vyber.html
   Zhoda surovín je len heuristika podľa názvu (nie vždy presná) — finálne ceny/výber vždy over pri zostavovaní týždňa.
5. **`docs/social.html` — hotové posty a stories.** Fakty o cenách počítané naživo z `ceny/*.json` + recepty naživo z `recepty/`/`fotky/` + evergreen tipy/brand posty z `social/tipy.json` a `social/brand.json`. Každá karta má "Kopírovať text" a "Story"/"Post" tlačidlo — grafika sa vyrenderuje priamo v prehliadači (canvas, jedna zo 6 striedajúcich sa šablón) a rovno stiahne, nič sa negeneruje cez AI ani neukladá do repa. Pozri `## Social obsah (social/)` vyššie pre presnú schému a pravidlá pri pridávaní tipov.
   **URL:** https://recepty.sporacek.sk/social.html

### Viacero obchodov

Každý obchod (Lidl, Kaufland, Tesco...) má **vlastný, nezávislý** týždenný výstup — vlastný priečinok `tydne/<rok>-W<týždeň>-<obchod>/`, vlastných 5 receptov, vlastný nákupný zoznam aj social obsah. Nemiešaj obchody do jedného výstupu.

---

## Dôležité upozornenia

- **Leták je len dočasný vstup.** Automatický zber akciových produktov stavia programátor — my ho tu neriešime a neukladáme dlhodobo.
- **Trvalá hodnota = databáza receptov.** Tá sa nesmie robiť dvakrát. Preto zapisuj dôsledne a konzistentne.
- Pri každom novom recepte **over duplicity** a **konzistenciu názvov surovín**. Toto je jediná vec, ktorá môže systém rozbiť.
