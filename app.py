"""Streamlit front-end: trusted knowledge search with explainable trust scores."""
import html

import pandas as pd
import streamlit as st
from pyvis.network import Network

import feedback
from query_parser import lookup_documents, parse_query
from seed_data import COUNTRIES
from trust_engine import EXPERT_WEIGHT, GENERIC_PENALTY, GREEN, SCOPE_PENALTY, YELLOW, TrustEngine

st.set_page_config(page_title="GRAPHLAS", layout="wide")

# Brand palette sampled from the SD Worx logo (blue, red, yellow); green is only used for "reliable".
BLUE, RED, YELLOW_HEX, GREEN_HEX = "#0868D8", "#E80828", "#F8B808", "#1E9E5A"
INK, MUTED, TINT = "#111111", "#5B6776", "#EAF5FF"
STATUS = {"green": (GREEN_HEX, "#FFFFFF", "Reliable"), "yellow": (YELLOW_HEX, INK, "Verify"),
          "red": (RED, "#FFFFFF", "Unreliable")}

TOPIC_EN = {
    "T_ouderschapsverlof": "Parental leave", "T_ziekteverlof": "Sick leave and guaranteed pay",
    "T_vakantiegeld": "Holiday pay", "T_loonberekening": "Payroll calculation and cut-off",
    "T_bedrijfswagen": "Company cars and benefit in kind", "T_pensioen": "Retirement age and schemes",
    "T_gdpr_loon": "Payroll record retention (GDPR)", "T_klant_onboarding": "Customer onboarding",
    "T_dertiende_maand": "Year-end bonus and 13th month", "T_maaltijdcheques": "Meal vouchers and allowances",
    "T_overuren": "Overtime and premiums", "T_opzegtermijn": "Notice period",
    "T_thuiswerk": "Home-working allowance", "T_loopbaanonderbreking": "Career break and sabbatical",
    "T_mobiliteitsbudget": "Mobility budget and commuting", "T_jaarlijks_verlof": "Annual leave",
}
TYPE_EN = {"policy": "Policy", "manual": "Manual", "checklist": "Checklist",
           "chat": "Chat thread", "email": "Email", "analysis": "Analysis"}
EXAMPLES = ["How much parental leave do I get in Belgium?", "What is the retirement age in Belgium?",
            "What is the payroll cut-off for Nike in Belgium?"]
EDGE_STYLE = {"WROTE": (BLUE, "wrote"), "REVIEWS": (GREEN_HEX, "reviewed"),
              "LINKS_TO": ("#9AA5B1", "links to"), "SUPERSEDES": (RED, "replaces")}
KEYWORD_HELP = """**Ask in your own words, or use keywords.** A topic plus an optional country and customer is enough.

| Topic | Keywords |
|---|---|
| Parental leave | parental leave, maternity, paternity |
| Sick leave | sick leave, sick pay |
| Holiday pay | holiday pay, vacation pay |
| Payroll cut-off | payroll, cut-off |
| Company cars | company car, benefit in kind |
| Retirement | retirement, pension |
| Record retention | data retention, GDPR |
| Customer onboarding | customer onboarding, go-live |
| Year-end bonus | year-end bonus, 13th month |
| Meal vouchers | meal voucher, meal allowance |
| Overtime | overtime |
| Notice period | notice period |
| Home working | home working, remote work |
| Career break | career break, sabbatical |
| Mobility budget | mobility budget, commuting |
| Annual leave | annual leave, vacation days |

**Countries:** Belgium (BE), Netherlands (NL), Germany (DE)  
**Customers:** Nike, AS Adventure, Decathlon, Zalando

Examples: *parental leave Belgium*, *payroll cut-off Nike BE*, *mobility budget Decathlon*. Dutch keywords also work."""
METHOD = {"llm": "AI model", "keyword": "keywords", "none": "none"}

st.markdown(f"""
<style>
.block-container {{ padding-top: 2.2rem; max-width: 1100px; }}
h1, h2, h3 {{ color: {INK}; letter-spacing: -0.01em; }}
.tk-rule {{ height: 4px; width: 120px; margin: .2rem 0 1.4rem 0;
  background: linear-gradient(90deg, {BLUE} 0 34%, {RED} 34% 67%, {YELLOW_HEX} 67% 100%); border-radius: 2px; }}
.tk-sub {{ color: {MUTED}; margin-top: -.4rem; }}
.tk-legend {{ display: flex; flex-wrap: wrap; gap: .6rem 1.2rem; align-items: center; background: {TINT};
  padding: .7rem 1rem; border-radius: 8px; margin: .6rem 0 1.2rem 0; font-size: .92rem; }}
.tk-legend .muted {{ color: {MUTED}; flex-basis: 100%; font-size: .85rem; }}
.tk-dot {{ display: inline-block; width: .65rem; height: .65rem; border-radius: 50%; margin-right: .45rem; }}
.tk-pill {{ display: inline-block; padding: .3rem .85rem; border-radius: 999px; font-weight: 700; font-size: 1.05rem; }}
.tk-score {{ text-align: right; }}
.tk-score small {{ display: block; color: {MUTED}; margin-top: .2rem; }}
.tk-meta {{ color: {MUTED}; font-size: .88rem; }}
.tk-reasons {{ list-style: none; padding-left: 0; margin: 0; }}
.tk-reasons li {{ padding: .22rem 0; }}
.tk-expert {{ border-left: 4px solid {BLUE}; background: {TINT}; padding: .8rem 1rem; border-radius: 4px; margin-top: .8rem; }}
.tk-expert b {{ color: {BLUE}; }}
</style>
""", unsafe_allow_html=True)


@st.cache_resource(show_spinner="Loading knowledge graph...")
def get_engine():
    return TrustEngine()


def status_color(t):
    return STATUS["green" if t >= GREEN else "yellow" if t >= YELLOW else "red"][0]


def display_title(engine, d):
    doc = engine.docs.loc[d]
    client = f" - {engine.client_names[doc.client]}" if doc.client else ""
    return f"{TYPE_EN[doc.doc_type]}: {TOPIC_EN[doc.topic_id]} ({doc.country}){client} v{doc.version}"


def demo_users(engine):
    """Simulated sign-in. Access to customer documents follows who manages that customer."""
    managers = {c: m for m, c, k in engine.g.edges(data="etype") if k == "MANAGES_CLIENT"}
    users = {}
    for c, p in ((c, managers[c]) for c in engine.client_names if c in managers):
        label = f"{engine.person_name(p)}, {engine.persons.role[p]} ({engine.client_names[c]})"
        users[label] = (p, frozenset({c}), False)
    hr = "P01"
    users[f"{engine.person_name(hr)}, {engine.persons.role[hr]} (no customer access)"] = (hr, frozenset(), False)
    users["Knowledge manager (all customers)"] = ("KM", frozenset(engine.client_names), True)
    return users


def cast_vote(engine, allowed, user_id, doc_id, vote):
    feedback.cast(engine.docs, allowed, user_id, doc_id, vote)


def legend():
    chips = "".join(
        f"<span><span class='tk-dot' style='background:{c}'></span><b>{rng}</b>&nbsp; {label}</span>"
        for c, rng, label in [(GREEN_HEX, f"{GREEN} - 100", "Reliable"),
                              (YELLOW_HEX, f"{YELLOW} - {GREEN - 1}", "Verify before use"),
                              (RED, f"0 - {YELLOW - 1}", "Unreliable")])
    st.markdown(f"<div class='tk-legend'>{chips}<span class='muted'>The Trust Score (0-100) combines how recent a document is, "
                f"whether it has an owner and reviews, whether other sources contradict it, and how expert its author is. "
                f"Open &quot;Why this score?&quot; on any result for the details.</span></div>", unsafe_allow_html=True)


def render_result(engine, r, user):
    bg, fg, label = STATUS[r["badge"]]
    with st.container(border=True):
        c1, c2 = st.columns([5, 1])
        client = f" &middot; {html.escape(engine.client_names[r['client']])}" if r["client"] else ""
        c1.markdown(f"**{html.escape(display_title(engine, r['doc_id']))}**  \nStated value: {html.escape(r['key_value'])}")
        c1.markdown(f"<span class='tk-meta'>{r['country']}{client} &middot; {r['doc_id']}</span>", unsafe_allow_html=True)
        c2.markdown(f"<div class='tk-score'><span class='tk-pill' style='background:{bg};color:{fg}'>{r['trust']:.0f}</span>"
                    f"<small>{label}</small></div>", unsafe_allow_html=True)
        with st.expander("Why this score?"):
            items = "".join(
                f"<li><span class='tk-dot' style='background:{GREEN_HEX if s > 0 else RED if s < 0 else '#9AA5B1'}'></span>"
                f"{html.escape(text)}</li>" for s, text in r["reasons"])
            st.markdown(f"<ul class='tk-reasons'>{items}</ul>", unsafe_allow_html=True)
        uid, allowed, _ = user
        d, mine = r["doc_id"], feedback.user_vote(r["doc_id"], user[0])
        confirms, flags = feedback.counts(d)
        b1, b2, b3 = st.columns([1.3, 1.7, 5], vertical_alignment="center")
        b1.button("Confirmed" if mine == "confirm" else "Confirm", key=f"confirm_{d}", width="stretch",
                  type="primary" if mine == "confirm" else "secondary",
                  on_click=cast_vote, args=(engine, allowed, uid, d, "confirm"))
        b2.button("Flagged" if mine == "flag" else "Flag as wrong", key=f"flag_{d}", width="stretch",
                  type="primary" if mine == "flag" else "secondary",
                  on_click=cast_vote, args=(engine, allowed, uid, d, "flag"))
        b3.markdown(f"<span class='tk-meta'>{confirms} confirmed, {flags} flagged by colleagues. "
                    f"Feedback moves the score; click again to undo.</span>", unsafe_allow_html=True)


def build_graph(engine, doc_ids, with_people=True, height="520px"):
    """pyvis graph of the given documents (+ their authors/reviewers). Built from our own data only."""
    net = Network(height=height, width="100%", directed=True, cdn_resources="remote")
    ids = set(doc_ids)
    for d in ids:
        t = engine.scores.trust[d]
        net.add_node(d, label=d, color=status_color(t), size=12 + 400 * engine.pagerank[d],
                     title=html.escape(f"{display_title(engine, d)}: {engine.scores.key_value[d]} (trust score {t:.0f})"))
    people = set()
    for u, v, k in engine.g.edges(data="etype"):
        if k in ("LINKS_TO", "SUPERSEDES") and u in ids and v in ids:
            net.add_edge(u, v, color=EDGE_STYLE[k][0], title=EDGE_STYLE[k][1], dashes=(k == "SUPERSEDES"))
        elif with_people and k in ("WROTE", "REVIEWS") and v in ids:
            if u not in people:
                active = bool(engine.persons.active[u])
                net.add_node(u, label=engine.person_name(u), shape="diamond", size=14,
                             color=BLUE if active else "#B0B8C2",
                             title=html.escape(f"{engine.person_name(u)} ({'active' if active else 'no longer with the company'})"))
                people.add(u)
            net.add_edge(u, v, color=EDGE_STYLE[k][0], title=EDGE_STYLE[k][1])
    return net.generate_html()


def search_tab(engine, country_choice, client_choice, user):
    if "q" not in st.session_state:
        st.session_state.q = ""
    cols = st.columns(len(EXAMPLES))
    for col, ex in zip(cols, EXAMPLES):
        if col.button(ex, width="stretch"):
            st.session_state.q = ex
    box, info = st.columns([12, 1], vertical_alignment="center")
    q = box.text_input("Ask a question", key="q", max_chars=300, label_visibility="collapsed",
                       placeholder="Ask a question, e.g. How much parental leave do I get in Belgium?")
    with info.popover("Info", icon=":material/info:"):
        st.markdown(KEYWORD_HELP)
    legend()
    if not q.strip():
        return
    intent = parse_query(q)
    if not intent["api_ok"] and len(q.split()) > 4:  # only for free sentences, not for plain keywords
        st.warning("API not working, so your question was searched by keywords. "
                   "Use keywords from the Info button for the best results.")
    if not intent["topic_id"]:
        st.warning("I could not recognise the topic. Try one of: " + ", ".join(TOPIC_EN.values()))
        return
    country = intent["country"] if country_choice == "Auto-detect" else (None if country_choice == "All" else country_choice)
    client_ids = {v: k for k, v in engine.client_names.items()}
    client = intent["client"] if client_choice == "Auto-detect" else (None if client_choice == "None" else client_ids[client_choice])
    allowed = user[1]
    if client and client not in allowed:
        st.error(f"You do not have access to {engine.client_names[client]} documents. "
                 "Switch user in the sidebar (demo sign-in) to a person who manages this customer.")
        return
    st.session_state.last_topic = intent["topic_id"]
    st.caption(f"Understood: {TOPIC_EN[intent['topic_id']]}  |  Country: {country or 'all'}  |  "
               f"Customer: {engine.client_names.get(client, 'none')}  |  Interpreted by: {METHOD[intent['method']]}")
    doc_ids = lookup_documents(engine.g, {**intent, "client": client}, allowed)
    ranked = engine.rank(doc_ids, country, client, {d: feedback.adjustment(d) for d in doc_ids})
    in_scope = [r for r in ranked if r["in_scope"]][:8]
    other = [r for r in ranked if not r["in_scope"]][:5]
    results = in_scope or other
    values = {}
    for r in in_scope:
        values.setdefault((r["client"], r["country"]), set()).add(r["key_value"])
    for (c, land), vals in values.items():
        if len(vals) > 1:
            who = f"{engine.client_names[c]}, " if c else ""
            st.error(f"Sources disagree ({who}{land}): " + "  vs  ".join(sorted(vals)))
    st.markdown("#### Results, highest trust first")
    for r in results:
        render_result(engine, r, user)
    if in_scope and other:
        with st.expander(f"Documents for other countries ({len(other)})"):
            for r in other:
                render_result(engine, r, user)
    if not in_scope or max(r["trust"] for r in in_scope) < YELLOW:
        ex = engine.suggest_expert(intent["topic_id"], client)
        st.markdown(f"<div class='tk-expert'><b>Not sure? Ask this expert.</b><br>{html.escape(ex['name'])} &middot; "
                    f"{html.escape(ex['role'])} &middot; {html.escape(ex['department'])} ({ex['country']})</div>",
                    unsafe_allow_html=True)
    with st.expander("Knowledge graph for this search"):
        st.caption("Diamond = person (grey = no longer with the company). Circle = document (colour = trust score, "
                   "size = how often it is linked). Blue line = wrote, green = reviewed, grey = links to, red dashed = replaces.")
        st.iframe(build_graph(engine, [r["doc_id"] for r in results]), height=540)


def graph_tab(engine):
    topics = list(TOPIC_EN)
    idx = topics.index(st.session_state.get("last_topic", topics[0]))
    topic = st.selectbox("Topic (follows your last search)", topics, index=idx, format_func=TOPIC_EN.get)
    st.caption("All general documents on this topic. Colour = trust score, size = how often a document is linked. "
               "A large red circle is popular but unreliable.")
    docs = engine.docs[(engine.docs.topic_id == topic) & (engine.docs.client == "")].index
    st.iframe(build_graph(engine, docs, with_people=False), height=540)
    st.subheader("Knowledge risks by topic")
    risks = engine.topic_risks()
    risks["topic"] = risks.pop("topic_id").map(TOPIC_EN)
    risks["bus-factor risk"] = risks["bus-factor risk"].map({True: "Yes", False: "No"})
    st.caption("Bus-factor risk: the knowledge on a topic depends on one person, or on someone who has left.")
    st.dataframe(risks[["topic", "documents", "active authors", "top author", "top author share", "bus-factor risk"]],
                 hide_index=True, width="stretch")
    st.subheader("Experts for this topic")
    ex = pd.DataFrame([{"name": engine.persons.name[p], "department": engine.persons.department[p],
                        "active": "Yes" if engine.persons.active[p] else "No", "expertise score": round(s, 2)}
                       for p, s in sorted(engine.expert[topic].items(), key=lambda kv: -kv[1])[:6]])
    st.dataframe(ex, hide_index=True, width="stretch")


def method_tab(engine, user):
    st.subheader("How the Trust Score is calculated")
    st.markdown(f"""
1. **Understand the question.** The topic, country and customer are extracted from the question and checked against fixed lists.
2. **Retrieve candidates.** A fixed lookup returns the documents on that topic. Customer documents are only included when the question names that customer.
3. **Measure signals.** For each document: age, owner, department, whether the owner is still active, reviews, version, how often it is linked, trust inherited from verified documents, contradictions with other documents, and whether it has been replaced.
4. **Estimate reliability.** The signals are combined into a reliability score, learned from (simulated) user feedback about documents that turned out to be wrong or outdated.
5. **Add author expertise** ({EXPERT_WEIGHT:.0%} of the score). Expertise comes from who writes, reviews and is linked on the topic. Authors who have left count as zero.
6. **Adjust for context.** A document for another country is multiplied by {SCOPE_PENALTY}. A general policy, when the question is about a specific customer, is multiplied by {GENERIC_PENALTY}.
7. **Sort and label.** Results are ordered from highest to lowest score. {GREEN}-100 is reliable, {YELLOW}-{GREEN - 1} needs verification, below {YELLOW} is unreliable. If nothing scores above {YELLOW}, the most relevant active expert is suggested.
""")
    st.subheader("Is the top result really the right one?")
    st.markdown("The simulated data contains a hidden ground truth: does a document state the current value or an outdated one? "
                "That truth is never used to calculate scores. For every group of documents (same topic, country and customer) "
                "that contains both correct and outdated documents, we check whether the top-ranked one is correct. "
                "The ranking is scored on documents it was not trained on.")
    _, per_group = engine.evaluate()
    visible = {"-"} | {engine.client_names[c] for c in user[1]}
    per_group = per_group[per_group.customer.isin(visible)]
    summary = {"groups": len(per_group), **{k: float(per_group[k].mean())
                                            for k in ["ranking", "newest", "most_linked", "random"]}}
    c = st.columns(4)
    c[0].metric("Our ranking", f"{summary['ranking']:.0%}")
    c[1].metric("Newest document", f"{summary['newest']:.0%}")
    c[2].metric("Most linked document", f"{summary['most_linked']:.0%}")
    c[3].metric("Random pick", f"{summary['random']:.0%}")
    st.caption(f"Share of groups where the top result is correct, across {summary['groups']} groups.")
    st.info("Limitation: the data is simulated. This shows the approach can recognise the right document, not how well it performs "
            "in a real organisation. Real validation needs expert review and user feedback.")
    with st.expander("Results per group"):
        t = per_group.copy()
        t["topic"] = t.pop("topic_id").map(TOPIC_EN)
        for k in ("ranking", "newest", "most_linked"):
            t[k] = t[k].map({1: "correct", 0: "wrong"})
        t["random"] = t["random"].map("{:.0%}".format)
        t = t.rename(columns={"ranking": "our ranking", "newest": "newest document",
                              "most_linked": "most linked", "random": "chance of a correct pick"})
        st.dataframe(t[["topic", "country", "customer", "documents", "our ranking", "newest document",
                        "most linked", "chance of a correct pick"]], hide_index=True, width="stretch")


def main():
    engine = get_engine()
    st.title("GRAPHLAS")
    st.markdown("<div class='tk-rule'></div>", unsafe_allow_html=True)
    st.markdown("<p class='tk-sub'>Find it. Understand it. Trust it.</p>",
                unsafe_allow_html=True)
    users = demo_users(engine)
    st.sidebar.header("Signed in as")
    user = users[st.sidebar.selectbox("Demo sign-in", list(users), label_visibility="collapsed")]
    st.sidebar.caption("Customer documents are only visible to people who manage that customer.")
    st.sidebar.header("Filters")
    country_choice = st.sidebar.selectbox("Country", ["Auto-detect", "All", *COUNTRIES])
    client_choice = st.sidebar.selectbox("Customer", ["Auto-detect", "None",
                                                      *[engine.client_names[c] for c in engine.client_names if c in user[1]]])
    st.sidebar.caption(f"{len(engine.docs[engine.docs.client == ''])} general documents, {len(engine.persons)} people, "
                       f"{len(user[1])} customer(s) accessible (simulated)")
    if user[2] and st.sidebar.button("Reset colleague feedback"):  # knowledge managers only
        feedback.reset()
    t1, t2, t3 = st.tabs(["Search", "Knowledge graph", "Method and validation"])
    with t1:
        search_tab(engine, country_choice, client_choice, user)
    with t2:
        graph_tab(engine)
    with t3:
        method_tab(engine, user)


main()
