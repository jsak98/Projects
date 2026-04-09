import streamlit as st
from datetime import date, datetime
from services.appointment_service import AppointmentService
from services.patient_service import PatientService
from services.notification_service import notify_appointment_confirmed
from utils.slot_generator import format_slot

st.title("📅 Appointments")

appt_svc = AppointmentService()
patient_svc = PatientService()
user = st.session_state.get('user', {})

tab_today, tab_book, tab_forms, tab_block = st.tabs([
    "Today's Schedule", "Book Appointment", "Form Requests", "Block Slots"
])

# ── TODAY'S SCHEDULE ─────────────────────────────────────────
with tab_today:
    selected_date = st.date_input("Select Date", value=date.today())
    result = appt_svc.get_by_date(selected_date)

    if not result.success:
        st.error(result.message)
    elif not result.data:
        st.info("No appointments for this date.")
    else:
        for a in result.data:
            slot_str = a['time_slot'].strftime('%I:%M %p') if hasattr(a['time_slot'], 'strftime') else str(a['time_slot'])
            status_badge = {'confirmed':'🟢','pending':'🟡','completed':'✅','cancelled':'🔴'}.get(a['status'],'⚪')

            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 4, 3])
                with col1:
                    st.markdown(f"### {slot_str}")
                with col2:
                    st.markdown(f"{status_badge} **{a['full_name']}**")
                    st.caption(f"📞 {a['phone']}  |  {a.get('reason') or 'General checkup'}")
                with col3:
                    if a['status'] == 'pending':
                        if st.button("✅ Confirm", key=f"conf_{a['id']}"):
                            r = appt_svc.confirm(a['id'], user_id=user.get('id'))
                            st.toast(r.message)
                            st.rerun()
                    if a['status'] == 'confirmed':
                        if st.button("🏁 Complete", key=f"comp_{a['id']}"):
                            r = appt_svc.complete(a['id'], user_id=user.get('id'))
                            st.toast(r.message)
                            st.rerun()
                    if a['status'] in ('pending', 'confirmed'):
                        if st.button("❌ Cancel", key=f"canc_{a['id']}"):
                            r = appt_svc.cancel(a['id'], user_id=user.get('id'))
                            st.toast(r.message)
                            st.rerun()

# ── BOOK APPOINTMENT ─────────────────────────────────────────
with tab_book:
    st.subheader("Book a New Appointment")

    search = st.text_input("🔍 Search patient by name or phone")
    patient_id = None

    if search:
        pr = patient_svc.search(search)
        if pr.success and pr.data:
            options = {f"{p.full_name} — {p.phone}": p.id for p in pr.data}
            chosen = st.selectbox("Select Patient", list(options.keys()))
            patient_id = options[chosen]
        else:
            st.warning("No patients found. Register them first in the Patients tab.")

    appt_date = st.date_input("Appointment Date", min_value=date.today())

    if appt_date:
        slot_result = appt_svc.get_available_slots(appt_date)
        if not slot_result.success:
            st.error(slot_result.message)
        elif not slot_result.data:
            st.warning("No available slots on this date.")
        else:
            slots = slot_result.data
            slot_labels = [format_slot(s) for s in slots]
            slot_map = dict(zip(slot_labels, slots))

            st.markdown("**Available Slots**")
            # Display as a visual grid
            cols = st.columns(6)
            selected_slot_label = st.selectbox("Choose a time slot", slot_labels)
            selected_slot = slot_map[selected_slot_label]

    reason = st.text_input("Reason for visit (optional)")

    if st.button("📌 Book Appointment", type="primary"):
        if not patient_id:
            st.error("Please select a patient first.")
        else:
            r = appt_svc.book(
                patient_id=patient_id,
                appt_date=appt_date,
                time_slot=selected_slot,
                reason=reason,
                requested_via='manual',
                status='confirmed',
                doctor_id=user.get('id') if user.get('role') == 'doctor' else None,
                user_id=user.get('id')
            )
            if r.success:
                st.success(r.message)
                # Send confirmation notification
                patient = patient_svc.get_by_id(patient_id).data
                if patient:
                    notify_appointment_confirmed(
                        patient_name=patient.full_name,
                        patient_email=patient.email,
                        patient_phone=patient.phone,
                        appt_date=appt_date,
                        time_slot=selected_slot,
                        telegram_chat_id=patient.telegram_chat_id,
                    )
                    st.info("📧 Confirmation sent via Email & Telegram")
            else:
                st.error(r.message)

# ── GOOGLE FORM REQUESTS ─────────────────────────────────────
with tab_forms:
    st.subheader("📋 Pending Google Form Requests")
    st.caption("These are appointment requests submitted via the Google Form. Review and confirm or reassign slots.")

    if st.button("🔄 Refresh"):
        st.rerun()

    pr = appt_svc.get_pending_form_requests()
    if not pr.success:
        st.error(pr.message)
    elif not pr.data:
        st.info("No pending form requests.")
    else:
        for req in pr.data:
            slot_str = req['time_slot'].strftime('%I:%M %p') if hasattr(req['time_slot'], 'strftime') else str(req['time_slot'])
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 3, 2])
                with c1:
                    st.markdown(f"**{req['full_name']}** — {req['phone']}")
                    st.caption(f"Requested: {req['appointment_date']} at {slot_str}")
                with c2:
                    st.caption(f"Reason: {req.get('reason') or '—'}")
                with c3:
                    if st.button("✅ Confirm", key=f"form_conf_{req['id']}"):
                        r = appt_svc.confirm(req['id'], user_id=user.get('id'))
                        st.toast(r.message)
                        if r.success:
                            notify_appointment_confirmed(
                                patient_name=req['full_name'],
                                patient_email=None,  # not in form request dict, skips email
                                patient_phone=req['phone'],
                                appt_date=req['appointment_date'],
                                time_slot=req['time_slot'],
                            )
                        st.rerun()
                    if st.button("❌ Cancel", key=f"form_canc_{req['id']}"):
                        r = appt_svc.cancel(req['id'], user_id=user.get('id'))
                        st.toast(r.message)
                        st.rerun()

# ── BLOCK SLOTS ───────────────────────────────────────────────
with tab_block:
    st.subheader("🚫 Block Time Slots")
    st.caption("Block out times for meetings, breaks, or holidays.")

    if user.get('role') != 'doctor':
        st.warning("Only doctors can block slots.")
    else:
        with st.form("block_form"):
            b_date  = st.date_input("Date to block", min_value=date.today())
            b_start = st.time_input("Start time")
            b_end   = st.time_input("End time")
            b_reason = st.text_input("Reason", placeholder="e.g. CME Meeting, Personal")
            submitted = st.form_submit_button("🚫 Block Slots")

        if submitted:
            if b_start >= b_end:
                st.error("Start time must be before end time.")
            else:
                r = appt_svc.block_slot(b_date, b_start, b_end, b_reason, user_id=user.get('id'))
                if r.success:
                    st.success(r.message)
                else:
                    st.error(r.message)
