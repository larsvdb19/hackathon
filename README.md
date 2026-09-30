# Trusted Knowledge (Tectonic Hackathon, SD Worx challenge)

Zoekapp die bij elk antwoord een **Trust Score** toont, **uitlegt waarom**, tegenstrijdige bronnen
zichtbaar maakt en bij twijfel de juiste expert voorstelt. Uitleg in gewone taal: zie `CLAUDE.md`.
Alle data is gesimuleerd (proof of concept).

## Starten
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python seed_data.py          # maakt data/*.csv
cp .env.example .env         # vul daarna GOOGLE_API_KEY in (optioneel)
streamlit run app.py         # opent http://localhost:8501
```
Zonder API-key werkt de app ook: de vraag wordt dan op trefwoorden begrepen.

## Wat is onaf
- Gesimuleerde data en feedback-labels; geen echte bronnen gekoppeld.
- Geen login of rechtenbeheer.
- Conflictdetectie gebruikt een vaste "waarde" per document, geen vrije-tekst-NLP.
