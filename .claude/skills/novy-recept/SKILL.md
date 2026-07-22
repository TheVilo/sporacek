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
3. **Zostav recept** podľa štandardnej štruktúry (viď šablónu nižšie) — id, názov, suroviny a množstvá z `suroviny.md` (chýbajúce doplň do číselníka), nutričné hodnoty (odhad), postup po slovensky, tagy podľa taxonómie. **Bez ceny** — pozri nižšie.
4. **Zapíš recept** do `recepty/<id>.md`.
5. **Vygeneruj fotku** podľa `.claude/skills/generovanie-fotiek/SKILL.md`, ulož do `fotky/<id>.jpg`, doplň `foto_url`.
6. **Ak existuje** artifact „databáza receptov" (URL v CLAUDE.md), doplň doň nový recept — nič iné v ňom neregeneruj.
7. **Commitni a pushni.**

## Šablóna receptu

**Všetky recepty musia mať presne túto štruktúru** — jednotný formát je kritický, aby ich vedela appka aj `build_databaza.py` spoľahlivo čítať. Nikdy nepoužívaj YAML frontmatter ani polia navyše (žiadne `historia_pouzitia` a pod.). Po zápise over, že recept sedí na túto šablónu; `python3 scripts/build_databaza.py` navyše nahlási každý recept mimo formátu.

```markdown
# <Kuchársky lákavý názov>

**slug:** <id>
**porcie:** 2
**čas prípravy:** <X> minút

---

## Foto prompt
"<anglický foto prompt, fotorealistický, teplé domáce svetlo, 9:16, bez textu>"

---

## Suroviny (pre 2 osoby)

| Surovina | Množstvo |
|---|---|
| ... | ... |

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
`#typ` `#surovina` `#výživa` `#náročnosť` (len hodnoty z taxonómie v CLAUDE.md)
```

## Recept nikdy neobsahuje cenu ani väzbu na konkrétny týždeň/obchod

Recepty sú nezastarateľná databáza — suroviny, množstvá, postup, fotka, tagy z taxonómie. **Žiadna cena, nikde.** Cena sa počíta až vtedy, keď niekto skladá konkrétny týždeň alebo custom výber (`.claude/skills/tyzdenny-vystup/SKILL.md`), z aktuálnych cien v danej chvíli — nie pri tvorbe receptu.

Rovnaký princíp platí pre čokoľvek viazané na konkrétny obchod/dátum (napr. "týždeň: 29/2026 · Lidl", tag `#akcia-lidl`, poznámka "platí len v utorok") — **do receptu to nepatrí nikdy**, aj keby recept práve vznikol z konkrétneho letáku. Taká informácia patrí výhradne do `tydne/<týždeň>/`, lebo ten istý recept sa časom použije v mnohých ďalších týždňoch a obchodoch.
