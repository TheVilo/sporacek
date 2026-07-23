# Plán vývoja appky — záväzné poradie fáz

Dohodnuté 07/2026. Nová session: **prečítaj tento súbor skôr, než čokoľvek
navrhneš k appke** — rozhodnutia tu už padli, neotváraj ich nanovo bez
výslovnej požiadavky používateľa.

## Rozhodnutá architektúra (nemeniť bez dôvodu)

- **Android teraz**: Kotlin + Jetpack Compose, vlastné repo (`sporacek-android`).
- **iOS neskôr**: SwiftUI, vlastný projekt.
- **Zdieľa sa**: API kontrakt (`docs/data/SCHEMA.md`), dizajnové tokeny
  (`docs/app/tokens.json`), doménová logika cez **Kotlin Multiplatform**
  modul `shared` (Ktor + kotlinx.serialization + SQLDelight). **UI sa
  nezdieľa** (plynulosť = natívne UI na oboch platformách).
- **MVP beží úplne bez ostrého backendu**: obsah ťahá zo statického API v1
  (GitHub Pages, už beží), užívateľské dáta (špajza, watchlist, úspory,
  zoznamy) žijú **lokálne v telefóne** (SQLDelight), notifikácie „zlacnelo"
  rieši WorkManager denným pollingom API + lokálna notifikácia.
- **Repository pattern povinne** — obrazovky nevolajú HTTP; výmena
  statického API za ostrý backend = zmena base URL, nie kódu.
- Rozsah MVP podľa design handoffu: **1 deň, 1 osoba**, 24 obrazoviek.
- Detaily pre vývojára: `docs/app/README.md`; dátový kontrakt: `docs/data/SCHEMA.md`.

## Fázy

| fáza | čo | stav |
|---|---|---|
| 0 | Obsahový základ: databáza + API v1 + náhľady + tokeny + Compose téma | ✅ hotové, na `main` |
| 1 | Kostra `sporacek-android` repa: KMP `shared` + `androidApp`, téma z `docs/app/android/` | ⬜ ďalší krok |
| 2 | Vertikálny rez: zoznam receptov → detail → dark mode → offline cache — v plnej kvalite (scroll, animácie), overí architektúru | ⬜ |
| 3 | Hlavný tok MVP: Domov → Nastav → Loading → Plán → Zoznam → Nákup → Varenie → úspora | ⬜ |
| 4 | Huby: Sledujem, Špajza, Úspory + WorkManager notifikácie | ⬜ |
| 5 | Beta: Play Internal Testing (publikum zo social), meranie, ladenie | ⬜ |
| 6 | Ostrý backend — až keď treba účty/sync/push; dodrží API kontrakt, obsahová pipeline ostáva v tomto repe | ⬜ |
| 7 | iOS: SwiftUI + hotový `shared` modul + Swift téma z `tokens.json` | ⬜ |

## Otvorené rozhodnutia

- **Špajza a spoplatnenie**: design handoff ju má v MVP; skôr bola plánovaná
  ako platená fáza 2. Dohodnuté smerovanie: **postaviť v MVP**, o spoplatnení
  rozhodnúť pri launchi (feature flag). Ak sa to zmení, aktualizuj tu.

## Účty / registrácie / náklady (kedy čo treba)

- **Teraz (fázy 0–4): nič.** Hosting obsahu = GitHub Pages (beží), doména
  beží, Gemini API na fotky beží. Žiadny server, žiadne nové registrácie.
- **Pred fázou 5**: Google Play Developer účet — jednorazovo 25 USD,
  registrácia trvá pár dní (identita), vybaviť s predstihom.
- **Fáza 6**: výber hostingu backendu sa rieši až vtedy (žiadna registrácia
  vopred).
- **Pred fázou 7**: Apple Developer Program — 99 USD/rok.
