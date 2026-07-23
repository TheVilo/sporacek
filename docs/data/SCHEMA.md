# Dátový kontrakt pre appku (schema_verzia 2)

Všetko generuje `scripts/build_databaza.py` (automaticky po každej zmene
zdrojov) — **nikdy needituj ručne**, pri ďalšom builde by sa zmena prepísala.

## API v1 — týmto sa napájajú appky (Android/iOS)

Base URL: `https://recepty.sporacek.sk/api/v1/`

| endpoint | obsah | kedy ho appka volá |
|---|---|---|
| `meta.json` | verzia schémy, obchody, `aktualny_letak_od` | pri štarte (staré dáta? nový leták?) |
| `recepty/index.json` | ľahký zoznam receptov (názov, náhľad, tagy, kcal, alergény, `najlacnejsie`) ~10 KB gzip | zoznam / scroll / vyhľadávanie |
| `recepty/{slug}.json` | plný recept (suroviny s `id`+`mnozstvo_g`, postup, `ceny_za_porciu` s nákupom) | otvorenie detailu |
| `suroviny/index.json` | ľahký zoznam surovín (kategória, trvanlivosť, sezóna, `aktualne_najlacnejsie`) | watchlist / špajza výber |
| `suroviny/{id}.json` | plný záznam vrátane histórie cien a štatistík | detail suroviny / graf ceny |

**Pravidlá kontraktu:**
- Tvary polí sú rovnaké ako v `databaza.json` (popis nižšie) — index súbory sú len výrezy.
- URL fotiek (`foto_url` plná, `foto_nahlad_url` 320 px náhľad pre zoznamy) sú **absolútne** — appka si nikdy neskladá cesty k obrázkom sama, hosting sa dá presunúť bez zmeny appky.
- Dnes to servíruje GitHub Pages ako statické súbory. **Budúci backend musí dodržať rovnaké cesty a tvary** — potom sa v appke mení len base URL, nič iné. Toto je jediné miesto, na ktoré sa appky viažu natvrdo.
- Zmena tvaru poľa = nový `schema_verzia` v `meta.json` (appka si ju overuje).

## databaza.json — celý dataset v jednom súbore

`https://recepty.sporacek.sk/data/databaza.json` (~2,3 MB, ~190 KB gzip) —
používajú ho webové stránky repa; appky preferujú API v1 vyššie.

Koreň: `{ meta, suroviny[], recepty[] }`.

## meta

| pole | význam |
|---|---|
| `schema_verzia` | verzia schémy (teraz 2) — appka si ju over |
| `generovane` | UTC timestamp buildu |
| `obchody[]` | zoznam obchodov v databáze |
| `aktualny_letak_od` | `{obchod: dátum}` — začiatok najnovšieho letáku per obchod. Ceny receptov sú počítané výhradne z týchto letákov. |

## suroviny[]

Kanonická surovina. `id` je stabilný slug — **všetko sa spája cez `id`**
(recept ↔ surovina ↔ cena ↔ špajza ↔ watchlist).

| pole | význam |
|---|---|
| `id`, `nazov`, `kategoria` | identita ("kuracie-prsia", „kuracie prsia", „Mäso a ryby") |
| `jednotka` | základná jednotka suroviny: `g` / `ml` / `ks` |
| `trvanlivost` | `cerstve` (kúpiť na daný týždeň) / `trvanlive` (zásoba do špajze) |
| `gramy_za_ks` | priemerná hmotnosť 1 kusa v g (cibuľa 110, strúčik cesnaku 5) — na prepočty ks↔g; `null` ak sa nepoužíva |
| `spotreba_dni` | odhad „spotrebuj do X dní" pre špajzu; `null` = v horizonte plánovania nevyprší |
| `alergeny[]` | EÚ alergény suroviny: `lepok`, `laktoza`, `vajcia`, `ryby`, `korysy`, `orechy`, `arasidy`, `soja`, `sezam`, `zeler`, `horcica`. **Odhad — pri vážnej alergii vždy odkáž na etiketu.** |
| `sezona[]` | mesiace sezóny (marhule `[6,7,8]`); `null` = bez výraznej sezóny |
| `bezna_cena`, `bezne_balenie` | kurátorovaná bežná cena mimo akcie (soľ, korenie, múka…) — fallback, keď surovina nie je v aktuálnom letáku |
| `statistiky` | `{bezna_jednotkova_cena, min_jednotkova_cena, pocet_zaznamov}` z celej histórie — na „zlacnelo o X %"; `null` kým niet dát |
| `aktualne_najlacnejsie` | kde je surovina teraz najlacnejšia: `{obchod, nazov_v_letaku, zlavnena_cena, mnozstvo, jednotkova_cena, zlava, podmienka, platnost_do}`; `null` ak nie je v žiadnom aktuálnom letáku |
| `ceny[]` | história cien (posledných ~12 týždňov; staršie sú len v `ceny/*.json` repa) |

### suroviny[].ceny[] (jeden záznam = jedna letáková cena)

`{ obchod, nazov_v_letaku, nazov_norm, mnozstvo, balenie_qty, balenie_jednotka,
zlavnena_cena, povodna_cena, zlava, jednotkova_cena, platnost_od, platnost_do,
podmienka, kategoria_letak }`

- `nazov_v_letaku` = konkrétny produkt („Kuracie prsia Domäsko") — toto zobrazuj v nákupnom zozname.
- `nazov_norm` = normalizovaný názov (malé písmená, bez diakritiky) — **na produktový watchlist**: user sleduje „rajo maslo" → matchuj substring proti `nazov_norm` naprieč záznamami, žiadne vlastné porovnávanie reťazcov.
- `podmienka` — ak nie je `null` (napr. „s Lidl Plus"), **nikdy nezobrazuj cenu bez nej**.
- `jednotkova_cena` = € za 1 g/ml/ks (podľa `balenie_jednotka`).

## recepty[]

| pole | význam |
|---|---|
| `slug`, `nazov`, `porcie`, `cas_pripravy`, `foto_url`, `tagy[]` | základ; fotka je relatívna cesta v repe (`https://raw.githubusercontent.com/TheVilo/sporacek/main/<foto_url>`) |
| `suroviny[]` | pozri nižšie |
| `postup[]` | kroky (hotové texty po slovensky) |
| `nutricne` | `{kcal, bielkoviny_g, sacharidy_g, tuky_g}` na porciu — **odhad**, vždy označ ako približné |
| `alergeny[]`, `vegetarianske`, `veganske` | odvodené automaticky zo surovín — na filter „Diéta a alergény" |
| `sezonne_suroviny[]` | `[{id, mesiace}]` — ktoré suroviny receptu majú sezónu (na „práve v sezóne") |
| `ceny_za_porciu[]` | cena per obchod, zoradené: spoľahlivé od najlacnejšej |
| `najlacnejsie` | súhrn pre kartu: `{obchod, cena_za_porciu, usetris_za_porciu}`; `null` ak nič nie je spoľahlivé |

### recepty[].suroviny[]

`{ nazov, mnozstvo, id, qty, jednotka, mnozstvo_g }`

- `id` → suroviny[] (môže byť `null` — napr. voda; vtedy len zobraz text).
- `qty` + `jednotka` = strojovo čitateľné množstvo; `mnozstvo_g` = to isté v g/ml
  (ks prepočítané cez `gramy_za_ks`). **Škálovanie porcií:** vynásob `qty`
  pomerom porcií. **Zlúčenie nákupu z viacerých receptov:** sčítaj `mnozstvo_g` per `id`.
- `qty` môže byť `null` (nekvantifikovateľné) — zobraz text `mnozstvo`.
- Kuchynské miery sú definované v builde: PL=15 g/ml, ČL=5, štipka=0,5,
  „podľa chuti"=2 g (nominálne), plátok=15 g, vetvička=2 g…

### recepty[].ceny_za_porciu[] (jeden záznam = jeden obchod)

`{ obchod, cena_za_porciu, usetris_za_porciu, napar_surovin, z_letaku, odhadom,
spolu_surovin, spolahlive, platnost_od, platnost_do, nakup[] }`

- `spolahlive` = aspoň polovica surovín ocenená **a** ocenené suroviny pokrývajú ≥ 80 % známej hmotnosti receptu (aby cena nechýbala práve hlavnej surovine) → len vtedy zobrazuj cenu ako hlavný údaj.
- `z_letaku` vs `odhadom`: koľko cien je z aktuálneho letáku vs. z bežnej ceny.
  V UI: „2,15 € / porcia (3 suroviny odhadom)".
- `platnost_od/do` = spoločné okno platnosti letákových cien receptu.

### nakup[] (nákupný zoznam receptu v danom obchode)

`{ id, surovina, kupit, zdroj_ceny, balenie, balenie_qty, balenie_jednotka,
cena_balenia, povodna_cena, akcia, podmienka, trvanlivost, cena_v_recepte,
usetris_v_recepte, mnozstvo_g }`

- `kupit` = presný produkt z letáku; pri `zdroj_ceny: "bezna"` je `null` →
  zaraď do skupiny **„bežná cena / asi máš doma"** (soľ, korenie…).
- Počet balení = `ceil(mnozstvo_g / balenie_qty)` (pri zlučovaní receptov sčítaj `mnozstvo_g` per `id` cez všetky recepty nákupu).
- **Zvyšok do špajze** = `balenie_qty − mnozstvo_g` (per `id`; expirácia zo `suroviny.spotreba_dni`).
- „Ušetríš" = `usetris_v_recepte` (rozdiel oproti `povodna_cena`, prepočítaný na použité množstvo).

## Zásady

1. Všetky ceny sú **odhady z verejných letákov** — pri zobrazení uvádzaj obchod a platnosť.
2. Cena s podmienkou sa nikdy nezobrazuje bez podmienky.
3. Alergény a nutričné hodnoty sú odhady, nie garancia.
4. Užívateľské dáta (špajza, watchlist, história nákupov, obľúbené) žijú v appke — databáza je read-only obsah; prepájaj ich cez `id` (suroviny) a `nazov_norm` (produkty).
