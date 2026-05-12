import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from io import StringIO
import base64
from pathlib import Path

st.set_page_config(page_title="Skill Development MIS", layout="wide")

# ---------------- GOOGLE SHEETS CONNECTION ----------------
# Get your Google Sheet ID from the URL
# https://docs.google.com/spreadsheets/d/1MEHTubLQE36RB0Rg5k-aGPdrcV2QuTCG5U8yZCNU0qk/edit?gid=64238622#gid=64238622
SHEET_ID = st.secrets.get("sheet_id", "1MEHTubLQE36RB0Rg5k-aGPdrcV2QuTCG5U8yZCNU0qk")
SHEET_NAME = "Sheet1"

def load_data():
    """Load data from Google Sheets using CSV export"""
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"
        response = requests.get(url)
        
        if response.status_code == 200:
            df = pd.read_csv(StringIO(response.text))
            
            # If empty or just headers
            if df.empty or len(df) == 0:
                return pd.DataFrame(columns=[
                    "Student Name","Gender","Address","District","State",
                    "Training Institution","Trade","Training Status",
                    "Start Date","End Date","Placement Hotel",
                    "Placement Status","Placement Date"
                ])
            return df
        else:
            st.error("Could not connect to Google Sheets. Make sure the sheet is public.")
            return pd.DataFrame(columns=[
                "Student Name","Gender","Address","District","State",
                "Training Institution","Trade","Training Status",
                "Start Date","End Date","Placement Hotel",
                "Placement Status","Placement Date"
            ])
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(columns=[
            "Student Name","Gender","Address","District","State",
            "Training Institution","Trade","Training Status",
            "Start Date","End Date","Placement Hotel",
            "Placement Status","Placement Date"
        ])

def save_data_to_session(df):
    """Save data to session state (since writing to Google Sheets requires API auth)"""
    st.session_state['pending_data'] = df
    return True


def render_interpretation(df_view, dimension):
    """Render a separate chart + quick interpretation for a selected dimension."""
    if dimension not in df_view.columns:
        st.warning(f"Column '{dimension}' not found in the dataset.")
        return

    dim_data = (
        df_view[dimension]
        .fillna("Not Provided")
        .replace("", "Not Provided")
        .value_counts()
        .reset_index()
    )
    dim_data.columns = [dimension, "Count"]

    if dim_data.empty:
        st.info(f"No data available for {dimension}.")
        return

    st.plotly_chart(px.bar(dim_data, x=dimension, y="Count"), use_container_width=True)

    top_row = dim_data.iloc[0]
    top_name = top_row[dimension]
    top_count = int(top_row["Count"])
    total = int(dim_data["Count"].sum())
    top_pct = (top_count / total) * 100 if total else 0

    st.markdown(
        f"- **Top {dimension}**: `{top_name}` with **{top_count}** students "
        f"(**{top_pct:.1f}%** of shown records).\n"
        f"- **Unique values**: **{len(dim_data)}**.\n"
        f"- **Total mapped records**: **{total}**."
    )

# Load data
df = load_data()

# Check for pending data from form submission
if 'pending_data' in st.session_state:
    df = st.session_state['pending_data']

# ---------------- MENU ----------------
menu = st.sidebar.radio("Navigation", ["Dashboard", "Add Student", "Data Quality", "View All Students"])


def set_dashboard_background(image_path: str = "Sunbird Logo.png"):
    """Apply a subtle centered background logo to the dashboard page."""
    image_file = Path(image_path)
    if not image_file.exists():
        return

    encoded = base64.b64encode(image_file.read_bytes()).decode()
    st.markdown(
        f"""
        <style>
            [data-testid="stAppViewContainer"] {{
                background-image:
                    linear-gradient(rgba(255, 255, 255, 0.88), rgba(255, 255, 255, 0.88)),
                    url("data:image/png;base64,{encoded}");
                background-repeat: no-repeat;
                background-position: center 180px;
                background-size: min(380px, 45vw);
                background-attachment: fixed;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )

# ---------------- DASHBOARD ----------------
if menu == "Dashboard":
    set_dashboard_background()
    st.title("📊 Skill Development Dashboard")
    
    st.info("💡 **Note**: To save data permanently, manually paste new entries into your Google Sheet, or download the backup CSV and upload it to the sheet.")

    if not df.empty:
        # Filters
        inst_options = df["Training Institution"].dropna().unique().tolist()
        status_options = df["Training Status"].dropna().unique().tolist()
        district_options = df["District"].dropna().unique().tolist()
        state_options = df["State"].dropna().unique().tolist()
        
        inst_filter = st.sidebar.multiselect(
            "Institution",
            inst_options,
            default=inst_options
        )

        status_filter = st.sidebar.multiselect(
            "Training Status",
            status_options,
            default=status_options
        )
        
        district_filter = st.sidebar.multiselect(
            "District",
            district_options,
            default=district_options
        )
        
        state_filter = st.sidebar.multiselect(
            "State",
            state_options,
            default=state_options
        )

        filtered = df[
            (df["Training Institution"].isin(inst_filter)) &
            (df["Training Status"].isin(status_filter)) &
            (df["District"].isin(district_filter)) &
            (df["State"].isin(state_filter))
        ]
    else:
        filtered = df

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Students", len(filtered))
    col2.metric("Ongoing", len(filtered[filtered["Training Status"]=="Ongoing"]) if not filtered.empty else 0)
    col3.metric("Completed", len(filtered[filtered["Training Status"]=="Completed"]) if not filtered.empty else 0)
    col4.metric("Districts", filtered["District"].nunique() if not filtered.empty else 0)

    if not filtered.empty:
        # Charts
        st.subheader("Institution-wise Students")
        inst_chart = filtered.groupby("Training Institution").size().reset_index(name="Count")
        st.plotly_chart(px.bar(inst_chart, x="Training Institution", y="Count"), use_container_width=True)

        # District-wise Distribution
        st.subheader("District-wise Students")
        district_chart = filtered.groupby("District").size().reset_index(name="Count")
        st.plotly_chart(px.bar(district_chart, x="District", y="Count"), use_container_width=True)

        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("Training Status Distribution")
            st.plotly_chart(px.pie(filtered, names="Training Status"), use_container_width=True)
        
        with col_right:
            st.subheader("State-wise Distribution")
            st.plotly_chart(px.pie(filtered, names="State"), use_container_width=True)

        st.subheader("Institution vs Status")
        inst_status = filtered.groupby(["Training Institution","Training Status"]).size().reset_index(name="Count")
        st.plotly_chart(px.bar(inst_status, x="Training Institution", y="Count", color="Training Status", barmode="stack"), use_container_width=True)

        # Placement Section
        st.subheader("🏨 Placement Overview")

        placed = len(filtered[filtered["Placement Status"]=="Placed"])
        not_placed = len(filtered[filtered["Placement Status"]=="Not Placed"])

        col4, col5 = st.columns(2)
        col4.metric("Placed", placed)
        col5.metric("Not Placed", not_placed)

        if "Placement Hotel" in filtered.columns:
            hotel_data = filtered[filtered["Placement Status"]=="Placed"]
            if not hotel_data.empty:
                hotel_chart = hotel_data.groupby("Placement Hotel").size().reset_index(name="Count")
                if not hotel_chart.empty:
                    st.plotly_chart(px.bar(hotel_chart, x="Placement Hotel", y="Count"), use_container_width=True)

        # Data Interpretation Section
        st.subheader("📌 Data Interpretation (Separate Views)")
        st.markdown("Interpretation shown separately for each required dimension.")

        st.markdown("#### 1) Training Institution")
        render_interpretation(filtered, "Training Institution")

        st.markdown("#### 2) Placement Status")
        render_interpretation(filtered, "Placement Status")

        st.markdown("#### 3) Placement Hotel")
        render_interpretation(filtered, "Placement Hotel")

        st.markdown("#### 4) Trade")
        render_interpretation(filtered, "Trade")

        # Backup Button
        st.download_button(
            "📥 Download Backup CSV",
            filtered.to_csv(index=False).encode('utf-8'),
            "backup.csv",
            "text/csv",
            help="Download and manually upload this to your Google Sheet to save permanently"
        )
    else:
        st.info("📝 No data available. Add students to see the dashboard.")

# ---------------- ADD STUDENT ----------------
elif menu == "Add Student":
    st.title("➕ Add New Student")
    
    st.warning("⚠️ **Manual Save Required**: After adding a student, download the CSV and paste it into your Google Sheet to save permanently.")

    with st.form("student_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Student Name *")
            gender = st.selectbox("Gender", ["Male","Female","Other"])
            address = st.text_area("Address")
            district = st.text_input("District *")
            state = st.text_input("State *")
        
        with col2:
            institution = st.text_input("Training Institution *")
            trade = st.text_input("Trade")
            status = st.selectbox("Training Status", ["Ongoing","Completed","Dropped"])
            start = st.date_input("Start Date")
            end = st.date_input("End Date")

        st.subheader("Placement Details")
        
        col3, col4 = st.columns(2)
        
        with col3:
            placement_hotel = st.text_input("Placement Hotel")
            placement_status = st.selectbox("Placement Status", ["Placed","Not Placed"])
        
        with col4:
            placement_date = st.date_input("Placement Date")

        submitted = st.form_submit_button("💾 Add to Session (Download CSV to Save Permanently)")

        if submitted:
            if not name or not institution or not district or not state:
                st.error("❌ Name, Institution, District, and State are required fields!")
            elif end < start:
                st.error("❌ End date cannot be before start date")
            else:
                new_row = {
                    "Student Name": name,
                    "Gender": gender,
                    "Address": address,
                    "District": district,
                    "State": state,
                    "Training Institution": institution,
                    "Trade": trade,
                    "Training Status": status,
                    "Start Date": str(start),
                    "End Date": str(end),
                    "Placement Hotel": placement_hotel,
                    "Placement Status": placement_status,
                    "Placement Date": str(placement_date)
                }
                
                new_data = pd.DataFrame([new_row])
                updated_df = pd.concat([df, new_data], ignore_index=True)
                
                if save_data_to_session(updated_df):
                    st.success("✅ Student added to session!")
                    st.info("👉 Go to Dashboard and click 'Download Backup CSV', then paste into your Google Sheet")
                    st.balloons()

# ---------------- VIEW ALL STUDENTS ----------------
elif menu == "View All Students":
    st.title("👥 All Students")
    
    if not df.empty:
        # Search functionality
        search = st.text_input("🔍 Search by name, district, or institution")
        
        if search:
            mask = df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)
            display_df = df[mask]
        else:
            display_df = df
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=600
        )
        
        st.info(f"Showing {len(display_df)} of {len(df)} students")
        
        # Download button
        st.download_button(
            "📥 Download All Data",
            display_df.to_csv(index=False).encode('utf-8'),
            "all_students.csv",
            "text/csv"
        )
    else:
        st.info("📝 No students added yet.")

# ---------------- DATA QUALITY ----------------
elif menu == "Data Quality":
    st.title("⚠️ Data Quality Check")

    if not df.empty:
        missing_status = df[df["Training Status"].isna() | (df["Training Status"]=="")]
        missing_inst = df[df["Training Institution"].isna() | (df["Training Institution"]=="")]
        missing_district = df[df["District"].isna() | (df["District"]=="")]
        missing_state = df[df["State"].isna() | (df["State"]=="")]

        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Missing Status", len(missing_status))
        with col2:
            st.metric("Missing Institution", len(missing_inst))
        with col3:
            st.metric("Missing District", len(missing_district))
        with col4:
            st.metric("Missing State", len(missing_state))

        st.subheader("Records Missing Training Status")
        if not missing_status.empty:
            st.dataframe(missing_status, use_container_width=True)
        else:
            st.success("✅ No missing training status")

        st.subheader("Records Missing Institution")
        if not missing_inst.empty:
            st.dataframe(missing_inst, use_container_width=True)
        else:
            st.success("✅ No missing institution")
            
        st.subheader("Records Missing District")
        if not missing_district.empty:
            st.dataframe(missing_district, use_container_width=True)
        else:
            st.success("✅ No missing district")
            
        st.subheader("Records Missing State")
        if not missing_state.empty:
            st.dataframe(missing_state, use_container_width=True)
        else:
            st.success("✅ No missing state")
            
    else:
        st.info("📝 No data to check")
