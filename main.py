import json
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# --- Google Sheets Setup ---
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

    st.success("✅ Connected to Google Sheets!")

except Exception as e:
    st.error(f"❌ Failed to load data from Google Sheets: {e}")
    st.stop()
