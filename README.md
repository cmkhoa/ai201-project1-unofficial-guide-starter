# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

This system covers UIC's Computer Science program — specifically course difficulty, workload, professor quality, and scheduling advice. While the official course catalog tells you *what* a course covers, it says nothing about whether the exams are brutal, which professor to pick, or whether taking three core classes in the same semester is survivable. That knowledge lives scattered across Reddit threads and RateMyProfessors reviews, which take hours to track down and are hard to search systematically. This guide aggregates all of it into a single queryable source grounded in real student experience.

---

## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | UIC Catalog — BS in CS | Official catalog | https://catalog.uic.edu/ucat/colleges-depts/engineering/cs/bs-cs/ |
| 2 | UIC Catalog — CS Course Descriptions | Official catalog | https://catalog.uic.edu/ucat/course-descriptions/cs/ |
| 3 | Reddit: UIC CS Courses Advice | Reddit thread | https://www.reddit.com/r/uichicago/comments/1nc39vw/uic_cs_courses_advice/ |
| 4 | Reddit: UIC CS Courses | Reddit thread | https://www.reddit.com/r/uichicago/comments/zgmng3/uic_cs_courses/ |
| 5 | Reddit: Easy 400-Level CS Classes | Reddit thread | https://www.reddit.com/r/uichicago/comments/1g61kar/easy_400_lvl_cs_classes/ |
| 6 | Reddit: CS 361/362/341 Workload | Reddit thread | https://www.reddit.com/r/uichicago/comments/1juv3tv/how_is_the_work_load_for_these_classes_is_cs_361/ |
| 7 | RateMyProfessors — Ajay Kshemkalyani | Professor review | https://www.ratemyprofessors.com/professor/1120062 |
| 8 | RateMyProfessors — Zoa Katok | Professor review | https://www.ratemyprofessors.com/professor/2972083 |
| 9 | RateMyProfessors — Zhaochen Gu | Professor review | https://www.ratemyprofessors.com/professor/3052028 |
| 10 | RateMyProfessors — Gonzalo Bello Lander | Professor review | https://www.ratemyprofessors.com/professor/2283856 |
| 11 | RateMyProfessors — Mitchell Theys | Professor review | https://www.ratemyprofessors.com/professor/297361 |
| 12 | RateMyProfessors — Jan Verschelde | Professor review | https://www.ratemyprofessors.com/professor/1077446 |
| 13 | RateMyProfessors — George Maratos | Professor review | https://www.ratemyprofessors.com/professor/2844376 |

---

## Chunking Strategy

**Chunk size:** Variable, targeting ≤400 characters, with different strategies per document type.

**Overlap:** 0 characters. Reviews and comments are already self-contained units, so overlap would just duplicate context without adding value.

**Why these choices fit your documents:**
- **Catalog docs** (`uic_bs_cs.txt`, `uic_cs_courses.txt`) use a **recursive character splitter** that tries to break on `\n\n`, then `\n`, then `. `, then ` ` — in that order. This preserves the linear structure of the catalog (section headings stay with their content) while keeping chunks under 400 characters for embedding quality.
- **RateMyProfessor files** use **per-review chunking** — one chunk per student review. Each chunk has the professor name, course, rating, difficulty, grade, and tags prepended as metadata so the retriever has full context even without the surrounding document.
- **Reddit files** use **per-comment chunking** — one chunk per post or comment. Each chunk is prefixed with the subreddit name and thread title so the model knows where the opinion came from.

**Preprocessing:** All Reddit files were manually cleaned before chunking — upvote/downvote counts, award icons, promoted ads, navigation UI text, and timestamps were stripped. Only usernames, flair, and comment bodies were kept.

**Final chunk count:** 104 chunks across 13 documents.

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers`. It's a lightweight (80MB), fast, locally-run model that produces 384-dimensional embeddings. It works well on short review-style text and runs entirely on CPU, which matters for a free-tier dev environment.

**Production tradeoff reflection:** For a real deployment I would weigh switching to OpenAI's `text-embedding-3-small`. It has a much larger context window (8192 tokens vs ~256 for MiniLM), handles longer catalog sections without truncation, and generally produces better semantic representations for domain-specific academic text. The tradeoff is cost (API-hosted, per-token pricing) and latency (network round-trip per query vs. local inference). If multilingual support were needed — e.g., UIC students who write reviews in Spanish or Chinese — a multilingual model like `paraphrase-multilingual-MiniLM-L12-v2` would be worth considering before jumping to a paid API.

---

## Grounded Generation

**System prompt grounding instruction:**

> *"You are an unofficial academic advisor for UIC Computer Science students. Your job is to answer questions using ONLY the information in the provided documents. Do not use any outside knowledge or general assumptions. If the documents contain enough information, give a clear, direct answer. Refer to sources naturally (e.g. 'According to student reviews...', 'Reddit users note...'). If the documents do not contain enough information to answer the question, respond with exactly: 'I don't have enough information on that.' Never fabricate details, professor names, course facts, or opinions not present in the documents."*

The retrieved chunks are numbered `[1]` through `[5]` and passed verbatim as the only context in the user message. `temperature=0.2` further suppresses the model's tendency to drift into training-data knowledge.

**How source attribution is surfaced in the response:**
Source attribution is assembled **programmatically** after generation — the LLM never decides what to cite. The `ask()` function inspects the `filename` field in each retrieved chunk's metadata and maps it to a human-readable label and hyperlink URL using a hard-coded lookup table (`SOURCE_LABELS`, `SOURCE_URLS` in `query.py`). The Gradio UI renders these as clickable markdown links, e.g. `[RateMyProfessors — George Maratos](https://www.ratemyprofessors.com/professor/2844376)`. This guarantees that every source shown to the user corresponds to an actual retrieved document, not a hallucinated citation.

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | Who is the best professor for CS 361? | George Maratos | Named Maratos, cited Reddit + RMP reviews with direct quotes | Relevant | Accurate |
| 2 | Should I take CS 211, 251, and 261 all in the same semester? | Probably not | Correctly advised against it, cited u/DankMagician2500 and Prof Kidane's own warning | Relevant | Accurate |
| 3 | Is it a good idea to take CS 361, 362, and 341 together? | Doable, but 362 is the hardest | Said doable, flagged 362 as the hardest, cited u/Archer2108 | Relevant | Accurate |
| 4 | What do students think of Professor Gonzalo Bello for CS 301? | Extremely well-reviewed | Summarized 5.0 reviews, quoted "clear, engaging, well-organized" and "the goat" | Relevant | Accurate |
| 5 | What are some easier 400-level CS courses to take? | CS 418 and CS 407 mentioned as options | Identified CS 418 and CS 407 but ended with "I don't have enough information" due to no direct recommendation in the thread | Relevant | Partially accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

**Question that failed:** *"In which semester should a student take CS 111 per the catalog?"*

**What the system returned:** `"I don't have enough information on that."` — retrieved Reddit chunks instead of any catalog content.

**Root cause (tied to a specific pipeline stage):** The failure originates at the **document ingestion stage**. The UIC catalog page scraped (`uic_bs_cs.txt`) lists CS 111 only as a category requirement ("select from CS 111, 112, or 113") — it does not contain a semester-by-semester plan. The catalog source simply does not publish recommended sequencing in that format. Because the relevant fact is absent from the documents, no amount of retrieval improvement can surface it. The retriever correctly ranked catalog chunks lower than Reddit chunks, which at least mention CS 111 in scheduling discussions, but the LLM found none of them sufficient to answer the specific question — and correctly refused.

**What you would change to fix it:** Add a source that *does* contain semester-by-semester sequencing — for example, a UIC CS department advising sheet, a sample 4-year plan PDF, or a Reddit thread specifically about course sequencing. Alternatively, scrape the UIC CS department's advising pages, which often include suggested semester plans that the main catalog does not.

---

## Spec Reflection

**One way the spec helped you during implementation:**
Defining the chunking strategy in `planning.md` before writing any code forced an early decision about document heterogeneity. Because the spec explicitly noted that catalog pages are linear and ordered while reviews are short and self-contained, the implementation naturally arrived at three different chunking strategies (recursive for catalogs, per-review for RMP, per-comment for Reddit) rather than applying a one-size-fits-all fixed-size split. Without that upfront thinking, a uniform approach would have either over-chunked reviews (splitting a single comment mid-sentence) or under-chunked catalog sections (keeping 2,000-character blocks that hurt embedding quality).

**One way your implementation diverged from the spec, and why:**
The spec proposed fixed-size chunking for catalog documents. During implementation this was changed to a recursive character splitter that respects natural text boundaries (`\n\n` → `\n` → `. ` → ` `). Fixed-size splitting was cutting mid-sentence through course descriptions like "CS 361 (4 hrs): Systems programming covering virtual memory, I/O..." which broke the semantic unit. The recursive approach kept each course description intact as a chunk, which improved retrieval precision on course-specific questions.

---

## AI Usage

**Instance 1**

- *What I gave the AI:* The `Chunking Strategy` and `Architecture` sections of `planning.md`, plus a request to implement two chunking strategies — recursive for catalog docs and per-unit for reviews/comments.
- *What it produced:* A `chunk_catalog()` function using a recursive character splitter, a `chunk_reviews()` function splitting on `REVIEW |` markers, and a `chunk_reddit()` function splitting on `COMMENT |` markers. All integrated into a single `ingest.py` pipeline that writes to ChromaDB.
- *What I changed or overrode:* Changed the chunking strategy for catalog documents from the originally planned fixed-size approach to recursive splitting, since mid-sentence splits were breaking course description units. I also directed the AI to prepend structured metadata (professor name, course, rating) to each review chunk rather than storing it only as ChromaDB metadata fields, so the embedded text itself carries context.

**Instance 2**

- *What I gave the AI:* The `Retrieval Approach` section of `planning.md` (hybrid BM25 + vector, top-k=5, Reciprocal Rank Fusion) and the pipeline architecture diagram.
- *What it produced:* `retrieve.py` with `build_retriever()` loading ChromaDB + building a BM25 index in memory, and `retrieve()` running both searches and merging via RRF (k=60). Also produced `query.py` with a grounding-enforcing system prompt and programmatic source attribution, and a Gradio `app.py` with example question buttons.
- *What I changed or overrode:* Replaced the initial example questions in `app.py` (which referenced professors not in the document index) with questions verified to return grounded answers. Also tightened the system prompt after observing the model draw on general CS knowledge — added the explicit instruction "Never fabricate details, professor names, course facts, or opinions not present in the documents."
