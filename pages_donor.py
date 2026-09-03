"""
Page: Donor Registration
"""

import streamlit as st
from database import add_donor, get_all_donors
from matching_engine import ORGANS, BLOOD_COMPATIBILITY
from ai_assistant import donor_health_tips

BLOOD_TYPES = list(BLOOD_COMPATIBILITY.keys())

INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
    "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim",
    "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
    "West Bengal", "Delhi", "Chandigarh", "Puducherry", "Other",
]


def show():
    st.title("🩸 Donor Registration")
    st.markdown(
        "Register as a blood or organ donor. Your registration could save a life today."
    )

    tab_register, tab_view = st.tabs(["📋 Register as Donor", "👥 View All Donors"])

    # ── Registration Form ──────────────────────────────────────────────────────
    with tab_register:
        with st.form("donor_form", clear_on_submit=True):
            st.subheader("Personal Information")
            col1, col2, col3 = st.columns(3)
            with col1:
                name = st.text_input("Full Name *", placeholder="e.g. Arjun Kumar")
            with col2:
                age = st.number_input("Age *", min_value=18, max_value=65, value=25)
            with col3:
                gender = st.selectbox("Gender *", ["Male", "Female", "Other"])

            col4, col5 = st.columns(2)
            with col4:
                phone = st.text_input("Phone Number *", placeholder="+91 9876543210")
            with col5:
                email = st.text_input("Email (optional)", placeholder="donor@email.com")

            st.divider()
            st.subheader("Medical Information")

            col6, col7 = st.columns(2)
            with col6:
                blood_type = st.selectbox("Blood Type *", BLOOD_TYPES)
            with col7:
                organs = st.multiselect(
                    "Organs / Components willing to donate *",
                    options=ORGANS,
                    default=["Blood"],
                    help="You can select multiple organs. 'Blood' means whole-blood donation.",
                )

            st.divider()
            st.subheader("Location")
            col8, col9, col10 = st.columns(3)
            with col8:
                city = st.text_input("City *", placeholder="e.g. Mumbai")
            with col9:
                state = st.selectbox("State *", INDIAN_STATES)
            with col10:
                country = st.text_input("Country", value="India")

            col11, col12 = st.columns(2)
            with col11:
                lat = st.number_input(
                    "Latitude (optional, for precise matching)",
                    min_value=-90.0, max_value=90.0, value=0.0, format="%.4f"
                )
            with col12:
                lon = st.number_input(
                    "Longitude (optional, for precise matching)",
                    min_value=-180.0, max_value=180.0, value=0.0, format="%.4f"
                )

            st.divider()
            consent = st.checkbox(
                "I voluntarily consent to donate and confirm the above information is accurate. *"
            )

            submitted = st.form_submit_button("✅ Register as Donor", use_container_width=True)

        if submitted:
            # Validation
            errors = []
            if not name.strip():
                errors.append("Full name is required.")
            if not phone.strip():
                errors.append("Phone number is required.")
            if not city.strip():
                errors.append("City is required.")
            if not organs:
                errors.append("Please select at least one organ / blood.")
            if not consent:
                errors.append("You must provide consent to register.")

            if errors:
                for e in errors:
                    st.error(e)
            else:
                donor_data = {
                    "name":       name.strip(),
                    "age":        int(age),
                    "gender":     gender,
                    "blood_type": blood_type,
                    "phone":      phone.strip(),
                    "email":      email.strip(),
                    "city":       city.strip(),
                    "state":      state,
                    "country":    country.strip() or "India",
                    "lat":        lat if lat != 0.0 else None,
                    "lon":        lon if lon != 0.0 else None,
                    "organs":     organs,
                }
                donor_id = add_donor(donor_data)
                st.success(
                    f"🎉 Thank you, **{name}**! You are registered as Donor #{donor_id}. "
                    "Your generosity can save lives!"
                )
                st.balloons()

                # AI Health Tips
                if st.session_state.get("gemini_ready", False):
                    with st.spinner("Generating personalised health tips for you…"):
                        tips = donor_health_tips(blood_type, organs)
                    st.info("### 💡 Personalised Preparation Tips\n\n" + tips)

    # ── View All Donors ────────────────────────────────────────────────────────
    with tab_view:
        st.subheader("Registered Donors")
        donors = get_all_donors()

        if not donors:
            st.info("No donors registered yet. Be the first!")
            return

        # Filter controls
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filter_bt = st.selectbox("Filter by Blood Type", ["All"] + BLOOD_TYPES, key="fbt")
        with col_f2:
            filter_organ = st.selectbox("Filter by Organ", ["All"] + ORGANS, key="forg")
        with col_f3:
            filter_state = st.selectbox(
                "Filter by State", ["All"] + sorted({d["state"] for d in donors}), key="fst"
            )

        filtered = donors
        if filter_bt != "All":
            filtered = [d for d in filtered if d["blood_type"] == filter_bt]
        if filter_organ != "All":
            filtered = [d for d in filtered if filter_organ in d.get("organs", [])]
        if filter_state != "All":
            filtered = [d for d in filtered if d["state"] == filter_state]

        st.caption(f"Showing **{len(filtered)}** of **{len(donors)}** active donors")

        for donor in filtered:
            with st.expander(
                f"🩸 {donor['name']} — {donor['blood_type']} — {donor['city']}, {donor['state']}"
            ):
                c1, c2, c3 = st.columns(3)
                c1.metric("Blood Type", donor["blood_type"])
                c2.metric("Age", donor["age"])
                c3.metric("Gender", donor["gender"])

                st.write(f"**Organs available:** {', '.join(donor['organs'])}")
                st.write(f"**Location:** {donor['city']}, {donor['state']}, {donor['country']}")
                st.write(f"**Phone:** {donor['phone']}")
                if donor.get("email"):
                    st.write(f"**Email:** {donor['email']}")
                st.caption(f"Registered: {donor['registered_at']}")
