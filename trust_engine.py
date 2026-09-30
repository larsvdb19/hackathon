"""Trust engine: graph metrics + text similarity -> XGBoost -> explainable Trust Score.

Pipeline
  1. Graph features per document: PageRank, TrustRank (personalised PageRank seeded on
     verified documents), clustering coefficient, Louvain communities (silo measure),
     in-degree.
  2. Metadata features: age (decay), missing owner/department, inactive owner, reviewers,
     version, superseded, conflict (same topic+country, different stated value),
     TF-IDF similarity to other documents on the topic.
  3. XGBoost (monotone constraints) predicts P(unreliable), trained on simulated user
     feedback. `verified` is NOT a feature, only a TrustRank seed.
  4. Person graph: personalised PageRank per topic = expert score; betweenness = bus factor.
  5. Trust Score = 85% ML score + 15% author expert score, then a scope (country) penalty.
  Explanations: XGBoost feature contributions (SHAP-style, via pred_contribs) + rule texts.
"""
import numpy as np
import pandas as pd
import networkx as nx
import xgboost as xgb
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import roc_auc_score
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from seed_data import DATA_DIR, REFERENCE_DATE, load_graph

FEATURES = ["age_days", "no_owner", "no_dept", "owner_inactive", "n_reviewers", "version",
            "in_degree", "pagerank", "trustrank", "clustering", "ext_link_ratio",
            "conflict_share", "superseded", "sim_max"]
MONOTONE = {"age_days": 1, "no_owner": 1, "owner_inactive": 1, "n_reviewers": -1,
            "trustrank": -1, "superseded": 1}
NICE = {"age_days": "leeftijd", "no_owner": "geen eigenaar", "no_dept": "geen afdeling",
        "owner_inactive": "eigenaar niet actief", "n_reviewers": "aantal reviewers",
        "version": "versienummer", "in_degree": "aantal inkomende links",
        "pagerank": "populariteit (PageRank)", "trustrank": "vertrouwen via links (TrustRank)",
        "clustering": "onderlinge clustering", "ext_link_ratio": "links buiten eigen cluster",
        "conflict_share": "conflict met andere documenten", "superseded": "vervangen door nieuwere versie",
        "sim_max": "overlap met ander document"}
EXPERT_WEIGHT = 0.15
GREEN, YELLOW = 70, 45
SCOPE_PENALTY = 0.6
GENERIC_PENALTY = 0.85


def badge(score):
    return "green" if score >= GREEN else "yellow" if score >= YELLOW else "red"


class TrustEngine:
    def __init__(self, graph=None):
        self.g = graph or load_graph()
        self.docs = pd.DataFrame([{"doc_id": n, **a} for n, a in self.g.nodes(data=True)
                                  if a["ntype"] == "Document"]).set_index("doc_id")
        self.persons = pd.DataFrame([{"person_id": n, **a} for n, a in self.g.nodes(data=True)
                                     if a["ntype"] == "Person"]).set_index("person_id")
        self.client_names = {n: a["name"] for n, a in self.g.nodes(data=True) if a["ntype"] == "Client"}
        self.reviewers = {}
        for u, v, k in self.g.edges(data="etype"):
            if k == "REVIEWS":
                self.reviewers.setdefault(v, []).append(u)
        self.superseded_by = {}
        for u, v, k in self.g.edges(data="etype"):
            if k == "SUPERSEDES":
                self.superseded_by.setdefault(v, []).append(u)
        self._graph_metrics()
        self._person_scores()
        self._features()
        self._fit()
        self._score()

    # ---- graph + person metrics --------------------------------------------------
    def _graph_metrics(self):
        dg = nx.DiGraph()
        dg.add_nodes_from(self.docs.index)
        dg.add_edges_from((u, v) for u, v, k in self.g.edges(data="etype") if k == "LINKS_TO")
        self.doc_graph = dg
        seeds = {d: float(v) for d, v in self.docs.verified.items()}
        self.pagerank = nx.pagerank(dg)
        self.trustrank = nx.pagerank(dg, personalization=seeds)
        und = dg.to_undirected()
        self.clustering = nx.clustering(und)
        comms = nx.community.louvain_communities(und, seed=42)
        self.community = {d: i for i, c in enumerate(comms) for d in c}
        self.ext_ratio = {}
        for d in und:
            nb = list(und[d])
            self.ext_ratio[d] = (sum(self.community[n] != self.community[d] for n in nb) / len(nb)) if nb else 0.0

    def _person_scores(self):
        pg = nx.DiGraph()
        pg.add_nodes_from(self.persons.index)

        def bump(a, b):
            if a != b:
                w = pg.get_edge_data(a, b, {"weight": 0})["weight"]
                pg.add_edge(a, b, weight=w + 1)

        author = self.docs.author_id
        for a, b in self.doc_graph.edges:
            bump(author[a], author[b])
        for d, revs in self.reviewers.items():
            for r in revs:
                bump(r, author[d])
        self.person_graph = pg
        self.betweenness = nx.betweenness_centrality(pg)
        self.expert = {}
        for topic in self.g.nodes:
            if self.g.nodes[topic]["ntype"] not in ("Topic", "Client"):
                continue
            key = "topic_id" if self.g.nodes[topic]["ntype"] == "Topic" else "client"
            td = self.docs[(self.docs[key] == topic) & (self.docs.client == "" if key == "topic_id" else True)]
            pers = {p: 0.01 for p in self.persons.index}
            for d, row in td.iterrows():
                pers[row.author_id] += 1.0
                for r in self.reviewers.get(d, []):
                    pers[r] += 0.5
            s = nx.pagerank(pg, personalization=pers, weight="weight")
            top = max(s.values())
            self.expert[topic] = {p: v / top for p, v in s.items()}

    # ---- features ------------------------------------------------------------------
    def _features(self):
        d = self.docs
        f = pd.DataFrame(index=d.index)
        f["age_days"] = (REFERENCE_DATE - d.last_modified).dt.days
        f["no_owner"] = (d.owner_id == "").astype(int)
        f["no_dept"] = (d.department == "").astype(int)
        f["owner_inactive"] = [int(not self.persons.active[o or a]) for o, a in zip(d.owner_id, d.author_id)]
        f["n_reviewers"] = [len(self.reviewers.get(x, [])) for x in d.index]
        f["version"] = d.version
        f["in_degree"] = [self.doc_graph.in_degree(x) for x in d.index]
        f["pagerank"] = [self.pagerank[x] for x in d.index]
        f["trustrank"] = [self.trustrank[x] for x in d.index]
        f["clustering"] = [self.clustering[x] for x in d.index]
        f["ext_link_ratio"] = [self.ext_ratio[x] for x in d.index]
        f["superseded"] = [int(x in self.superseded_by) for x in d.index]
        # conflict: same topic + country, different stated value
        # conflict_share = share of the other documents in that group stating a different value
        self.conflicts, share = {}, {}
        for _, grp in d.groupby(["topic_id", "country", "client"]):
            for x in grp.index:
                diff = [y for y in grp.index if grp.key_value[y] != grp.key_value[x]]
                diff.sort(key=lambda y: grp.last_modified[y], reverse=True)
                share[x] = len(diff) / max(len(grp) - 1, 1)
                if diff:
                    self.conflicts[x] = diff
        f["conflict_share"] = [share[x] for x in d.index]
        # text overlap with other documents on the same topic
        sim = cosine_similarity(TfidfVectorizer().fit_transform(d.text))
        np.fill_diagonal(sim, 0)
        tv = (d.topic_id + "|" + d.client).to_numpy(dtype=object)
        same_topic = tv[:, None] == tv[None, :]
        f["sim_max"] = (sim * same_topic).max(axis=1)
        self.X = f[FEATURES]

    # ---- model -----------------------------------------------------------------------
    def _fit(self):
        fb = pd.read_csv(DATA_DIR / "feedback.csv").set_index("doc_id")
        y = fb.unreliable.reindex(self.X.index).values
        params = dict(n_estimators=120, max_depth=3, learning_rate=0.1, subsample=0.9,
                      monotone_constraints=tuple(MONOTONE.get(c, 0) for c in FEATURES),
                      eval_metric="logloss", random_state=42)
        cv = StratifiedKFold(5, shuffle=True, random_state=42)
        oof = cross_val_predict(xgb.XGBClassifier(**params), self.X, y, cv=cv, method="predict_proba")[:, 1]
        self.cv_auc = roc_auc_score(y, oof)
        self.oof = pd.Series(oof, index=self.X.index)  # out-of-fold predictions, used for honest evaluation
        self.model = xgb.XGBClassifier(**params).fit(self.X, y)
        self.p_unreliable = self.model.predict_proba(self.X)[:, 1]
        contrib = self.model.get_booster().predict(xgb.DMatrix(self.X), pred_contribs=True)
        self.contrib = pd.DataFrame(contrib[:, :-1], index=self.X.index, columns=FEATURES)

    def _score(self):
        s = self.docs[["title", "doc_type", "topic_id", "country", "client", "key_value", "author_id",
                       "owner_id", "last_modified", "verified"]].copy()
        s["ml_score"] = 100 * (1 - self.p_unreliable)
        exp = []
        for d, row in s.iterrows():
            a = row.author_id
            ctx = row.client or row.topic_id  # client documents: expertise on that client
            exp.append(self.expert[ctx][a] if self.persons.active[a] else 0.0)
        s["author_expert"] = exp
        s["trust"] = (1 - EXPERT_WEIGHT) * s.ml_score + EXPERT_WEIGHT * 100 * s.author_expert
        self.scores = s

    # ---- query-time API ----------------------------------------------------------------
    def person_name(self, p):
        return self.persons.name[p]

    def reasons(self, d, country=None):
        """List of (sign, text); sign is +1 (good), -1 (bad) or 0 (info)."""
        x, row, out = self.X.loc[d], self.scores.loc[d], []
        yrs = x.age_days / 365
        out.append((-1, f"Last updated {yrs:.1f} years ago") if yrs >= 1.5
                   else (1, f"Recently updated ({int(x.age_days)} days ago)"))
        if x.no_owner:
            out.append((-1, "No owner assigned"))
        else:
            out.append((1, f"Owner: {self.person_name(row.owner_id)}"))
        if x.owner_inactive:
            who = self.person_name(row.owner_id or row.author_id)
            out.append((-1, f"{who} no longer works at the company"))
        elif row.author_expert >= 0.5:
            where = f"customer {self.g.nodes[row.client]['name']}" if row.client else "this topic"
            out.append((1, f"Author {self.person_name(row.author_id)} is a top expert for {where}"))
        if x.no_dept:
            out.append((-1, "No department assigned"))
        revs = self.reviewers.get(d, [])
        out.append((1, "Reviewed by " + ", ".join(self.person_name(r) for r in revs)) if revs
                   else (-1, "Never reviewed"))
        if row.verified:
            out.append((1, "Verified policy (trusted source)"))
        for o in self.superseded_by.get(d, []):
            out.append((-1, f"Replaced by {o}"))
        diff = self.conflicts.get(d, [])
        for o in diff[:2]:
            out.append((-1, f"Contradicts {o}: '{self.docs.key_value[d]}' versus '{self.docs.key_value[o]}'"))
        if len(diff) > 2:
            out.append((-1, f"... and {len(diff) - 2} more documents stating a different value"))
        if x.n_reviewers == 0 and x.ext_link_ratio == 0 and self.doc_graph.degree(d) >= 2:
            out.append((-1, "Echo chamber: only linked to documents in the same cluster and never reviewed"))
        if x.in_degree >= 4 and row.ml_score < 50:
            out.append((-1, f"Linked {int(x.in_degree)} times but probably outdated: popular is not the same as reliable"))
        if country and row.country != country:
            out.append((-1, f"Applies to {row.country}, not {country} (score x{SCOPE_PENALTY})"))
        return out

    def top_contributions(self, d, n=4):
        """Largest model contributions, as (feature label, effect on trust)."""
        c = self.contrib.loc[d]
        top = c.reindex(c.abs().sort_values(ascending=False).index)[:n]
        return [(NICE[k], -float(v)) for k, v in top.items()]  # minus: log-odds of UNreliable

    def rank(self, doc_ids, country=None, client=None, adjustments=None):
        """Rank documents. `client` (C_xxx) = the customer the question is about; generic
        documents then count slightly less than that client's own agreements.
        `adjustments` = {doc_id: (score delta, [(sign, reason)])}, e.g. colleague feedback."""
        res = []
        for d in doc_ids:
            row = self.scores.loc[d]
            t = row.trust * (SCOPE_PENALTY if country and row.country != country else 1.0)
            extra = []
            if row.client:
                extra.append((0, f"Customer-specific document for {self.g.nodes[row.client]['name']}"))
            elif client:
                t *= GENERIC_PENALTY
                extra.append((-1, f"General policy: {self.g.nodes[client]['name']} may have its own agreements (score x{GENERIC_PENALTY})"))
            delta, notes = (adjustments or {}).get(d, (0, []))
            t = min(100.0, max(0.0, t + delta))
            res.append({"doc_id": d, "title": row.title, "country": row.country, "key_value": row.key_value,
                        "client": row.client, "extra": extra,
                        "topic_id": row.topic_id, "trust": round(float(t), 1), "badge": badge(t),
                        "ml_score": round(float(row.ml_score), 1), "reasons": self.reasons(d, country) + extra + notes, "feedback_delta": delta,
                        "contributions": self.top_contributions(d), "in_scope": not country or row.country == country})
        return sorted(res, key=lambda r: -r["trust"])

    def suggest_expert(self, topic_id, client=None):
        """Most expert ACTIVE person for the client (if given) or topic; inactive people are skipped."""
        sc = {p: v for p, v in self.expert[client or topic_id].items() if self.persons.active[p]}
        p = max(sc, key=sc.get)
        r = self.persons.loc[p]
        return {"person_id": p, "name": r["name"], "department": r.department, "role": r.role,
                "country": r.country, "score": round(sc[p], 2)}

    def evaluate(self):
        """Is the top-ranked document really a correct one? Uses the hidden ground truth
        (does the document state the CURRENT value?) and OUT-OF-FOLD model predictions, so the
        model never scores documents it was trained on. Only groups (topic, country, client)
        that contain both correct and outdated documents are counted (others are trivial).
        Baselines: newest document, most linked (PageRank), random pick."""
        gt = pd.read_csv(DATA_DIR / "ground_truth.csv").set_index("doc_id").states_current_value
        trust = (1 - EXPERT_WEIGHT) * 100 * (1 - self.oof) + EXPERT_WEIGHT * 100 * self.scores.author_expert
        pr = pd.Series(self.pagerank)
        rows = []
        for (topic, country, client), grp in self.docs.groupby(["topic_id", "country", "client"]):
            ok = gt[grp.index]
            if ok.sum() == 0 or ok.sum() == len(grp):
                continue
            rows.append({"topic_id": topic, "country": country,
                         "customer": self.g.nodes[client]["name"] if client else "-", "documents": len(grp),
                         "ranking": int(ok[trust[grp.index].idxmax()]),
                         "newest": int(ok[grp.last_modified.idxmax()]),
                         "most_linked": int(ok[pr[grp.index].idxmax()]),
                         "random": float(ok.mean())})
        per_group = pd.DataFrame(rows)
        summary = {"groups": len(per_group),
                   **{k: float(per_group[k].mean()) for k in ["ranking", "newest", "most_linked", "random"]},
                   "auc_vs_truth": float(roc_auc_score(gt[trust.index], trust))}
        return summary, per_group

    def topic_risks(self):
        """Per topic: active authors, share of the top author, bus-factor flag."""
        rows = []
        for t, td in self.docs[self.docs.client == ""].groupby("topic_id"):
            share = td.author_id.value_counts(normalize=True)
            act = [p for p in share.index if self.persons.active[p]]
            rows.append({"topic_id": t, "documents": len(td),
                         "active authors": len(act), "top author": self.person_name(share.index[0]),
                         "top author share": round(float(share.iloc[0]), 2),
                         "bus-factor risk": len(act) <= 1 or not self.persons.active[share.index[0]]})
        return pd.DataFrame(rows)


if __name__ == "__main__":
    e = TrustEngine()
    print(f"XGBoost cross-validated AUC: {e.cv_auc:.2f} (simulated data)")
    print("\nHero documents:")
    print(e.scores.loc[["D901", "D902", "D903", "D904", "D905", "D911", "D912", "D921"],
                       ["title", "ml_score", "author_expert", "trust"]].round(1).to_string())
    print("\nTrust badge counts:", e.scores.trust.map(badge).value_counts().to_dict())
    print("Expert fallback pensioen:", e.suggest_expert("T_pensioen"))
    print("\nD902 reasons:"); [print(" ", s, t) for s, t in e.reasons("D902", "BE")]
    print("D902 model contributions:", e.top_contributions("D902"))
    print("\n", e.topic_risks().to_string())
