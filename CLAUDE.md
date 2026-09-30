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

Huidige fase: **4 (bouwen)** – eerste werkende versie staat (data, trust engine, parser, app). Open: Gemini-key, Aikido-scan, rolverdeling, pitch.

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

## Uitleg voor collega's (zo leg je het uit aan de bazen)

### Het probleem in één zin
Medewerkers vinden wel documenten, maar weten niet of ze er **op kunnen vertrouwen**: is het actueel, geldt het voor mijn land, spreekt een ander document het tegen, en wie kan ik vragen als ik twijfel?

### Onze oplossing in één zin
Een zoekapp die bij elk antwoord een **Trust Score (0-100, groen/geel/rood)** toont, **uitlegt waarom**, tegenstrijdige bronnen **zichtbaar** maakt en bij twijfel **de juiste collega** voorstelt.

### Hoe werkt het? (5 stappen, simpel)
1. **Kennis als netwerk.** We zien de kennis van het bedrijf als een kaart van bolletjes: documenten, mensen en onderwerpen, met lijntjes ertussen ("Sofie schreef dit", "Thomas controleerde dat", "dit document verwijst naar dat document"). Dit heet een **graaf**. Net zoals Obsidian of een stamboom.
2. **Signalen meten.** Uit dat netwerk en de metadata halen we signalen: Hoe oud is het? Heeft het een eigenaar? Is het gecontroleerd? Werkt de schrijver nog hier? Spreekt het een ander document tegen? Wordt het alleen geciteerd door een kleine kliek?
3. **Een model leert wat betrouwbaar is.** Een machine-learningmodel (**XGBoost**) leert uit gebruikersfeedback ("dit bleek fout of verouderd") welke signalen samenhangen met onbetrouwbare documenten. Het geeft elk document een score.
4. **Expertise meewegen.** Via **PageRank** op het personennetwerk zien we wie op een onderwerp écht de expert is (veel geschreven, veel gebruikt, veel door collega's gecontroleerd). Die expertise telt mee in de score (15 procent).
5. **Uitleggen, niet verbergen.** Bij elk resultaat klap je open: "Dit document is 5 jaar oud, vervangen door een nieuwere versie en spreekt D901 tegen. Toch wordt het veel gelinkt: populair is niet betrouwbaar."

### De Trust Score in gewone woorden
Score = **85 procent** "hoe betrouwbaar is dit document volgens het model" + **15 procent** "hoe groot is de expertise van de auteur". Geldt het document voor een **ander land** dan gevraagd, dan wordt de score **x0,6** (een Nederlands document is geen antwoord voor België).
Kleuren: groen vanaf 70, geel vanaf 45, rood eronder.

### Waar gebruiken we AI (LLM)?
**Alleen om de vraag te begrijpen.** "Hoeveel ouderschapsverlof krijg ik in België?" wordt `{onderwerp: ouderschapsverlof, land: BE}`. Het LLM (Google Gemini) schrijft **geen** databasequeries en **beslist niet** over betrouwbaarheid. De score komt uit ons transparante model. Dat is veiliger (geen injectie), goedkoper, en uitlegbaar. Zonder LLM werkt de app ook, dan zoekt hij op trefwoorden.

### Demo-scenario's (3 minuten)
1. **"Hoeveel ouderschapsverlof krijg ik in België?"** De app toont een rode banner: bronnen spreken elkaar tegen (3 versus 4 maanden). Het actuele beleid (D901) is groen. Het oude beleid (D902) is rood, terwijl het **het vaakst gelinkt** is. Dat is het kernverhaal: populair is niet betrouwbaar.
2. **"Wat is de pensioenleeftijd in België?"** Alle bronnen zijn rood, want de schrijver is vertrokken. De app toont: "Vraag het aan **An Willems**". Gert Hermans is wel "expert", maar werkt niet meer hier, dus hij wordt overgeslagen.
3. **Tab "Kennisgraaf en risico's":** de kaart van documenten (groen/rood, grootte = populariteit), plus onderwerpen met een **bus-factor-risico** (kennis zit bij één persoon), bijvoorbeeld bedrijfswagen en pensioen.

### Hoe past dit bij de jurering?
- **Fit (30 procent):** precies de trust-vraag uit de challenge: Trust, Detect (conflicten en verouderd) en Connect (expert vinden).
- **Originaliteit (30 procent):** vertrouwen als score uit een graaf, met uitleg en conflictdetectie. Niet nog een chatbot.
- **Technical ability (30 procent):** werkende graaf, ML-model, PageRank/TrustRank/communities, Streamlit-app.
- **Security (10 procent):** geen vrije queries, invoervalidatie, geen secrets in code, Aikido-scan.

### Eerlijke beperkingen (benoem ze zelf in de pitch)
- **Alle data is gesimuleerd** (463 documenten, 64 personen, 16 onderwerpen, 4 klanten, 3 landen). De beleidswaarden zijn illustratief.
- Het model is getraind op **gesimuleerde feedback**. De score van het model (AUC rond 0,85) zegt dus vooral dat de pipeline werkt, niet hoe goed het in het echt zou zijn. In het echt komt de feedback uit duimpjes en correcties van gebruikers.
- Conflicten worden gevonden via een "stated value" per document. Echte tekst vergt extra NLP (volgende stap).
- Geen login/rechtenbeheer in de PoC. In productie zou je zoekresultaten filteren op wat iemand mag zien.

### Verwachte vragen van bazen
- *Waarom geen gewone AI-chatbot?* Een chatbot vat samen, maar zegt niet of de bron klopt. Wij tonen het vertrouwen en de reden.
- *Kan dit schalen?* Ja: graafmetrics en scoring zijn batchberekeningen. Bronnen als SharePoint, Confluence en Teams zijn te koppelen, en documenten worden automatisch opnieuw gescoord.
- *Hoe komt het model aan labels?* In productie: gebruikersfeedback, correcties en reviewresultaten. Nu: gesimuleerd.
- *Wat als het model het mis heeft?* Daarom altijd de uitleg en de expert-fallback. Mensen blijven beslissen.
- *Is mijn data veilig?* De LLM ziet enkel de vraag van de gebruiker, geen documenten. Er worden geen queries door het LLM gegenereerd.

### Woordenlijst
- **Graaf:** netwerk van bolletjes (nodes) en lijntjes (edges).
- **PageRank:** hoe belangrijk is een bolletje, omdat belangrijke bolletjes ernaar wijzen (zoals Google).
- **TrustRank:** PageRank die start bij gecontroleerde documenten: vertrouwen "vloeit" via links verder.
- **Betweenness:** hoe vaak een persoon een brug is tussen anderen (waar kennis afhangt van één persoon).
- **Louvain/community:** automatisch gevonden groepen, handig om silo's te zien.
- **Clustering coefficient:** verwijzen de buren van een document vooral naar elkaar (echokamer)?
- **XGBoost:** ML-model dat uit voorbeelden leert; hier om de kans op "onbetrouwbaar" te voorspellen.
- **SHAP-achtige uitleg:** hoeveel elk signaal bijdroeg aan een score.
- **Bus-factor:** als één persoon weggaat, verdwijnt de kennis.

### Bestanden
| Bestand | Wat |
|---|---|
| `seed_data.py` | maakt de gesimuleerde data (`data/*.csv`) en laadt de graaf |
| `trust_engine.py` | graafmetrics, features, XGBoost, Trust Score, uitleg, expert-suggestie |
| `query_parser.py` | vraag -> onderwerp en land (Gemini, met trefwoorden als terugval) |
| `app.py` | Streamlit-interface |
| `context/` | challenge-guide en het oorspronkelijke ideeplan |
| `.env` | jouw geheime sleutels (staat NIET op GitHub) |

## Beslissingen & MVP-scope
Bron van het idee: `context/ai_system_prompt.txt` (Neo4j-plan), aangepast:
- **Graaf: `networkx` in-memory, geen Neo4j/Docker.** Nodes `Document`, `Person`, `Topic`; edges `WROTE`, `LINKS_TO`, `REVIEWS`, `BELONGS_TO_TOPIC` (+ `CONFLICTS_WITH`/`SUPERSEDES`). Dummydata uit een seed-script (`seed_data.py`), met bewust ingebouwde conflicten (zelfde topic, ander land/waarde) en verouderde documenten.
- **Trust Score = ML-model (XGBoost, scikit-learn voor pipeline) op metadata- en graaf-features** (decay, completeness, fragmentation/conflict, scope-match) + expert-score van de auteur (PageRank, per topic gepersonaliseerd). Getraind op **gesimuleerde dummydata**; labels = gesimuleerde gebruikersfeedback ("bleek fout/verouderd"). Transparant benoemen als proof of concept. Model moet uitlegbaar blijven (bv. logistic regression/kleine boom + bijdrage per feature).
- **LLM (Gemini via Google Cloud/Vertex AI): enkel intent-extractie** (`{topic, land, doc_type}` als JSON, gevalideerd tegen vaste lijst) en eventueel korte uitleg op basis van de scores. **Geen text-to-Cypher/vrije queries**; daarna vaste, veilige opzoekingen. Keyword-fallback als de API faalt.
- Context-aware: de zoekvraag heeft een land/scope; documenten voor een ander land worden afgestraft.
- UI (Streamlit): zoekbalk, groen/geel/rood badge, uitklapbare uitleg per resultaat, "Informatie onzeker? Vraag het aan [expert]", grafweergave (pyvis) van bronnen en conflicten.
- Security: geen secrets in code (`.env`), invoervalidatie, geen vrije queries, geen IDOR.
- Buiten scope: echte data/integraties, login-systeem, Neo4j, echt getrainde productiemodellen.
- **Data (klaar):** `python seed_data.py` schrijft `data/*.csv`; `from seed_data import load_graph` geeft de networkx-graaf (463 docs, 64 personen, 16 topics, 4 klanten, 3 landen). Demo-scenario's: ouderschapsverlof BE (D901-D905), pensioen BE met vertrokken expert (D911-D913), echo chamber bedrijfswagen BE (D921-D926), Nike cut-off BE waar de klantafspraak het standaardbeleid overschrijft (D931-D933).
- **Klanten (Nike, AS Adventure, Decathlon, Zalando):** klantspecifieke documenten met afwijkende afspraken. Vertrouwelijkheid: klantdocumenten worden alleen getoond als de vraag die klant noemt. Bij een klantvraag tellen algemene documenten x0,85.
- **Validatie:** `TrustEngine.evaluate()` (tab "Validatie en methode"): is de nummer 1 per groep een document met de actuele waarde? Out-of-fold model vs nieuwste document vs meest gelinkt vs willekeurig. De AUC in de app is één modelgetal, geen score per vraag.
- Rolverdeling: nog in te vullen.
