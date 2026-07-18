---
name: tyzdenny-vystup
description: Použi pri spracovaní týždenného letáku (akciové produkty) na recepty, nákupný zoznam, ceny a obsah pre Stories. Trigger frázy - "leták", "týždenný výstup", "priprav recepty na tento týždeň", priloženie PDF/screenshotu letáku, alebo žiadosť o nákupný zoznam/úsporu na týždeň.
---

# Spracovanie týždenného letáku

Pravidlá pre recepty (id, suroviny, tagy, tón) sú v koreňovom `CLAUDE.md` — načítaj si ich, ak ešte nie sú v kontexte.

## Postup

1. **Prečítaj leták** (PDF/screenshot/text) → vypíš akciové produkty s cenami.
2. **Prehľadaj `recepty/`** → zisti, čo už máme, aby nevznikli duplicity.
3. **Navrhni 5 obedov (Po–Pi), vždy pre 2 osoby**, podľa pravidiel z CLAUDE.md.
   - prednostne použi existujúce recepty z databázy, ak sedia na akciu
   - nové recepty vytvor len ak treba
4. **Prepočítaj:**
   - cenu za porciu pre každé jedlo
   - kompletný nákupný zoznam s cenami
   - celkovú cenu nákupu
   - úsporu oproti bežným cenám
5. **Ku každému receptu daj `foto_prompt`** (šablóna nižšie).
6. **Priprav texty do Stories** (názov jedla + cena za porciu).
7. **Zapíš:**
   - nové recepty do `recepty/`
   - nové suroviny do `suroviny.md`
   - výstup týždňa do `tydne/RRRR-MM-DD.md`

## Šablóna foto promptu (pre nanobanana)

**Kritická podmienka: fotka musí vyzerať ako amatérska mobilná fotka, NIE ako profesionálna/umelecká food photography.** Toto je nezmeniteľná požiadavka pri každom recepte — bežný človek odfotí telefónom svoje jedlo tesne pred jedením, nie štylista jedla pre časopis.

```
Realistická fotka jedla odfotená mobilom, akoby ju spravil bežný človek doma tesne pred jedlom: [NÁZOV JEDLA].
Obyčajný tanier na kuchynskom stole alebo pracovnej doske — nie štylizovaná scéna.
Vyzerá presne ako obyčajný Instagram Stories/WhatsApp odfotok, NIE profesionálna food photography.
Bežné, mierne nerovnomerné domáce svetlo (stropné alebo denné z okna) — nie naaranžované "zlaté" svetlo.
Celý záber ostrý, BEZ bokehu/rozostreného pozadia — mobilné fotky nemajú hĺbku ostrosti ako profi objektív.
Mierne nedokonalý, neštudovaný uhol (zhora alebo tak, ako by človek prirodzene fotil vlastné jedlo).
ŽIADNE štylizované rekvizity — žiadne plátené obrúsky, vintage dosky na krájanie, fľaše vína, umelo poukladané bylinky, kvety, sviečky.
Obyčajná kuchyňa alebo stôl v pozadí, taký, aký reálne je — nie upravený "moodboard".
Voľné miesto navrchu alebo po strane na text.
Bez textu a bez loga v obrázku.
Formát 9:16 (Instagram Stories).
```
