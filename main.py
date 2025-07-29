import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from io import BytesIO
from matplotlib import pyplot as plt

# ---------- CONFIG ----------
st.set_page_config(page_title="Inspection App", layout="wide")

# ---------- LOGIN ----------
def login(email, password):
    try:
        users = st.secrets["users"]
        for user in users:
            if user["email"] == email and user["password"] == password:
                return user
        return None
    except KeyError:
        st.error("⚠️ No users found in secrets.toml — please check your [[users]] block.")
        st.stop()

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
    st.rerun()

# ---------- HELPER FUNCTIONS & CONSTANTS ----------

# -------------------- CONSTANT LISTS --------------------
# Station, Footplate & Gate Lists
import re

def normalize(text):
    """Convert feedback text to a clean lowercase string."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)  # collapse multiple spaces
    return text.strip()

def classify_feedback(feedback):
    if not isinstance(feedback, str) or feedback.strip() == "":
        return "Pending"

    feedback_normalized = normalize(feedback)

    # Make sure it's a string
    if not isinstance(feedback_normalized, str):
        feedback_normalized = ""

    date_found = bool(re.search(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', feedback_normalized))

    pending_keywords = [
        "will be", "needful", "to be", "pending", "not done", "awaiting",
        "waiting", "yet to", "next time", "follow up", "tdc", "t d c",
        "will attend", "will be attended", "scheduled", "reminder",
        "to inform", "to counsel", "to submit", "to do", "to replace",
        "remains", "still", "under process", "not yet", "to be done",
        "will be ensure", "during next", "action will be taken"
    ]

    resolved_keywords = [
        "attended", "solved", "submitted", "done", "completed", "informed",
        "tdc work completed", "replaced", "message given", "msg given", "msg sent",
        "info shared", "informed to", "communicated", "counseled", "counselled",
        "handled", "resolved", "action taken", "spoken to", "talked to", "warned",
        "met", "discussion held", "report sent", "notified", "explained",
        "work completed", "acknowledged", "visited", "briefed", "guided",
        "message", "msg", "on ", "working properly", "checked found working",
        "noted please", "noted", "updated by", "adv to", "counselled the staff",
        "counselled the", "checked and found", "maintained", "for needful action",
        "provided at", "in working condition", "is working", "found working",
        "equipment is working", "item is working",
        "noted it will be attended during the next primary maintenance",
        "operational feasibility", "will be provided", "will be supplied shortly"
    ]

    found_resolved = any(kw in feedback_normalized for kw in resolved_keywords)
    found_pending = any(kw in feedback_normalized for kw in pending_keywords)

    if found_resolved or date_found:
        return "Resolved"
    if found_pending:
        return "Pending"
    return "Pending"


def load_data():
    try:
        data = sheet.get_all_values()
        if not data or not data[0] or len(data) < 2:
            st.info("Google Sheet is empty or only contains headers.")
            return pd.DataFrame(columns=columns)

        df = pd.DataFrame(data[1:], columns=data[0])
        if 'Date of Inspection' in df.columns:
            df['Date of Inspection'] = pd.to_datetime(
                df['Date of Inspection'], errors='coerce'
            ).dt.strftime('%d.%m.%y')
        return df
    except gspread.exceptions.APIError as e:
        st.error(f"Google Sheets API Error loading data: {e}")
        st.info("Check your sheet ID and service account permissions.")
        return pd.DataFrame(columns=columns)
    except Exception as e:
        st.error(f"Unexpected error loading data: {e}")
        return pd.DataFrame(columns=columns)

def apply_common_filters(df, prefix=""):
    return df

# -------------------- HELPER FUNCTIONS --------------------
# All functions are defined here before they are called in the UI logic.

def load_data():
    """Loads all records from the Google Sheet and returns a DataFrame."""
    try:
        data = sheet.get_all_values()
        if not data:
            st.warning("Google Sheet is empty or unreadable.")
            return pd.DataFrame(columns=columns)

        # Check if the first row is actually headers
        # If the sheet might sometimes be truly empty, handle that gracefully
        if not data[0] or len(data) < 2:  # Check if header row is empty or only header exists
            st.info("Google Sheet is empty or only contains headers.")
            return pd.DataFrame(columns=columns)

        df = pd.DataFrame(data[1:], columns=data[0])

        # Ensure 'Date of Inspection' is in correct format for consistent processing
        if 'Date of Inspection' in df.columns:
            # Attempt to convert to datetime, then back to the desired string format
            # This handles potential mixed formats better for consistency
            df['Date of Inspection'] = pd.to_datetime(df['Date of Inspection'], errors='coerce').dt.strftime('%d.%m.%y')
        return df
    except gspread.exceptions.APIError as e:
        st.error(f"Google Sheets API Error loading data: {e}")
        st.info("Please check your sheet ID and service account permissions.")
        return pd.DataFrame(columns=columns)
    except Exception as e:
        st.error(f"An unexpected error occurred while loading data: {e}")
        return pd.DataFrame(columns=columns)


def apply_common_filters(df, prefix=""):
    return df  # placeholder for now, extend if you have common filters

# ---------- MAIN APP ----------
st.title("📋 Safety Inspection Entry & Viewer")
tabs = st.tabs(["📊 View Records"])

with tabs[0]:
    st.subheader("📊 View & Filter Records")
    df = load_data()

    if df.empty:
        st.warning("No records found")
    else:
        df["Date of Inspection"] = pd.to_datetime(df["Date of Inspection"], format="%d.%m.%y", errors="coerce")
        df["_original_sheet_index"] = df.index

        for col in ["Type of Inspection", "Location", "Head", "Sub Head", 
                    "Deficiencies Noted", "Inspection By", "Action By", "Feedback"]:
            if col not in df.columns:
                df[col] = ""

        df["Status"] = df["Feedback"].apply(classify_feedback)

        # Filters
        import datetime

        if df["Date of Inspection"].notna().any():
            min_date = df["Date of Inspection"].min().date()
            max_date = df["Date of Inspection"].max().date()
        else:
            today = datetime.date.today()
            min_date = today - datetime.timedelta(days=30)
            max_date = today
        
        start_date, end_date = st.date_input(
            "📅 Select Date Range",
            value=[min_date, max_date],
            key="view_date_range"
        )


        col1, col2 = st.columns(2)
        st.session_state.view_type_filter = col1.multiselect("Type of Inspection", sorted(df["Type of Inspection"].dropna().unique()))
        st.session_state.view_location_filter = col2.selectbox("Location", [""] + sorted(df["Location"].dropna().unique()))

        col3, col4 = st.columns(2)
        st.session_state.view_head_filter = col3.multiselect("Head", HEAD_LIST[1:])
        sub_opts = sorted({s for h in st.session_state.view_head_filter for s in SUBHEAD_LIST.get(h, [])})
        st.session_state.view_sub_filter = col4.selectbox("Sub Head", [""] + sub_opts)

        selected_status = st.selectbox("🔘 Status", ["All", "Pending", "Resolved"], key="view_status_filter")

        # Apply Filters
        filtered = df[
            (df["Date of Inspection"] >= pd.to_datetime(start_date)) &
            (df["Date of Inspection"] <= pd.to_datetime(end_date))
        ]
        if st.session_state.view_type_filter:
            filtered = filtered[filtered["Type of Inspection"].isin(st.session_state.view_type_filter)]
        if st.session_state.view_location_filter:
            filtered = filtered[filtered["Location"] == st.session_state.view_location_filter]
        if st.session_state.view_head_filter:
            filtered = filtered[filtered["Head"].isin(st.session_state.view_head_filter)]
        if st.session_state.view_sub_filter:
            filtered = filtered[filtered["Sub Head"] == st.session_state.view_sub_filter]
        if selected_status != "All":
            filtered = filtered[filtered["Status"] == selected_status]

        filtered = apply_common_filters(filtered, prefix="view_")
        filtered = filtered.applymap(lambda x: x.replace("\n", " ") if isinstance(x, str) else x)
        filtered = filtered.sort_values("Date of Inspection")
        filtered["User Feedback/Remark"] = ""

        st.write(f"🔹 Showing {len(filtered)} record(s) from **{start_date.strftime('%d.%m.%Y')}** to **{end_date.strftime('%d.%m.%Y')}**")

        # Summary Counts
        pending_count = (filtered["Status"] == "Pending").sum()
        resolved_count = (filtered["Status"] == "Resolved").sum()
        total_count = len(filtered)

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("🟨 Pending", pending_count)
        col_b.metric("🟩 Resolved", resolved_count)
        col_c.metric("📊 Total Records", total_count)

        if not filtered.empty:
            summary = filtered["Status"].value_counts().reindex(["Pending", "Resolved"], fill_value=0).reset_index()
            summary.columns = ["Status", "Count"]
            summary.loc[len(summary.index)] = ["Total", summary["Count"].sum()]

            # Chart + Table
            fig, axes = plt.subplots(1, 2, figsize=(12, 5))
            axes[0].pie(
                summary.loc[summary["Status"] != "Total", "Count"],
                labels=summary.loc[summary["Status"] != "Total", "Status"],
                autopct=lambda pct: f"{pct:.1f}%\n({int(round(pct / 100 * total_count))})",
                startangle=90,
                colors=["#1f77b4", "#7fc6f2"]
            )
            axes[0].set_title("")

            axes[1].axis('off')
            table_data = [["Status", "Count"]] + summary.values.tolist()
            tbl = axes[1].table(cellText=table_data, loc='center')
            tbl.auto_set_font_size(False)
            tbl.set_fontsize(10)
            tbl.scale(1, 1.6)

            plt.tight_layout(rect=[0, 0.05, 1, 0.90])
            fig.text(0.5, 0.96, "📈 Pending vs Resolved Records", ha='center', fontsize=14, fontweight='bold')

            buf = BytesIO()
            plt.savefig(buf, format="png", dpi=200)
            buf.seek(0)
            plt.close()

            st.image(buf, use_container_width=True)

            st.download_button("📥 Download Graph + Table (PNG)", buf, "status_summary.png", "image/png")

            export_df = filtered[[
                "Date of Inspection", "Type of Inspection", "Location", "Head", "Sub Head",
                "Deficiencies Noted", "Inspection By", "Action By", "Feedback", "User Feedback/Remark"
            ]].copy()
            export_df["Date of Inspection"] = export_df["Date of Inspection"].dt.strftime('%d-%m-%Y')
            towb = BytesIO()
            export_df.to_excel(towb, index=False)
            towb.seek(0)

            st.download_button("📥 Export Filtered Records to Excel", towb,
                               "filtered_records.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            st.markdown("### 📄 Preview of Filtered Records")
            st.dataframe(export_df, use_container_width=True, hide_index=True)
