"""Streamlit front-end: trusted knowledge search with explainable trust scores."""
import html

import pandas as pd
import streamlit as st
from pyvis.network import Network

from query_parser import lookup_documents, parse_query
from seed_data import COUNTRIES, TOPICS
from trust_engine import GREEN, YELLOW, TrustEngine

st.set_page_config(page_title="Trusted Knowledge", page_icon="🧭", layout="wide")

ICON = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
HEX = {"green": "#2e9e5b", "yellow": "#e0a800", "red": "#d64545"}
LABEL = {"green": "Betrouwbaar", "yellow": "Controleer", "red": "Onbetrouwbaar"}
TOPIC_NAMES = {f"T_{k}": v[0] for k, v in TOPICS.items()}
EXAMPLES = ["Hoeveel ouderschapsverlof krijg ik in België?", "Wat is de pensioenleeftijd in België?",
            "Hoe werkt de bedrijfswagen in België?"]


@st.cache_resource(show_spinner="Trust engine opbouwen...")
def get_engine():
    return TrustEngine()


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


def graph_html(engine, topic_id):
    net = Network(height="520px", width="100%", directed=True, cdn_resources="remote")
    docs = engine.docs[engine.docs.topic_id == topic_id].index
    for d in docs:
        t = engine.scores.trust[d]
        net.add_node(d, label=d, color=HEX[("green" if t >= GREEN else "yellow" if t >= YELLOW else "red")],
                     size=12 + 400 * engine.pagerank[d],
                     title=html.escape(f"{engine.scores.title[d]}: {engine.scores.key_value[d]} (trust {t:.0f})"))
    for u, v in engine.doc_graph.subgraph(docs).edges:
        net.add_edge(u, v, color="#999999")
    return net.generate_html()


def search_tab(engine, country_choice):
    if "q" not in st.session_state:
        st.session_state.q = ""
    cols = st.columns(len(EXAMPLES))
    for col, ex in zip(cols, EXAMPLES):
        if col.button(ex, width='stretch'):
            st.session_state.q = ex
    q = st.text_input("Stel een vraag", key="q", max_chars=300, placeholder="Bijv. Hoeveel ouderschapsverlof krijg ik in België?")
    if not q.strip():
        return
    intent = parse_query(q)
    if not intent["topic_id"]:
        st.warning("Ik snap het onderwerp niet. Probeer: " + ", ".join(TOPIC_NAMES.values()))
        return
    country = intent["country"] if country_choice == "Automatisch" else (None if country_choice == "Alle" else country_choice)
    st.caption(f"Begrepen: **{TOPIC_NAMES[intent['topic_id']]}** · land: **{country or 'alle'}** · via {intent['method']}")
    results = engine.rank(lookup_documents(engine.g, intent), country)[:6]
    in_scope = [r for r in results if r["in_scope"]]
    values = {r["key_value"] for r in in_scope}
    if len(values) > 1:
        st.error("Bronnen spreken elkaar tegen: " + " ↔ ".join(sorted(values)))
    for r in results:
        render_result(r)
    if not in_scope or max(r["trust"] for r in in_scope) < YELLOW:
        ex = engine.suggest_expert(intent["topic_id"])
        st.info(f"**Informatie onzeker? Vraag het aan deze expert.**  \n"
                f"{ex['name']} · {ex['role']} · {ex['department']} ({ex['country']})")


def insights_tab(engine):
    topic = st.selectbox("Onderwerp", list(TOPIC_NAMES), format_func=TOPIC_NAMES.get)
    st.caption("Kleur = trust score, grootte = populariteit (PageRank). Een groot rood punt is populair maar onbetrouwbaar.")
    st.iframe(graph_html(engine, topic), height=540)
    st.subheader("Kennisrisico's per onderwerp")
    st.dataframe(engine.topic_risks(), hide_index=True, width='stretch')
    st.subheader("Experts voor dit onderwerp")
    ex = pd.DataFrame([{"naam": engine.persons.name[p], "afdeling": engine.persons.department[p],
                        "actief": bool(engine.persons.active[p]), "expert-score": round(s, 2)}
                       for p, s in sorted(engine.expert[topic].items(), key=lambda kv: -kv[1])[:6]])
    st.dataframe(ex, hide_index=True, width='stretch')


def main():
    engine = get_engine()
    st.title("🧭 Trusted Knowledge")
    st.caption("Find it. Understand it. Trust it. — gesimuleerde data, proof of concept")
    country_choice = st.sidebar.selectbox("Land", ["Automatisch", "Alle", *COUNTRIES])
    st.sidebar.metric("Model AUC (gesimuleerd)", f"{engine.cv_auc:.2f}")
    t1, t2 = st.tabs(["Zoeken", "Kennisgraaf en risico's"])
    with t1:
        search_tab(engine, country_choice)
    with t2:
        insights_tab(engine)


main()
