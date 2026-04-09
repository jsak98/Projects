import streamlit as st
from datetime import date
from services.appointment_service import AppointmentService
from services.patient_service import PatientService

st.title("📊 Dashboard")

appt_svc = AppointmentService()
patient_svc = PatientService()

today = date.today()

col1, col2, col3, col4 = st.columns(4)

# Today's appointments
appts = appt_svc.get_by_date(today)
today_appts = appts.data or []
confirmed = [a for a in today_appts if a['status'] == 'confirmed']
pending   = [a for a in today_appts if a['status'] == 'pending']

# Total patients
all_patients = patient_svc.get_all()
total_patients = len(all_patients.data) if all_patients.data else 0

with col1:
    st.metric("Today's Appointments", len(today_appts))
with col2:
    st.metric("Confirmed", len(confirmed))
with col3:
    st.metric("Pending", len(pending))
with col4:
    st.metric("Total Patients", total_patients)

st.divider()

st.subheader(f"📅 Today's Schedule — {today.strftime('%A, %d %B %Y')}")

if not today_appts:
    st.info("No appointments scheduled for today.")
else:
    for a in today_appts:
        status_color = {
            'confirmed': '🟢',
            'pending':   '🟡',
            'completed': '✅',
            'cancelled': '🔴',
        }.get(a['status'], '⚪')

        slot_str = a['time_slot'].strftime('%I:%M %p') if hasattr(a['time_slot'], 'strftime') else str(a['time_slot'])
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 3, 2])
            with c1:
                st.markdown(f"**{slot_str}**")
            with c2:
                st.markdown(f"{status_color} **{a['full_name']}** — {a.get('reason','') or 'General'}")
                st.caption(f"📞 {a['phone']}")
            with c3:
                st.caption(a['status'].title())
