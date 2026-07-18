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

```
Fotorealistická fotografia jedla: [NÁZOV JEDLA], porcia na jednoduchom tanieri.
Domáca kuchyňa, prirodzené teplé svetlo z okna, drevený alebo svetlý stôl.
Reálny, útulný, domácky vzhľad — nie reklamná, prehnane naštylizovaná scéna.
Teplé zemité tóny (pieskova, terakota, zelené akcenty), mäkké tiene.
Pohľad zhora alebo mierne zboku, plytká hĺbka ostrosti.
Voľné miesto navrchu alebo po strane na text.
Bez textu a bez loga v obrázku.
Formát 9:16 (Instagram Stories).
```
