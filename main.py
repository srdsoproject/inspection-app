import streamlit as st
import pandas as pd
import datetime
from io import BytesIO
import matplotlib.pyplot as plt
import gspread
from google.oauth2.service_account import Credentials

# --- Streamlit Config ---
st.set_page_config(page_title="Inspection App", layout="wide")

# --- Authentication ---
def check_login(username, password):
    return username == st.secrets["login"]["username"] and password == st.secrets["login"]["password"]

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if check_login(username, password):
            st.session_state.logged_in = True
            st.success("✅ Login successful!")
            st.experimental_rerun()
        else:
            st.error("❌ Invalid credentials")
    st.stop()

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

    SHEET_ID = st.secrets["sheets"]["sheet_id"]
    SHEET_NAME = st.secrets["sheets"]["sheet_name"]

    sheet = gc.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    st.success("✅ Connected to Google Sheets!")

except Exception as e:
    st.error(f"❌ Failed to load data from Google Sheets: {e}")
    st.stop()

# --- Helper Function ---
def classify_feedback(feedback):
    if pd.isna(feedback) or str(feedback).strip() == "":
        return "Pending"
    return "Resolved"

# --- UI ---
st.title("📋 Safety Inspection Entry & Viewer")
tabs = st.tabs(["📊 View Records"])

with tabs[0]:
    st.subheader("📊 View & Filter Records")

    if df.empty:
        st.warning("No records found")
    else:
        df["Date of Inspection"] = pd.to_datetime(
            df["Date of Inspection"], format="%d.%m.%y", errors="coerce"
        )
        df["_original_sheet_index"] = df.index

        for col in ["Type of Inspection", "Location", "Head", "Sub Head", 
                    "Deficiencies Noted", "Inspection By", "Action By", "Feedback"]:
            if col not in df.columns:
                df[col] = ""

        df["Status"] = df["Feedback"].apply(classify_feedback)

        # --- Safe Date Handling ---
        if df["Date of Inspection"].notna().any():
            min_date = df["Date of Inspection"].min().date()
            max_date = df["Date of Inspection"].max().date()
        else:
            today = datetime.date.today()
            min_date = today - datetime.timedelta(days=30)
            max_date = today

        start_date, end_date = st.date_input(
            "📅 Select Date Range",
            [min_date, max_date],
            key="view_date_range"
        )

        # --- Filters ---
        col1, col2 = st.columns(2)
        col1.multiselect("Type of Inspection", sorted(df["Type of Inspection"].dropna().unique()), key="view_type_filter")
        col2.selectbox("Location", [""] + sorted(df["Location"].dropna().unique()), key="view_location_filter")

        selected_status = st.selectbox("🔘 Status", ["All", "Pending", "Resolved"], key="view_status_filter")

        # --- Apply Filters ---
        filtered = df[
            (df["Date of Inspection"] >= pd.to_datetime(start_date)) &
            (df["Date of Inspection"] <= pd.to_datetime(end_date))
        ]

        if st.session_state.view_type_filter:
            filtered = filtered[filtered["Type of Inspection"].isin(st.session_state.view_type_filter)]
        if st.session_state.view_location_filter:
            filtered = filtered[filtered["Location"] == st.session_state.view_location_filter]
        if selected_status != "All":
            filtered = filtered[filtered["Status"] == selected_status]

        filtered = filtered.applymap(lambda x: x.replace("\n", " ") if isinstance(x, str) else x)
        filtered = filtered.sort_values("Date of Inspection")
        filtered["User Feedback/Remark"] = ""

        st.write(f"🔹 Showing {len(filtered)} record(s) from **{start_date}** to **{end_date}**")

        # --- Summary Metrics ---
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
            total_count = summary["Count"].sum()
            summary.loc[len(summary.index)] = ["Total", total_count]

            # --- Pie Chart + Table ---
            fig, axes = plt.subplots(1, 2, figsize=(12, 5))

            axes[0].pie(
                summary.loc[summary["Status"] != "Total", "Count"],
                labels=summary.loc[summary["Status"] != "Total", "Status"],
                autopct=lambda pct: f"{pct:.1f}%\n({int(round(pct / 100 * total_count))})",
                startangle=90,
                colors=["#1f77b4", "#7fc6f2"]
            )
            axes[0].set_title("Status Distribution")

            axes[1].axis('off')
            table_data = [["Status", "Count"]] + summary.values.tolist()
            tbl = axes[1].table(cellText=table_data, loc='center')
            tbl.auto_set_font_size(False)
            tbl.set_fontsize(10)
            tbl.scale(1, 1.6)

            buf = BytesIO()
            plt.savefig(buf, format="png", dpi=200)
            buf.seek(0)
            plt.close()

            st.image(buf, use_container_width=True)

            # --- Export Buttons ---
            st.download_button("📥 Download Graph + Table (PNG)", data=buf,
                               file_name="status_summary.png", mime="image/png")

            export_df = filtered[[ "Date of Inspection", "Type of Inspection", "Location", "Head", 
                                   "Sub Head", "Deficiencies Noted", "Inspection By", 
                                   "Action By", "Feedback", "User Feedback/Remark" ]].copy()

            export_df["Date of Inspection"] = export_df["Date of Inspection"].dt.strftime('%d-%m-%Y')
            towb = BytesIO()
            export_df.to_excel(towb, index=False)
            towb.seek(0)

            st.download_button("📥 Export Filtered Records to Excel", data=towb,
                               file_name="filtered_records.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            st.markdown("### 📄 Preview of Filtered Records")
            st.dataframe(export_df, use_container_width=True, hide_index=True)
