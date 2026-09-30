"""Export the knowledge graph as an Obsidian vault (markdown + [[wikilinks]]).

Run `python export_obsidian.py`, then in Obsidian: "Open folder as vault" -> obsidian_vault/,
open the Graph view. Documents are coloured by trust (green/yellow/red), people, topics and
clients by type. Simulated data; the vault has no access control, so do not share it like the app.
"""
import json
import re
import shutil
from collections import defaultdict
from pathlib import Path

from trust_engine import TrustEngine, badge

OUT = Path(__file__).parent / "obsidian_vault"
NL_BADGE = {"green": "groen", "yellow": "geel", "red": "rood"}
COLORS = {"groen": 0x2E9E5B, "geel": 0xE0A800, "rood": 0xD64545,
          "persoon": 0x4A7BD0, "onderwerp": 0x8A5CC2, "klant": 0xE07B28}


def safe(name):
    """File-system and wikilink safe note name."""
    return re.sub(r'[\\/:*?"<>|#^\[\]]', "", name).strip()


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main():
    e = TrustEngine()
    g = e.g
    if OUT.exists():
        shutil.rmtree(OUT)

    def doc_link(d):  # docs are files named by id, shown with their title
        return f"[[{d}|{e.docs.title[d]}]]"

    def name_of(n):
        a = g.nodes[n]
        return safe(a["name"])

    out_edges, in_edges = defaultdict(lambda: defaultdict(list)), defaultdict(lambda: defaultdict(list))
    for u, v, k in g.edges(data="etype"):
        out_edges[u][k].append(v)
        in_edges[v][k].append(u)

    # ---- documents ---------------------------------------------------------------------
    for d, row in e.scores.iterrows():
        doc = e.docs.loc[d]
        color = NL_BADGE[badge(row.trust)]
        lines = ["---", f"aliases: [\"{doc.title}\"]", f"tags: [document, {color}]",
                 f"trust: {row.trust:.0f}", f"kleur: {color}", f"onderwerp: \"{g.nodes[doc.topic_id]['name']}\"",
                 f"land: {doc.country}", f"klant: \"{g.nodes[doc.client]['name'] if doc.client else ''}\"",
                 f"type: {doc.doc_type}", f"laatst_aangepast: {doc.last_modified.date()}",
                 f"waarde: \"{doc.key_value}\"", f"geverifieerd: {str(bool(doc.verified)).lower()}", "---", "",
                 f"# {doc.title}", "", f"**Trust Score: {row.trust:.0f} ({color})** · {doc.key_value}", "",
                 "## Verbindingen",
                 f"- Auteur: [[{name_of(doc.author_id)}]]"]
        if doc.owner_id:
            lines.append(f"- Eigenaar: [[{name_of(doc.owner_id)}]]")
        revs = in_edges[d]["REVIEWS"]
        if revs:
            lines.append("- Gereviewd door: " + ", ".join(f"[[{name_of(r)}]]" for r in revs))
        lines.append(f"- Onderwerp: [[{name_of(doc.topic_id)}]]")
        if doc.client:
            lines.append(f"- Klant: [[{name_of(doc.client)}]]")
        for k, label in (("LINKS_TO", "Verwijst naar"), ("SUPERSEDES", "Vervangt")):
            targets = sorted(set(out_edges[d][k]))
            if targets:
                lines.append(f"- {label}: " + ", ".join(doc_link(t) for t in targets))
        sup = sorted(set(in_edges[d]["SUPERSEDES"]))
        if sup:
            lines.append("- Vervangen door: " + ", ".join(doc_link(t) for t in sup))
        conflicts = e.conflicts.get(d, [])
        if conflicts:  # plain text on purpose: links would make the graph unreadable
            lines.append(f"- Spreekt tegen (zelfde onderwerp/land/klant): {', '.join(conflicts[:5])}")
        lines += ["", "## Waarom deze score", *[f"- {'✅' if s > 0 else '⚠️' if s < 0 else 'ℹ️'} {t}" for s, t in e.reasons(d)], ""]
        write(OUT / "documenten" / f"{d}.md", "\n".join(lines))

    # ---- people, topics, clients --------------------------------------------------------------
    for p, a in e.persons.iterrows():
        wrote = sorted(set(out_edges[p]["WROTE"]))
        reviewed = sorted(set(out_edges[p]["REVIEWS"]))
        lines = ["---", "tags: [persoon]", f"afdeling: \"{a.department}\"", f"land: {a.country}",
                 f"actief: {str(bool(a.active)).lower()}", "---", "", f"# {a['name']}", "",
                 f"{a.role} · {a.department} ({a.country})" + ("" if a.active else " · **niet meer actief**"), "",
                 f"- Schreef {len(wrote)} documenten, reviewde {len(reviewed)}",
                 f"- Betweenness (brug tussen kennisgebieden): {e.betweenness[p]:.3f}"]
        write(OUT / "personen" / f"{safe(a['name'])}.md", "\n".join(lines) + "\n")
    for t in [n for n, a in g.nodes(data=True) if a["ntype"] == "Topic"]:
        n_docs = len(in_edges[t]["BELONGS_TO_TOPIC"])
        top = sorted(e.expert[t].items(), key=lambda kv: -kv[1])[:3]
        lines = ["---", "tags: [onderwerp]", "---", "", f"# {g.nodes[t]['name']}", "",
                 f"Afdeling: {g.nodes[t]['department']} · {n_docs} documenten", "", "## Top-experts",
                 *[f"- [[{name_of(p)}]] ({s:.2f})" for p, s in top]]
        write(OUT / "onderwerpen" / f"{name_of(t)}.md", "\n".join(lines) + "\n")
    for c in e.client_names:
        a = g.nodes[c]
        mgr = in_edges[c]["MANAGES_CLIENT"]
        lines = ["---", "tags: [klant]", "---", "", f"# {a['name']}", "", f"Landen: {a['countries']}",
                 *[f"- Accountmanager: [[{name_of(m)}]]" for m in mgr]]
        write(OUT / "klanten" / f"{name_of(c)}.md", "\n".join(lines) + "\n")

    # ---- preconfigured graph colours ------------------------------------------------------------
    write(OUT / ".obsidian" / "graph.json", json.dumps({
        "showTags": False, "showOrphans": True, "nodeSizeMultiplier": 1.3, "linkDistance": 120,
        "colorGroups": [{"query": f"tag:#{t}", "color": {"a": 1, "rgb": c}} for t, c in COLORS.items()]}, indent=2))

    # ---- check: every wikilink must point to an existing note ---------------------------------
    notes = {p.stem for p in OUT.rglob("*.md")}
    broken = {m for p in OUT.rglob("*.md") for m in re.findall(r"\[\[([^\]|]+)", p.read_text(encoding="utf-8")) if m not in notes}
    print(f"{len(notes)} notities in {OUT}; ontbrekende linkdoelen: {len(broken)} {sorted(broken)[:5]}")


if __name__ == "__main__":
    main()
