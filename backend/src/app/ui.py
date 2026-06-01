"""
src/app/ui.py
──────────────
Section 12 of the Implementation Guide: App Design (Option A – Gradio prototype).

Recommended UI features from the guide:
  - chat history window
  - clear note that the assistant is supportive but not emergency care
  - calm, non-clinical visual design
"""

from __future__ import annotations

import gradio as gr

from src.app.service import chat_logic
from src.app.logging import get_ui_history

_DESCRIPTION = (
    "**MyAlly** is an empathetic support assistant for students. "
    "It is not a therapist, diagnostician, or emergency service. "
    "If you are in immediate danger, please contact your local emergency services "
    "or a crisis helpline right away."
)


def build_ui() -> gr.ChatInterface:
    """Return a configured Gradio ChatInterface."""
    return gr.ChatInterface(
        fn=chat_logic,
        title="MyAlly – Student Mental-Health Support",
        description=_DESCRIPTION,
        chatbot=gr.Chatbot(
            height=650,
            value=get_ui_history(),
            placeholder=(
                "Hi, I'm MyAlly. You can share how you're feeling or ask a "
                "question about stress, anxiety, sleep, or anything on your mind."
            ),
        ),
        textbox=gr.Textbox(
            placeholder="Type your message here …",
            container=False,
        ),
        examples=[
            "I've been feeling really overwhelmed with exams lately.",
            "I feel so lonely here, I don't know anyone.",
            "What are some coping strategies for anxiety?",
            "I haven't been able to sleep for days because of stress.",
        ],
        cache_examples=False,
    )


def launch_ui() -> None:
    """Build and launch the Gradio UI."""
    ui = build_ui()
    print("MyAlly is ready. Logs → rag_reference_logs.jsonl")
    ui.launch(inbrowser=True)
