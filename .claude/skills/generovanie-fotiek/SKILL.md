---
name: generovanie-fotiek
description: Použi vždy, keď treba vygenerovať fotku jedla pre recept (foto_url) cez Gemini/nanobanana. Trigger frázy - "vygeneruj fotku", "dorob fotky k receptom", "foto pre recept", chýbajúci foto_url v recepte.
---

# Generovanie fotiek receptov (Gemini / nanobanana)

Fotky **sú súčasťou repa** (priečinok `fotky/`, viď `CLAUDE.md`) — generuj ich do dočasného súboru, over si ich, potom ulož do `fotky/<id>.jpg`, commitni a pushni. Cez GitHub/git pull sa dostanú aj do lokálnej zložky `sporacek`.

## Kritická, nemeniteľná podmienka: štýl kuchárskeho blogu/Instagramu — chutné, vkusné, ale nie sterilná reklama

Fotky **musia vyzerať ako fotka z obľúbeného kuchárskeho blogu alebo food Instagramu** — presne taký štýl ako majú weby typu Running to the Kitchen, BBC Good Food, Delish. **Nie** amatérsky narýchlo odfotený telefónny snímok, **ale ani** sterilná komerčná reklamná studio scéna.

Povolené a žiadané: prirodzené jasné denné svetlo (často s teplými slnečnými odleskami), jedlo pekne a chutne naaranžované s jemným garnišom (čerstvé bylinky, sezam, nastrúhaný syr...), fotené zhora alebo z uhla 3/4, vkusné reálne rekvizity v primeranej miere (plátený/textilný obrúsok, drevená doska, paličky, malá miska s prísadou, pohár nápoja), mierny prirodzený bokeh na pozadí je v poriadku. Pozadie: pekný drevený stôl, svetlá kamenná/mramorová doska alebo plech na pečenie — nie sterilné biele štúdio.

Nikdy ale: prehnane geometrické/umelé aranžovanie, prehnane veľa rekvizít naraz (max 2-3), text alebo logo v obrázku.

Presná šablóna promptu je v `.claude/skills/tyzdenny-vystup/SKILL.md` — použi ju vždy, aj mimo týždenného letáku.

Presná šablóna promptu je v `.claude/skills/tyzdenny-vystup/SKILL.md` — použi ju vždy, aj mimo týždenného letáku.

## Kritické: fotka musí zodpovedať receptu — najprv si ho celý prečítaj

Pred písaním/použitím `foto_prompt` si **vždy prečítaj celý `.md` súbor receptu** (suroviny aj postup), nie len jeho existujúci `foto_prompt`. Model si často domyslí prílohy, ktoré recept vôbec neobsahuje (napr. zemiaková kaša, fazuľky) — na fotke smie byť **len to, čo je v recepte** (suroviny + spôsob podávania z postupu, napr. "podávaj s chlebom alebo ryžou"). Ak `foto_prompt` v recepte spomína niečo, čo tam nepatrí, over to a oprav.

## Čo je treba

- **`GEMINI_API_KEY`** v premennej prostredia. Ak nie je nastavená, popros o ňu používateľa (Google AI Studio → API key). Zatiaľ sa nedá trvalo uložiť ako env premenná tohto prostredia, takže ju na začiatku session treba dostať znova.
- Balík **`google-genai`** (`pip install google-genai`).

## Dôležité: NEPOUŽÍVAJ priame curl/REST volania

Kľúč použitý v tomto projekte je **naviazaný na service account** (Google Cloud "account-bound API key"). Priame REST volania (`curl` s `?key=...` alebo hlavičkou `x-goog-api-key`) na `generativelanguage.googleapis.com` **konzistentne zlyhávajú** s chybou:

```
403 PERMISSION_DENIED — "Method doesn't allow unregistered callers (callers without established identity)"
```

Toto nie je problém proxy ani neplatný kľúč — je to limitácia tohto typu kľúča pri holom REST volaní. **Funguje len oficiálne `google-genai` SDK**, ktoré autorizáciu rieši inak (interne). Vždy generuj fotky cez SDK, nikdy cez curl.

Ak SDK aj tak vráti podobnú 403 chybu, over v Google Cloud Console (`APIs & Services → Enabled APIs`, projekt **sporacek**), či je zapnuté **Generative Language API** — bez toho zlyháva všetko, aj SDK.

## Ako vygenerovať fotku

Použi hotový skript `scripts/generate_photo.py`:

```bash
export GEMINI_API_KEY="..."
python3 scripts/generate_photo.py "<foto_prompt z receptu>" /tmp/vystup.png --aspect 9:16
```

Alebo priamo v Pythone (napr. na vygenerovanie viacerých fotiek naraz):

```python
import os
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
resp = client.models.generate_content(
    model="gemini-2.5-flash-image",   # lacný "nanobanana", pár centov/fotka
    contents=foto_prompt,
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(aspect_ratio="9:16"),
    ),
)
for part in resp.candidates[0].content.parts:
    if part.inline_data:
        with open(output_path, "wb") as f:
            f.write(part.inline_data.data)
```

## Model a cena

- **`gemini-2.5-flash-image`** ("Nano Banana") — predvolený, štandardné rozlíšenie. Rádovo pár centov za fotku. Použi tento pre bežné recepty.
- **`gemini-3-pro-image`** ("Nano Banana Pro") — výrazne drahší, najmä pri 2K/4K rozlíšení. Použi len ak si o to používateľ vyslovene povie (kvalitnejšia/väčšia fotka).

## Foto prompt

Šablóna promptu (fotorealistická, teplé domáce svetlo, 9:16, bez textu/loga) je v `.claude/skills/tyzdenny-vystup/SKILL.md`. Každý recept má vlastný `foto_prompt` — použi presne ten text, prípadne doplň "Format 9:16, no text or logos." ak chýba.

## Po vygenerovaní

1. Over si obrázok (prezri si ho) — food fotka musí vyzerať domácky/reálne, nie ako reklama.
2. Ulož fotku do `fotky/<id>.jpg` v repe (formát JPG, konvertuj ak treba). Fotky **sú súčasťou repa** — commitni a pushni ich, nech sa cez GitHub/git pull dostanú aj do lokálnej zložky `sporacek` na počítači.
3. Doplň `foto_url` v `.md` súbore receptu ako relatívnu cestu, napr. `foto_url: fotky/<id>.jpg`.
