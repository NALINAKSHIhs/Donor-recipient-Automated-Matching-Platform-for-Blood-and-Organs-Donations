"""
Page: AI Triage Assistant – conversational chatbot powered by Gemini 2.5 Flash.
"""

import streamlit as st
from ai_assistant import triage_chat


def show():
    st.title("🤖 AI Triage Assistant")
    st.markdown(
        "Chat with **LifeLink AI** — ask about blood type compatibility, organ donation, "
        "the registration process, or anything related to donations."
    )

    if not st.session_state.get("gemini_ready", False):
        st.warning(
            "⚠️ Please enter your **Gemini API Key** in the sidebar to activate the AI Assistant."
        )
        st.stop()

    # Initialise chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "chat_display" not in st.session_state:
        # Display format: list of {"role": "user"|"assistant", "content": "text"}
        st.session_state.chat_display = [
            {
                "role": "assistant",
                "content": (
                    "Hello! I'm LifeLink AI, your donation coordination assistant. "
                    "I can help you understand blood type compatibility, explain the donation process, "
                    "or guide you through posting an urgent request. How can I assist you today?"
                ),
            }
        ]

    # Display conversation
    for msg in st.session_state.chat_display:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Quick question chips
    st.markdown("**Quick Questions:**")
    qcol1, qcol2, qcol3, qcol4 = st.columns(4)
    quick_questions = [
        "What blood types are compatible with O-?",
        "Can I donate a kidney while alive?",
        "How does the matching score work?",
        "What should I do to prepare for blood donation?",
    ]
    for i, (col, q) in enumerate(zip([qcol1, qcol2, qcol3, qcol4], quick_questions)):
        if col.button(q, key=f"qq_{i}", use_container_width=True):
            st.session_state["_quick_q"] = q

    # Handle quick question injection
    if "_quick_q" in st.session_state:
        user_input = st.session_state.pop("_quick_q")
    else:
        user_input = None

    # Chat input
    typed = st.chat_input("Ask LifeLink AI anything about donations…")
    if typed:
        user_input = typed

    if user_input:
        # Show user message
        with st.chat_message("user"):
            st.write(user_input)
        st.session_state.chat_display.append({"role": "user", "content": user_input})

        # Build history in Gemini format
        gemini_history = []
        for msg in st.session_state.chat_history:
            gemini_history.append({"role": msg["role"], "parts": [msg["content"]]})

        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                response = triage_chat(gemini_history, user_input)
            st.write(response)

        # Update histories
        st.session_state.chat_display.append({"role": "assistant", "content": response})
        st.session_state.chat_history.append({"role": "user",  "content": user_input})
        st.session_state.chat_history.append({"role": "model", "content": response})

    # Clear chat
    if st.button("🗑️ Clear Conversation", use_container_width=False):
        st.session_state.chat_history = []
        st.session_state.chat_display = []
        st.rerun()
