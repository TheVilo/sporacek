# Handoff: Sporáček — MVP aplikácia (24 obrazoviek)

## Overview
Sporáček je mobilná appka, ktorá premieňa aktuálne akcie v obchodoch na hotový nápad, čo navariť. Používateľ povie, na čo má chuť → AI zostaví jedálniček a nákupný zoznam z akciových surovín → zoznam pošle rodine nakúpiť → keď je nakúpené, vráti sa a varí krok za krokom. Úsporu si overí odfotením účtenky. Uložené recepty, sledované suroviny, špajza a história nákupov majú spoločný domov v spodnom menu.

Tento balík obsahuje **kompletný interaktívny prototyp všetkých 24 schválených obrazoviek MVP** + odvodený UI Kit (dizajnové tokeny) na presnú implementáciu.

## About the Design Files
Súbory v tomto balíku sú **dizajnové referencie vytvorené v HTML** — prototypy, ktoré ukazujú zamýšľaný vzhľad a správanie, **nie produkčný kód na priame skopírovanie**.

Úloha je **znovu vytvoriť tieto HTML návrhy v cieľovom prostredí** (React / React Native / Vue / SwiftUI / Flutter…) podľa jeho zavedených vzorov a knižníc. Ak projekt zatiaľ nemá prostredie, zvoľ najvhodnejší framework (pre mobilnú appku odporúčam **React Native / Expo** alebo natívne) a implementuj návrhy tam.

> **Formát súborov:** návrhy sú `.dc.html` (Design Component) súbory. Otvoria sa v prehliadači aj samostatne. Každá obrazovka je vlastný súbor; `ALL SCREENS MVP.dc.html` ich skladá do jednej mapy a `Sporacek MVP.dc.html` do preklikateľného toku. HTML/CSS v nich je zdroj pravdy pre presné hodnoty (farby, rozmery, texty).

## Fidelity
**High-fidelity (hifi).** Návrhy sú pixel-perfect s finálnymi farbami, typografiou, spacingom a textami. Vývojár má UI zreprodukovať verne pomocou existujúcich knižníc a vzorov v kódovej báze. Všetky presné hodnoty sú v `UI Kit.dc.html` a v CSS jednotlivých obrazoviek.

## Screenshots (PNG) — pozri sem najprv
Priečinok **`screenshots/`** obsahuje PNG renders každej obrazovky v tvare telefónu (664 × 1436 px, @2x) — presne to, od čoho sa má implementácia odraziť. Ak nevieš vykresliť `.dc.html`, riaď sa týmito obrázkami + hodnotami nižšie.

| PNG | Obrazovka | HTML zdroj |
|---|---|---|
| `00-ui-kit.png` | UI Kit / tokeny | `UI Kit.dc.html` |
| `01-home.png` | Domov | `AppHomeScreen.dc.html` |
| `02-preferences.png` | Nastav varenie | `AppPreferencesScreen.dc.html` |
| `03-loading.png` | AI generuje plán | `AppLoadingScreen.dc.html` |
| `04-plan.png` | Jedálniček | `AppPlanScreen.dc.html` |
| `05-recipes.png` | Prehľad receptov | `AppRecipesScreen.dc.html` |
| `06-recipe-detail.png` | Recept · detail | `AppRecipeScreen.dc.html` |
| `07-list.png` | Nákupný zoznam | `AppListScreen.dc.html` |
| `08-shop.png` | Môj nákup | `AppShopScreen.dc.html` |
| `09-cooking.png` | Varenie | `AppCookingScreen.dc.html` |
| `10-welcome.png` | Vitaj | `AppWelcomeScreen.dc.html` |
| `11-auth.png` | Prihlásenie | `AppAuthScreen.dc.html` |
| `12-location.png` | Poloha | `AppLocationScreen.dc.html` |
| `13-tracking.png` | Sledujem — hub | `AppTrackingScreen.dc.html` |
| `14-saved.png` | Uložené recepty | `AppSavedScreen.dc.html` |
| `15-watchlist.png` | Sledované suroviny | `AppWatchlistScreen.dc.html` |
| `16-shopping-history.png` | História nákupov | `AppShoppingHistoryScreen.dc.html` |
| `17-receipt.png` | Účtenka | `AppReceiptScreen.dc.html` |
| `18-done.png` | Overená úspora | `AppDoneScreen.dc.html` |
| `19-savings.png` | Úspory | `AppSavingsScreen.dc.html` |
| `20-profile.png` | Profil | `AppProfileScreen.dc.html` |
| `21-allergens.png` | Alergény | `AppAllergensScreen.dc.html` |
| `22-store.png` | Obchod | `AppStoreScreen.dc.html` |
| `23-error.png` | Chyba | `AppErrorScreen.dc.html` |
| `24-empty-list.png` | Prázdny zoznam | `AppEmptyListScreen.dc.html` |

## Design Tokens

### Farby
| Token | Hex | Použitie |
|---|---|---|
| `--c-forest` | `#204432` | Primárna značka, text, tmavé karty |
| `--c-forest-deep` | `#163021` | Rám telefónu, hĺbka |
| `--c-forest-ink` | `#0E1F16` | Text na sage pozadí |
| `--c-terracotta` | `#BA5F3F` | Akcent, CTA tlačidlá, úspory |
| `--c-terracotta-dark` | `#8A4429` | Hover na akcent |
| `--c-sage` | `#7FA38C` | Sekundárny akcent, "nakúpené" tagy |
| `--c-wheat` | `#E7D6B4` | Zvýraznené karty, badge cien |
| `--c-cream` | `#FAF6EE` | Pozadie appky |
| `--c-sand` | `#F4EFE3` | Vnorené karty, riadky |
| `--c-linen` | `#E8E3D8` | Pozadie stránky / plátna |
| `--c-white` | `#FFFFFF` | Karty na creame |
| `--c-text` | `#204432` | Nadpisy |
| `--c-text-2` | `#4B6357` | Odseky, popisy |
| `--c-text-muted` | `#7A8A80` | Meta údaje, popisky |
| `--c-text-faint` | `#9AA8A0` | Neaktívne položky v navigácii |
| `--c-border` | `rgba(32,68,50,0.08)` | Jemný obrys kariet |

### Typografia
Dva rezy: **Plus Jakarta Sans** (400/500/600/700/800) pre UI, **Source Serif 4** (500/600) pre citáty/positioning. H1 a H2 responzívne cez `clamp()`.

| Rola | Veľkosť | Weight | Letter-spacing | Line-height |
|---|---|---|---|---|
| Display / H1 | `clamp(30px, 5vw, 44px)` | 800 | -0.03em | 1.03 |
| H2 · sekcia | `clamp(20px, 3vw, 26px)` | 800 | -0.02em | 1.1 |
| H3 · titul karty | 22px | 800 | -0.02em | 1.15 |
| Title | 20px | 800 | -0.02em | 1.15 |
| Subtitle | 17px | 700 | -0.01em | 1.3 |
| Body large | 16px | 600 | 0 | 1.5 |
| Body | 14px | 500 | 0 | 1.55 |
| Caption | 12px | 600 | 0 | 1.4 |
| Micro | 11px | 700 | 0 | 1.3 |

### Spacing
Základ 2px. Bežná mierka: 4, 6, 8, 10, 12, 14, 16, 18, 20, 24, 32, 48 px. Padding kariet 14–22px, gap medzi kartami 12–14px, sekcie 48–64px.

### Border radius
`sm 10px` · `md 14px` · `lg 18px` · `xl 20px` · `2xl 24px` · `pill 999px` · `phone (rám) 38px vnútro / 48px vonok`.

### Tiene
- Border: `1px solid rgba(32,68,50,0.08)`
- Karta (elevated): `0 20px 40px rgba(32,68,50,0.26)`
- Float (telefón/modal): `0 30px 60px rgba(22,48,33,0.25)`

Kompletná živá referencia + copy-paste `:root {}` blok: **`UI Kit.dc.html`**.

### Ikony
**Material Symbols Outlined** (Google Fonts). Použité váhy: `FILL 0/1, wght 400/500, GRAD 0, opsz 24`. Aktívny tab v nave = FILL 1. Kľúčové ikony: `home, skillet, kitchen, notifications_active, savings, shopping_cart, play_arrow, receipt_long, check, chevron_right, search, restaurant`.

## Screens / Views
Rozmer návrhového rámu obrazovky: **332 × 718 px** (obsah), preview viewport 390 × 844 (iPhone). Každá obrazovka = samostatný súbor.

### A · Hlavný tok
| # | Súbor | Názov | Účel |
|---|---|---|---|
| 01 | `AppHomeScreen.dc.html` | Domov | Vstupný bod — chuť + spustenie sporáčika, prehľad úspor a tipov |
| 02 | `AppPreferencesScreen.dc.html` | Nastav varenie | Používateľ povie na čo má chuť (MVP: 1 deň, 1 osoba) |
| 03 | `AppLoadingScreen.dc.html` | AI generuje plán | Zostavuje recepty z akcií, overuje sklad (tmavé pozadie #204432) |
| 04 | `AppPlanScreen.dc.html` | Jedálniček na dnes | Vygenerované jedlá, recept sa dá zameniť |
| 05 | `AppRecipesScreen.dc.html` | Prehľad receptov | Výber receptu a pridanie na deň |
| 06 | `AppRecipeScreen.dc.html` | Recept · detail | Suroviny, postup, cena za porciu |
| 07 | `AppListScreen.dc.html` | Nákupný zoznam | Upraviteľný, zdieľa sa s rodinou, uloží nákup. Deteguje suroviny v špajze → "máš v špajzi" namiesto ceny |
| 08 | `AppShopScreen.dc.html` | Môj nákup (uložený) | Uložený nákup s receptami — výber čo dnes uvariť |
| 09 | `AppCookingScreen.dc.html` | Varenie | Krok za krokom podľa receptu (jeden krok naraz). Po dovarení pridá zvyšné suroviny do Špajzy |

### B · Overenie úspory
| # | Súbor | Názov | Účel |
|---|---|---|---|
| 10 | `AppReceiptScreen.dc.html` | Účtenka | Odfotenie/nahranie účtenky na overenie |
| 11 | `AppDoneScreen.dc.html` | Overená úspora | Výsledok — koľko sa reálne ušetrilo |

### C · Sledujem (hub v spodnom menu)
| # | Súbor | Názov | Účel |
|---|---|---|---|
| 12 | `AppPantryScreen.dc.html` | Špajza | Čo mám doma; napĺňa sa po varení; znižuje košík |
| 13 | `AppTrackingScreen.dc.html` | Sledujem — hub | Rozcestník: watchlist, uložené, história |
| 14 | `AppWatchlistScreen.dc.html` | Sledované suroviny | Suroviny, ktoré chce sledovať v akciách |
| 15 | `AppSavedScreen.dc.html` | Uložené recepty | Obľúbené / uložené recepty |
| 16 | `AppShoppingHistoryScreen.dc.html` | História nákupov | Staré nákupy a zoznamy |
| 17 | `AppSavingsScreen.dc.html` | Úspory | Prehľad úspor. Zobrazuje "Špajza · žiadne plytvanie" |

### D · Nastavenia
| # | Súbor | Názov | Účel |
|---|---|---|---|
| 18 | `AppProfileScreen.dc.html` | Profil | Používateľské nastavenia |
| 19 | `AppAllergensScreen.dc.html` | Alergény | Nastavenie alergénov / obmedzení |
| 20 | `AppStoreScreen.dc.html` | Obchod | Výber preferovaného obchodu / lokality |

### E · Onboarding & stavy
| # | Súbor | Názov | Účel |
|---|---|---|---|
| 21 | `AppWelcomeScreen.dc.html` | Vitaj | Prvé spustenie |
| 22 | `AppAuthScreen.dc.html` | Prihlásenie | Registrácia / prihlásenie |
| 23 | `AppLocationScreen.dc.html` | Poloha | Povolenie polohy pre akcie v okolí |
| 24 | `AppEmptyListScreen.dc.html` | Prázdny zoznam | Empty state nákupného zoznamu |
| — | `AppErrorScreen.dc.html` | Chyba | Error state (mimo 24, demo) |

> Presné rozloženie, texty a hodnoty každej obrazovky si prečítaj priamo v jej `.dc.html` súbore — inline `style` atribúty obsahujú finálne hodnoty.

## Interactions & Behavior
- **Navigácia:** 5-tab spodné menu (Domov / Recepty / Špajza / Sledujem / Úspory), aktívny tab má ikonu FILL 1 + farbu `#204432`, neaktívne `#9AA8A0`.
- **Hlavný tok:** Domov → Nastav → Loading → Plán → (Recepty/Detail) → Zoznam → *(nákup)* → Môj nákup → Varenie → Účtenka → Overená úspora.
- **Varenie** je jednokrokové (jeden krok naraz), nie celý postup naraz — pozri `AppCookingScreen`.
- **List → Shop:** zoznam ide priamo do "Môj nákup", žiadna medziobrazovka potvrdenia.
- **Loading obrazovka** je dočasný stav s tmavým pozadím, prechod na Plán po dokončení generovania.
- **Toast:** po dovarení receptu sa zobrazí potvrdenie o pridaní zvyškov do Špajzy.

## State Management
Kľúčové entity a stavy pre implementáciu:
- **Preferencie varenia** — chuť, počet dní (MVP: 1), počet osôb (MVP: 1).
- **Vygenerovaný plán** — zoznam receptov na deň; recept je zameniteľný.
- **Nákupný zoznam** — položky s cenou a obchodom; položka môže byť príznak "v špajzi" (nepočíta sa do košíka).
- **Špajza (pantry)** — suroviny, ktoré používateľ má doma. Napĺňa sa automaticky po dovarení (zvyšné suroviny) a **odpočítava sa** z nasledujúceho košíka.
- **Úspory** — kumulatívna suma + tento týždeň; overená účtenkou.
- **Watchlist** — sledované suroviny; notifikácia keď zlacnejú.
- **Uložené recepty**, **história nákupov**.
- **Používateľ** — profil, alergény, preferovaný obchod, poloha.

Pantry logika (dôležité, prepojené end-to-end):
1. Varenie receptu → zvyšné suroviny sa pridajú do Špajzy (toast).
2. Nákupný zoznam deteguje suroviny vlastnené v Špajze → zobrazí "máš v špajzi" namiesto ceny a odpočíta ich z celkového košíka.
3. Úspory zobrazujú "Špajza · žiadne plytvanie".

## Responsive behavior
Obrazovky sú navrhnuté pre mobilný viewport (390 × 844, obsah 332 × 718). Pri implementácii do responzívneho prostredia použi tekutý layout (flex/grid, gap), fixné šírky z návrhu ber ako pomer, nie absolútno. UI Kit má H1/H2 už definované cez `clamp()`.

## Assets
- **Logo:** `SporacekLogo.dc.html` (horizontálne), `SporacekLogoV.dc.html` (vertikálne), `SporacekMark.dc.html` (značka/symbol). Sú to inline SVG, farbia sa cez `currentColor`. Priečinok `logo-pack/` v hlavnom projekte obsahuje exportované varianty.
- **Fotky jedál:** priečinok `fotky/` — reálne fotky receptov použité na kartách (napr. `bryndzove-halusky-slanina.jpg`, `hovedzi-gulas-zemiaky-mrkva.jpg`, `cestoviny-kuracie-spenat-smotana.jpg`, `grilovane-kuracie-stehna-kalerabovy-salat.jpg`). V produkcii nahradiť skutočnými fotkami receptov z CMS.
- **Ikony:** Material Symbols Outlined (Google Fonts CDN) — netreba lokálne assety.
- **Fonty:** Plus Jakarta Sans + Source Serif 4 (Google Fonts).

## Files
- `UI Kit.dc.html` — **dizajnové tokeny** (farby, typografia, spacing, radius, tiene, komponenty, copy-paste `:root`). Začni tu.
- `ALL SCREENS MVP.dc.html` — mapa všetkých 24 obrazoviek podľa typu (najlepší prehľad).
- `Sporacek MVP.dc.html` — preklikateľný interaktívny tok.
- `App*.dc.html` — jednotlivé obrazovky (zdroj pravdy pre hodnoty).
- `SporacekLogo/LogoV/Mark.dc.html` — logo assety.
- `fotky/` — obrázky jedál.
- `support.js`, `image-slot.js`, `__navslot.dc.html` — runtime prototypu (netreba portovať; slúžia len na spustenie HTML prototypov v prehliadači).

### Ako si prototyp spustiť
Otvor `ALL SCREENS MVP.dc.html` alebo `Sporacek MVP.dc.html` v prehliadači (cez lokálny server, napr. `npx serve` v tomto priečinku — kvôli fetchu susedných `.dc.html`). `support.js` je runtime, ktorý HTML komponenty vykreslí; do produkčného kódu ho neportuj.
