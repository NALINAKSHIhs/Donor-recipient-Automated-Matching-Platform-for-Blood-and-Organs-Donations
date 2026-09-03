"""
Page: Dashboard – platform statistics and AI-generated summary.
"""

import streamlit as st
from database import get_all_donors, get_all_requests, get_connection
from ai_assistant import generate_stats_summary
from collections import Counter


def _get_stats() -> dict:
    donors  = get_all_donors()
    all_req = get_all_requests()
    open_r  = [r for r in all_req if r["status"] == "Open"]

    conn = get_connection()
    total_matches = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
    conn.close()

    # Most requested organ
    if all_req:
        top_organ = Counter(r["needed_organ"] for r in all_req).most_common(1)[0][0]
    else:
        top_organ = "N/A"

    # Most common donor blood type
    if donors:
        top_blood = Counter(d["blood_type"] for d in donors).most_common(1)[0][0]
    else:
        top_blood = "N/A"

    # Blood-type distribution in requests
    bt_req_counter   = Counter(r["blood_type"]   for r in all_req)
    organ_req_counter= Counter(r["needed_organ"] for r in all_req)
    bt_donor_counter = Counter(d["blood_type"]   for d in donors)

    return {
        "total_donors":    len(donors),
        "active_donors":   sum(1 for d in donors if d.get("available")),
        "open_requests":   len(open_r),
        "total_requests":  len(all_req),
        "total_matches":   total_matches,
        "top_organ":       top_organ,
        "top_blood":       top_blood,
        "bt_req":          bt_req_counter,
        "organ_req":       organ_req_counter,
        "bt_donor":        bt_donor_counter,
        "donors":          donors,
        "requests":        all_req,
    }


def show():
    st.title("📊 Platform Dashboard")
    st.markdown("Real-time overview of all donors, requests, and matches on the platform.")

    stats = _get_stats()

    # ── KPI Row ────────────────────────────────────────────────────────────────
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    kpi1.metric("Total Donors",     stats["total_donors"])
    kpi2.metric("Active Donors",    stats["active_donors"])
    kpi3.metric("Open Requests",    stats["open_requests"])
    kpi4.metric("Total Requests",   stats["total_requests"])
    kpi5.metric("Matches Made",     stats["total_matches"])

    st.divider()

    # ── AI Summary ─────────────────────────────────────────────────────────────
    if st.session_state.get("gemini_ready", False):
        if st.button("🤖 Generate AI Platform Summary", use_container_width=True):
            with st.spinner("Generating summary with Gemini 2.5 Flash…"):
                summary = generate_stats_summary(stats)
            st.info(summary)
    else:
        st.info(
            "💡 Add your Gemini API key in the sidebar to enable AI-generated platform summaries."
        )

    st.divider()

    # ── Charts ──────────────────────────────────────────────────────────────────
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("🩸 Donor Blood-Type Distribution")
        if stats["bt_donor"]:
            bt_labels = list(stats["bt_donor"].keys())
            bt_values = list(stats["bt_donor"].values())
            chart_data = {"Blood Type": bt_labels, "Count": bt_values}
            st.bar_chart(chart_data, x="Blood Type", y="Count", use_container_width=True)
        else:
            st.info("No donor data yet.")

    with col_r:
        st.subheader("🫀 Most Requested Organs")
        if stats["organ_req"]:
            org_labels = list(stats["organ_req"].keys())
            org_values = list(stats["organ_req"].values())
            chart_data2 = {"Organ": org_labels, "Requests": org_values}
            st.bar_chart(chart_data2, x="Organ", y="Requests", use_container_width=True)
        else:
            st.info("No request data yet.")

    col_l2, col_r2 = st.columns(2)
    with col_l2:
        st.subheader("📋 Requests by Blood Type")
        if stats["bt_req"]:
            bt_r_labels = list(stats["bt_req"].keys())
            bt_r_values = list(stats["bt_req"].values())
            chart_data3 = {"Blood Type": bt_r_labels, "Requests": bt_r_values}
            st.bar_chart(chart_data3, x="Blood Type", y="Requests", use_container_width=True)
        else:
            st.info("No request data yet.")

    with col_r2:
        st.subheader("📅 Request Status Breakdown")
        if stats["requests"]:
            status_counter = Counter(r["status"] for r in stats["requests"])
            s_labels = list(status_counter.keys())
            s_values = list(status_counter.values())
            chart_data4 = {"Status": s_labels, "Count": s_values}
            st.bar_chart(chart_data4, x="Status", y="Count", use_container_width=True)
        else:
            st.info("No request data yet.")

    st.divider()

    # ── Recent Activity ────────────────────────────────────────────────────────
    st.subheader("🕒 Recent Activity")
    tab_d, tab_r = st.tabs(["Latest Donors", "Latest Requests"])

    with tab_d:
        donors_sorted = sorted(
            stats["donors"], key=lambda x: x["registered_at"], reverse=True
        )[:10]
        if donors_sorted:
            display = [
                {
                    "Name":       d["name"],
                    "Blood Type": d["blood_type"],
                    "Organs":     ", ".join(d["organs"]),
                    "Location":   f"{d['city']}, {d['state']}",
                    "Registered": d["registered_at"],
                }
                for d in donors_sorted
            ]
            st.dataframe(display, use_container_width=True)
        else:
            st.info("No donors yet.")

    with tab_r:
        reqs_sorted = sorted(
            stats["requests"], key=lambda x: x["posted_at"], reverse=True
        )[:10]
        if reqs_sorted:
            display_r = [
                {
                    "Patient":    r["patient_name"],
                    "Blood Type": r["blood_type"],
                    "Organ":      r["needed_organ"],
                    "Urgency":    r["urgency"],
                    "Status":     r["status"],
                    "Hospital":   r["hospital"],
                    "Posted":     r["posted_at"],
                }
                for r in reqs_sorted
            ]
            st.dataframe(display_r, use_container_width=True)
        else:
            st.info("No requests yet.")
