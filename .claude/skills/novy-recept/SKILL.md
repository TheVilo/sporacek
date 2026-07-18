---
name: novy-recept
description: Použi pri pridávaní jedného nového receptu do databázy mimo týždenného letáku — napr. keď používateľ nájde inšpiráciu, chce rozšíriť databázu, alebo požiada "pridaj recept", "vygeneruj X nových receptov", "spravme nový recept na...". Nepoužívaj pri spracovaní týždenného letáku (na to je tyzdenny-vystup).
---

# Pridanie nového receptu

Pravidlá pre recepty (id, suroviny, tagy, tón) sú v koreňovom `CLAUDE.md` — načítaj si ich, ak ešte nie sú v kontexte.

## Kľúčové pravidlo: nevymýšľaj recepty

Recept **nikdy nevymýšľaj od stola**. Vždy najprv vyhľadaj reálnu inšpiráciu na internete (WebSearch) — overený, skutočne fungujúci recept (pomery surovín, časy varenia, techniku). Potom ho:

- **preformuluj do vlastných slov**, neprekladaj mechanicky/doslovne
- **priprav pre 2 osoby**, preveď na metrické jednotky
- **zjednoduš** podľa pravidiel „čo je dobrý šporáček recept" (málo krokov, bežné vybavenie, lacné suroviny)
- **napíš plynulou, prirodzenou slovenčinou** — postup má znieť, akoby ho napísal človek, čo vie variť, nie strojový preklad. Krátke jasné vety, konkrétne časy a množstvá.
- **Postup je vždy v rozkazovacom spôsobe, jednotné číslo (ty), dôsledne.** Najčastejšie chyby, na ktoré si dávaj pozor:
  - zlý tvar rozkazovacieho spôsobu (napr. „okoreni" namiesto „okoreň", „zalejaj" namiesto „zalej", „uvari" namiesto „uvar")
  - zámena s neurčitkom (napr. „znížiť teplotu" namiesto „zníž teplotu")
  - zámena s množným/formálnym tvarom „vy" (napr. „duste" namiesto „dus")
  - Po napísaní si postup **prečítaj ešte raz vetu po vete** a over si každé sloveso v rozkazovacom spôsobe — toto je jediná časť receptu, kde sa doteraz opakovane objavili gramatické chyby.

## Postup

1. **Over duplicity** — prehľadaj `recepty/`, či podobný recept už existuje. Ak áno, neduplikuj, uprav používateľa.
2. **Vyhľadaj inšpiráciu na internete** (WebSearch) pre daný typ jedla.
3. **Zostav recept** podľa štandardnej štruktúry (viď šablónu nižšie) — id, názov, suroviny z `suroviny.md` (chýbajúce doplň do číselníka), cena za porciu (odhad podľa bežných cien, ak recept nie je viazaný na konkrétny leták), nutričné hodnoty (odhad), postup po slovensky, tagy podľa taxonómie.
4. **Zapíš recept** do `recepty/<id>.md`.
5. **Vygeneruj fotku** podľa `.claude/skills/generovanie-fotiek/SKILL.md`, ulož do `fotky/<id>.jpg`, doplň `foto_url`.
6. **Ak existuje** artifact „databáza receptov" (URL v CLAUDE.md), doplň doň nový recept — nič iné v ňom neregeneruj.
7. **Commitni a pushni.**

## Šablóna receptu

```markdown
# <Kuchársky lákavý názov>

**slug:** <id>
**porcie:** 2
**čas prípravy:** <X> minút
**cena za porciu:** <X,XX> €/osoba
**týždeň:** — (mimo týždenného letáku)

---

## Foto prompt
"<anglický foto prompt, fotorealistický, teplé domáce svetlo, 9:16, bez textu>"

---

## Suroviny (pre 2 osoby)

| Surovina | Množstvo | Cena |
|---|---|---|
| ... | ... | ... |

**Celkom: X,XX € → X,XX €/osoba**

---

## Nutričné hodnoty (na porciu, odhad)

| | |
|---|---|
| Energia | ~XXX kcal |
| Bielkoviny | XX g |
| Sacharidy | XX g |
| Tuky | XX g |

---

## Postup

1. ...
2. ...

---

## Tagy
`#typ` `#surovina` `#výživa` `#náročnosť` `#cena` (len hodnoty z taxonómie v CLAUDE.md)
```

## Cena mimo letáku

Ak recept nevzniká z konkrétneho týždenného letáku, použi bežné (nie akciové) ceny slovenských reťazcov ako odhad. Označ to jasne — pole `týždeň` necháva prázdne alebo „—", nie konkrétny dátum letáku.
