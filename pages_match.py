"""
Page: Find Matches – runs the matching engine and shows results with AI explanations.
"""

import streamlit as st
from database import (
    get_all_requests, get_request_by_id,
    get_all_donors, get_donor_by_id,
    save_matches, get_matches_for_request,
    update_request_status,
)
from matching_engine import find_top_matches, BLOOD_COMPATIBILITY
from ai_assistant import explain_match

URGENCY_COLORS = {
    "Critical": "🔴",
    "High":     "🟠",
    "Medium":   "🟡",
    "Low":      "🟢",
}


def _score_bar(score: float) -> str:
    filled = int(score * 10)
    bar = "█" * filled + "░" * (10 - filled)
    return f"`{bar}` {score:.0%}"


def show():
    st.title("🔍 Find Matches")
    st.markdown(
        "Select an open request to automatically find the best-matched donors "
        "using blood-type compatibility, organ availability, and location proximity."
    )

    open_requests = get_all_requests(status="Open")
    if not open_requests:
        st.info("No open requests at the moment. Post a request first.")
        return

    # Request selector
    req_options = {
        f"#{r['id']} — {r['patient_name']} ({r['blood_type']}, "
        f"{r['needed_organ']}, {r['urgency']}) @ {r['hospital']}, {r['city']}": r["id"]
        for r in open_requests
    }

    selected_label = st.selectbox("Select a Request", list(req_options.keys()))
    selected_req_id = req_options[selected_label]
    request = get_request_by_id(selected_req_id)

    if not request:
        st.error("Request not found.")
        return

    # Request summary card
    urgency_icon = URGENCY_COLORS.get(request["urgency"], "⚪")
    st.markdown(f"### {urgency_icon} Request #{request['id']} Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Blood Type", request["blood_type"])
    col2.metric("Organ Needed", request["needed_organ"])
    col3.metric("Urgency", request["urgency"])
    col4.metric("Status", request["status"])
    st.write(
        f"**Patient:** {request['patient_name']}, Age {request['age']}  |  "
        f"**Hospital:** {request['hospital']}, {request['city']}, {request['state']}"
    )
    if request.get("notes"):
        st.caption(f"Notes: {request['notes']}")

    st.divider()

    # Matching controls
    col_a, col_b = st.columns(2)
    with col_a:
        top_n = st.slider("Number of top matches to show", 3, 20, 10)
    with col_b:
        ai_explain = st.toggle(
            "🤖 AI Explanation for top match",
            value=False,
            help="Requires Gemini API key configured in the sidebar.",
        )

    run_match = st.button("▶ Run Matching Engine", use_container_width=True, type="primary")

    if run_match:
        donors = get_all_donors()
        if not donors:
            st.warning("No donors registered yet. Please ask donors to register first.")
            return

        with st.spinner("Running compatibility analysis…"):
            matches = find_top_matches(request, donors, top_n=top_n)

        if not matches:
            st.error(
                "No compatible donors found. The matching engine found no donors with "
                "a compatible blood type and the required organ in the database."
            )
            return

        st.success(f"Found **{len(matches)}** compatible donor(s)!")

        # Persist matches to DB
        db_matches = [
            {
                "request_id": selected_req_id,
                "donor_id":   m["donor_id"],
                "score":      m["score"],
                "ai_notes":   "",
                "status":     "Pending",
            }
            for m in matches
        ]
        save_matches(db_matches)
        update_request_status(selected_req_id, "Matched")

        # ── Results table ───────────────────────────────────────────────────
        st.markdown("### 🏆 Top Matched Donors")

        for rank, m in enumerate(matches, start=1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"#{rank}")
            blood_badge = "✅ Exact" if m["blood_match"] == "Exact" else "🔄 Compatible"
            dist_label = f"{m['distance_km']} km away" if m["distance_km"] else "Distance unknown"

            with st.expander(
                f"{medal} {m['donor_name']} — {m['donor_blood_type']} — "
                f"{m['donor_city']}, {m['donor_state']}  |  Score: {m['score']:.0%}"
            ):
                col_x, col_y, col_z = st.columns(3)
                col_x.metric("Match Score", f"{m['score']:.0%}")
                col_y.metric("Blood Match", blood_badge)
                col_z.metric("Distance", dist_label)

                st.write(f"**Blood Type:** {m['donor_blood_type']}  |  {blood_badge}")
                st.write(f"**Available Organs:** {', '.join(m['donor_organs'])}")
                st.write(f"**Contact:** {m['donor_phone']}")
                st.write(f"**Location:** {m['donor_city']}, {m['donor_state']}")

                st.markdown("**Compatibility Score**")
                st.progress(m["score"])

                # AI explanation for top match (rank 1) when toggled
                if ai_explain and rank == 1 and st.session_state.get("gemini_ready", False):
                    donor_full = get_donor_by_id(m["donor_id"])
                    if donor_full:
                        with st.spinner("Generating AI explanation…"):
                            explanation = explain_match(donor_full, request, m["score"])
                        st.info(f"**🤖 AI Match Explanation:**\n\n{explanation}")
                elif ai_explain and rank == 1 and not st.session_state.get("gemini_ready", False):
                    st.warning(
                        "Configure your Gemini API key in the sidebar to see AI explanations."
                    )

        # Quick contact summary
        st.divider()
        st.markdown("### 📞 Quick Contact List")
        contact_data = [
            {
                "Rank":       rank,
                "Donor":      m["donor_name"],
                "Blood Type": m["donor_blood_type"],
                "Organ":      ", ".join(m["donor_organs"]),
                "Location":   f"{m['donor_city']}, {m['donor_state']}",
                "Phone":      m["donor_phone"],
                "Score":      f"{m['score']:.0%}",
            }
            for rank, m in enumerate(matches, start=1)
        ]
        st.dataframe(contact_data, use_container_width=True)

    # ── Previously saved matches ────────────────────────────────────────────
    saved = get_matches_for_request(selected_req_id)
    if saved and not run_match:
        st.info(
            f"This request has **{len(saved)}** previously saved match(es). "
            "Click **Run Matching Engine** to refresh."
        )
        with st.expander("View Saved Matches"):
            for m in saved:
                st.write(
                    f"• **{m['donor_name']}** ({m['donor_bt']}) — "
                    f"{m['donor_city']}, {m['donor_state']} — "
                    f"Score: {m['score']:.0%} — Status: {m['status']}"
                )
