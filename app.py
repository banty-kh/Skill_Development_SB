import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from io import StringIO
import base64
from pathlib import Path

st.set_page_config(page_title="Skill Development Dashboard", layout="wide")

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
            # Normalize column names from Sheets (trim spaces, remove BOM)
            df.columns = [str(c).replace("\ufeff", "").strip() for c in df.columns]
            
            # If empty or just headers
            if df.empty or len(df) == 0:
                return pd.DataFrame(columns=[
                    "Student Name","Gender","Address","District","State",
                    "Training Institution","Trade","Training Status",
                    "Start Date","End Date","Placement Hotel",
                    "Placement Status","Placement Date"
                ])

            # Ensure required columns always exist to prevent KeyError in UI filters
            required_cols = [
                "Student Name","Gender","Address","District","State",
                "Training Institution","Trade","Training Status",
                "Start Date","End Date","Placement Hotel",
                "Placement Status","Placement Date"
            ]
            for col in required_cols:
                if col not in df.columns:
                    df[col] = pd.NA

            # Normalize string values to avoid filter/group mismatches caused by extra spaces
            string_cols = [
                "Student Name","Gender","Address","District","State",
                "Training Institution","Trade","Training Status",
                "Placement Hotel","Placement Status"
            ]
            for col in string_cols:
                df[col] = df[col].astype("string").str.strip()

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

# ---------------- MENU ----------------
logo_path = Path("Sunbird Logo.png")
if logo_path.exists():
    st.sidebar.image(str(logo_path), use_container_width=True)

menu = st.sidebar.radio("Navigation", ["Dashboard", "Data Quality", "View All Students"])


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

    st.info("💡 **Note**: Dashboard data is loaded directly from your Google Sheet. Update the sheet to update charts.")

    ctrl_col1, ctrl_col2 = st.columns([1, 2])
    with ctrl_col1:
        if st.button("🔄 Reload from Google Sheet", use_container_width=True):
            st.rerun()

    palette_options = {
        "Plotly": px.colors.qualitative.Plotly,
        "Set2": px.colors.qualitative.Set2,
        "Safe": px.colors.qualitative.Safe,
        "Pastel": px.colors.qualitative.Pastel,
        "Dark24": px.colors.qualitative.Dark24,
    }
    with ctrl_col2:
        palette_name = st.selectbox("🎨 Graph Color Theme", list(palette_options.keys()), index=0)
    color_sequence = palette_options[palette_name]

    filtered = df.copy()

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Students", len(filtered))
    col2.metric("Ongoing", len(filtered[filtered["Training Status"]=="Ongoing"]) if not filtered.empty else 0)
    col3.metric("Completed", len(filtered[filtered["Training Status"]=="Completed"]) if not filtered.empty else 0)
    col4.metric("Placed", len(filtered[filtered["Placement Status"]=="Placed"]) if not filtered.empty else 0)

    if not filtered.empty:
        st.subheader("📈 Student Count Graphs")

        trade_chart = filtered.groupby("Trade").size().reset_index(name="Number of Students")
        st.markdown("#### 1) Trade-wise")
        st.plotly_chart(px.bar(trade_chart, x="Trade", y="Number of Students", color="Trade", color_discrete_sequence=color_sequence), use_container_width=True)

        partner_chart = filtered.groupby("Training Institution").size().reset_index(name="Number of Students")
        st.markdown("#### 2) Partner Institution-wise")
        st.plotly_chart(px.bar(partner_chart, x="Training Institution", y="Number of Students", color="Training Institution", color_discrete_sequence=color_sequence), use_container_width=True)

        district_chart = filtered.groupby("District").size().reset_index(name="Number of Students")
        st.markdown("#### 3) District-wise")
        st.plotly_chart(px.bar(district_chart, x="District", y="Number of Students", color="District", color_discrete_sequence=color_sequence), use_container_width=True)

        state_chart = filtered.groupby("State").size().reset_index(name="Number of Students")
        st.markdown("#### 4) State-wise")
        st.plotly_chart(px.bar(state_chart, x="State", y="Number of Students", color="State", color_discrete_sequence=color_sequence), use_container_width=True)

        status_chart = filtered.groupby("Training Status").size().reset_index(name="Number of Students")
        st.markdown("#### 5) Training Status-wise")
        st.plotly_chart(px.bar(status_chart, x="Training Status", y="Number of Students", color="Training Status", color_discrete_sequence=color_sequence), use_container_width=True)

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
                    st.plotly_chart(px.bar(hotel_chart, x="Placement Hotel", y="Count", color="Placement Hotel", color_discrete_sequence=color_sequence), use_container_width=True)

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

    else:
        st.info("📝 No data available. Please update your Google Sheet to see dashboard data.")

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
