# Tectonic Hackathon, SD Worx challenge: GRAPHLAS

Context: SD Worx is a company that helps organizations manage HR, payroll and workforce operations.

Problem statement: SD Worx is looking for a way to find organizational knowledge more easily, verify its reliability and share it more efficiently with its customers.

Proof of concept: GRAPHLAS is an application that can help with this. It is a graph-based framework that can provide answers to questions asked by customers and shows a Trust Score with each answer, explains why, makes conflicting sources visible and suggests the right expert in case of doubt.

## Architecture

- `app.py`: the Streamlit-interface
* `trust_engine.py`: Trust scoring
* `query_parser.py`: Question interpretation
* `seed_data.py`: Simulated data

## Installation guide

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python seed_data.py          # maakt data/*.csv
cp .env.example .env         # vul daarna GOOGLE_API_KEY in (optioneel)
streamlit run app.py         # opent http://localhost:8501
```

Zonder API-key werkt de app ook: de vraag wordt dan op trefwoorden begrepen.


## Unfinished

- Gesimuleerde data en feedback-labels; geen echte bronnen gekoppeld.
- Geen login of rechtenbeheer.
- Conflictdetectie gebruikt een vaste "waarde" per document, geen vrije-tekst-NLP.
