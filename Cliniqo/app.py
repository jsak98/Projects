import streamlit as st

st.set_page_config(
    page_title="Clinic Management",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- Simple session-based auth ----------
if 'user' not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.title("🏥 Clinic Management System")
    st.subheader("Please log in")

    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log In")

    if submitted:
        # Import here to avoid early DB calls
        from db.connection import DBConn
        import bcrypt

        with DBConn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, name, email, password, role FROM users WHERE email=%s AND is_active=TRUE",
                    (email,)
                )
                row = cur.fetchone()

        if row and bcrypt.checkpw(password.encode(), row[3].encode()):
            st.session_state.user = {
                'id': row[0], 'name': row[1],
                'email': row[2], 'role': row[4]
            }
            st.rerun()
        else:
            st.error("Invalid email or password")
    st.stop()

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user['name']}")
    st.caption(f"Role: {st.session_state.user['role'].title()}")
    st.divider()
    st.page_link("pages/1_dashboard.py",     label="📊 Dashboard",      icon="📊")
    st.page_link("pages/2_patients.py",      label="👥 Patients",       icon="👥")
    st.page_link("pages/3_appointments.py",  label="📅 Appointments",   icon="📅")
    st.page_link("pages/4_consultations.py", label="🩺 Consultations",  icon="🩺")
    st.divider()
    if st.button("🚪 Log Out", use_container_width=True):
        st.session_state.user = None
        st.rerun()

# ---------- Home ----------
st.title("🏥 Welcome to Clinic Management")
st.info("Use the sidebar to navigate between modules.")
