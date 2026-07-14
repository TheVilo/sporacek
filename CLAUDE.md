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
| `CLAUDE.md` | tento súbor — pravidlá a postup |
| `znalostna-baza/` | brand manuál, obsahová stratégia |
| `suroviny.md` | **číselník surovín** — jednotné názvy (kritické!) |
| `recepty/` | jeden súbor = jeden recept |
| `tydne/` | výstup týždňa (leták → recepty → nákup → úspora) |

Fotky **nie sú v repe.** Recept drží len odkaz (`foto_url`).

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
- Súbor sa volá podľa **id** (napr. `kremove-kuracie-rizoto-sampinony.jpg`).
- Recept obsahuje:
  - `foto_prompt` — zadanie pre generátor (nanobanana), aby sa dala fotka kedykoľvek pregenerovať
  - `foto_url` — odkaz na hotovú fotku (doplní sa po vygenerovaní)

---

## Čo je dobrý šporáček recept

1. **Jednoduchý** — málo krokov, bežné vybavenie kuchyne.
2. **Lacný** — základ tvoria akciové suroviny.
3. **Chutný a zdravý** — lacné nesmie znamenať zlé.
4. **Prekrývajúce sa suroviny** — v rámci týždňa sa suroviny opakujú, nič sa nevyhodí.
5. **Realistický** — jedlo, ktoré si bežný človek naozaj uvarí.

---

## Týždenný postup (keď dostanem leták)

1. **Prečítaj leták** (PDF/screenshot/text) → vypíš akciové produkty s cenami.
2. **Prehľadaj `recepty/`** → zisti, čo už máme, aby nevznikli duplicity.
3. **Navrhni 5 obedov (Po–Pi), vždy pre 2 osoby**, podľa pravidiel vyššie.
   - prednostne použi existujúce recepty z databázy, ak sedia na akciu
   - nové recepty vytvor len ak treba
4. **Prepočítaj:**
   - cenu za porciu pre každé jedlo
   - kompletný nákupný zoznam s cenami
   - celkovú cenu nákupu
   - úsporu oproti bežným cenám
5. **Ku každému receptu daj `foto_prompt`** (viď nižšie).
6. **Priprav texty do Stories** (názov jedla + cena za porciu).
7. **Zapíš:**
   - nové recepty do `recepty/`
   - nové suroviny do `suroviny.md`
   - výstup týždňa do `tydne/RRRR-MM-DD.md`

---

## Šablóna foto promptu (pre nanobanana)

```
Fotorealistická fotografia jedla: [NÁZOV JEDLA], porcia na jednoduchom tanieri.
Domáca kuchyňa, prirodzené teplé svetlo z okna, drevený alebo svetlý stôl.
Reálny, útulný, domácky vzhľad — nie reklamná, prehnane naštylizovaná scéna.
Teplé zemité tóny (piesková, terakota, zelené akcenty), mäkké tiene.
Pohľad zhora alebo mierne zboku, plytká hĺbka ostrosti.
Voľné miesto navrchu alebo po strane na text.
Bez textu a bez loga v obrázku.
Formát 9:16 (Instagram Stories).
```

---

## Dôležité upozornenia

- **Leták je len dočasný vstup.** Automatický zber akciových produktov stavia programátor — my ho tu neriešime a neukladáme dlhodobo.
- **Trvalá hodnota = databáza receptov.** Tá sa nesmie robiť dvakrát. Preto zapisuj dôsledne a konzistentne.
- Pri každom novom recepte **over duplicity** a **konzistenciu názvov surovín**. Toto je jediná vec, ktorá môže systém rozbiť.
