"""
Page: Urgent Request Posting
"""

import streamlit as st
from database import add_request, get_all_requests, update_request_status
from matching_engine import ORGANS, BLOOD_COMPATIBILITY
from ai_assistant import analyze_urgency

BLOOD_TYPES = list(BLOOD_COMPATIBILITY.keys())

INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
    "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim",
    "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
    "West Bengal", "Delhi", "Chandigarh", "Puducherry", "Other",
]

URGENCY_COLORS = {
    "Critical": "🔴",
    "High":     "🟠",
    "Medium":   "🟡",
    "Low":      "🟢",
}


def show():
    st.title("🚨 Urgent Donation Requests")
    st.markdown(
        "Post an urgent request for blood or organ donation on behalf of a patient."
    )

    tab_post, tab_view = st.tabs(["📢 Post a Request", "📋 View All Requests"])

    # ── Post a Request ─────────────────────────────────────────────────────────
    with tab_post:
        with st.form("request_form", clear_on_submit=True):
            st.subheader("Patient Information")
            col1, col2, col3 = st.columns(3)
            with col1:
                patient_name = st.text_input("Patient Full Name *", placeholder="e.g. Priya Sharma")
            with col2:
                age = st.number_input("Patient Age *", min_value=0, max_value=120, value=35)
            with col3:
                gender = st.selectbox("Gender *", ["Male", "Female", "Other"])

            col4, col5 = st.columns(2)
            with col4:
                contact_phone = st.text_input(
                    "Contact Phone *", placeholder="Family / Hospital contact number"
                )
            with col5:
                contact_email = st.text_input("Contact Email (optional)")

            st.divider()
            st.subheader("Medical Need")

            col6, col7, col8 = st.columns(3)
            with col6:
                blood_type = st.selectbox("Patient Blood Type *", BLOOD_TYPES)
            with col7:
                needed_organ = st.selectbox("Organ / Component Needed *", ORGANS)
            with col8:
                urgency = st.selectbox(
                    "Urgency Level *",
                    ["Critical", "High", "Medium", "Low"],
                    index=1,
                    help="Critical = life-threatening within 24 h; High = within a week.",
                )

            notes = st.text_area(
                "Clinical Notes (optional)",
                placeholder="Briefly describe the patient's condition, doctor's notes, etc.",
                height=100,
            )

            ai_urgency_btn = st.form_submit_button(
                "🤖 AI Urgency Analysis (optional)", use_container_width=False
            )

            st.divider()
            st.subheader("Hospital & Location")

            hospital = st.text_input("Hospital Name *", placeholder="e.g. AIIMS Delhi")
            col9, col10, col11 = st.columns(3)
            with col9:
                city = st.text_input("City *", placeholder="e.g. Delhi")
            with col10:
                state = st.selectbox("State *", INDIAN_STATES, key="req_state")
            with col11:
                country = st.text_input("Country", value="India", key="req_country")

            col12, col13 = st.columns(2)
            with col12:
                lat = st.number_input(
                    "Latitude (optional)", min_value=-90.0, max_value=90.0,
                    value=0.0, format="%.4f", key="req_lat"
                )
            with col13:
                lon = st.number_input(
                    "Longitude (optional)", min_value=-180.0, max_value=180.0,
                    value=0.0, format="%.4f", key="req_lon"
                )

            st.divider()
            submitted = st.form_submit_button("🚨 Post Urgent Request", use_container_width=True)

        # AI Urgency (outside form so it doesn't clear on submit)
        if ai_urgency_btn and st.session_state.get("gemini_ready", False):
            with st.spinner("Analysing urgency with AI…"):
                analysis = analyze_urgency(notes, needed_organ, int(age))
            st.info(f"**AI Urgency Analysis:**\n\n{analysis}")
        elif ai_urgency_btn:
            st.warning("Configure your Gemini API key in the sidebar to use AI analysis.")

        if submitted:
            errors = []
            if not patient_name.strip():
                errors.append("Patient name is required.")
            if not contact_phone.strip():
                errors.append("Contact phone is required.")
            if not hospital.strip():
                errors.append("Hospital name is required.")
            if not city.strip():
                errors.append("City is required.")

            if errors:
                for e in errors:
                    st.error(e)
            else:
                req_data = {
                    "patient_name":  patient_name.strip(),
                    "age":           int(age),
                    "gender":        gender,
                    "blood_type":    blood_type,
                    "phone":         contact_phone.strip(),
                    "email":         contact_email.strip(),
                    "hospital":      hospital.strip(),
                    "city":          city.strip(),
                    "state":         state,
                    "country":       country.strip() or "India",
                    "lat":           lat if lat != 0.0 else None,
                    "lon":           lon if lon != 0.0 else None,
                    "needed_organ":  needed_organ,
                    "urgency":       urgency,
                    "notes":         notes.strip(),
                }
                req_id = add_request(req_data)
                st.success(
                    f"✅ Request posted! Request ID **#{req_id}**. "
                    "Go to **Find Matches** to find compatible donors."
                )
                st.balloons()

    # ── View All Requests ──────────────────────────────────────────────────────
    with tab_view:
        st.subheader("Posted Requests")

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            status_filter = st.selectbox(
                "Filter by Status", ["All", "Open", "Matched", "Fulfilled", "Closed"],
                key="req_status_filter"
            )
        with col_s2:
            organ_filter = st.selectbox(
                "Filter by Organ", ["All"] + ORGANS, key="req_organ_filter"
            )

        all_requests = get_all_requests(status=None if status_filter == "All" else status_filter)

        if organ_filter != "All":
            all_requests = [r for r in all_requests if r["needed_organ"] == organ_filter]

        if not all_requests:
            st.info("No requests found with the selected filters.")
            return

        st.caption(f"Showing **{len(all_requests)}** request(s)")

        for req in all_requests:
            urgency_icon = URGENCY_COLORS.get(req["urgency"], "⚪")
            with st.expander(
                f"{urgency_icon} #{req['id']} — {req['patient_name']} "
                f"({req['blood_type']}, {req['needed_organ']}) — "
                f"{req['hospital']}, {req['city']}"
            ):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Blood Type", req["blood_type"])
                c2.metric("Organ Needed", req["needed_organ"])
                c3.metric("Urgency", req["urgency"])
                c4.metric("Status", req["status"])

                st.write(f"**Patient:** {req['patient_name']}, Age {req['age']}, {req['gender']}")
                st.write(f"**Hospital:** {req['hospital']}, {req['city']}, {req['state']}")
                st.write(f"**Contact:** {req['phone']}")
                if req.get("notes"):
                    st.write(f"**Notes:** {req['notes']}")
                st.caption(f"Posted: {req['posted_at']}")

                # Quick status update
                new_status = st.selectbox(
                    "Update status",
                    ["Open", "Matched", "Fulfilled", "Closed"],
                    index=["Open", "Matched", "Fulfilled", "Closed"].index(req["status"]),
                    key=f"status_{req['id']}",
                )
                if st.button("Update", key=f"upd_{req['id']}"):
                    update_request_status(req["id"], new_status)
                    st.success("Status updated!")
                    st.rerun()
