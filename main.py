import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# ---------- CONFIG ----------
st.set_page_config(page_title="Inspection App", layout="wide")

# ---------- USER AUTH ----------
# Example users - ideally store in secrets.toml
USERS = [
    {"name": "Raj", "email": "admin@example.com", "password": "123"},
    {"name": "User", "email": "a", "password": "123"},
    {"name": "DRM/SUR", "email": "drm@sur.railnet.gov.in", "password": "123"},
    {"name": "ADRM/SUR", "email": "adrm@sur.railnet.gov.in", "password": "123"},
]

def login(email, password):
    for user in USERS:
        if user["email"] == email and user["password"] == password:
            return user
    return None

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = {}

if not st.session_state.logged_in:
    st.title("🔐 Login to Safety Inspection App")
    with st.form("login_form", clear_on_submit=True):
        email = st.text_input("📧 Email")
        password = st.text_input("🔒 Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            user = login(email, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.success(f"✅ Welcome, {user['name']}!")
                st.rerun()
            else:
                st.error("❌ Invalid email or password.")
    st.stop()

# ---------- GOOGLE SHEETS CONNECTION ----------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

try:
    service_account_info = dict(st.secrets["gcp_service_account"])
    if "private_key" in service_account_info:
        service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")

    creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    gc = gspread.authorize(creds)

    SHEET_ID = "1_WQyJCtdXuAIQn3IpFTI4KfkrveOHosNsvsZn42jAvw"
    SHEET_NAME = "Sheet1"
    sheet = gc.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

    st.sidebar.success("✅ Connected to Google Sheets!")

except Exception as e:
    st.sidebar.error(f"❌ Failed to connect: {e}")
    st.stop()

# ---------- SIDEBAR ----------
st.sidebar.markdown(f"👤 Logged in as: **{st.session_state.user['name']}**")
st.sidebar.markdown(f"📧 {st.session_state.user['email']}")
if st.sidebar.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.session_state.user = {}
    st.experimental_rerun()

# ---------- LOAD DATA ----------
try:
    data = sheet.get_all_records()
    if data:
        st.subheader("📋 Inspection Records")

        try:
            from st_aggrid import AgGrid, GridOptionsBuilder
            df = pd.DataFrame(data)
            gb = GridOptionsBuilder.from_dataframe(df)
            gb.configure_pagination()
            grid_options = gb.build()
            AgGrid(df, gridOptions=grid_options, height=400, theme="balham")
        except Exception:
            st.warning("⚠️ 'streamlit-aggrid' not installed. Showing default table.")
            import pandas as pd
            df = pd.DataFrame(data)
            st.dataframe(df)

    else:
        st.info("ℹ️ No records found in Google Sheet.")

except Exception as e:
    st.error(f"❌ Failed to load data: {e}")
