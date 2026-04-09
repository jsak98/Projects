import streamlit as st
from datetime import date
from services.patient_service import PatientService

st.title("👥 Patients")

svc = PatientService()
user = st.session_state.get('user', {})
tab_list, tab_add = st.tabs(["Patient List", "Add New Patient"])

# ── LIST TAB ──────────────────────────────────────────────────
with tab_list:
    search = st.text_input("🔍 Search by name or phone", placeholder="Start typing...")
    if search:
        result = svc.search(search)
    else:
        result = svc.get_all()

    if not result.success:
        st.error(result.message)
    elif not result.data:
        st.info("No patients found.")
    else:
        for p in result.data:
            with st.expander(f"👤 {p.full_name}  |  📞 {p.phone}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**DOB:** {p.dob or '—'}")
                    st.write(f"**Gender:** {p.gender or '—'}")
                    st.write(f"**Blood Type:** {p.blood_type or '—'}")
                    st.write(f"**Email:** {p.email or '—'}")
                    st.write(f"**Address:** {p.address or '—'}")
                with col2:
                    st.write(f"**Allergies:** {p.allergies or '—'}")
                    st.write(f"**Chronic Conditions:** {p.chronic_conditions or '—'}")
                    st.write(f"**Emergency Contact:** {p.emergency_contact_name or '—'} {p.emergency_contact_phone or ''}")
                    st.write(f"**Insurance:** {p.insurance_provider or '—'} / {p.insurance_id or '—'}")
                    st.write(f"**Consent:** {'✅' if p.consent_given_at else '❌'}")
                    st.write(f"**Telegram:** {'✅ Linked' if p.telegram_chat_id else '❌ Not linked'}")

                st.divider()
                edit_col, del_col = st.columns([1, 1])

                # Edit
                with edit_col:
                    if st.button("✏️ Edit", key=f"edit_{p.id}"):
                        st.session_state[f'editing_{p.id}'] = True

                # Delete (doctor only)
                with del_col:
                    if user.get('role') == 'doctor':
                        if st.button("🗑️ Delete", key=f"del_{p.id}", type="secondary"):
                            st.session_state[f'confirm_delete_{p.id}'] = True

                if st.session_state.get(f'confirm_delete_{p.id}'):
                    st.warning(f"Are you sure you want to delete **{p.full_name}**? This cannot be undone.")
                    y, n = st.columns(2)
                    with y:
                        if st.button("Yes, delete", key=f"yes_{p.id}", type="primary"):
                            r = svc.delete(p.id, user_id=user.get('id'))
                            if r.success:
                                st.success(r.message)
                                st.session_state.pop(f'confirm_delete_{p.id}', None)
                                st.rerun()
                            else:
                                st.error(r.message)
                    with n:
                        if st.button("Cancel", key=f"no_{p.id}"):
                            st.session_state.pop(f'confirm_delete_{p.id}', None)
                            st.rerun()

                # Inline Edit Form
                if st.session_state.get(f'editing_{p.id}'):
                    st.subheader("Edit Patient")
                    with st.form(key=f"edit_form_{p.id}"):
                        f_name   = st.text_input("Full Name*", value=p.full_name,                    key=f"f_name_{p.id}")
                        f_phone  = st.text_input("Phone*", value=p.phone,                            key=f"f_phone_{p.id}")
                        f_dob    = st.date_input("Date of Birth", value=p.dob, min_value=date(1950, 1, 1), max_value=date.today(), key=f"f_dob_{p.id}")
                        f_gender = st.selectbox("Gender", ['', 'male', 'female', 'other'],
                                                index=['', 'male', 'female', 'other'].index(p.gender or ''), key=f"f_gender_{p.id}")
                        f_blood  = st.selectbox("Blood Type",
                                                ['', 'A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-'],
                                                index=['', 'A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-'].index(p.blood_type or ''), key=f"f_blood_{p.id}")
                        f_email  = st.text_input("Email", value=p.email or '',                       key=f"f_email_{p.id}")
                        f_addr   = st.text_area("Address", value=p.address or '',                    key=f"f_addr_{p.id}")
                        f_allerg = st.text_area("Allergies", value=p.allergies or '',                key=f"f_allerg_{p.id}")
                        f_chron  = st.text_area("Chronic Conditions", value=p.chronic_conditions or '', key=f"f_chron_{p.id}")
                        f_ecname = st.text_input("Emergency Contact Name", value=p.emergency_contact_name or '', key=f"f_ecname_{p.id}")
                        f_ecph   = st.text_input("Emergency Contact Phone", value=p.emergency_contact_phone or '', key=f"f_ecph_{p.id}")
                        f_ins    = st.text_input("Insurance Provider", value=p.insurance_provider or '', key=f"f_ins_{p.id}")
                        f_insid  = st.text_input("Insurance ID", value=p.insurance_id or '',         key=f"f_insid_{p.id}")
                        save = st.form_submit_button("💾 Save Changes")

                    if save:
                        r = svc.update(p.id, {
                            'full_name': f_name, 'phone': f_phone,
                            'dob': f_dob, 'gender': f_gender or None,
                            'blood_type': f_blood or None,
                            'email': f_email, 'address': f_addr,
                            'allergies': f_allerg,
                            'chronic_conditions': f_chron,
                            'emergency_contact_name': f_ecname,
                            'emergency_contact_phone': f_ecph,
                            'insurance_provider': f_ins, 'insurance_id': f_insid,
                        }, user_id=user.get('id'))
                        if r.success:
                            st.success(r.message)
                            st.session_state.pop(f'editing_{p.id}', None)
                            st.rerun()
                        else:
                            st.error(r.message)


# ── ADD TAB ───────────────────────────────────────────────────
with tab_add:
    st.subheader("New Patient Registration")
    with st.form("add_patient_form"):
        col1, col2 = st.columns(2)
        with col1:
            n_name   = st.text_input("Full Name *")
            n_phone  = st.text_input("Phone *")
            n_dob    = st.date_input("Date of Birth", value=None, min_value=date(1950, 1, 1), max_value=date.today())
            n_gender = st.selectbox("Gender", ['', 'male', 'female', 'other'])
            n_blood  = st.selectbox("Blood Type", ['', 'A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-'])
            n_email  = st.text_input("Email")
        with col2:
            n_addr   = st.text_area("Address")
            n_allerg = st.text_area("Allergies")
            n_chron  = st.text_area("Chronic Conditions")
            n_ecname = st.text_input("Emergency Contact Name")
            n_ecph   = st.text_input("Emergency Contact Phone")
            n_ins    = st.text_input("Insurance Provider")
            n_insid  = st.text_input("Insurance ID")

        st.divider()
        n_consent = st.checkbox("Patient has given consent for data collection (DPDP Act)")
        submitted = st.form_submit_button("➕ Register Patient", type="primary")

    if submitted:
        r = svc.create({
            'full_name': n_name, 'phone': n_phone,
            'dob': n_dob, 'gender': n_gender or None,
            'blood_type': n_blood or None,
            'email': n_email, 'address': n_addr,
            'allergies': n_allerg, 'chronic_conditions': n_chron,
            'emergency_contact_name': n_ecname,
            'emergency_contact_phone': n_ecph,
            'insurance_provider': n_ins, 'insurance_id': n_insid,
            'consent_given': n_consent,
        }, user_id=user.get('id'))
        if r.success:
            st.success(r.message)
        else:
            st.error(r.message)
