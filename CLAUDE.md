# Hackathon – context voor deze chat

## Situatie
- Hackathon van **4 uur**, team van **4 personen**, doel: een werkende **MVP**.
- Opdracht en context staan in de map `context/` (guide PDF). Nog niet bepaald welk concreet probleem we kiezen.
- We bouwen de code via deze terminal, samen met Claude.
- Repo: https://github.com/larsvdb19/hackathon (remote `origin`, map `/home/daria/Documents/Tectonic`).
- Taal van communicatie: **Nederlands**. Code, variabelen en commentaar: Engels tenzij anders gevraagd.

## Tijdsplanning (4 uur)
1. **Idee begrijpen + brainstormen** – opdracht lezen, vragen, ideeën verzamelen.
2. **Idee reduceren tot MVP** – wat is de kleinste versie die de kernwaarde toont? Alles anders = "nice to have".
3. **Bouwstrategie + rolverdeling** – architectuur, bestandsstructuur, wie doet wat (4 rollen, weinig merge-conflicten).
4. **Bouwen** – snel itereren, eerst een end-to-end skelet, dan verfijnen.
5. **Testen** – happy path met demo-data, edge cases, bugs fixen.
6. **Pitch + eindproduct** – demo-flow, slides/verhaal, app stabiel en opgeschoond.

Huidige fase: **1 (idee begrijpen + brainstormen)** – opdracht is binnen.

## Tech stack
- Python 3.13, **Streamlit** als front-end/demo-app (waarschijnlijk).
- pandas/numpy/scipy/statsmodels, scikit-learn, matplotlib/seaborn/plotly.
- Virtuele omgeving: `.venv/` in de projectmap (`source .venv/bin/activate`).
- Starten: `streamlit run app.py`.

## Werkafspraken voor Claude
- Hou het **klein en snel**: MVP boven perfectie, geen over-engineering, geen onnodige abstracties.
- Geef bij keuzes een aanbeveling in plaats van een lijst met opties.
- Zet dingen in aparte modules zodat 4 mensen parallel kunnen werken (bv. `app.py`, `data.py`, `model.py`, `pages/`).
- Commit/push alleen op vraag van het team; werk bij voorkeur met korte feature-branches.
- Gebruik realistische demo-/dummydata als echte data ontbreekt, en zeg dat duidelijk.
- Bewaar hieronder beslissingen, zodat de context behouden blijft.

## Opdracht: SD Worx (NIET KBC)
Wij werken **enkel aan de SD Worx-challenge**. De KBC-challenge in de guide negeren.
Bron: `context/tectonic-hackathon-participants-guide.pdf` (Tectonic Hackathon, 30 sep 2026).

**Titel:** "Unlock the Knowledge Within" – *Find it. Understand it. Trust it.*
**Vraag:** "How might we turn fragmented organisational knowledge into a trusted shared resource?"

**Achtergrond**
- SD Worx: HR, payroll en workforce-operaties; 10.000+ medewerkers, 100.000+ klanten, 6M+ payslips, actief in 100+ landen.
- Kennis zit verspreid in policies, handleidingen, procedures, checklists, e-mails, chats, Teams, gedeelde bestanden, workflows, business-data en in de hoofden van experts.
- Het echte probleem is **vertrouwen**, niet zoeken: een zoekopdracht geeft tien antwoorden, een AI-assistent vat ze samen, maar is het antwoord **betrouwbaar, actueel en relevant** voor deze klant/dit land/deze situatie?
- Voorbeeld uit de guide: drie documenten (één recent, één zonder eigenaar, één mogelijk voor een ander land) + tegenstrijdige info uit een Teams-gesprek. Medewerker vindt info maar kan er niet met vertrouwen op handelen. Ook: een consultant die een klantportfolio overneemt (handover).
- Kernvragen: Wat is betrouwbaar? Wat is actueel? Wat geldt in deze context? Waar zitten de gaten? Wie heeft relevante expertise? Welk antwoord moet iemand vertrouwen?

**Opdracht:** bouw een gefocuste proof of concept die organisatiekennis makkelijker te vinden, vertrouwen of delen maakt. **Kies één betekenisvol probleem**, niet alles oplossen.
- Focus op **één rol, één workflow, één kennisbron of één trust-signaal**.
- Maak het moment van twijfel tastbaar en toon de stap van "ik vond iets" naar "ik snap waarom ik hierop kan vertrouwen".
- Geen black box: maak vertrouwen zichtbaar, uitlegbaar en nuttig. Begin niet bij technologie maar bij het moment van twijfel/frictie.

**Inspiratiegebieden (geen checklist)**
- **Trust:** herkennen of info relevant en betrouwbaar is.
- **Capture:** waardevolle kennis toegankelijk maken voorbij inboxen, documenten en silo's.
- **Detect:** tegenstrijdige, dubbele, ontbrekende of verouderde kennis zichtbaar maken.
- **Connect:** de juiste expertise vinden als documenten niet volstaan.

## Beoordeling & inleveren
**Juryscore:** Originaliteit 30% · Technical ability ("werkt het?") 30% · Fit met de challenge 30% · Security 10%.

**Inleveren via Builderbase** (één teamlid): korte beschrijving, **demovideo < 3 min**, **GitHub-repolink**, **screenshots van het Aikido-platform** (voor en na).

**Aikido (security, 10%)**: account via "Continue with GitHub", repo koppelen, AI Code Audit draaien (Code Security Audit; baseline), gevonden issues fixen en als opgelost markeren, screenshot voor en na. Checkt o.a. business-logic flaws, IDOR, authenticatie, autorisatie. Score = resterende issues. -> Plan een baseline-scan vroeg in en een fix-ronde vóór het einde; bouw geen onveilige auth/datatoegang.

**Regels**
- Bouwen binnen de officiële tijdslot; **final means final** (na indienen geen code- of submissionwijzigingen).
- **Repo publiek** houden tot na de jurering; korte **README** (project, hoe runnen, wat onaf is).
- Links controleren (repo, demo, materialen toegankelijk voor jury).
- **Nooit wachtwoorden, API-keys of vertrouwelijke data uploaden** (gebruik `.env`, staat in `.gitignore`).
- Geen plagiaat/valsspelen; instructies van organisatoren volgen.

## Partner-tools (credits via Discord/Builderbase, optioneel)
- **Cursor** (coding agent), **ElevenLabs** (text-to-speech, bv. voor demo/voice), **Google Cloud** (GCP-credentials via teamlink in Builderbase, 1 week geldig), **Aikido** (security-audit, verplicht).

## Beslissingen & MVP-scope
Bron van het idee: `context/ai_system_prompt.txt` (Neo4j-plan), aangepast:
- **Graaf: `networkx` in-memory, geen Neo4j/Docker.** Nodes `Document`, `Person`, `Topic`; edges `WROTE`, `LINKS_TO`, `REVIEWS`, `BELONGS_TO_TOPIC` (+ `CONFLICTS_WITH`/`SUPERSEDES`). Dummydata uit een seed-script (`seed_data.py`), met bewust ingebouwde conflicten (zelfde topic, ander land/waarde) en verouderde documenten.
- **Trust Score = ML-model (XGBoost, scikit-learn voor pipeline) op metadata- en graaf-features** (decay, completeness, fragmentation/conflict, scope-match) + expert-score van de auteur (PageRank, per topic gepersonaliseerd). Getraind op **gesimuleerde dummydata**; labels = gesimuleerde gebruikersfeedback ("bleek fout/verouderd"). Transparant benoemen als proof of concept. Model moet uitlegbaar blijven (bv. logistic regression/kleine boom + bijdrage per feature).
- **LLM (Gemini via Google Cloud/Vertex AI): enkel intent-extractie** (`{topic, land, doc_type}` als JSON, gevalideerd tegen vaste lijst) en eventueel korte uitleg op basis van de scores. **Geen text-to-Cypher/vrije queries**; daarna vaste, veilige opzoekingen. Keyword-fallback als de API faalt.
- Context-aware: de zoekvraag heeft een land/scope; documenten voor een ander land worden afgestraft.
- UI (Streamlit): zoekbalk, groen/geel/rood badge, uitklapbare uitleg per resultaat, "Informatie onzeker? Vraag het aan [expert]", grafweergave (pyvis) van bronnen en conflicten.
- Security: geen secrets in code (`.env`), invoervalidatie, geen vrije queries, geen IDOR.
- Buiten scope: echte data/integraties, login-systeem, Neo4j, echt getrainde productiemodellen.
- **Data (klaar):** `python seed_data.py` schrijft `data/*.csv`; `from seed_data import load_graph` geeft de networkx-graaf (78 docs, 24 personen, 8 topics). Demo-scenario's: ouderschapsverlof BE (D901-D905), pensioen BE met vertrokken expert (D911-D913), echo chamber bedrijfswagen BE (D921-D926).
- Rolverdeling: nog in te vullen.
