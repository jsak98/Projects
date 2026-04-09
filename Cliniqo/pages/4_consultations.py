import streamlit as st
from datetime import date
from services.consultation_service import ConsultationService, PrescriptionService
from services.patient_service import PatientService
from services.notification_service import notify_consultation_report

st.title("🩺 Consultations")

cons_svc    = ConsultationService()
rx_svc      = PrescriptionService()
patient_svc = PatientService()
user        = st.session_state.get('user', {})

tab_view, tab_add = st.tabs(["View Consultations", "New Consultation"])

# ── VIEW ─────────────────────────────────────────────────────
with tab_view:
    search_view = st.text_input("🔍 Search patient by name or phone", key="cons_search_view")
    if search_view:
        pr = patient_svc.search(search_view)
        if pr.success and pr.data:
            options = {f"{p.full_name} — {p.phone}": p.id for p in pr.data}
            chosen  = st.selectbox("Select Patient", list(options.keys()), key="cons_select_view")
            patient_id = options[chosen]

            cr = cons_svc.get_by_patient(patient_id)
            if not cr.success:
                st.error(cr.message)
            elif not cr.data:
                st.info("No consultations found for this patient.")
            else:
                for c in cr.data:
                    with st.expander(f"📋 {c['visit_date']} — {c.get('diagnosis') or 'No diagnosis recorded'}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Doctor:** {c['doctor_name']}")
                            st.write(f"**Chief Complaint:** {c.get('chief_complaint') or '—'}")
                            st.write(f"**Diagnosis:** {c.get('diagnosis') or '—'}")
                        with col2:
                            st.write(f"**Clinical Notes:** {c.get('clinical_notes') or '—'}")
                            st.write(f"**Tests Ordered:** {c.get('tests_ordered') or '—'}")
                            st.write(f"**Follow-up Date:** {c.get('follow_up_date') or '—'}")

                        st.divider()
                        st.markdown("**💊 Prescriptions**")
                        rx = rx_svc.get_by_consultation(c['id'])
                        if rx.success and rx.data:
                            for p in rx.data:
                                with st.container(border=True):
                                    c1, c2, c3 = st.columns(3)
                                    with c1:
                                        st.markdown(f"**{p['medication_name']}**")
                                        st.caption(f"Dosage: {p.get('dosage') or '—'}")
                                    with c2:
                                        st.caption(f"Frequency: {p.get('frequency') or '—'}")
                                        st.caption(f"Duration: {p.get('duration_days') or '—'} days")
                                    with c3:
                                        st.caption(f"Refills: {p.get('refills_allowed', 0)}")
                                        if user.get('role') == 'doctor':
                                            if st.button("🗑️", key=f"del_rx_{p['id']}"):
                                                r = rx_svc.delete(p['id'], user_id=user.get('id'))
                                                st.toast(r.message)
                                                st.rerun()
                                    if p.get('instructions'):
                                        st.caption(f"📝 {p['instructions']}")
                        else:
                            st.caption("No prescriptions for this visit.")

                        if user.get('role') == 'doctor':
                            with st.popover("➕ Add Prescription"):
                                with st.form(key=f"rx_form_{c['id']}"):
                                    med_name      = st.text_input("Medication Name *", key=f"rx_med_{c['id']}")
                                    rc1, rc2      = st.columns(2)
                                    with rc1:
                                        dosage    = st.text_input("Dosage",    key=f"rx_dose_{c['id']}")
                                        frequency = st.text_input("Frequency", key=f"rx_freq_{c['id']}")
                                    with rc2:
                                        duration  = st.number_input("Duration (days)", min_value=1, max_value=365, value=7, key=f"rx_dur_{c['id']}")
                                        refills   = st.number_input("Refills",          min_value=0, max_value=10,  value=0, key=f"rx_ref_{c['id']}")
                                    instructions  = st.text_area("Instructions", key=f"rx_ins_{c['id']}")
                                    add_rx = st.form_submit_button("💾 Save", type="primary")

                                if add_rx:
                                    r = rx_svc.create({
                                        'consultation_id': c['id'],
                                        'patient_id': patient_id,
                                        'medication_name': med_name,
                                        'dosage': dosage,
                                        'frequency': frequency,
                                        'duration_days': duration,
                                        'instructions': instructions,
                                        'refills_allowed': refills,
                                    }, user_id=user.get('id'))
                                    if r.success:
                                        st.success(r.message)
                                        st.rerun()
                                    else:
                                        st.error(r.message)
        else:
            st.info("Search for a patient above to view their consultations.")

# ── NEW CONSULTATION ──────────────────────────────────────────
with tab_add:
    st.subheader("Record New Consultation")

    if user.get('role') != 'doctor':
        st.warning("Only doctors can record consultations.")
    else:
        search_add  = st.text_input("🔍 Search patient", key="cons_search_add")
        patient_id2 = None
        patient_obj = None

        if search_add:
            pr2 = patient_svc.search(search_add)
            if pr2.success and pr2.data:
                options2    = {f"{p.full_name} — {p.phone}": p for p in pr2.data}
                chosen2     = st.selectbox("Select Patient", list(options2.keys()), key="cons_select_add")
                patient_obj = options2[chosen2]
                patient_id2 = patient_obj.id
            else:
                st.warning("No patients found.")

        with st.form("new_consultation"):
            visit_date      = st.date_input("Visit Date", value=date.today())
            chief_complaint = st.text_input("Chief Complaint")
            clinical_notes  = st.text_area("Clinical Notes")
            diagnosis       = st.text_input("Diagnosis")
            tests_ordered   = st.text_area("Tests Ordered")
            follow_up_date  = st.date_input("Follow-up Date (optional)", value=None)

            st.divider()
            st.markdown("**💊 Prescriptions** — fill only the ones needed")

            prescriptions = []
            for i in range(1, 6):
                st.markdown(f"*Medication {i}*")
                pc1, pc2, pc3 = st.columns(3)
                with pc1:
                    mname = st.text_input("Name",              key=f"med_name_{i}")
                    dose  = st.text_input("Dosage",            key=f"med_dose_{i}")
                with pc2:
                    freq  = st.text_input("Frequency",         key=f"med_freq_{i}")
                    dur   = st.number_input("Duration (days)", min_value=0, max_value=365, value=0, key=f"med_dur_{i}")
                with pc3:
                    ref   = st.number_input("Refills",          min_value=0, max_value=10,  value=0, key=f"med_ref_{i}")
                    ins   = st.text_input("Instructions",       key=f"med_ins_{i}")

                if mname.strip():
                    prescriptions.append({
                        'medication_name': mname.strip(),
                        'dosage': dose, 'frequency': freq,
                        'duration_days': dur if dur > 0 else None,
                        'refills_allowed': ref, 'instructions': ins,
                    })

            submitted = st.form_submit_button("💾 Save Consultation", type="primary")

        if submitted:
            if not patient_id2:
                st.error("Please select a patient.")
            else:
                r = cons_svc.create({
                    'patient_id':       patient_id2,
                    'doctor_id':        user['id'],
                    'visit_date':       visit_date,
                    'chief_complaint':  chief_complaint,
                    'clinical_notes':   clinical_notes,
                    'diagnosis':        diagnosis,
                    'tests_ordered':    tests_ordered,
                    'follow_up_date':   follow_up_date,
                }, user_id=user.get('id'))

                if r.success:
                    for rx_data in prescriptions:
                        rx_data['consultation_id'] = r.data.id
                        rx_data['patient_id']      = patient_id2
                        rx_svc.create(rx_data, user_id=user.get('id'))

                    st.success(f"Consultation saved with {len(prescriptions)} prescription(s) ✅")

                    # Send report notification
                    if patient_obj:
                        notify_consultation_report(
                            patient_name=patient_obj.full_name,
                            patient_email=patient_obj.email,
                            patient_phone=patient_obj.phone,
                            visit_date=visit_date,
                            diagnosis=diagnosis,
                            prescriptions=prescriptions,
                            follow_up_date=follow_up_date,
                            telegram_chat_id=patient_obj.telegram_chat_id,
                        )
                        st.info("📧 Consultation report sent via Email & Telegram")
                else:
                    st.error(r.message)
