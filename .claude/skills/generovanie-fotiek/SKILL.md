---
name: generovanie-fotiek
description: Použi vždy, keď treba vygenerovať fotku jedla pre recept (foto_url) cez Gemini/nanobanana. Trigger frázy - "vygeneruj fotku", "dorob fotky k receptom", "foto pre recept", chýbajúci foto_url v recepte.
---

# Generovanie fotiek receptov (Gemini / nanobanana)

Fotky **sú súčasťou repa** (priečinok `fotky/`, viď `CLAUDE.md`) — generuj ich do dočasného súboru, over si ich, potom ulož do `fotky/<id>.jpg`, commitni a pushni. Cez GitHub/git pull sa dostanú aj do lokálnej zložky `sporacek`.

## Kritická, nemeniteľná podmienka: štýl "Modern Editorial & Elevated Lifestyle" — food blog/Instagram, nie sterilná reklama

Fotky **musia vyzerať ako fotka z obľúbeného kuchárskeho blogu alebo food Instagramu** — presne taký štýl ako majú weby typu Running to the Kitchen, BBC Good Food, Delish. **Nie** amatérsky narýchlo odfotený telefónny snímok, **ale ani** sterilná komerčná reklamná studio scéna.

Povolené a žiadané: prirodzené jasné denné svetlo (často s teplými slnečnými odleskami), jedlo pekne a chutne naaranžované s jemným garnišom (čerstvé bylinky, sezam, nastrúhaný syr...), fotené zhora alebo z uhla 3/4, vkusné reálne rekvizity v primeranej miere (plátený/textilný obrúsok, drevená doska, paličky, malá miska s prísadou, pohár nápoja), mierny prirodzený bokeh na pozadí je v poriadku. Pozadie: pekný drevený stôl, svetlá kamenná/mramorová doska alebo plech na pečenie — nie sterilné biele štúdio.

Nikdy ale: prehnane geometrické/umelé aranžovanie, prehnane veľa rekvizít naraz (max 2-3), text alebo logo v obrázku, **para/dym stúpajúci z jedla** (pri horúcich jedlách — polievky, vývary, čaje — pôsobí v AI-generovaných fotkách vždy nápadne umelo/falošne, radšej vynechaj), **tmavé pozadie/props (čierna bridlica a pod.) ani ostré dramatické bočné svetlo** (side-light, backlit okenná scéna) — v praxi to vyjde príliš tmavo/umelo/"studio" namiesto svetlého a vzdušného. Vždy radšej explicitne napíš "soft, evenly diffused bright daylight, no harsh directional shadows". **Prehnane sýte, „neónové" farby** (typicky pri jedlách s paprikovou/paradajkovou omáčkou — guláše, paprikáše, lečo — vychádzajú kričiaco oranžovo-červené, čo pôsobí umelo). Vždy pridaj `natural, realistic home-cooked food colours, not oversaturated or neon` a pri paprikových/paradajkových omáčkach opíš farbu ako `muted brownish paprika-red`, nie „rich/vibrant red".

**Presná šablóna (2-krokový proces — analýza receptu + 10 kompozičných variantov) je nižšie v tejto sekcii, v `## Foto prompt — 2-krokový proces`.** Použi ju vždy, aj mimo týždenného letáku. (`tyzdenny-vystup/SKILL.md` na ňu len odkazuje, nedrží vlastnú kópiu — nech nevznikajú dve verzie, ktoré sa časom rozídu.)

## Kritické: fotka musí zodpovedať receptu — najprv si ho celý prečítaj

Pred písaním/použitím `foto_prompt` si **vždy prečítaj celý `.md` súbor receptu** (suroviny aj postup), nie len jeho existujúci `foto_prompt`. Model si často domyslí prílohy, ktoré recept vôbec neobsahuje (napr. zemiaková kaša, fazuľky, orechy, práškový cukor, zmrzlina) — na fotke smie byť **len to, čo je v recepte** (suroviny + spôsob podávania z postupu, napr. "podávaj s chlebom alebo ryžou"). Ak `foto_prompt` v recepte spomína niečo, čo tam nepatrí, over to a oprav. Toto sa v praxi stáva často aj pri dobre napísanom prompte — po vygenerovaní si obrázok vždy pozorne pozri (viď "Po vygenerovaní" nižšie) a pri najmenšej pochybnosti prompt sprav presnejší a generuj znova.

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

Chyba **`429 RESOURCE_EXHAUSTED — monthly spending cap`** znamená vyčerpaný mesačný limit útraty projektu — nie je to chyba kódu ani kľúča. Vyriešiť ju vie len používateľ na https://ai.studio/spend (zvýšiť cap alebo počkať na nový mesiac). Recepty vtedy commitni bez fotky — `build_databaza.py` chýbajúce fotky nahlási v reporte, takže sa na ne nezabudne.

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

## Foto prompt — 2-krokový proces

### Krok 1: z receptu vytvor presný anglický opis jedla

Priprav si opis jedla — analyzuj recept podľa týchto pravidiel (rovnaké pravidlá platia, či fotíš finálne servírované jedlo, alebo krok postupu, viď nižšie):

1. Ignoruj pôvodný názov receptu, ak je vizuálne neúplný.
2. Analyzuj zoznam ingrediencií a gramáže: všetko, čo má významný objem (mäso, prílohy, veľká zelenina, cesto), MUSÍ byť v opise.
3. Skontroluj krok "Servírovanie" (posledné vety postupu): ak sa jedlo niečím polieva, posýpa (bylinky, syr) alebo ukladá na niečo špecifické, zahrň to.
4. Filtruj neviditeľné veci: úplne ignoruj suroviny, ktoré vo finále nevidno (rozpustený olej, soľ v marináde, cukor v ceste, prelisovaný cesnak).
5. **Opíš jedlo tak, ako reálne vyzerá po danej technike z postupu — nielen podľa surovín.** Prečítaj kroky prípravy a zohľadni ich vo vizuáli (nakrájané na kocky, pečené do zlatista, rozmixované na krém, opečené vcelku vs. po kúskoch…). Časté chyby, na ktoré si dávaj pozor:
   - **Mäso opečené vcelku a až potom nakrájané** (steak, karé, roláda, pečienka) → plátky majú **svetlý šťavnatý stred a len tenký opečený okraj**, NIE každý kúsok opečený dookola. (Opak: kocky mäsa opekané zvlášť sú opečené zo všetkých strán.)
   - Mäso „prepečené/medium" → opíš farbu rezu (ružový stred pri hovädzom medium-rare, biely pri prepečenom kuracom).
   - Cesto/pečivo „prekrojené" → ukáž vrstvy/striedku.
   Vždy nech fotka sedí s tým, čo v poslednom kroku reálne leží na tanieri, vrátane spôsobu úpravy.
6. **Kritické, navyše oproti pôvodnému zadaniu:** ak niektorý z 10 promptov nižšie žiada `[INÁ INGREDIENCIA]` (napr. "malá miska s...", "dipping bowl of..."), táto vec **musí byť reálna surovina z receptu** (dresing, omáčka, príloha, posyp) — nikdy nič vymyslené navyše. Ak recept nemá vhodnú "druhú" ingredienciu na vedľajšiu misku, vynechaj tú časť promptu radšej, než si niečo domýšľať.

7. **Realistická a chutná porcia (na počte porcií nezáleží).** Nezáleží, koľko porcií je na fotke — appka si množstvá prepočíta, niekedy sa jednoducho uvarí viac. Dôležité je, aby jedlo vyzeralo **reálne, chutne a pekne**, a aby hlavná zložka a príloha boli v **prirodzenom pomere** (nie kopa mäsa s trochou ryže — to pôsobí neprirodzene). Radšej pekná apetítna porcia než snaha o „presne jednu porciu".

8. **Mäkké/drobivé suroviny nezobrazuj ako dokonalý geometrický tvar.** Feta, tvaroh, bryndza, mozzarella nikdy nie sú hladký kváder/valec s ostrými hranami — v realite sú drobivé alebo natrhané, s nerovnými okrajmi (feta nalámaná na kusy alebo rozdrobená, mozzarella natrhaná). Vždy to tak opíš (napr. „a rustic, crumbly slab of feta with uneven broken edges").

9. **Slovenské halušky/strapačky = drobné Spätzle, NIE gnocchi.** Gemini z „potato dumplings" robí gnocchi, aj keď pridáš „not gnocchi". Overené riešenie: **vôbec nepoužívaj slová „dumpling" ani „gnocchi" v kladnom zmysle** a oprie to o Spätzle. Použi presne: „Slovak halušky (Slovak-style Spätzle): many tiny, thin, squiggly, irregular soft strands and drops of potato dough, each only about 1–2 cm, with rough torn uneven edges and no defined round shape, looking exactly like small German Spätzle egg noodles — absolutely NOT round gnocchi and NOT smooth oval dumplings". Platí pre bryndzové halušky, strapačky, halušky s kapustou a pod.

Výstup kroku 1: jeden súvislý anglický popisný názov jedla (max 15-20 slov), presne opisujúci, čo reálne leží na tanieri — týmto nahraď `[NAZOV RECEPTU]` v šablóne nižšie.

### Krok 2: vlož opis do jednej z 10 kompozičných šablón

Máme **10 overených promptov** (štýl "Modern Editorial & Elevated Lifestyle") — každý je iná kompozícia/scéna, aby fotky naprieč receptami nepôsobili identicky. Vyber ten, ktorý sedí typu jedla (napr. polievka/krém → miska zhora, mäso s prílohou → 3/4 alebo 45°, pečivo/dezert → detail vrstiev alebo mramor), a **striedaj ich** — neopakuj rovnaký template pri receptoch tesne po sebe. Ak sa niektorý template pri používaní ukáže ako nevhodný alebo treba pridať ďalší (napr. chýba dobrý štýl pre raňajky), uprav/pridaj ho priamo tu.

Na koniec vybraného promptu vždy pripoj: `No text, no logo, no watermark in the image.` a `Natural, realistic home-cooked food colours, not oversaturated or neon.` Pri horúcich jedlách (polievky, vývary, čaje a pod.) pripoj aj `No visible steam or smoke rising from the food.` — para v AI-generovaných fotkách takmer vždy vyzerá nápadne umelo.

**1. Moderný detail s hĺbkou (Editorial štýl)**
```
A bright, airy, modern editorial food photograph in a vertical 9:16 format. A close-up of [NAZOV RECEPTU] in a sleek white ceramic bowl on a smooth light oak table, capturing an elevated home cooking aesthetic. The [HLAVNÁ ČASŤ POSTUPU] is sharply focused. To add life, the background is beautifully blurred, showing a modern water glass and a small contemporary dish of [INÁ INGREDIENCIA]. A modern brushed steel fork rests on a casually draped light grey linen napkin. Natural scattered crumbs of [DÔLEŽITÉ INGREDIENCIE] and fresh [HLAVNÁ BYLINKA] add a credible, lived-in feel. Soft daylight.
```

**2. Živý "Flat Lay" (zhora, teplý minimalizmus)**
```
A bright, warm minimalist top-down flat-lay photograph, vertical 9:16 format. [NAZOV RECEPTU] served in a minimalist matte ceramic plate on a clean, smooth light wood table. A softly wrinkled neutral linen napkin lies beneath a modern matte silver knife and fork. The table isn't empty; a few scattered pieces of raw [DÔLEŽITÉ INGREDIENCIE] and a pinch of salt add an authentic, lived-in lifestyle feel. Crisp, diffused natural daylight highlights the [HLAVNÁ ČASŤ POSTUPU]. Film grain.
```

**3. Zdieľaný stôl (Elevated Lifestyle)**
```
A contemporary, bright lifestyle food photo in a 9:16 format, capturing an elevated home cooking moment. [NAZOV RECEPTU] in a modern large matte bowl, centered on a smooth oak table. Next to it, adding depth to the editorial scene, is a smaller minimalist bowl filled with [INÁ INGREDIENCIA]. A casually draped linen cloth with a modern matte silver fork. Scattered fresh [HLAVNÁ BYLINKA] around the bowl. Soft, airy natural window light.
```

**4. "Príprava v procese" na hladkej doske** — vhodné aj na `postup`/proces fotky (nižšie)
```
A bright, airy, modern editorial in-progress cooking snap, 9:16 format. [NAZOV RECEPTU] resting on a sleek, clean light wood cutting board with an organic, lived-in feel. A modern brushed stainless steel knife sits nearby alongside raw [DÔLEŽITÉ INGREDIENCIE]. The background is blurred, showing a modern ceramic pinch bowl. The [HLAVNÁ ČASŤ POSTUPU] looks fresh, garnished with [HLAVNÁ BYLINKA]. Natural, dynamic composition with soft directional daylight.
```

**5. Matná čierna a dub (Warm Minimalism)**
```
A bright, airy, modern editorial food photograph, vertical 9:16, embracing warm minimalism. A fresh serving of [NAZOV RECEPTU] in a minimalist matte black ceramic bowl on a smooth light oak table. A softly draped, slightly messy light grey linen napkin lies nearby with a sleek matte black spoon. Blurred background features a small contemporary dipping bowl of [INÁ INGREDIENCIA]. Scattered crumbs or a stray leaf of [HLAVNÁ BYLINKA] sit on the table for an authentic, elevated home cooking vibe. Soft diffused daylight.
```

**6. Kremeň a moderná elegancia**
```
A bright, modern elegant food photo with an elevated lifestyle aesthetic, 9:16 format. [NAZOV RECEPTU] in a matte geometric bowl sitting on a clean white quartz kitchen island. A casually wrinkled neutral napkin holds a modern brass fork. The blurred background adds editorial depth with a small dish of [INÁ INGREDIENCIA]. Stray leaves of [HLAVNÁ BYLINKA] and a dash of pepper on the counter. Crisp, natural side-light highlighting the [HLAVNÁ ČASŤ POSTUPU].
```

**7. Sústredený detail na vrstvy (Editorial Close-up)**
```
A bright, modern editorial side-angle close-up, 9:16 format, showcasing elevated home cooking. Showing the appetizing layers and texture of [NAZOV RECEPTU] on a smooth light wood surface. A modern matte silver serving spoon rests naturally at the edge. The background is blurred but shows a sleek glass of water to add realism and a lived-in feel. A few natural crumbs of [DÔLEŽITÉ INGREDIENCIE] and fresh [HLAVNÁ BYLINKA]. Soft, airy daylight.
```

**8. Širšia scéna s dynamikou (zdieľaný moment)**
```
A bright, wider modern editorial table scene, 9:16 format, blending warm minimalism and a lived-in lifestyle aesthetic. [NAZOV RECEPTU] in a centerpiece minimalist matte bowl on a smooth wood table. The scene is rich but clean: a softly wrinkled linen napkin, modern cutlery, a small side bowl of [INÁ INGREDIENCIA], and a modern drinking glass. Fresh [HLAVNÁ BYLINKA] generously garnishing the [HLAVNÁ ČASŤ POSTUPU]. Natural window light.
```

**9. Hladký mramor a zátišie**
```
A bright, high-end editorial food photo with a lived-in feel, 9:16 format. [NAZOV RECEPTU] on a sleek white plate over a smooth marble counter. Modern matte brass cutlery rests on a casually messy, unironed linen cloth to break the perfection and add organic texture. A small side dish with [DÔLEŽITÉ INGREDIENCIE] sits in the softly blurred background. Garnished with [HLAVNÁ BYLINKA]. Crisp, diffused daylight.
```

**10. Dynamické servírovanie**
```
A bright, airy, dynamic 45-degree angle editorial shot, 9:16 format. Capturing an elevated home cooking style with [NAZOV RECEPTU] in a modern matte bowl on a clean oak surface. Right next to it is a contemporary dish of [INÁ INGREDIENCIA], tying into the meal. A modern brushed fork leans casually on the bowl. A few pieces of [HLAVNÁ BYLINKA] scattered naturally on the table for that authentic lifestyle touch. The [HLAVNÁ ČASŤ POSTUPU] looks vibrant. Soft, welcoming daylight.
```

Každý recept má svoj vygenerovaný text uložený v `foto_prompt` poli/sekcii — použi presne ten text pri generovaní.

### Fotky postupu (voliteľné, zatiaľ nepoužívané pravidelne)

Rovnaký 2-krokový proces vieme použiť aj na fotky **kroku postupu**, nie len finálneho jedla — napr. na Stories "za scénou" alebo budúci krok-za-krokom obsah. Rozdiel: v kroku 1 namiesto finálneho servírovania opíš konkrétny medzikrok (napr. "opekanie cibule dozlata", "krájanie papriky na prúžky"), a v kroku 2 najčastejšie sedí **template č. 4** (in-progress, doska, nôž). Zatiaľ toto nerobíme automaticky pri každom recepte — použi len keď si o to používateľ vyslovene povie.

## Po vygenerovaní

1. Over si obrázok (prezri si ho) — food fotka musí vyzerať domácky/reálne, nie ako reklama.
2. Ulož fotku do `fotky/<id>.jpg` v repe (formát JPG, konvertuj ak treba). Fotky **sú súčasťou repa** — commitni a pushni ich, nech sa cez GitHub/git pull dostanú aj do lokálnej zložky `sporacek` na počítači.
3. Doplň `foto_url` v `.md` súbore receptu ako relatívnu cestu, napr. `foto_url: fotky/<id>.jpg`.
