import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import plotly.graph_objects as go
from dateutil import parser
import re
import os

# Try AgGrid, fallback if missing
try:
    from streamlit_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
    aggrid_available = True
except ImportError:
    st.warning("⚠️ 'streamlit-aggrid' not installed. Falling back to default table display.")
    aggrid_available = False

# ✅ Set page config ONCE
st.set_page_config(page_title="Safety Inspection App", layout="wide")

# --- Load Users from secrets.toml ---
try:
    USERS = st.secrets["users"]
except KeyError:
    st.error("⚠️ No users found in secrets.toml — please check your [[users]] block.")
    USERS = []

def login(email, password):
    for user in USERS:
        if user["email"] == email and user["password"] == password:
            return user
    return None

# --- Session State ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = {}

# --- Login UI ---
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
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

# --- Google Sheets Setup ---
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

try:
    service_account_info = st.secrets["gcp_service_account"].to_dict()
    service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")
    creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    gc = gspread.authorize(creds)

    SHEET_ID = "1_WQyJCtdXuAIQn3IpFTI4KfkrveOHosNsvsZn42jAvw"
    SHEET_NAME = "Sheet1"
    sheet = gc.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

    st.success("✅ Connected to Google Sheets!")
except Exception as e:
    st.error(f"❌ Failed to load data from Google Sheets: {e}")
    st.stop()

# --- Sidebar: User Info & Logout ---
st.sidebar.markdown(f"👤 Logged in as: **{st.session_state.user.get('name')}**")
st.sidebar.markdown(f"📧 {st.session_state.user.get('email')}")
if st.sidebar.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.session_state.user = {}
    st.rerun()

# --- Main App Content ---
columns = [
    "Type of Inspection", "Location", "Month", "Date of Inspection",
    "Head", "Sub Head", "Deficiencies Noted", "Inspection By", "Action By", "Feedback"
]

try:
    data = sheet.get_all_records()
    if aggrid_available:
        gb = GridOptionsBuilder.from_dataframe(pd.DataFrame(data))
        gb.configure_pagination()
        gb.configure_side_bar()
        gridOptions = gb.build()
        AgGrid(pd.DataFrame(data), gridOptions=gridOptions,
               update_mode=GridUpdateMode.SELECTION_CHANGED,
               data_return_mode=DataReturnMode.FILTERED)
    else:
        st.dataframe(pd.DataFrame(data))
except Exception as e:
    st.error(f"⚠️ Could not load data: {e}")
