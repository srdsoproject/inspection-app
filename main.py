# ==================== CONFIG ====================
import streamlit as st

# ✅ Must be the first Streamlit command
st.set_page_config(page_title="Safety Inspection App", layout="wide")

import gspread
from google.oauth2.service_account import Credentials
import plotly.graph_objects as go
from dateutil import parser
import importlib.util

# ==================== LOGIN HANDLING ====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = {}

def login(email, password):
    try:
        USERS = st.secrets["users"]
        for user in USERS:
            if user["email"] == email and user["password"] == password:
                return user
    except Exception:
        st.warning("⚠️ Could not load users. Check [[users]] block in secrets.toml.")
    return None

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
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

# ==================== GOOGLE SHEETS CONNECTION ====================
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

# ==================== SIDEBAR ====================
st.sidebar.markdown(f"👤 Logged in as: **{st.session_state.user.get('name')}**")
st.sidebar.markdown(f"📧 {st.session_state.user.get('email')}")
if st.sidebar.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.session_state.user = {}
    st.rerun()

# ==================== DATA DISPLAY ====================
try:
    data = sheet.get_all_records()

    if importlib.util.find_spec("streamlit_aggrid") is not None:
        from streamlit_aggrid import AgGrid, GridOptionsBuilder
        import pandas as pd

        df = pd.DataFrame(data)
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_pagination()
        grid_options = gb.build()
        AgGrid(df, gridOptions=grid_options)
    else:
        st.warning("⚠️ 'streamlit-aggrid' not installed. Falling back to default table display.")
        import pandas as pd
        df = pd.DataFrame(data)
        st.dataframe(df)
except Exception as e:
    st.error(f"❌ Could not load data: {e}")
