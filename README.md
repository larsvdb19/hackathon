# GRAPHLAS

**Find it. Understand it. Trust it.**
Tectonic Hackathon, SD Worx challenge: *"How might we turn fragmented organisational knowledge into a trusted shared resource?"*

All data in this repository is **simulated**. GRAPHLAS is a proof of concept.

---

## 1. What is GRAPHLAS?

### The problem SD Worx has
SD Worx's knowledge lives everywhere: policies, manuals, chats, emails and in the heads of experts. Finding information is only the first step. A search returns ten answers, and an AI assistant can summarise them, but the hard question stays open: **is this answer reliable, current, and does it apply to this country and this customer?**
Typical situations: two documents that contradict each other, a policy nobody owns anymore, a document written by someone who has left, a customer agreement that overrides the standard rule.

### How GRAPHLAS solves it
GRAPHLAS gives every answer a **Trust Score from 0 to 100**, explains **why** in plain language, shows when sources **contradict** each other, and suggests the **right colleague to ask** when no document can be trusted. Colleagues can **confirm or flag** a document, and the score moves with their feedback.

### What it addresses
| Problem | What GRAPHLAS does |
|---|---|
| **Trustworthy documentation:** can I rely on this document? | Trust Score, colour, and a "Why this score?" explanation for every result |
| **Conflicting or outdated information** | Red banner when sources disagree, flags replaced and outdated documents, even when they are popular |
| **Connections between documents and questions** | A question is linked to a topic, country and customer, and documents are connected through who wrote, reviewed and linked them |
| **Finding the right person** | Expert suggestion (only people who still work at the company) and a knowledge-risk view |
| **Customer-specific knowledge** | Customer agreements rank above the general policy, and only people who manage that customer can see them |
| **A shared, living resource** | Confirm or flag a document, and the score updates immediately |

---

## 2. How it works 

### The two key ideas
**1. A graph** turns the company's knowledge into a map. **2. A machine-learning model** reads that map, together with the documents' own properties, and estimates how reliable each document is.

### Part 1: the graph
Imagine a map of dots connected by lines.
- **Dots** are documents, people, topics and customers (547 in our data: 463 documents, 64 people, 16 topics, 4 customers).
- **Lines** say how they relate: *wrote*, *reviewed*, *links to*, *replaces*, *belongs to topic*, *is about customer*.

We then measure each dot with a few simple statistics. They tell us how **important** a document is and where trust comes from. Important does not automatically mean reliable, so these statistics are only ingredients for the model.

| Statistic (plain words) | Technical name | What it tells us |
|---|---|---|
| How often is a document linked, especially by other important documents? | PageRank | Popularity. The old policy on parental leave is very popular, but wrong. |
| How much trust reaches a document from **verified** documents along the links? | TrustRank | Trust spreads through links, like a good reputation. |
| Do a document's neighbours only refer to each other? | Clustering | A closed group that never gets checked from outside (an "echo chamber"). |
| How many of its links leave its own group? | Communities (Louvain) | Documents that live in a silo. |
| How many links point to it? | In-degree | Basic usage. |
| Who is a real expert on a topic? | Personalised PageRank on the people network | People who write, get reviewed and get linked on a topic. Used for the expert score. |
| Who is a bridge between groups? | Betweenness | Shows knowledge that depends on a few people. Used in the knowledge-risk view, not in the score. |

Is the graph really used to judge importance and reliability? **Yes, in two ways.** The document statistics above are inputs to the model (about a fifth of what the model learned from, in our simulated data). The expertise statistic adds 15 percent directly to the final score. The strongest signals are actually **conflicts with other documents** and **age**. We report this honestly: the graph adds context that simple rules cannot see, such as popular-but-wrong documents and closed clusters.

### Part 2: the machine-learning model
- **What it is:** an XGBoost model, a set of many small decision trees where each tree corrects the mistakes of the previous ones.
- **What it learns from:** examples of documents and what colleagues said about them. Here this feedback is **simulated**. A document counts as *unreliable* when colleagues flag it as wrong in at least 35 percent of its views.
- **What it reads:** 14 signals per document: age, whether it has an owner and department, whether the owner still works here, number of reviewers, version, whether it has been replaced, how much it contradicts similar documents, text overlap, and the graph statistics above.
- **What it returns:** the probability that a document is unreliable. We turn that into a reliability score: `100 x (1 - probability)`.
- **Safety rails:** the model cannot learn that an *older* document is *more* reliable (monotonic constraints). Whether a document is "verified" is only used to spread trust in the graph, never as a direct input.
- **Explainability:** every score comes with plain-language reasons, such as "last updated 4.9 years ago" and "contradicts D901".

### The Trust Score
```
Trust Score = 85% x reliability score (model)  +  15% x author expertise (graph)
then adjusted for context and feedback
```
| Adjustment | Effect |
|---|---|
| Document is for another country than the question | multiplied by 0.6 |
| General policy, while the question is about a specific customer | multiplied by 0.85 |
| A colleague confirms the document | +4 points each (max +12) |
| A colleague flags the document as wrong | -8 points each (max -32) |

**Reading the score**
| Score | Colour | Meaning |
|---|---|---|
| 70 - 100 | Green | Reliable |
| 45 - 69 | Yellow | Verify before use |
| 0 - 44 | Red | Unreliable |

If nothing scores above 45, GRAPHLAS suggests the most relevant expert who still works at the company.

### Does it pick the right document?
The simulated data has a hidden ground truth: does a document state the current value or an outdated one? That truth is never used in the score. For each group of documents (same topic, country and customer) that contains both correct and outdated documents, we check whether the top-ranked document is correct, using predictions on documents the model did not train on.

| Method | Top result is correct |
|---|---|
| **GRAPHLAS ranking** | **about 88%** |
| Simply the newest document | about 82% |
| Simply the most linked document | about 58% |
| Random pick | about 64% |

This shows the approach works on simulated data. It is not a claim about accuracy in a real organisation. The same table is in the app, under *Method and validation*.

---

## 3. How to look at the website

Start the app (see section 4) and open http://localhost:8501.

**Sidebar**
- **Signed in as:** a demo sign-in. Customer documents are only visible to people who manage that customer. Try *Laura Goossens (Nike)*, then ask about AS Adventure to see access being refused.
- **Filters:** country and customer. *Auto-detect* reads them from your question.

**Tab "Search"**
1. Type a question, or click an example. Press the **Info** button next to the search bar for keywords. Without an AI key, keyword questions still work.
2. The **legend** explains the three colours.
3. A **red banner** appears when sources contradict each other.
4. Results are listed **from highest to lowest Trust Score**. Open **Why this score?** for the reasons.
5. Use **Confirm** or **Flag as wrong** to give feedback. The score changes immediately.
6. If no result is trustworthy, **"Not sure? Ask this expert"** names a colleague.
7. **Knowledge graph for this search** shows the documents and the people behind them.

**Tab "Knowledge graph":** all documents on a topic (colour = Trust Score, size = how often it is linked), a table of **knowledge risks** (topics that depend on one person or on someone who left), and the experts per topic.

**Tab "Method and validation":** the calculation step by step and the validation table above.

**Suggested first questions**
- *How much parental leave do I get in Belgium?* Sources disagree, and the most linked document is the wrong one.
- *What is the retirement age in Belgium?* Nothing is reliable, so an expert is suggested.
- *What is the payroll cut-off for Nike in Belgium?* A customer agreement overrides the general policy.

---

## 4. How to run it yourself

Requirements: Python 3 (developed and tested on 3.13).

```bash
git clone https://github.com/larsvdb19/hackathon
cd hackathon
python3 -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python seed_data.py            # regenerates data/*.csv (already included, same result every time)
cp .env.example .env           # optional: add a Google API key, see below
streamlit run app.py           # opens http://localhost:8501
```

**AI key (optional).** With a `GOOGLE_API_KEY` in `.env` (create one in Google AI Studio or Google Cloud), GRAPHLAS understands free sentences through Gemini. Without it, the app falls back to keyword matching and shows *"API not working"* for longer sentences. Never commit `.env`; it is git-ignored.

**Obsidian graph (optional).** The folder `obsidian_vault/` is included. In Obsidian choose *Open folder as vault* and open the graph view (Ctrl+G). Regenerate it with `python export_obsidian.py`.

**Results are reproducible:** the data uses a fixed random seed and the model a fixed `random_state`. Small differences are possible with other library versions.

| File | Purpose |
|---|---|
| `app.py` | Streamlit interface |
| `trust_engine.py` | Graph statistics, features, model, Trust Score, explanations, validation |
| `query_parser.py` | Turns a question into topic, country and customer, and enforces access to customer documents |
| `feedback.py` | Confirm and flag votes, with an access check |
| `seed_data.py` | Generates the simulated knowledge graph (`data/`) |
| `export_obsidian.py` | Exports the graph as an Obsidian vault |
| `context/` | The challenge guide and the original idea |

---

## 5. Security and privacy
- The AI model only reads the user's question. It extracts topic, country and customer, checked against fixed lists. It never writes database queries and never decides trust.
- Customer documents and votes are protected by a server-side access check, not just by the interface.
- No secrets in the repository. Input is sanitised and length-limited.

## 6. Unfinished and next steps
- All data and the user feedback used for training are simulated. Next step: connect SharePoint, Confluence and Teams, and learn from real feedback.
- The sign-in is a demo. A real deployment needs proper authentication and roles.
- Conflicts are detected through a stated value per document. Reading free text to compare claims is future work.
- Knowledge that is not written down is not captured yet. We only show which topics depend on too few people.
