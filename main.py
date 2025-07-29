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

# Station, Footplate & Gate Lists
station_list = [
    'BRB', 'MLM', 'BGVN', 'JNTR', 'PRWD', 'WSB', 'PPJ', 'JEUR', 'KEM', 'BLNI', 'DHS', 'KWV', 'WDS',
    'MA', 'AAG', 'MKPT', 'MO', 'MVE', 'PK', 'BALE', "SUR", 'TKWD', 'HG', 'TLT', 'AKOR', 'NGS', 'BOT', 'DUD',
    'KUI', 'GDGN', 'GUR', 'HHD', 'SVG', 'BBD', 'TJSP', 'KLBG', 'HQR', 'MR', 'SDB', 'WADI', 'ARAG',
    'BLNK', 'SGRE', 'KVK', 'LNP', 'DLGN', 'JTRD', 'MSDG', 'JVA', 'WSD', 'SGLA', 'PVR', 'MLB', 'SEI', 'BTW',
    'PJR', 'DRSV', 'YSI', 'KMRD', 'DKY', 'MRX', 'OSA', 'HGL', 'LUR'
]

footplate_list = [
    "SUR-DD", "SUR-WADI", "LUR-KWV", 'KWV-MRJ',
    'DD-SUR', 'WADI-SUR', 'KWV-LUR', 'MRJ-KWV'
]

gate_list = [
    'LC-19', 'LC-22A', 'LC-25', 'LC-26', 'LC-27C', 'LC-28', 'LC-30', 'LC-31', 'LC-35', 'LC-37',
    'LC-40', 'LC-41', 'LC-43', 'LC-44', 'LC-45', 'LC-46C', 'LC-54', 'LC-61', 'LC-66', 'LC-74',
    'LC-76', 'LC-78', 'LC-82', 'LC-1', 'LC-60A', 'LC-1 TLT ZCL', 'LC-1 ACC', 'LC-2 ACC', 'LC-91',
    'LC-22', 'LC-24', 'LC-31', 'LC-32', 'LC-49', 'LC-70', 'LC-10', 'LC-34', 'LC-36', 'LC-44',
    'LC-47', 'LC-55', 'LC-59', 'LC-2', 'LC-4', 'LC-5', 'LC-6', 'LC-57', 'LC-62', 'LC-66', 'LC-70',
    'LC-39', 'LC-2/C', 'LC-6/C', 'LC-10', 'LC-11', 'LC-15/C', 'LC-21', 'LC-26-A', 'LC-34', 'LC-36',
    'LC-44', 'LC-47', 'LC-55', 'LC-57', 'LC-59', 'LC-60', 'LC-61'
]

# Head & Subhead for inspections
HEAD_LIST = ["", "ELECT/TRD", "ELECT/G", "ELECT/TRO", "SIGNAL & TELECOM", "OPTG",
             "ENGINEERING", "COMMERCIAL", "C&W", "WORKSITE INSPECTION"]

SUBHEAD_LIST = {
    "ELECT/TRD": ["", "T/W WAGON", "TSS/SP/SSP", "OHE SECTION", "OHE STATION", "MISC"],
    "ELECT/G": ["", "TL/AC COACH", "POWER/PANTRY CAR", "WIRING/EQUIPMENT", "UPS", "AC", "DG", "SOLAR LIGHT", "MISC"],
    "ELECT/TRO": ["", "RUNNING ROOM DEFICIENCIES", "LOBBY DEFICIENCIES", "LRD RELATED", "PERSONAL STORE",
                  "PR RELATED", "CMS", "MISC"],
    "WORKSITE INSPECTION": ["", "PWAY WORKS", "CIVIL WORKS", "MISC"],
    "SIGNAL & TELECOM": ["", "SIGNAL PUTBACK/BLANK", "OTHER SIGNAL FAILURE", "BPAC", "GATE", "RELAY ROOM",
                         "STATION(VDU/BLOCK INSTRUMENT)", "MISC", "CCTV", "DISPLAY BOARDS"],
    "OPTG": ["", "SWR/CSR/CSL/TWRD", "COMPETENCY RELATED", "STATION RECORDS", "STATION DEFICIENCIES",
             "SM OFFICE DEFICIENCIES", "MISC"],
    "ENGINEERING": ["", "ROUGH RIDING", "TRACK NEEDS ATTENTION", "MISC"],
    "COMMERCIAL": ["", "TICKETING RELATED/MACHINE", "IRCTC", "MISC"],
    "C&W": ["", "BRAKE BINDING", 'WHEEL DEFECT', 'TRAIN PARTING', 'PASSENGER AMENITIES',
            'AIR PRESSURE LEAKAGE', 'DAMAGED UNDER GEAR PARTS', 'MISC'],
}

INSPECTION_BY_LIST = [""] + [
    'DRM/SUR', 'ADRM', 'Sr.DSO', 'Sr.DOM', 'Sr.DEN/S', 'Sr.DEN/C', 'Sr.DEN/Co', 'Sr.DSTE',
    'Sr.DEE/TRD', 'Sr.DEE/G', 'Sr.DME', 'Sr.DCM', 'Sr.DPO', 'Sr.DFM', 'Sr.DMM', 'DSC',
    'DME,DEE/TRD', 'DFM', 'DSTE/HQ', 'DSTE/KLBG', 'ADEN/T/SUR', 'ADEN/W/SUR', 'ADEN/KWV',
    'ADEN/PVR', 'ADEN/LUR', 'ADEN/KLBG', 'ADSTE/SUR', 'ADSTE/I/KWV', 'ADSTE/II/KWV',
    'ADME/SUR', 'AOM/GD', 'AOM/GEN', 'ACM/Cog', 'ACM/TC', 'ACM/GD', 'APO/GEN', 'APO/WEL',
    'ADFM/I', 'ADFMII', 'ASC', 'ADSO'
]

ACTION_BY_LIST = [""] + [
    'DRM/SUR', 'ADRM', 'Sr.DSO', 'Sr.DOM', 'Sr.DEN/S', 'Sr.DEN/C', 'Sr.DEN/Co', 'Sr.DSTE',
    'Sr.DEE/TRD', 'Sr.DEE/G', 'Sr.DME', 'Sr.DCM', 'Sr.DPO', 'Sr.DFM', 'Sr.DMM', 'DSC'
]
# -------------------- SESSION STATE INIT --------------------
# Initialize session state variables for filters if they don't exist
# These ensure filters persist across reruns.
if "head" not in st.session_state:
    st.session_state.head = ""
if "sub_head" not in st.session_state:
    st.session_state.sub_head = ""

# Initialize filter states for "View Records" tab
if "view_type_filter" not in st.session_state:
    st.session_state.view_type_filter = []
if "view_location_filter" not in st.session_state:
    st.session_state.view_location_filter = ""
if "view_head_filter" not in st.session_state:
    st.session_state.view_head_filter = []
if "view_sub_filter" not in st.session_state:
    st.session_state.view_sub_filter = ""
if "view_insp" not in st.session_state:
    st.session_state.view_insp = []
if "view_action" not in st.session_state:
    st.session_state.view_action = []
if "view_from" not in st.session_state:
    st.session_state.view_from = None
if "view_to" not in st.session_state:
    st.session_state.view_to = None
def classify_feedback(feedback):
    if pd.isna(feedback) or feedback.strip() == "":
        return "Pending"
    return "Resolved"

def load_data():
    try:
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"❌ Could not load records: {e}")
        return pd.DataFrame()

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
