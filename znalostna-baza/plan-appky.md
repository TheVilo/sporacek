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
- **Špajza = vyťahovanie, nie hromadenie** (dohodnuté 07/2026, detail v
  `architektura.md` sekcia „Appka: API v1..."): Špajza obrazovka má aktívne
  radiť recepty podľa pokrytia surovinami zo špajze + `spotreba_dni`, nie
  byť pasívny zoznam. K tomu dve doplnkové funkcie: zásobný nákup (nudge v
  nákupnom zozname pri lacných trvanlivých surovinách z obľúbených
  receptov) a AI odfotenie špajze na automatické pridanie položiek (platený
  tier, vision model). Zaraď do Fázy 4 (huby) pri návrhu Špajza obrazovky.

## Účty / registrácie / náklady (kedy čo treba)

- **Teraz (fázy 0–4): nič, ani Play Developer účet.** Hosting obsahu =
  GitHub Pages (beží), doména beží, Gemini API na fotky beží. Testovanie
  appky je zadarmo bez akejkoľvek registrácie: vlastný telefón cez USB
  (Android Studio → Run), emulátor, alebo zdieľanie buildu s pár ľuďmi cez
  **Firebase App Distribution** (zadarmo, obdoba TestFlightu — žiadny Play
  poplatok, žiadny limit testerov). Play účet sa **nedá** obísť len pre
  interný testing (Google vyžaduje $25 registráciu pre akýkoľvek prístup
  do Play Console, aj internal track) — preto sa mu vyhýbame, kým netreba.
- **Pred fázou 5** (Play Internal/Closed Testing): Google Play Developer
  účet — jednorazovo 25 USD, registrácia trvá pár dní (identita), vybaviť
  s predstihom. Počítaj aj s tým, že Google od nových účtov vyžaduje
  **closed testing s min. 12 testermi počas 14 dní** pred pustením appky
  do produkcie — dôvod navyše otestovať poriadne cez Firebase zadarmo
  najprv a Play účet založiť až tesne pred touto fázou.
- **Fáza 6**: výber hostingu backendu sa rieši až vtedy (žiadna registrácia
  vopred).
- **Pred fázou 7**: Apple Developer Program — 99 USD/rok.

### E-maily na doméne (dohodnuté)

Developer účty sa registrujú na doménové adresy (nie súkromný Gmail),
v kuchárskom duchu značky, **vždy bez diakritiky** (`kuchar`, nie „kuchár"
— pozor, telefón diakritiku rád doplní sám):

- `kuchar@sporacek.sk` — login/vlastník developer účtov (Google Play, Apple).
  Google účet sa dá vytvoriť s nedomácou adresou („použiť existujúcu").
- `kotlik@sporacek.sk` — verejný support e-mail v Store listingu
  (povinný, bude dostávať spam — zámerne iná než login adresa).
- Navyše aliasy `podpora@` a `info@` presmerované do tej istej schránky ako
  `kotlik@` — bežné adresy si ľudia domyslia, kuchárske nie; alias nič nestojí.
- Doména musí poštu reálne prijímať (stačí forwarding — Cloudflare Email
  Routing / registrátor), inak hrozí zmeškanie overovacích/policy mailov
  a suspendácia účtu. Na účte `kuchar@` povinne 2FA + záložný telefón/e-mail.
