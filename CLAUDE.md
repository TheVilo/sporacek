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
| `znalostna-baza/aliasy.json` | **kurátorovaná alias-vrstva** — pre každé `id` suroviny (slug zo `suroviny.md`) doplnené aliasy (ako sa volá v letákoch) + základná jednotka. Toto robí párovanie leták↔surovina deterministickým (pozri nižšie). |
| `scripts/build_databaza.py` | build skript, ktorý spojí `suroviny.md` + `aliasy.json` + `ceny/` + `recepty/` do jednej databázy pre appku |
| `docs/data/databaza.json` | **generovaná hlavná databáza** (needituj ručne!) — každá surovina s cenami (platnosť od-do, podmienka) + každý recept napárovaný na `id` s cenou za porciu per obchod. Zdroj, z ktorého číta appka (pozri nižšie). |
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

## Hlavná databáza pre appku (`docs/data/databaza.json`)

**Účel:** appka (a časom aj stránky) si má **ťahať dáta z jednej databázy**, nie pri každom rendrovaní nanovo hádať, ktorá letáková položka je ktorá surovina. Preto existuje kanonická vrstva, ktorá spája `recept → surovina → cena` **deterministicky cez stabilné `id`**.

**Ako to funguje (3 zdroje pravdy + 1 generovaný výstup):**

1. `suroviny.md` — kanonický zoznam surovín. Z názvu sa robí `id` (slug bez diakritiky, napr. „kuracie prsia" → `kuracie-prsia`). Zdroj pravdy pre to, **ktoré suroviny existujú**.
2. `znalostna-baza/aliasy.json` — kurátorované **aliasy** (ako sa tá istá surovina volá v letákoch, napr. `kuracie-prsia` ← „Kuracie prsné rezne", „Kuracie rezne") + **základná jednotka** (g/ml/ks). Toto je tá jediná vec, ktorú treba udržiavať ručne — a je to zámerne tak (rovnako ako `suroviny.md`, párovanie je jediné, čo môže systém rozbiť). Aliasy sa porovnávajú normalizovane (bez diakritiky) ako podreťazec; najdlhší alias vyhráva. **Nepoužívaj priveľmi všeobecné aliasy** (napr. samotné „kuracie") — chytali by nesúvisiace položky.
3. `ceny/*.json` + `recepty/*.md` — cenníky a recepty (bez zmeny, len sa z nich číta).

→ `scripts/build_databaza.py` to spojí do **`docs/data/databaza.json`** (schema_verzia 2): koreň `{ meta, suroviny[], recepty[] }`. Každá surovina má `{ id, nazov, kategoria, jednotka, trvanlivost, gramy_za_ks, spotreba_dni, alergeny[], statistiky, ceny[] }`, kde každá cena nesie `{ obchod, nazov_v_letaku, mnozstvo, balenie_qty, balenie_jednotka, zlavnena_cena, povodna_cena, zlava, jednotkova_cena, platnost_od, platnost_do, podmienka }` — teda **cena + platnosť od-do + podmienka** (napr. „s Lidl Plus"). `statistiky` = bežná/min jednotková cena z celej histórie (pre „zlacnelo o X %" a social fakty). Každý recept má suroviny napárované na `id` **s normalizovaným množstvom** (`qty`, `jednotka`, `mnozstvo_g` — nech appka vie škálovať porcie a zlučovať nákupy bez parsovania textov), odvodené `alergeny[]` + `vegetarianske`/`veganske` (zo surovín, nie ručne), `ceny_za_porciu[]` per obchod (`cena_za_porciu`, `usetris_za_porciu`, `spolahlive`, `nakup[]`) a súhrn `najlacnejsie`. Recept `.md` **naďalej nikdy neobsahuje cenu** — cena vzniká len tu, pri builde.

**Ceny receptov len z najnovšieho letáku.** `suroviny[].ceny[]` drží celú históriu (grafy, štatistiky), ale `ceny_za_porciu` sa počíta **výhradne z najnovšieho letáku každého obchodu** (`meta.aktualny_letak_od`) — inak by sa po pridaní ďalšieho týždňa miešali staré zľavy s novými.

**Konkrétny produkt (značka) pre nákupný zoznam.** Kanonické `id` je len na *párovanie a logiku receptu* — je jedno, akej značky sú kuracie prsia. Ale **nákupný zoznam musí userovi povedať, čo presne kúpiť**, preto každá cena drží `nazov_v_letaku` (konkrétny produkt zo zľavy, napr. „Kuracie prsia Domäsko") a každá položka v `ceny_za_porciu[].nakup[]` nesie `{ id, surovina, kupit (nazov_v_letaku), balenie, balenie_qty, balenie_jednotka, cena_balenia, povodna_cena, akcia, podmienka, trvanlivost, cena_v_recepte, usetris_v_recepte, mnozstvo_g }`. Z toho sa poskladá nákupný zoznam so správnym produktom aj s úsporou („ušetríš €X" = rozdiel oproti pôvodnej cene, prepočítaný na použité množstvo) — a z `balenie_qty` − `mnozstvo_g` zvyšok do špajze.

**Alergény a diéty (`alergeny`, `spotreba_dni` v `aliasy.json`).** Per surovina kurátorované EÚ alergény (`lepok`, `laktoza`, `vajcia`, `ryby`, `korysy`, `orechy`, `arasidy`, `soja`, `sezam`, `zeler`, `horcica`) a odhad trvanlivosti čerstvej suroviny v dňoch (`spotreba_dni`, default podľa kategórie). Alergény receptu aj príznaky `vegetarianske`/`veganske` sa **odvodzujú automaticky zo surovín** pri builde — nikdy sa needitujú per recept (odvodenie je robustnejšie a nezastará). Sú to odhady — appka pri vážnych alergiách vždy odkáže na etiketu výrobku.

**`trvanlivost` (`cerstve` | `trvanlive`).** Rozlišuje, či sa surovina kupuje čerstvá na daný týždeň (mäso, mliečne, čerstvá zelenina/ovocie), alebo je to **trvanlivá zásoba do špajze** (múka, olej, cestoviny, ryža, konzervy, korenie, aj skladovateľná zelenina — cibuľa, cesnak, zemiaky). Základ podľa kategórie, výnimky (konzervy, skladovateľná zelenina, pečivo) v `aliasy.json`. Slúži už dnes (nákupný zoznam oddelí „čerstvé na tento recept" od „trvanlivé, kúpiš raz") a je to **základ pre pripravovanú funkciu špajze** (viď nižšie).

**`gramy_za_ks` (prepočet kusov).** Recepty uvádzajú suroviny často v kusoch („1 ks cibuľa", „2 strúčiky cesnaku"), ale letáky ich predávajú na kg/balenie. Priemerná hmotnosť 1 kusa (v `aliasy.json`, napr. cibuľa 110 g, strúčik cesnaku 5 g, citrón 100 g) umožní prepočet ks→g, takže sa dá oceniť aj to, čo je v letáku len na váhu — vďaka tomu je spoľahlivo ocenených výrazne viac receptov. Objemové odhady (PL/lyžica ≈ 15 g/ml, ČL/lyžička ≈ 5 g/ml) rieši `build_databaza.py` priamo. Nákupný zoznam navyše drží `mnozstvo_g` (koľko recept reálne spotrebuje) — z toho a z veľkosti balenia sa dá dopočítať **zvyšok do špajze** (kúpiš hlavičku cesnaku, recept minie 2 strúčiky → zvyšok si odložíš).

**Pravidlo:** `docs/data/databaza.json` je **generovaný súbor, needituj ho ručne.** Keď sa zmení `recepty/`, `ceny/`, `suroviny.md` alebo `aliasy.json`, **prebuild-ni** ho:
```
python3 scripts/build_databaza.py
```
Skript na konci vypíše pokrytie (koľko surovín má cenu, koľko receptov je spoľahlivo ocenených, koľko letákových názvov ostalo nespárovaných) a nespárované názvy uloží do `scripts/.nesparovane.json` (ignorované gitom) — podľa neho vieš dopĺňať aliasy. Nespárované letákové názvy sú z veľkej časti **legitímne mimo záber** (značkové výrobky, nátierky, sladkosti, mäsové rezy mimo číselníka) — dopĺňaj alias len keď ide o surovinu, ktorá **je** v `suroviny.md`.

**Úplnosť číselníka (dôležité):** každá surovina použitá v ktoromkoľvek recepte **musí byť v `suroviny.md`** — aj tá, čo sa nekupuje pri každom jedle (olivový olej, korenie). Vďaka tomu dostane odhad ceny, keď sa objaví v letáku. Build to kontroluje: nespárované suroviny receptu vypíše do reportu (okrem „voda", ktorá nie je surovina). Keď tam nejaká vyskočí, doplň ju do `suroviny.md` (a podľa potreby alias do `aliasy.json`).

**Vzťah k `docs/vyber.html`:** stránka `vyber.html` dnes robí to isté párovanie naživo v prehliadači (bez aliasov, len podreťazec). `databaza.json` je presnejšia (má aliasy) a je určená appke; stránky sa na ňu môžu časom prepnúť, aby existovala **jedna** párovacia logika. Dovtedy sú obe konzistentné v princípe (rovnaká normalizácia aj prepočet jednotiek).

**Pripravovaná funkcia „špajža" (platená).** Trvanlivé suroviny (`trvanlivost: "trvanlive"`), ktoré sa neminú, si user odloží do špajze; môže si tam pridať aj to, čo má doma. Šporáček s tým potom **počíta pri odhade ceny aj nákupnom zozname** — čo je v špajži, sa neduplikuje do nákupu a recepty sa uprednostne skladajú tak, aby sa domáce zásoby spotrebovali (ďalšia forma šetrenia). Preto databáza už teraz rozlišuje `trvanlivost` a v nákupnom zozname drží `id` + konkrétny produkt — špajža sa bude porovnávať práve cez `id`. (Samotná špajža sa rieši ako ďalší krok, dátový model je na ňu pripravený.)

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

### formát súboru (jednotný — dôležité)
**Všetky recepty majú presne rovnakú štruktúru** — nikdy nie polovica takto a polovica inak (napr. YAML frontmatter). Kanonická šablóna je v `.claude/skills/novy-recept/SKILL.md`: `# Názov`, potom `**slug:** **porcie:** **čas prípravy:** **foto_url:**`, a sekcie `## Foto prompt`, `## Suroviny (pre N osoby)`, `## Nutričné hodnoty (na porciu, odhad)`, `## Postup`, `## Tagy`. Žiadne polia navyše (napr. `historia_pouzitia` — recept sa neviaže na dátumy). `scripts/build_databaza.py` formát kontroluje a nahlási každý recept, ktorý sa odchýli — build musí byť bez týchto varovaní.

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
- **surovina:** kura, bravčové, hovädzie, ryba, morčacie, morské-plody, bezmäsité, strukoviny, jahňacie, kačacie
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
- Spracovanie letáku do cenovej databázy `ceny/` (overenie JSON-u z Gemini alebo import z PDF) → `.claude/skills/ceny-z-letaku/SKILL.md`. Obsahuje hotový Gemini prompt aj postup na kontrolu (vnútornú + náhodnú proti PDF) a import.

> **Po každej zmene `ceny/`, `recepty/`, `suroviny.md` alebo `aliasy.json` prebuild-ni hlavnú databázu:** `python3 scripts/build_databaza.py` (pozri sekciu „Hlavná databáza pre appku"). Na `main` to po pushi spraví aj GitHub Action `.github/workflows/build-databaza.yml` automaticky (deterministický skript, bez AI) — lokálny rebuild sa ale stále hodí, nech vidíš report pokrytia a formátové varovania hneď.

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
4. **`docs/vyber.html` — "Čo navariť" (predtým "zostav týždeň", premenované — nie je viazané na konkrétny týždeň).** Vyberieš obchod a štýl jedla (tagy), stránka pri každom recepte naživo prepočíta **odhadovanú cenu za porciu**: napáruje suroviny receptu (`recepty/*.md`) na položky letáku (`ceny/<obchod>-*.json`) podľa názvu, prevedie množstvo receptu (g/ml/ks, PL/ČL odhadom) na rovnakú jednotku ako balenie v letáku a vynásobí cenou za jednotku. Recept dostane cenu len keď sa takto vie oceniť aspoň polovica surovín ("spoľahlivé") — inak sa ukáže "cenu sa nepodarilo spoľahlivo odhadnúť" namiesto zavádzajúceho čísla. Recepty sa zoraďujú od najlacnejšieho (spoľahlivé) po nespoľahlivé. Zaškrtneš recepty, tlačidlo "Skopírovať výber" skopíruje zoznam (aj s cenou) do schránky — ten sa potom pošle v chate a z neho sa spracuje `tydne/<týždeň>/` presne podľa `.claude/skills/tyzdenny-vystup/SKILL.md` (táto stránka nič sama neukladá — GitHub Pages nevie zapisovať do repa).
   **URL:** https://recepty.sporacek.sk/vyber.html
   Párovanie aj prepočet množstva sú heuristika podľa názvu/textu (nie vždy presná) — finálne ceny vždy over pri zostavovaní týždňa.
5. **`docs/social.html` — hotové posty a stories.** Fakty o cenách počítané naživo z `ceny/*.json` + recepty naživo z `recepty/`/`fotky/` + evergreen tipy/brand posty z `social/tipy.json` a `social/brand.json`. Každá karta má "Kopírovať text" a "Story"/"Post" tlačidlo — grafika sa vyrenderuje priamo v prehliadači (canvas, jedna zo 6 striedajúcich sa šablón) a rovno stiahne, nič sa negeneruje cez AI ani neukladá do repa. Pozri `## Social obsah (social/)` vyššie pre presnú schému a pravidlá pri pridávaní tipov.
   **URL:** https://recepty.sporacek.sk/social.html

### Viacero obchodov

Každý obchod (Lidl, Kaufland, Tesco...) má **vlastný, nezávislý** týždenný výstup — vlastný priečinok `tydne/<rok>-W<týždeň>-<obchod>/`, vlastných 5 receptov, vlastný nákupný zoznam aj social obsah. Nemiešaj obchody do jedného výstupu.

---

## Dôležité upozornenia

- **Leták je len dočasný vstup.** Automatický zber akciových produktov stavia programátor — my ho tu neriešime a neukladáme dlhodobo.
- **Trvalá hodnota = databáza receptov.** Tá sa nesmie robiť dvakrát. Preto zapisuj dôsledne a konzistentne.
- Pri každom novom recepte **over duplicity** a **konzistenciu názvov surovín**. Toto je jediná vec, ktorá môže systém rozbiť.
