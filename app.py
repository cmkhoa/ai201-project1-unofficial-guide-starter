"""
Stage 5 — Gradio interface.
Run: python app.py  →  http://localhost:7860
"""

import gradio as gr
from query import ask

TITLE = "UIC CS Unofficial Guide"
DESCRIPTION = (
    "Ask anything about UIC CS courses, professors, and course load. "
    "Answers are grounded in real student reviews and the UIC course catalog."
)
EXAMPLES = [
    "Who is the best professor for CS 361?",
    "Should I take CS 211, 251, and 261 all in the same semester?",
    "Is it a good idea to take CS 361, 362, and 341 together?",
    "What do students think of Professor Gonzalo Bello for CS 301?",
    "What are some easier 400-level CS courses to take?",
]


def handle_query(question: str):
    if not question.strip():
        return "", ""

    result = ask(question)
    answer = result["answer"]

    # Build source list with markdown hyperlinks (programmatic, not LLM-generated)
    source_lines = []
    for s in result["sources"]:
        if s["url"]:
            source_lines.append(f"• [{s['label']}]({s['url']})")
        else:
            source_lines.append(f"• {s['label']}")
    sources_md = "\n".join(source_lines)

    return answer, sources_md


with gr.Blocks(title=TITLE, theme=gr.themes.Soft()) as demo:
    gr.Markdown(f"# {TITLE}")
    gr.Markdown(DESCRIPTION)

    with gr.Row():
        with gr.Column(scale=3):
            inp = gr.Textbox(
                label="Your question",
                placeholder="e.g. Who should I take for CS 361?",
                lines=2,
            )
            btn = gr.Button("Ask", variant="primary")
        with gr.Column(scale=1):
            gr.Markdown("**Example questions:**")
            for ex in EXAMPLES:
                gr.Button(ex, size="sm").click(
                    fn=lambda q=ex: q, outputs=inp
                )

    answer_box = gr.Textbox(label="Answer", lines=8, interactive=False)
    sources_box = gr.Markdown(label="Sources")

    btn.click(handle_query, inputs=inp, outputs=[answer_box, sources_box])
    inp.submit(handle_query, inputs=inp, outputs=[answer_box, sources_box])

if __name__ == "__main__":
    demo.launch()
