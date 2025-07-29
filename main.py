import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Safety Inspection App", layout="wide")

# ---------------- LOGIN PLACEHOLDER ----------------
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
            # ✅ For now, dummy login. You can later connect to [[users]] in secrets.toml
            if email == "admin@example.com" and password == "123":
                st.session_state.logged_in = True
                st.session_state.user = {"name": "Admin", "email": email}
                st.success("✅ Welcome, Admin!")
                st.rerun()
            else:
                st.error("❌ Invalid credentials")

    st.stop()

# ---------------- GOOGLE SHEETS CONNECTION ----------------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

try:
    # Load service account from secrets
    service_account_info = st.secrets["gcp_service_account"].to_dict()
    # Ensure private_key newlines are properly set
    service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")

    creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    gc = gspread.authorize(creds)

    SHEET_ID = "1_WQyJCtdXuAIQn3IpFTI4KfkrveOHosNsvsZn42jAvw"
    SHEET_NAME = "Sheet1"
    sheet = gc.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    st.success("✅ Connected to Google Sheets!")

except Exception as e:
    st.error(f"❌ Failed to load data from Google Sheets: {e}")
    st.stop()

# ---------------- SIDEBAR USER INFO ----------------
st.sidebar.markdown(f"👤 Logged in as: **{st.session_state.user.get('name')}**")
st.sidebar.markdown(f"📧 {st.session_state.user.get('email')}")
if st.sidebar.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.session_state.user = {}
    st.rerun()

# ---------------- DISPLAY DATA ----------------
st.header("📊 Safety Inspection Records")

try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_side_bar()
    grid_options = gb.build()

    AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        data_return_mode=DataReturnMode.FILTERED,
        theme="alpine",
        fit_columns_on_grid_load=True,
    )

except ModuleNotFoundError:
    st.warning("⚠️ 'streamlit-aggrid' not installed. Falling back to default table display.")
    st.dataframe(df)
