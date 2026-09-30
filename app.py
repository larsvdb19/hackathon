"""Streamlit front-end: trusted knowledge search with explainable trust scores."""
import html

import pandas as pd
import streamlit as st
from pyvis.network import Network

from query_parser import lookup_documents, parse_query
from seed_data import COUNTRIES, TOPICS
from trust_engine import EXPERT_WEIGHT, GENERIC_PENALTY, GREEN, SCOPE_PENALTY, YELLOW, TrustEngine

st.set_page_config(page_title="Trusted Knowledge", page_icon="🧭", layout="wide")

ICON = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
HEX = {"green": "#2e9e5b", "yellow": "#e0a800", "red": "#d64545"}
LABEL = {"green": "Betrouwbaar", "yellow": "Controleer", "red": "Onbetrouwbaar"}
TOPIC_NAMES = {f"T_{k}": v[0] for k, v in TOPICS.items()}
EXAMPLES = ["Hoeveel ouderschapsverlof krijg ik in België?", "Wat is de pensioenleeftijd in België?",
            "Wat is de cut-off voor Nike in België?"]
EDGE_STYLE = {"WROTE": ("#4a7bd0", "schreef"), "REVIEWS": ("#2e9e5b", "reviewt"),
              "LINKS_TO": ("#999999", "linkt naar"), "SUPERSEDES": ("#d64545", "vervangt")}


@st.cache_resource(show_spinner="Trust engine opbouwen...")
def get_engine():
    return TrustEngine()


@st.cache_data(ttl=3600, show_spinner=False)
def cached_parse(q):
    """Same question = same intent, and far fewer LLM calls (quota)."""
    return parse_query(q)


def trust_color(t):
    return HEX["green" if t >= GREEN else "yellow" if t >= YELLOW else "red"]


def render_result(r):
    with st.container(border=True):
        c1, c2 = st.columns([5, 1])
        c1.markdown(f"**{html.escape(r['title'])}**  \n{html.escape(r['key_value'])} · {r['country']} · `{r['doc_id']}`")
        c2.markdown(f"<div style='text-align:right;font-size:1.6rem;font-weight:700;color:{HEX[r['badge']]}'>"
                    f"{ICON[r['badge']]} {r['trust']:.0f}</div>"
                    f"<div style='text-align:right;color:{HEX[r['badge']]}'>{LABEL[r['badge']]}</div>",
                    unsafe_allow_html=True)
        with st.expander("Waarom deze score?"):
            for sign, text in r["reasons"]:
                st.markdown(f"{'✅' if sign > 0 else '⚠️' if sign < 0 else 'ℹ️'} {text}")
            st.caption("Grootste invloed in het ML-model (+ verhoogt, − verlaagt de score):")
            st.bar_chart(pd.DataFrame(r["contributions"], columns=["factor", "effect"]).set_index("factor"))


def build_graph(engine, doc_ids, with_people=True, height="520px"):
    """pyvis graph of the given documents (+ their authors/reviewers). Built from our own data only."""
    net = Network(height=height, width="100%", directed=True, cdn_resources="remote")
    ids = set(doc_ids)
    for d in ids:
        t = engine.scores.trust[d]
        net.add_node(d, label=d, color=trust_color(t), size=12 + 400 * engine.pagerank[d],
                     title=html.escape(f"{engine.scores.title[d]}: {engine.scores.key_value[d]} (trust {t:.0f})"))
    people = set()
    for u, v, k in engine.g.edges(data="etype"):
        if k == "LINKS_TO" and u in ids and v in ids or k == "SUPERSEDES" and u in ids and v in ids:
            net.add_edge(u, v, color=EDGE_STYLE[k][0], title=EDGE_STYLE[k][1], dashes=(k == "SUPERSEDES"))
        elif with_people and k in ("WROTE", "REVIEWS") and v in ids:
            if u not in people:
                active = bool(engine.persons.active[u])
                net.add_node(u, label=engine.person_name(u), shape="diamond", size=14,
                             color="#4a7bd0" if active else "#b0b0b0",
                             title=html.escape(f"{engine.person_name(u)} ({'actief' if active else 'niet meer actief'})"))
                people.add(u)
            net.add_edge(u, v, color=EDGE_STYLE[k][0], title=EDGE_STYLE[k][1])
    return net.generate_html()


def search_tab(engine, country_choice, client_choice):
    if "q" not in st.session_state:
        st.session_state.q = ""
    cols = st.columns(len(EXAMPLES))
    for col, ex in zip(cols, EXAMPLES):
        if col.button(ex, width="stretch"):
            st.session_state.q = ex
    q = st.text_input("Stel een vraag", key="q", max_chars=300,
                      placeholder="Bijv. Hoeveel ouderschapsverlof krijg ik in België?")
    if not q.strip():
        return
    intent = cached_parse(q)
    if not intent["topic_id"]:
        st.warning("Ik snap het onderwerp niet. Probeer: " + ", ".join(TOPIC_NAMES.values()))
        return
    country = intent["country"] if country_choice == "Automatisch" else (None if country_choice == "Alle" else country_choice)
    client_ids = {v: k for k, v in engine.client_names.items()}
    client = intent["client"] if client_choice == "Automatisch" else (None if client_choice == "Geen" else client_ids[client_choice])
    st.session_state.last_topic = intent["topic_id"]
    st.caption(f"Begrepen: **{TOPIC_NAMES[intent['topic_id']]}** · land: **{country or 'alle'}** · "
               f"klant: **{engine.client_names.get(client, 'geen')}** · via {intent['method']}")
    results = engine.rank(lookup_documents(engine.g, {**intent, "client": client}), country, client)[:8]
    in_scope = [r for r in results if r["in_scope"]]
    by_client = {}
    for r in in_scope:
        by_client.setdefault((r["client"], r["country"]), set()).add(r["key_value"])
    for (c, land), values in by_client.items():
        if len(values) > 1:
            who = f" ({engine.client_names[c] + ', ' if c else ''}{land})"
            st.error(f"Bronnen spreken elkaar tegen{who}: " + " ↔ ".join(sorted(values)))
    for r in results:
        render_result(r)
    if not in_scope or max(r["trust"] for r in in_scope) < YELLOW:
        ex = engine.suggest_expert(intent["topic_id"], client)
        st.info(f"**Informatie onzeker? Vraag het aan deze expert.**  \n"
                f"{ex['name']} · {ex['role']} · {ex['department']} ({ex['country']})")
    with st.expander("Kennisgraaf van deze zoekopdracht"):
        st.caption("Ruit = persoon (grijs = niet meer actief) · cirkel = document (kleur = trust, grootte = populariteit) · "
                   "blauw = schreef · groen = reviewt · grijs = linkt naar · rood gestreept = vervangt")
        st.iframe(build_graph(engine, [r["doc_id"] for r in results]), height=540)


def insights_tab(engine):
    topics = list(TOPIC_NAMES)
    idx = topics.index(st.session_state.get("last_topic", topics[0]))
    topic = st.selectbox("Onderwerp (volgt je laatste zoekopdracht)", topics, index=idx, format_func=TOPIC_NAMES.get)
    st.caption("Alle algemene documenten van dit onderwerp. Kleur = trust score, grootte = populariteit (PageRank). "
               "Een groot rood punt is populair maar onbetrouwbaar.")
    docs = engine.docs[(engine.docs.topic_id == topic) & (engine.docs.client == "")].index
    st.iframe(build_graph(engine, docs, with_people=False), height=540)
    st.subheader("Kennisrisico's per onderwerp")
    st.dataframe(engine.topic_risks(), hide_index=True, width="stretch")
    st.subheader("Experts voor dit onderwerp")
    ex = pd.DataFrame([{"naam": engine.persons.name[p], "afdeling": engine.persons.department[p],
                        "actief": bool(engine.persons.active[p]), "expert-score": round(s, 2)}
                       for p, s in sorted(engine.expert[topic].items(), key=lambda kv: -kv[1])[:6]])
    st.dataframe(ex, hide_index=True, width="stretch")


def validation_tab(engine):
    st.subheader("Is het bovenste document echt het beste?")
    st.markdown(
        "We kennen in de gesimuleerde data de **verborgen waarheid**: zegt een document de **actuele** waarde of een "
        "verouderde? Die waarheid is nooit een feature van het model. Per groep documenten (zelfde onderwerp, land en klant, "
        "met zowel juiste als verouderde documenten) kijken we of de **nummer 1** een juist document is. "
        "Het model wordt daarvoor beoordeeld met **out-of-fold** voorspellingen: het scoort dus nooit documenten waarop het getraind is.")
    summary, per_group = engine.evaluate()
    c = st.columns(4)
    c[0].metric("Ons model", f"{summary['model']:.0%}")
    c[1].metric("Nieuwste document", f"{summary['nieuwste']:.0%}")
    c[2].metric("Meest gelinkt (PageRank)", f"{summary['meest gelinkt']:.0%}")
    c[3].metric("Willekeurig", f"{summary['willekeurig']:.0%}")
    st.caption(f"Top-1 juist, over {summary['groepen']} groepen. AUC van de Trust Score tegen de waarheid: "
               f"{summary['auc_vs_waarheid']:.2f}. AUC van het model tegen de (ruizige) feedbacklabels: {engine.cv_auc:.2f} "
               "(één getal voor het hele model, geen score per vraag; het verandert alleen als de data verandert).")
    st.warning("Beperking: dit is gesimuleerde data. Het toont dat de pipeline het juiste document kan herkennen, "
               "niet hoe goed het in een echt bedrijf werkt. Echte validatie: experts laten beoordelen en gebruikersfeedback meten.")
    with st.expander("Resultaat per groep"):
        st.dataframe(per_group, hide_index=True, width="stretch")
    st.subheader("Stappen van de berekening")
    st.markdown(f"""
1. **Vraag begrijpen:** Gemini (of trefwoorden) haalt onderwerp, land en klant uit de vraag. De uitkomst wordt gecontroleerd tegen vaste lijsten.
2. **Kandidaten ophalen:** vaste opzoeking van documenten van het onderwerp. Klantdocumenten komen er alleen bij als de vraag die klant noemt (vertrouwelijkheid).
3. **Signalen per document:** leeftijd, eigenaar, afdeling, eigenaar actief, aantal reviewers, versie, inkomende links, PageRank, TrustRank,
   clustering, aandeel links buiten het eigen cluster, conflict met andere documenten, vervangen, tekstoverlap.
4. **ML-model (XGBoost):** voorspelt de kans dat een document onbetrouwbaar is. ML-score = 100 × (1 − die kans).
5. **Expertise:** personalized PageRank op het personennetwerk geeft de auteur een expert-score (0-1) voor het onderwerp of de klant. Niet meer actief = 0.
6. **Trust Score** = {1 - EXPERT_WEIGHT:.0%} × ML-score + {EXPERT_WEIGHT:.0%} × 100 × expert-score.
7. **Context:** ander land = × {SCOPE_PENALTY}. Algemeen document bij een vraag over een klant = × {GENERIC_PENALTY}.
8. **Sorteren en kleuren:** groen vanaf {GREEN}, geel vanaf {YELLOW}. Conflicten en uitleg per document. Is alles onder {YELLOW}, dan komt de expert-suggestie (alleen actieve mensen).
""")


def main():
    engine = get_engine()
    st.title("🧭 Trusted Knowledge")
    st.caption("Find it. Understand it. Trust it. — gesimuleerde data, proof of concept")
    country_choice = st.sidebar.selectbox("Land", ["Automatisch", "Alle", *COUNTRIES])
    client_choice = st.sidebar.selectbox("Klant", ["Automatisch", "Geen", *engine.client_names.values()])
    st.sidebar.caption(f"{len(engine.docs)} documenten · {len(engine.persons)} personen · "
                       f"{len(engine.client_names)} klanten · gesimuleerd")
    t1, t2, t3 = st.tabs(["Zoeken", "Kennisgraaf en risico's", "Validatie en methode"])
    with t1:
        search_tab(engine, country_choice, client_choice)
    with t2:
        insights_tab(engine)
    with t3:
        validation_tab(engine)


main()
