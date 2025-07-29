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


# -------------------- LOGIN SETUP --------------------
# Safe load of users from secrets
USERS = []
if "users" in st.secrets:
    USERS = st.secrets["users"]
else:
    st.warning("⚠️ No [[users]] block found in secrets.toml — login will not work.")


def login(email, password):
    """Validate login credentials"""
    for user in USERS:
        if user["email"] == email and user["password"] == password:
            return user
    return None


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = {}

if not st.session_state.logged_in:
    st.set_page_config(page_title="Login | Inspection App", layout="centered")
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


# -------------------- GOOGLE SHEETS SETUP --------------------
SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]
SHEET_ID = "1_WQyJCtdXuAIQn3IpFTI4KfkrveOHosNsvsZn42jAvw"
SHEET_NAME = "Sheet1"

sheet = None  # fallback if connection fails

try:
    service_account_info = st.secrets["gcp_service_account"].to_dict()
    service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")

    creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    st.success("✅ Connected to Google Sheets!")
except Exception as e:
    st.error(f"❌ Failed to connect to Google Sheets: {e}")
    st.info("Check your service account credentials and sharing permissions.")


# -------------------- MAIN APP --------------------
st.set_page_config(page_title="Safety Inspection App", layout="wide")
st.sidebar.markdown(f"👤 Logged in as: **{st.session_state.user.get('name')}**")
st.sidebar.markdown(f"📧 {st.session_state.user.get('email')}")
if st.sidebar.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.session_state.user = {}
    st.rerun()

columns = [
    "Type of Inspection", "Location", "Month", "Date of Inspection",
    "Head", "Sub Head", "Deficiencies Noted", "Inspection By", "Action By", "Feedback"
]

if sheet:
    try:
        records = sheet.get_all_records()
        st.subheader("📊 Inspection Records")
        if aggrid_available:
            gb = GridOptionsBuilder.from_dataframe(records)
            gb.configure_pagination(enabled=True)
            gb.configure_default_column(editable=False, groupable=True)
            grid_options = gb.build()
            AgGrid(records, gridOptions=grid_options, update_mode=GridUpdateMode.SELECTION_CHANGED)
        else:
            st.dataframe(records)
    except Exception as e:
        st.error(f"❌ Failed to load data from Google Sheets: {e}")
else:
    st.warning("⚠️ No data available because Google Sheets is not connected.")
