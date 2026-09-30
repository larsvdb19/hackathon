"""Dummy knowledge graph for the SD Worx hackathon PoC.

ALL DATA IS SIMULATED. Policy values are illustrative, not real legal advice.

Run `python seed_data.py` to (re)generate the CSV files in `data/`:
    persons.csv, topics.csv, documents.csv, edges.csv, feedback.csv
Other modules use `load_graph()` to get a networkx MultiDiGraph.

Graph model
    nodes:  Person (P01..), Document (D001..), Topic (T_<name>); node attr `ntype`
    edges:  WROTE (person->doc), REVIEWS (person->doc), LINKS_TO (doc->doc),
            BELONGS_TO_TOPIC (doc->topic), SUPERSEDES (newer doc->older doc); edge attr `etype`
    LINKS_TO is sometimes reciprocal (Obsidian-style backlinks).

`feedback.csv` = simulated user feedback (views, "wrong/outdated" flags) used as
training label `unreliable` for the trust model. The hidden ground truth (is the
stated value outdated?) is deliberately NOT saved in documents.csv, so the model
cannot simply read it off.

Planted demo scenarios (fixed ids)
    D901-D905  ouderschapsverlof BE: current verified policy, outdated policy that is
               still heavily linked, mis-scoped NL doc, ownerless Teams chat that
               contradicts the policy, correct-but-stale ownerless manual.
    D911-D913  pensioen BE: every doc old, author P15 has LEFT the company;
               only P12 (active reviewer) can still be asked -> expert fallback demo.
    D921-D926  bedrijfswagen BE: echo chamber of chats/mails that only link each other.
    bedrijfswagen overall: single expert P06 (bus-factor risk).
"""
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).parent / "data"
REFERENCE_DATE = pd.Timestamp("2026-09-30")
SEED = 42
COUNTRIES = ["BE", "NL", "DE"]

# topic_id -> (display name, home department)
TOPICS = {
    "ouderschapsverlof": ("Ouderschapsverlof", "HR Advisory"),
    "ziekteverlof": ("Ziekteverlof en gewaarborgd loon", "HR Advisory"),
    "vakantiegeld": ("Vakantiegeld", "Payroll"),
    "loonberekening": ("Loonberekening en cut-off", "Payroll"),
    "bedrijfswagen": ("Bedrijfswagen en voordeel alle aard", "Payroll"),
    "pensioen": ("Pensioenleeftijd en regeling", "Legal & Compliance"),
    "gdpr_loon": ("Bewaartermijn loonadministratie (GDPR)", "Legal & Compliance"),
    "klant_onboarding": ("Klant-onboarding", "Customer Success"),
}

# topic -> country -> (current value, outdated value)
VALUES = {
    "ouderschapsverlof": {"BE": ("4 maanden per ouder", "3 maanden per ouder"),
                          "NL": ("26 weken per ouder", "13 weken per ouder"),
                          "DE": ("36 maanden Elternzeit", "24 maanden Elternzeit")},
    "ziekteverlof": {"BE": ("30 dagen gewaarborgd loon", "14 dagen gewaarborgd loon"),
                     "NL": ("104 weken doorbetaling", "52 weken doorbetaling"),
                     "DE": ("6 weken Entgeltfortzahlung", "4 weken Entgeltfortzahlung")},
    "vakantiegeld": {"BE": ("92 procent dubbel vakantiegeld", "85 procent dubbel vakantiegeld"),
                     "NL": ("8 procent vakantiegeld", "7 procent vakantiegeld"),
                     "DE": ("geen wettelijk vakantiegeld", "1 maandsalaris vakantiegeld")},
    "loonberekening": {"BE": ("cut-off op de 20e", "cut-off op de 15e"),
                       "NL": ("cut-off op de 18e", "cut-off op de 12e"),
                       "DE": ("cut-off op de 22e", "cut-off op de 25e")},
    "bedrijfswagen": {"BE": ("CO2-gebonden VAA-formule", "brandstofgebonden VAA-formule"),
                      "NL": ("bijtelling 22 procent", "bijtelling 25 procent"),
                      "DE": ("1-procent-regel", "0,5-procent-regel")},
    "pensioen": {"BE": ("pensioenleeftijd 67 jaar", "pensioenleeftijd 65 jaar"),
                 "NL": ("AOW-leeftijd 67 jaar", "AOW-leeftijd 66 jaar"),
                 "DE": ("regelaltersgrenze 67 jaar", "regelaltersgrenze 65 jaar")},
    "gdpr_loon": {"BE": ("bewaartermijn 7 jaar", "bewaartermijn 5 jaar"),
                  "NL": ("bewaartermijn 7 jaar", "bewaartermijn 2 jaar"),
                  "DE": ("bewaartermijn 10 jaar", "bewaartermijn 6 jaar")},
    "klant_onboarding": {"BE": ("onboarding in 10 werkdagen", "onboarding in 20 werkdagen"),
                         "NL": ("onboarding in 10 werkdagen", "onboarding in 15 werkdagen"),
                         "DE": ("onboarding in 12 werkdagen", "onboarding in 25 werkdagen")},
}

# (person_id, name, department, country, role, active)
PERSONS = [
    ("P01", "Sofie Peeters", "HR Advisory", "BE", "Senior HR Advisor", True),
    ("P02", "Thomas Maes", "HR Advisory", "BE", "HR Advisor", True),
    ("P03", "Lotte de Vries", "HR Advisory", "NL", "HR Advisor", True),
    ("P04", "Jonas Becker", "HR Advisory", "DE", "HR Advisor", True),
    ("P05", "Emma Claes", "HR Advisory", "BE", "HR Advisor", True),
    ("P06", "Pieter Wouters", "Payroll", "BE", "Payroll Specialist", True),
    ("P07", "Nina Smit", "Payroll", "NL", "Payroll Specialist", True),
    ("P08", "Lukas Schmidt", "Payroll", "DE", "Payroll Specialist", True),
    ("P09", "Karel Mertens", "Payroll", "BE", "Payroll Specialist", False),
    ("P10", "Ines Jacobs", "Payroll", "BE", "Payroll Specialist", True),
    ("P11", "Marie Dubois", "Payroll", "BE", "Payroll Analyst", True),
    ("P12", "An Willems", "Legal & Compliance", "BE", "Legal Counsel", True),
    ("P13", "Bram Visser", "Legal & Compliance", "NL", "Legal Counsel", True),
    ("P14", "Hanna Weber", "Legal & Compliance", "DE", "Legal Counsel", True),
    ("P15", "Gert Hermans", "Legal & Compliance", "BE", "Senior Legal Counsel", False),
    ("P16", "Laura Goossens", "Customer Success", "BE", "Customer Success Lead", True),
    ("P17", "Daan Bakker", "Customer Success", "NL", "Customer Success Manager", True),
    ("P18", "Felix Wagner", "Customer Success", "DE", "Customer Success Manager", True),
    ("P19", "Yasmine El Amrani", "Customer Success", "BE", "Customer Success Manager", True),
    ("P20", "Tom Claessens", "Customer Success", "BE", "Customer Success Manager", True),
    ("P21", "Elise Vermeulen", "Payroll", "BE", "Payroll Specialist", True),
    ("P22", "Stijn Dewit", "Customer Success", "BE", "Implementation Consultant", True),
    ("P23", "Julia Fischer", "Legal & Compliance", "DE", "Legal Counsel", True),
    ("P24", "Robin Lambert", "HR Advisory", "BE", "Junior HR Advisor", True),
]

# topic -> experts, primary first (writes most documents on the topic)
TOPIC_EXPERTS = {
    "ouderschapsverlof": ["P01", "P02", "P05"],
    "ziekteverlof": ["P02", "P03", "P04"],
    "vakantiegeld": ["P06", "P07", "P21"],
    "loonberekening": ["P07", "P08", "P10"],
    "bedrijfswagen": ["P06"],  # bus factor: one expert only
    "pensioen": ["P15", "P12"],  # primary expert has left
    "gdpr_loon": ["P12", "P13", "P14", "P23"],
    "klant_onboarding": ["P16", "P19", "P20", "P22"],
}
AUTHOR_WEIGHTS = [0.6, 0.25, 0.1, 0.05]

DOC_TYPES = ["policy", "manual", "checklist", "chat", "email", "analysis"]
DOC_TYPE_WEIGHTS = [0.3, 0.25, 0.15, 0.1, 0.1, 0.1]
DOC_TYPE_LABEL = {"policy": "Beleid", "manual": "Handleiding", "checklist": "Checklist",
                  "chat": "Teams-gesprek", "email": "E-mail", "analysis": "Analyse"}
FILLER = {
    "policy": "Officieel beleid, goedgekeurd door de afdeling.",
    "manual": "Stap-voor-stap handleiding voor medewerkers.",
    "checklist": "Checklist om niets te vergeten bij de verwerking.",
    "chat": "Informele uitleg uit een Teams-kanaal, niet formeel bevestigd.",
    "email": "Doorgestuurde e-mail van een collega met uitleg.",
    "analysis": "Interne analyse met voorbeelden en randgevallen.",
}
OFFICIAL = ("policy", "manual")

# (topic, country) combos that are fully hand-crafted below
HAND_CRAFTED = {("ouderschapsverlof", "BE"), ("pensioen", "BE")}


def _sigmoid(x):
    return 1 / (1 + np.exp(-x))


def generate():
    """Build all tables. Returns dict of DataFrames."""
    rng = np.random.default_rng(SEED)
    persons = pd.DataFrame(PERSONS, columns=["person_id", "name", "department", "country", "role", "active"])
    active = dict(zip(persons.person_id, persons.active))
    person_dept = dict(zip(persons.person_id, persons.department))

    docs, truth = [], {}          # truth[doc_id] = stated value is outdated (hidden)
    reviews, links, supersedes = set(), set(), set()
    echo_ids = []
    counter = iter(range(1, 900))

    def add_doc(doc_id, topic, country, doc_type, age_days, old, author, owner, dept,
                verified=False, version=1):
        name = TOPICS[topic][0]
        value = VALUES[topic][country][1 if old else 0]
        modified = REFERENCE_DATE - pd.Timedelta(days=int(age_days))
        created = modified - pd.Timedelta(days=int(rng.integers(0, 400)) if version > 1 else 0)
        docs.append({
            "doc_id": doc_id,
            "title": f"{DOC_TYPE_LABEL[doc_type]}: {name} ({country}) v{version}",
            "doc_type": doc_type, "topic_id": f"T_{topic}", "country": country,
            "department": dept or "", "author_id": author, "owner_id": owner or "",
            "created": created.date().isoformat(), "last_modified": modified.date().isoformat(),
            "version": version, "key_value": value, "verified": bool(verified),
            "text": f"{name} ({country}). Regel: {value}. {FILLER[doc_type]}",
        })
        truth[doc_id] = bool(old)

    # ---- procedural documents -------------------------------------------------
    for topic, (_, home_dept) in TOPICS.items():
        experts = TOPIC_EXPERTS[topic]
        weights = np.array(AUTHOR_WEIGHTS[:len(experts)])
        weights = weights / weights.sum()
        for country in COUNTRIES:
            if (topic, country) in HAND_CRAFTED or (topic, country) == ("bedrijfswagen", "BE"):
                continue
            for _ in range(int(rng.integers(2, 5))):
                doc_type = str(rng.choice(DOC_TYPES, p=DOC_TYPE_WEIGHTS))
                age = int(np.clip(rng.gamma(1.5, 350) + 10, 10, 2000))
                old = rng.random() < 0.1 + 0.6 * min(age / 1500, 1)
                author = str(rng.choice(experts, p=weights)) if rng.random() > 0.15 \
                    else str(rng.choice(persons[persons.active].person_id))
                informal = doc_type in ("chat", "email")
                owner = None if rng.random() < (0.4 if informal else 0.12) else author
                dept = None if rng.random() < 0.15 else home_dept
                add_doc(f"D{next(counter):03d}", topic, country, doc_type, age, old,
                        author, owner, dept, version=int(rng.integers(1, 4)))

    # ---- hero 1: ouderschapsverlof BE ----------------------------------------
    hd = "HR Advisory"
    add_doc("D901", "ouderschapsverlof", "BE", "policy", 40, False, "P01", "P01", hd, True, 3)
    add_doc("D902", "ouderschapsverlof", "BE", "policy", 1800, True, "P01", "P01", hd, False, 1)
    add_doc("D903", "ouderschapsverlof", "NL", "policy", 120, False, "P03", "P03", hd, True, 2)
    add_doc("D904", "ouderschapsverlof", "BE", "chat", 520, True, "P05", None, None, False, 1)
    add_doc("D905", "ouderschapsverlof", "BE", "manual", 900, False, "P24", None, None, False, 1)
    reviews |= {("P02", "D901"), ("P05", "D901"), ("P02", "D902"), ("P03", "D903")}
    supersedes.add(("D901", "D902"))
    links |= {("D904", "D902"), ("D905", "D902"), ("D902", "D901"), ("D901", "D902")}

    # ---- hero 2: pensioen BE (all docs old, author has left) ------------------
    ld = "Legal & Compliance"
    add_doc("D911", "pensioen", "BE", "policy", 900, True, "P15", "P15", ld, False, 2)
    add_doc("D912", "pensioen", "BE", "manual", 1100, True, "P15", "P15", ld, False, 1)
    add_doc("D913", "pensioen", "BE", "analysis", 1400, True, "P15", "P15", ld, False, 1)
    reviews |= {("P12", "D911")}
    links |= {("D912", "D911"), ("D913", "D911")}

    # ---- hero 3: echo chamber, bedrijfswagen BE -------------------------------
    for i, doc_type in enumerate(["chat", "chat", "email", "chat", "email", "chat"]):
        did = f"D{921 + i}"
        add_doc(did, "bedrijfswagen", "BE", doc_type, int(rng.integers(500, 900)), True,
                "P09", None, None, False, 1)
        echo_ids.append(did)
    links |= {(echo_ids[i], echo_ids[(i + 1) % 6]) for i in range(6)}
    links |= {(echo_ids[(i + 1) % 6], echo_ids[i]) for i in range(0, 6, 2)}
    links |= {(echo_ids[0], echo_ids[3]), (echo_ids[2], echo_ids[5])}

    df = pd.DataFrame(docs)
    age_days = (REFERENCE_DATE - pd.to_datetime(df.last_modified)).dt.days
    df["age_days_"] = age_days
    by_id = df.set_index("doc_id")

    # ---- reviews and verification (procedural docs) ---------------------------
    hand_ids = {"D901", "D902", "D903", "D904", "D905", "D911", "D912", "D913"} | set(echo_ids)
    for row in df.itertuples():
        if row.doc_id in hand_ids:
            continue
        topic = row.topic_id[2:]
        p_review = 0.75 if row.doc_type in OFFICIAL else 0.05
        if rng.random() < p_review:
            pool = [p for p in TOPIC_EXPERTS[topic] if p != row.author_id and active[p]]
            if not pool:
                pool = [p for p in persons.person_id if active[p] and p != row.author_id
                        and person_dept[p] == TOPICS[topic][1]]
            reviews.add((str(rng.choice(pool)), row.doc_id))
    reviewed = {d for _, d in reviews}
    reviewer_of = {}
    for p, d in reviews:
        reviewer_of.setdefault(d, []).append(p)
    for i, row in df.iterrows():
        if row.doc_id in hand_ids:
            continue
        topic = row.topic_id[2:]
        expert_review = any(p in TOPIC_EXPERTS[topic] for p in reviewer_of.get(row.doc_id, []))
        df.at[i, "verified"] = bool(row.doc_type in OFFICIAL and expert_review
                                    and row.age_days_ < 500 and not truth[row.doc_id])

    # ---- links (topic-heavy => communities/silos) -----------------------------
    pool_ids = [d for d in df.doc_id if d not in echo_ids]
    topic_of = dict(zip(df.doc_id, df.topic_id))
    dept_of = dict(zip(df.doc_id, df.department))
    for d in pool_ids:
        for _ in range(int(rng.integers(0, 5))):
            r = rng.random()
            if r < 0.6:
                cand = [x for x in pool_ids if topic_of[x] == topic_of[d]]
            elif r < 0.8 and dept_of[d]:
                cand = [x for x in pool_ids if dept_of[x] == dept_of[d]]
            else:
                cand = pool_ids
            cand = [x for x in cand if x != d]
            if not cand:
                continue
            c = str(rng.choice(cand))
            links.add((d, c))
            if rng.random() < 0.25:
                links.add((c, d))
    # the outdated hero policy stays popular: other docs keep linking to it
    others = [d for d in pool_ids if topic_of[d] == "T_ouderschapsverlof" and d not in hand_ids]
    for d in others[:4]:
        links.add((d, "D902"))
    if others:
        links.add((others[-1], "D901"))

    # ---- supersedes between versions of the same (topic, country) -------------
    for _, g in df[~df.doc_id.isin(hand_ids | set(echo_ids))].groupby(["topic_id", "country"]):
        g = g.sort_values("last_modified")
        newest = g.iloc[-1]
        if truth[newest.doc_id]:
            continue
        for old_id in g[g.doc_id.map(truth)].doc_id:
            if rng.random() < 0.5:
                supersedes.add((newest.doc_id, old_id))

    # ---- edges ----------------------------------------------------------------
    rows = [(a, d, "WROTE") for d, a in zip(df.doc_id, df.author_id)]
    rows += [(p, d, "REVIEWS") for p, d in sorted(reviews)]
    rows += [(a, b, "LINKS_TO") for a, b in sorted(links) if a != b]
    rows += [(d, t, "BELONGS_TO_TOPIC") for d, t in zip(df.doc_id, df.topic_id)]
    rows += [(a, b, "SUPERSEDES") for a, b in sorted(supersedes)]
    edges = pd.DataFrame(rows, columns=["source", "target", "type"])

    # ---- simulated user feedback => training label ----------------------------
    in_deg = edges[edges.type == "LINKS_TO"].target.value_counts()
    fb = []
    for row in df.itertuples():
        no_owner = row.owner_id == ""
        inactive = not active[row.owner_id or row.author_id]
        old = truth[row.doc_id]
        logit = (-2.3 + 1.8 * old + 0.0012 * row.age_days_ + 0.9 * no_owner + 0.6 * inactive
                 + 0.8 * (old and no_owner) - 0.7 * row.verified
                 - 0.5 * (row.doc_id in reviewed) + rng.normal(0, 0.6))
        views = 20 + int(rng.poisson(8 * (1 + in_deg.get(row.doc_id, 0))))
        flags = int(rng.binomial(views, _sigmoid(logit) * 0.8))
        fb.append({"doc_id": row.doc_id, "views": views, "flags_wrong": flags,
                   "flag_rate": round(flags / views, 3), "unreliable": int(flags / views > 0.35)})

    topics = pd.DataFrame([(f"T_{k}", v[0], v[1]) for k, v in TOPICS.items()],
                          columns=["topic_id", "name", "department"])
    return {"persons": persons, "topics": topics,
            "documents": df.drop(columns="age_days_"), "edges": edges, "feedback": pd.DataFrame(fb)}


def save(tables):
    DATA_DIR.mkdir(exist_ok=True)
    for name, t in tables.items():
        t.to_csv(DATA_DIR / f"{name}.csv", index=False)


def load_graph():
    """Load the CSVs into a networkx MultiDiGraph (node attr `ntype`, edge attr `etype`)."""
    persons = pd.read_csv(DATA_DIR / "persons.csv")
    topics = pd.read_csv(DATA_DIR / "topics.csv")
    docs = pd.read_csv(DATA_DIR / "documents.csv", keep_default_na=False)
    edges = pd.read_csv(DATA_DIR / "edges.csv")
    g = nx.MultiDiGraph()
    for r in persons.to_dict("records"):
        g.add_node(r.pop("person_id"), ntype="Person", **r)
    for r in topics.to_dict("records"):
        g.add_node(r.pop("topic_id"), ntype="Topic", **r)
    for r in docs.to_dict("records"):
        r["last_modified"] = pd.Timestamp(r["last_modified"])
        r["created"] = pd.Timestamp(r["created"])
        g.add_node(r.pop("doc_id"), ntype="Document", **r)
    for r in edges.itertuples():
        g.add_edge(r.source, r.target, etype=r.type)
    return g


if __name__ == "__main__":
    tables = generate()
    save(tables)
    e, d, f = tables["edges"], tables["documents"], tables["feedback"]
    print("documents:", len(d), "| persons:", len(tables["persons"]), "| topics:", len(tables["topics"]))
    print(e.type.value_counts().to_string())
    print(f"unreliable label share: {f.unreliable.mean():.0%}")
    print(f"verified docs (TrustRank seeds): {int(d.verified.sum())}")
    print("saved to", DATA_DIR)
