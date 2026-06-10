"""
Stage 5 — Generation.

ask(question) → { "answer": str, "sources": list[dict] }

Sources are assembled programmatically (not by the LLM) so attribution
is always traceable to an actual retrieved chunk, not model imagination.
"""

import os
from dotenv import load_dotenv
from groq import Groq
from retrieve import build_retriever, retrieve

load_dotenv()

MODEL = "llama-3.3-70b-versatile"

# Source URLs keyed by filename, for hyperlink generation in the UI
SOURCE_URLS = {
    "uic_bs_cs.txt":              "https://catalog.uic.edu/ucat/colleges-depts/engineering/cs/bs-cs/",
    "uic_cs_courses.txt":         "https://catalog.uic.edu/ucat/course-descriptions/cs/",
    "reddit_1.txt":               "https://www.reddit.com/r/uichicago/comments/1nc39vw/uic_cs_courses_advice/",
    "reddit_2.txt":               "https://www.reddit.com/r/uichicago/comments/zgmng3/uic_cs_courses/",
    "reddit_3.txt":               "https://www.reddit.com/r/uichicago/comments/1g61kar/easy_400_lvl_cs_classes/",
    "reddit_4.txt":               "https://www.reddit.com/r/uichicago/comments/1juv3tv/how_is_the_work_load_for_these_classes_is_cs_361/",
    "rmp_ajay_kshemkalyani.txt":  "https://www.ratemyprofessors.com/professor/1120062",
    "rmp_zoa_katok.txt":          "https://www.ratemyprofessors.com/professor/2972083",
    "rmp_zhaochen_gu.txt":        "https://www.ratemyprofessors.com/professor/3052028",
    "rmp_gonzalo_bello.txt":      "https://www.ratemyprofessors.com/professor/2283856",
    "rmp_mitchell_theys.txt":     "https://www.ratemyprofessors.com/professor/297361",
    "rmp_jan_verschelde.txt":     "https://www.ratemyprofessors.com/professor/1077446",
    "rmp_george_maratos.txt":     "https://www.ratemyprofessors.com/professor/2844376",
}

SOURCE_LABELS = {
    "uic_bs_cs.txt":              "UIC Catalog — BS in CS",
    "uic_cs_courses.txt":         "UIC Catalog — CS Course Descriptions",
    "reddit_1.txt":               "Reddit: UIC CS Courses Advice (r/uichicago)",
    "reddit_2.txt":               "Reddit: UIC CS Courses (r/uichicago)",
    "reddit_3.txt":               "Reddit: Easy 400-Level CS Classes (r/uichicago)",
    "reddit_4.txt":               "Reddit: CS 361/362/341 Workload (r/uichicago)",
    "rmp_ajay_kshemkalyani.txt":  "RateMyProfessors — Ajay Kshemkalyani",
    "rmp_zoa_katok.txt":          "RateMyProfessors — Zoa Katok",
    "rmp_zhaochen_gu.txt":        "RateMyProfessors — Zhaochen Gu",
    "rmp_gonzalo_bello.txt":      "RateMyProfessors — Gonzalo Bello Lander",
    "rmp_mitchell_theys.txt":     "RateMyProfessors — Mitchell Theys",
    "rmp_jan_verschelde.txt":     "RateMyProfessors — Jan Verschelde",
    "rmp_george_maratos.txt":     "RateMyProfessors — George Maratos",
}

SYSTEM_PROMPT = """\
You are an unofficial academic advisor for UIC Computer Science students. \
Your job is to answer questions using ONLY the information in the provided documents. \
Do not use any outside knowledge or general assumptions.

Rules:
- If the documents contain enough information, give a clear, direct answer.
- Refer to sources naturally (e.g. "According to student reviews...", "Reddit users note...").
- If the documents do not contain enough information to answer the question, \
respond with exactly: "I don't have enough information on that."
- Never fabricate details, professor names, course facts, or opinions not present in the documents.\
"""

CONTEXT_TEMPLATE = """\
DOCUMENTS:
{context}

QUESTION: {question}

Answer using only the documents above.\
"""

# Shared retriever (loaded once at import time)
_retriever = None


def _get_retriever():
    global _retriever
    if _retriever is None:
        _retriever = build_retriever()
    return _retriever


def ask(question: str, top_k: int = 5) -> dict:
    """
    Full pipeline: retrieve → generate → attach sources.

    Returns:
        {
            "answer":  str,
            "sources": [{"label": str, "filename": str, "url": str}, ...]
        }
    """
    retriever = _get_retriever()
    chunks = retrieve(retriever, question, top_k=top_k)

    # Build numbered context block for the prompt
    context_lines = []
    for i, chunk in enumerate(chunks, 1):
        context_lines.append(f"[{i}] {chunk['text']}")
    context_block = "\n\n".join(context_lines)

    # Generate answer
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": CONTEXT_TEMPLATE.format(
                context=context_block,
                question=question,
            )},
        ],
        temperature=0.2,   # low temp for factual grounding
        max_tokens=512,
    )
    answer = response.choices[0].message.content.strip()

    # Assemble sources programmatically from retrieved chunk metadata
    seen = set()
    sources = []
    for chunk in chunks:
        fname = chunk["metadata"]["filename"]
        if fname not in seen:
            seen.add(fname)
            sources.append({
                "label":    SOURCE_LABELS.get(fname, fname),
                "filename": fname,
                "url":      SOURCE_URLS.get(fname, ""),
            })

    return {"answer": answer, "sources": sources}


if __name__ == "__main__":
    import sys
    queries = sys.argv[1:] or [
        "Who is the best professor for CS 361?",
        "Should I take CS 211, 251, and 261 all at the same time?",
        "What is the food like at the UIC dining hall?",   # out-of-scope test
    ]
    retriever = _get_retriever()
    for q in queries:
        print(f"\nQ: {q}")
        result = ask(q)
        print(f"A: {result['answer']}")
        print("Sources:")
        for s in result["sources"]:
            print(f"  • {s['label']}  →  {s['url']}")
        print("-" * 60)
