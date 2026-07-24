# Foto surovín — parkovaný prompt (zatiaľ NEAKTÍVNE)

Referencia pre budúcnosť. **Zatiaľ sa nič negeneruje** — spustí sa až keď sa rozhodne,
ako sa fotky surovín použijú v dizajne appky (napr. ikony v nákupnom zozname — sedí na heslo „Čo kúpiť").

Keď sa to raz rozbehne, treba doriešiť:
- **kam:** priečinok `fotky-suroviny/<slug>.jpg` (slug = surovina z `suroviny.md` bez diakritiky) + náhľady,
- **EN názov ku každej surovine** do promptu (napr. `bryndza → "a piece of Slovak bryndza sheep cheese"`),
- **build:** doplniť pole `foto` ku každej surovine v `docs/data/databaza.json` + zapísať do `docs/data/SCHEMA.md`,
- **rozsah:** buď len priced suroviny (~89), alebo celý číselník (150).

## Model a formát
- Model: **`gemini-3.1-flash-image`** (rovnako ako recepty).
- Aspect ratio: **1:1** (lepšie do gridu/ikon než 9:16).

## Finálny prompt (overený na 5 surovinách: maslo, paradajky, cibuľa, vajcia, syr)

Do `[...]` vlož presný anglický názov jednej suroviny (napr. `a block of fresh butter`,
`a few whole fresh red tomatoes`, `a single whole yellow onion`, `a handful of raw chicken breasts`):

```
A single, highly detailed fresh raw ingredient, presented directly on a seamless, pure white studio background. The specific ingredient, which is [PRESNÝ ANGLICKÝ NÁZOV SUROVINY], is the sole focus, viewed from a slightly elevated eye-level angle. The lighting is soft, even, diffuse, and shadowless, highlighting the natural colors, textures, and details without any complex reflections. No dishes, plates, bowls, containers, or additional props are visible. The entire frame is clean, minimalist, and perfectly isolated against the flawless white void. 1:1 aspect ratio. No text, no logo, no watermark in the image.
```

**Kľúčové:** žiaden tanier/miska/obrus/props — len samotná surovina na čistom bielom pozadí.
