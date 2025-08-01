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
station_list = ['BRB', 'MLM', 'BGVN', 'JNTR', 'PRWD', 'WSB', 'PPJ', 'JEUR', 'KEM', 'BLNI', 'DHS', 'KWV', 'WDS',
                'MA', 'AAG', 'MKPT', 'MO', 'MVE', 'PK', 'BALE', "SUR", 'TKWD', 'HG', 'TLT', 'AKOR', 'NGS', 'BOT', 'DUD',
                'KUI', 'GDGN', 'GUR', 'HHD', 'SVG', 'BBD', 'TJSP', 'KLBG', 'HQR', 'MR', 'SDB', 'WADI', 'ARAG',
                'BLNK', 'SGRE', 'KVK', 'LNP', 'DLGN', 'JTRD', 'MSDG', 'JVA', 'WSD', 'SGLA', 'PVR', 'MLB', 'SEI', 'BTW',
                'PJR', 'DRSV', 'YSI', 'KMRD', 'DKY', 'MRX', 'OSA', 'HGL', 'LUR']
footplate_list = ["SUR-DD", "SUR-WADI", "LUR-KWV", 'KWV-MRJ', 'DD-SUR', 'WADI-SUR', 'KWV-LUR', 'MRJ-KWV']
gate_list = ['LC-19', 'LC-22A', 'LC-25', 'LC-26', 'LC-27C', 'LC-28', 'LC-30', 'LC-31', 'LC-35', 'LC-37', 'LC-40',
             'LC-41', 'LC-43', 'LC-44', 'LC-45', 'LC-46C', 'LC-54', 'LC-61', 'LC-66', 'LC-74', 'LC-76', 'LC-78',
             'LC-82', 'LC-1', 'LC-60A', 'LC-1 TLT ZCL', 'LC-1 ACC', 'LC-2 ACC', 'LC-91', 'LC-22', 'LC-24', 'LC-31',
             'LC-32', 'LC-49', 'LC-70', 'LC-10', 'LC-34', 'LC-36', 'LC-44', 'LC-47', 'LC-55', 'LC-59', 'LC-2',
             'LC-4', 'LC-42', 'LC-02', 'LC-31',
             'LC-5', 'LC-6', 'LC-57', 'LC-62', 'LC-66', 'LC-70', 'LC-39', 'LC-2/C', 'LC-6/C', 'LC-10', 'LC-11',
             'LC-15/C', 'LC-21', 'LC-26-A', 'LC-34', 'LC-36', 'LC-44', 'LC-47', 'LC-55', 'LC-57', 'LC-59', 'LC-60',
             'LC-61']
HEAD_LIST = ["", "ELECT/TRD", "ELECT/G", "ELECT/TRO", "SIGNAL & TELECOM", "OPTG",
             "ENGINEERING", "COMMERCIAL", "C&W", "WORKSITE INSPECTION"]
SUBHEAD_LIST = {
    "ELECT/TRD": ["T/W WAGON", "TSS/SP/SSP", "OHE SECTION", "OHE STATION", "MISC"],
    "ELECT/G": ["TL/AC COACH", "POWER/PANTRY CAR", "WIRING/EQUIPMENT", "UPS", "AC", "DG", "SOLAR LIGHT", "MISC"],
    "ELECT/TRO": ["LOCO DEFECTS", "RUNNING ROOM DEFICIENCIES", "LOBBY DEFICIENCIES", "LRD RELATED", "PERSONAL STORE", "PR RELATED",
                  "CMS", "MISC"],
    "WORKSITE INSPECTION": [ "PWAY WORKS", "CIVIL WORKS", "MISC"],
    "SIGNAL & TELECOM": [ "SIGNAL PUTBACK/BLANK", "OTHER SIGNAL FAILURE", "BPAC", "GATE", "RELAY ROOM",
                         "STATION(VDU/BLOCK INSTRUMENT)", "MISC", "CCTV", "DISPLAY BOARDS"],
    "OPTG": [ "SWR/CSR/CSL/TWRD", "COMPETENCY RELATED", "STATION RECORDS", "STATION DEFICIENCIES",
             "SM OFFICE DEFICIENCIES", "MISC"],
    "ENGINEERING": [ "ROUGH RIDING", "TRACK NEEDS ATTENTION", "MISC"],
    "COMMERCIAL": [ "TICKETING RELATED/MACHINE", "IRCTC", "MISC"],
    "C&W": [ "BRAKE BINDING", 'WHEEL DEFECT', 'TRAIN PARTING', 'PASSENGER AMENITIES', 'AIR PRESSURE LEAKAGE',
            'DAMAGED UNDER GEAR PARTS', 'MISC'],
}
INSPECTION_BY_LIST = [""] + ['DRM/SUR', 'ADRM', 'Sr.DSO', 'Sr.DOM', 'Sr.DEN/S', 'Sr.DEN/C', 'Sr.DEN/Co', 'Sr.DSTE',
                             'Sr.DEE/TRD', 'Sr.DEE/G', 'Sr.DME', 'Sr.DCM', 'Sr.DPO', 'Sr.DFM', 'Sr.DMM', 'DSC',
                             'DME,DEE/TRD', 'DFM', 'DSTE/HQ', 'DSTE/KLBG', 'ADEN/T/SUR', 'ADEN/W/SUR', 'ADEN/KWV',
                             'ADEN/PVR', 'ADEN/LUR', 'ADEN/KLBG', 'ADSTE/SUR', 'ADSTE/I/KWV', 'ADSTE/II/KWV',
                             'ADME/SUR', 'AOM/GD', 'AOM/GEN', 'ACM/Cog', 'ACM/TC', 'ACM/GD', 'APO/GEN', 'APO/WEL',
                             'ADFM/I', 'ADFMII', 'ASC', 'ADSO']
ACTION_BY_LIST = [""] + ['DRM/SUR', 'ADRM', 'Sr.DSO', 'Sr.DOM', 'Sr.DEN/S', 'Sr.DEN/C', 'Sr.DEN/Co', 'Sr.DSTE',
                         'Sr.DEE/TRD', 'Sr.DEE/G', 'Sr.DME', 'Sr.DCM', 'Sr.DPO', 'Sr.DFM', 'Sr.DMM', 'DSC']
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
        "will be ensure", "during next", "action will be taken", "Will be supplied shortly."
    ]

    resolved_keywords = [
        "attended", "solved", "submitted", "done", "completed", "informed", "Confirmed by","confirmed by",
        "tdc work completed", "replaced", "message given", "msg given", "msg sent",
        "info shared", "informed to", "communicated", "counseled", "counselled", "Gate will be closed soon", "attending at the time", "Attending at time",
        "handled", "resolved", "action taken", "spoken to", "talked to", "warned", "counselling", "HUBLI", "working normal", "Working Normal",
        "met", "discussion held", "report sent", "notified", "explained", "NIL","nil", "na","NA",
        "work completed", "acknowledged", "visited", "briefed", "guided", "DG sets handover to KLBG", "handover",
        "message", "msg", "on ", "working properly", "checked found working", "Supply restored", 
        "noted please", "noted", "updated by", "adv to", "counselled the staff",
        "counselled the", "checked and found", "maintained", "for needful action", "Advised to ETL/CTO/UBL",
        "provided at", "in working condition", "is working", "found working",
        "equipment is working", "item is working", "As per plan", "Advised to ETL/",
        "noted it will be attended during the next primary maintenance", "Putright", "putright", "put right", "Put right",
        "operational feasibility", "will be provided", "will be supplied shortly", "advised to ubl"
    ]

    found_resolved = any(kw in feedback_normalized for kw in resolved_keywords)
    found_pending = any(kw in feedback_normalized for kw in pending_keywords)

    if found_resolved or date_found:
        return "Resolved"
    if found_pending:
        return "Pending"
    return "Pending"


def load_data():
    """Loads all records from the Google Sheet and returns a DataFrame."""
    try:
        data = sheet.get_all_values()

        # Check for empty or incomplete data
        if not data:
            st.warning("⚠️ Google Sheet is empty or unreadable.")
            return pd.DataFrame(columns=columns)
        if not data[0] or len(data) < 2:
            st.info("ℹ️ Google Sheet has only headers or no valid rows.")
            return pd.DataFrame(columns=columns)

        # Create DataFrame from sheet data
        df = pd.DataFrame(data[1:], columns=data[0])

        # Standardize 'Date of Inspection' if present
        if "Date of Inspection" in df.columns:
            df["Date of Inspection"] = pd.to_datetime(
                df["Date of Inspection"], errors="coerce"
            ).dt.strftime("%d.%m.%y")

        return df

    except gspread.exceptions.APIError as e:
        st.error(f"🚫 Google Sheets API Error: {e}")
        st.info("Please check your Sheet ID and service account permissions.")
        return pd.DataFrame(columns=columns)

    except Exception as e:
        st.error(f"❌ Unexpected error while loading data: {e}")
        return pd.DataFrame(columns=columns)


def match_exact(value_list, cell_value):
    """Checks if any value in value_list exactly matches a comma-separated item in cell_value."""
    if not isinstance(cell_value, str):
        return False
    cell_items = [item.strip() for item in cell_value.split(',')]
    return any(val == item for val in value_list for item in cell_items)


def apply_common_filters(df, prefix=""):
    """Applies common filters (Inspection By, Action By, Date Range) to a DataFrame.
    Filters are read from st.session_state using the given prefix."""
    with st.expander("🔍 Apply Additional Filters", expanded=True):
        col4, col5 = st.columns(2)
        # Widget creation. The 'key' automatically handles updating session_state.
        col4.multiselect(
            "Inspection By",
            INSPECTION_BY_LIST[1:],
            default=st.session_state.get(prefix + "insp", []),
            key=prefix + "insp"
        )
        col5.multiselect(
            "Action By",
            ACTION_BY_LIST[1:],
            default=st.session_state.get(prefix + "action", []),
            key=prefix + "action"
        )

        col6, col7 = st.columns(2)
        col6.date_input(
            "From Date",
            value=st.session_state.get(prefix + "from", None),
            key=prefix + "from"
        )
        col7.date_input(
            "To Date",
            value=st.session_state.get(prefix + "to", None),
            key=prefix + "to"
        )

    df_filtered = df.copy()

    # Apply filters based on session state values
    if st.session_state.get(prefix + "insp"):
        df_filtered = df_filtered[
            df_filtered["Inspection By"].apply(lambda x: match_exact(st.session_state[prefix + "insp"], x))]
    if st.session_state.get(prefix + "action"):
        df_filtered = df_filtered[
            df_filtered["Action By"].apply(lambda x: match_exact(st.session_state[prefix + "action"], x))]

    # Convert 'Date of Inspection' to datetime for comparison if it exists
    if "Date of Inspection" in df_filtered.columns:
        df_filtered["Date_dt"] = pd.to_datetime(df_filtered["Date of Inspection"], errors="coerce", format="%d.%m.%y")

        if st.session_state.get(prefix + "from"):
            df_filtered = df_filtered[df_filtered["Date_dt"] >= pd.to_datetime(st.session_state[prefix + "from"])]
        if st.session_state.get(prefix + "to"):
            df_filtered = df_filtered[df_filtered["Date_dt"] <= pd.to_datetime(st.session_state[prefix + "to"])]

        # Drop the temporary datetime column
        df_filtered = df_filtered.drop(columns=["Date_dt"], errors='ignore')

    return df_filtered
# -------------------- HELPER FUNCTIONS --------------------
# All functions are defined here before they are called in the UI logic.
# ---------- MAIN APP ----------
st.title("📋 Safety Inspection Viewer")
tabs = st.tabs(["📊 View Records"])

with tabs[0]:
    st.subheader("📊 View & Filter Records")
    df = load_data()

    if df.empty:
        st.warning("No records found")
    else:
        df["Date of Inspection"] = pd.to_datetime(df["Date of Inspection"], format="%d.%m.%y", errors="coerce")
        df["_original_sheet_index"] = df.index

        for col in ["Type of Inspection", "Location", "Head", "Sub Head", "Deficiencies Noted", "Inspection By", "Action By", "Feedback"]:
            if col not in df.columns:
                df[col] = ""

        df["Status"] = df["Feedback"].apply(classify_feedback)

        # Filters
        start_date, end_date = st.date_input(
            "📅 Select Date Range",
            [df["Date of Inspection"].min(), df["Date of Inspection"].max()],
            key="view_date_range"
        )

        col1, col2 = st.columns(2)
        col1.multiselect("Type of Inspection", sorted(df["Type of Inspection"].dropna().unique()), key="view_type_filter")
        col2.selectbox("Location", [""] + sorted(df["Location"].dropna().unique()), key="view_location_filter")

        col3, col4 = st.columns(2)
        col3.multiselect("Head", HEAD_LIST[1:], key="view_head_filter")
        sub_opts = sorted({s for h in st.session_state.view_head_filter for s in SUBHEAD_LIST.get(h, [])})
        col4.selectbox("Sub Head", [""] + sub_opts, key="view_sub_filter")

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
        # Summary Counts Display
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

            # Add total row to the table
            total_count = summary["Count"].sum()
            summary.loc[len(summary.index)] = ["Total", total_count]

            # Title Info
            dr = f"{start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')}"
            heads = ", ".join(st.session_state.view_head_filter) if st.session_state.view_head_filter else "All Heads"

            # Matplotlib chart and table
            fig, axes = plt.subplots(1, 2, figsize=(12, 5))

            wedges, texts, autotexts = axes[0].pie(
                summary.loc[summary["Status"] != "Total", "Count"],
                labels=summary.loc[summary["Status"] != "Total", "Status"],
                autopct=lambda pct: f"{pct:.1f}%\n({int(round(pct / 100 * total_count))})",
                startangle=90,
                colors=["#1f77b4", "#7fc6f2"]
            )
            axes[0].set_title("", fontsize=12)

            # Table on the right
            axes[1].axis('off')
            table_data = [["Status", "Count"]] + summary.values.tolist()

            table_data.append(["Date Range", dr])

            # Type of Inspection(s)
            type_filter = st.session_state.view_type_filter
            type_display = ", ".join(type_filter) if type_filter else "All Types"
            table_data.append(["Type of Inspection", type_display])

            # Location
            location_display = st.session_state.view_location_filter or "All Locations"
            table_data.append(["Location", location_display])

            # Head(s)
            table_data.append(["Heads", heads])

            # Sub Head (if selected)
            if st.session_state.view_sub_filter:
                table_data.append(["Sub Head", st.session_state.view_sub_filter])

            # Status Filter (if selected)
            if selected_status != "All":
                table_data.append(["Filtered Status", selected_status])

            tbl = axes[1].table(cellText=table_data, loc='center')
            tbl.auto_set_font_size(False)
            tbl.set_fontsize(10)
            tbl.scale(1, 1.6)

            plt.tight_layout(rect=[0, 0.05, 1, 0.90])

            # Title & context in figure
            fig.text(0.5, 0.96, "📈 Pending vs Resolved Records", ha='center', fontsize=14, fontweight='bold')
            fig.text(0.5, 0.03, f"Date Range: {dr}   |   Department: {heads}", ha='center', fontsize=10, color='gray')

            buf = BytesIO()
            plt.savefig(buf, format="png", dpi=200)
            buf.seek(0)
            plt.close()
             # fallback for your version


            st.image(buf, caption=None, use_column_width=True)

            # Download buttons
            st.download_button(
                "📥 Download Graph + Table (PNG)",
                data=buf,
                file_name="status_summary.png",
                mime="image/png"
            )

            export_df = filtered[[
                "Date of Inspection", "Type of Inspection", "Location", "Head", "Sub Head",
                "Deficiencies Noted", "Inspection By", "Action By", "Feedback", "User Feedback/Remark"
            ]].copy()

            export_df["Date of Inspection"] = export_df["Date of Inspection"].dt.strftime('%d-%m-%Y')
            towb = BytesIO()
            export_df.to_excel(towb, index=False)
            towb.seek(0)

            st.download_button(
                "📥 Export Filtered Records to Excel",
                data=towb,
                file_name="filtered_records.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            st.markdown("### 📄 Preview of Filtered Records")
            st.dataframe(export_df, use_container_width=True, hide_index=True)


