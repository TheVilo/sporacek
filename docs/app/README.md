# šporáček — podklady pre vývoj appky

Všetko, čo appka (Android teraz, iOS neskôr) potrebuje z tohto repa. Appky sa
stavajú v **samostatných repozitároch** — tu žije len obsah (dáta cez API),
dizajnové tokeny a ich referenčné platformové podoby.

## Čo je kde

| súbor | účel |
|---|---|
| `tokens.json` | **platformovo neutrálny zdroj dizajnových tokenov** (farby svetlá+tmavá, typografia, spacing, rádiusy) — z neho vychádzajú všetky platformové témy |
| `tokens.css` + `components.css` | webová podoba tokenov a komponentov (používa ich style guide, časom aj stránky repa) |
| `styleguide.html` | živá referencia — [recepty.sporacek.sk/app/styleguide.html](https://recepty.sporacek.sk/app/styleguide.html), prepínač svetlá/tmavá, kontrasty počítané naživo |
| `android/Color.kt` `Type.kt` `Theme.kt` | hotová Compose Material3 téma na skopírovanie do Android projektu |

Dátový kontrakt (API v1, endpointy, pravidlá): **`docs/data/SCHEMA.md`**.

## Architektúra appiek (dohodnuté smerovanie)

- **Android teraz:** Kotlin + Jetpack Compose. **iOS neskôr:** SwiftUI, vlastný projekt.
- **Zdieľa sa:** (1) API kontrakt, (2) dizajnové tokeny (`tokens.json`),
  (3) doménová logika cez **Kotlin Multiplatform** modul (Ktor +
  kotlinx.serialization + SQLDelight na offline cache) — dátová vrstva sa
  píše raz, iOS si ju pribalí ako framework.
- **Nezdieľa sa UI** — Compose a SwiftUI zvlášť. Zámerne: plynulosť
  (scroll, mikroanimácie, natívny pocit) sa nedá dosiahnuť zdieľaným UI.
- **Repository pattern povinne:** obrazovky nikdy nevolajú HTTP priamo;
  `RecipeRepository` má dnes implementáciu nad statickým API (GitHub Pages),
  zajtra nad ostrým backendom — UI sa nezmení.

## Zásady pre plynulosť (Android)

- Zoznamy: `LazyColumn` s `key = { it.slug }`, dátové triedy `@Immutable`,
  zoznamy ako `ImmutableList` — inak Compose prerenderúva a scroll sa seká.
- Obrázky: **Coil**, v zoznamoch vždy `foto_nahlad_url` (320 px, ~25 KB),
  plné `foto_url` až na detaile; placeholder farba `surface2`.
- Animácie: `animate*AsState` / `AnimatedVisibility` / shared element
  transitions; rešpektuj systémové "remove animations" (ako web rešpektuje
  `prefers-reduced-motion`).
- Offline: SQLDelight cache posledných dát — nákupný zoznam musí fungovať
  v obchode bez signálu.
