# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->
I chose the CS course catalog at my university, UIC. While the course catalog is easy to find, suggesting pairings for the student so that they have an easier time with the content can be harder and requires hours of reddit and ratemyprofessor to have an idea of what and who to take when.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | UIC Catalogs | BS in CS | https://catalog.uic.edu/ucat/colleges-depts/engineering/cs/bs-cs/ |
| 2 | UIC Catalogs | CS courses | https://catalog.uic.edu/ucat/course-descriptions/cs/ |
| 3 | Reddit  | CS course advice | https://www.reddit.com/r/uichicago/comments/1nc39vw/uic_cs_courses_advice/ |
| 4 | Reddit | CS course advice | https://www.reddit.com/r/uichicago/comments/zgmng3/uic_cs_courses/ |
| 5 | Reddit | 400 Level course advice | https://www.reddit.com/r/uichicago/comments/1g61kar/easy_400_lvl_cs_classes/ |
| 6 | Reddit | CS course advice | https://www.reddit.com/r/uichicago/comments/1juv3tv/how_is_the_work_load_for_these_classes_is_cs_361/ |
| 7 | RateMyProfessor | prof. review | https://www.ratemyprofessors.com/professor/1120062 |
| 8 | RateMyProfessor | prof. review | https://www.ratemyprofessors.com/professor/2972083 |
| 9 | RateMyProfessor | prof. review | https://www.ratemyprofessors.com/professor/3052028 |
| 10 | RateMyProfessor | prof. review | https://www.ratemyprofessors.com/professor/2283856 |
| 11 | RateMyProfessor | prof. review | https://www.ratemyprofessors.com/professor/297361 |
| 12 | RateMyProfessor | prof. review | https://www.ratemyprofessors.com/professor/1077446 |
| 13 | RateMyProfessor | prof. review | https://www.ratemyprofessors.com/professor/2844376 |

---

## Chunking Strategy

For this project, I am thinking of using some different chunking strategies. The catalogs would need to be recursively chunked, as they are big and their ordering matters. While the shorter, more concise reviews should be done using fixed-sized chunking.
**Chunk size:** Variable, targeting 300 - 400 characters. Metadata (professor name, relevant course information, and reviewer/review information should be prepended) for ratemyprofessor and reddit sources

**Overlap:** 0 characters

**Reasoning:** reviews and comments are short, so giving them the surrounding context of the professor and over arching comversation would allow for more information per chunk without taking too large a chunk

---

## Retrieval Approach

**Embedding model:** all-MiniLM-L6-v2 via sentence-transformers

**Top-k:** Top-k: 5 since I have a relatively small number of chunks (each chunk is a single comment or review). This is the right balance between low latency and enough context to answer most questions.

**Strategy**: a Hybrid vector search and keyword search. vector should cover the sentiment of reviews on a topic and keyword would make sure for to the point result 

**Production tradeoff reflection:** I may switch to more advanced models such as OpenAI's text-embedding-3-small, as it allows for a much more indepth vector and bigger context window.

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | Who can I pick to be the best for CS 251? | Daniel Ayala |
| 2 | Should I take CS 211, 251, 261 and 301 all at the same time? | Probably not |
| 3 | What courses should I take with CS 341 | CS 342 or CS 361 |
| 4 | What do most students think of professor Ayala | sweet and chill |
| 5 | How is CS 401 with DasGupta | Easy A |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. Sarcastic remarks in reviews

2. Contradictory reviews

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

graph TD
    A[1. Document Ingestion] -->|HTML Parser| B[2. Chunking]
    B -->|Prepend Metadata & Custom Splitter| C[3. Embedding & Vector Store]
    C -->|all-MiniLM-L6-v2 & ChromaDB| D1[4a. Vector Search]
    B -->|Keyword Path: BM25| D2[4b. Keyword Search]
    D1 -->|Cosine Similarity, Top-K = 5| M[Merge & Score: Top-K = 5]
    D2 -->|BM25| M
    M --> E[5. Generation]
    E -->|Structured LLM Prompt| F[ Output ]

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->
I plan on using Claude Code, asking it to implement for me 2 chunnking strategies that I need, with variable size and overlap. The architechtural section will be used to implement the rag pipeline.

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
