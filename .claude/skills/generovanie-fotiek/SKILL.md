---
name: generovanie-fotiek
description: Použi vždy, keď treba vygenerovať fotku jedla pre recept (foto_url) cez Gemini/nanobanana. Trigger frázy - "vygeneruj fotku", "dorob fotky k receptom", "foto pre recept", chýbajúci foto_url v recepte.
---

# Generovanie fotiek receptov (Gemini / nanobanana)

Fotky sa **negenerujú do repa** (`CLAUDE.md`) — vygeneruj ich mimo verzovania (napr. do scratchpadu), použi ich (napr. v artifacte alebo na upload), a do receptu zapíš len `foto_url` po nahratí niekam, kde je fotka dostupná.

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
2. Ulož fotku niekam, kde bude mať verejný/dostupný odkaz (zatiaľ nemáme vyriešené trvalé hosťovanie — rieš to podľa aktuálnej potreby, napr. priložením do artifactu alebo poslaním používateľovi).
3. Doplň `foto_url` v `.md` súbore receptu.
