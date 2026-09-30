# GRAPHLAS: 3-minute pitch

**Persona:** a payroll consultant who has just taken over a customer portfolio (an example from the challenge brief).
**Speaker plan:** one person talks, one person clicks. Total spoken text is about 420 words, so it fits in 3 minutes.

## Before you start (checklist)
- App running on http://localhost:8501, signed in as **Laura Goossens, Customer Success Lead (Nike)**.
- Sidebar: click **Reset colleague feedback** (only visible as Knowledge manager), then switch back to Laura.
- Country and Customer filters on **Auto-detect**. Test the Gemini key once. If the quota is used up, type short keyword questions.
- Browser zoom around 110 percent so the room can read the scores.

---

## 0:00 - 0:25 | The problem
*(slide or title screen: GRAPHLAS)*

"Every large organisation has a hidden superpower: its knowledge. But at SD Worx that knowledge is spread over policies, chats, mails and people's heads. A search returns ten answers. An AI assistant summarises them. The hard question is still open: **which answer can I trust?** Is it current? Does it apply to this country and this customer? And who can I ask if I am unsure?"

## 0:25 - 0:45 | The idea
"We built GRAPHLAS. It treats company knowledge as a **graph** of documents, people and customers, and gives every answer a **Trust Score** with a reason. Not a black box: you always see why."

## 0:45 - 1:25 | Demo 1: popular is not reliable
*Click the first example: "How much parental leave do I get in Belgium?"*

"A new consultant asks about parental leave in Belgium. GRAPHLAS warns immediately: **the sources disagree, 3 months versus 4 months.** The current, verified policy is green. The old policy is red, **even though it is the most linked document in the whole graph.** A normal search would put it first.
*Open 'Why this score?' on the red one.*
Here is why: almost five years old, replaced by a newer version, contradicted by another source, and linked eight times but probably outdated. Popular is not the same as reliable."

## 1:25 - 1:45 | Demo 2: no reliable answer, so ask a person
*Click: "What is the retirement age in Belgium?"*

"Sometimes no document is good enough. Here every Belgian source is red, because the author has left the company. GRAPHLAS does not guess. It says: **ask this expert**, and names a colleague who still works here. The departed expert is skipped, even though the graph says he knew the most."

## 1:45 - 2:15 | Demo 3: customer knowledge and access
*Click: "What is the payroll cut-off for Nike in Belgium?"*

"Now the handover. This consultant inherits Nike. Nike has its own agreement: cut-off on the 15th, not the standard 20th. The customer agreement ranks above the general policy, and an outdated Nike document is flagged.
*Type: payroll cut-off AS Adventure.*
But this consultant does not manage AS Adventure. **Access denied.** Customer documents only appear for the people who manage that customer, and the check runs on the server, not in the screen."

## 2:15 - 2:35 | A shared resource that learns
*Click Flag as wrong on a result, then point at the score.*

"Trust is shared. Any colleague can **confirm or flag** a document, and the score moves live. One vote per person, and only on documents you are allowed to see. That is how knowledge becomes a trusted shared resource instead of a pile of files."

## 2:35 - 2:55 | How it works, and how we know
*Switch to the Knowledge graph tab.*

"Behind the scenes: PageRank, trust that flows from verified documents, communities and bus-factor analysis, combined with a model trained on user feedback. The graph also shows **knowledge risks**: topics that depend on one person. We tested whether the top result is really the right one: **88 percent correct, against 82 percent for 'newest document' and 58 percent for 'most linked'.** We are honest: the data is simulated, so this proves the approach, not production accuracy."

## 2:55 - 3:00 | Close
"GRAPHLAS: find it, understand it, **trust it.** Thank you."

---

## If they ask (short answers)
- **Why not just a chatbot?** A chatbot summarises. It does not say whether the source is right. We show the trust and the reason.
- **Real data?** Simulated here. The same pipeline would read SharePoint, Confluence and Teams, and learn from real user feedback.
- **Does the AI see our documents?** No. The AI model only reads the question to find topic, country and customer. It does not write database queries and does not decide trust.
- **Scale?** The scoring is a batch calculation. Scores update when documents or feedback change.
- **Security?** Fixed lookups, input validation, no secrets in code, server-side access checks. *(Add the Aikido result here once the scan has run.)*

## Words to avoid
Do not say "XGBoost", "PageRank" or "AUC" unless asked. Say "a model trained on feedback" and "how often a document is linked".
