"""
LifeLink – AI-Powered Blood & Organ Donation Matching Platform
Main Streamlit entry point.

Run with:
    streamlit run app.py
"""

import streamlit as st
from database import init_db
from ai_assistant import init_gemini

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LifeLink – Donation Matching Platform",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Initialise database (idempotent) ──────────────────────────────────────────
init_db()

# ── Session defaults ──────────────────────────────────────────────────────────
if "gemini_ready" not in st.session_state:
    st.session_state["gemini_ready"] = False
if "page" not in st.session_state:
    st.session_state["page"] = "Dashboard"

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/"
        "Red_Cross_Symbol_of_Switzerland.svg/240px-Red_Cross_Symbol_of_Switzerland.svg.png",
        width=60,
    )
    st.title("🩸 LifeLink")
    st.caption("AI-Powered Donation Matching")
    st.divider()

    # Navigation
    PAGES = {
        "📊 Dashboard":           "Dashboard",
        "🩸 Register Donor":      "Register Donor",
        "🚨 Post Request":        "Post Request",
        "🔍 Find Matches":        "Find Matches",
        "🤖 AI Triage Assistant": "AI Assistant",
    }
    for label, page_id in PAGES.items():
        if st.button(label, use_container_width=True, key=f"nav_{page_id}"):
            st.session_state["page"] = page_id

    st.divider()

    # Gemini API Key configuration
    st.subheader("🔑 Gemini API Key")
    api_key_input = st.text_input(
        "Enter your Gemini API Key",
        type="password",
        placeholder="AIza…",
        help="Get your free key at https://aistudio.google.com/",
    )
    if st.button("✅ Activate AI Features", use_container_width=True):
        if api_key_input.strip():
            try:
                init_gemini(api_key_input.strip())
                st.session_state["gemini_ready"] = True
                st.success("Gemini 2.5 Flash activated!")
            except Exception as e:
                st.error(f"Failed to initialise Gemini: {e}")
        else:
            st.warning("Please enter a valid API key.")

    if st.session_state.get("gemini_ready"):
        st.success("✅ AI Active (Gemini 2.5 Flash)")
    else:
        st.info("⚠️ AI features inactive")

    st.divider()
    st.caption(
        "LifeLink v1.0  |  Built with Streamlit & Gemini 2.5 Flash\n\n"
        "Saving lives through intelligent matching."
    )

# ── Page routing ────────────────────────────────────────────────────────────────
import pages_dashboard as dash
import pages_donor    as donor
import pages_request  as request_page
import pages_match    as match_page
import pages_chat     as chat_page

current = st.session_state.get("page", "Dashboard")

if current == "Dashboard":
    dash.show()
elif current == "Register Donor":
    donor.show()
elif current == "Post Request":
    request_page.show()
elif current == "Find Matches":
    match_page.show()
elif current == "AI Assistant":
    chat_page.show()
else:
    dash.show()
