import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Skill Development MIS", layout="wide")

# ---------------- GOOGLE SHEETS CONNECTION ----------------
@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)


def load_data():
    """Load data from Google Sheets"""
    try:
        conn = get_connection()
        df = conn.read(worksheet="Sheet1", ttl=5)

        # If sheet is empty, return empty dataframe with correct columns
        if df.empty or len(df.columns) == 1:
            return pd.DataFrame(
                columns=[
                    "Student Name",
                    "Gender",
                    "Address",
                    "District",
                    "State",
                    "Training Institution",
                    "Trade",
                    "Training Status",
                    "Start Date",
                    "End Date",
                    "Placement Hotel",
                    "Placement Status",
                    "Placement Date",
                ]
            )
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(
            columns=[
                "Student Name",
                "Gender",
                "Address",
                "District",
                "State",
                "Training Institution",
                "Trade",
                "Training Status",
                "Start Date",
                "End Date",
                "Placement Hotel",
                "Placement Status",
                "Placement Date",
            ]
        )


def save_data(df):
    """Save data to Google Sheets"""
    try:
        conn = get_connection()
        conn.update(worksheet="Sheet1", data=df)
        return True
    except Exception as e:
        st.error(f"Error saving data: {e}")
        return False


# Load data
df = load_data()

# ---------------- MENU ----------------
menu = st.sidebar.radio(
    "Navigation", ["Dashboard", "Add Student", "Data Quality", "View All Students"]
)

# ---------------- DASHBOARD ----------------
if menu == "Dashboard":
    st.title("📊 Skill Development Dashboard")

    if not df.empty:
        # Filters
        inst_options = df["Training Institution"].dropna().unique().tolist()
        status_options = df["Training Status"].dropna().unique().tolist()
        district_options = df["District"].dropna().unique().tolist()
        state_options = df["State"].dropna().unique().tolist()

        inst_filter = st.sidebar.multiselect(
            "Institution",
            inst_options,
            default=inst_options,
        )

        status_filter = st.sidebar.multiselect(
            "Training Status",
            status_options,
            default=status_options,
        )

        district_filter = st.sidebar.multiselect(
            "District",
            district_options,
            default=district_options,
        )

        state_filter = st.sidebar.multiselect(
            "State",
            state_options,
            default=state_options,
        )

        filtered = df[
            (df["Training Institution"].isin(inst_filter))
            & (df["Training Status"].isin(status_filter))
            & (df["District"].isin(district_filter))
            & (df["State"].isin(state_filter))
        ]
    else:
        filtered = df

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Students", len(filtered))
    col2.metric(
        "Ongoing",
        len(filtered[filtered["Training Status"] == "Ongoing"])
        if not filtered.empty
        else 0,
    )
    col3.metric(
        "Completed",
        len(filtered[filtered["Training Status"] == "Completed"])
        if not filtered.empty
        else 0,
    )
    col4.metric("Districts", filtered["District"].nunique() if not filtered.empty else 0)

    if not filtered.empty:
        # Charts
        st.subheader("Institution-wise Students")
        inst_chart = (
            filtered.groupby("Training Institution").size().reset_index(name="Count")
        )
        st.plotly_chart(
            px.bar(inst_chart, x="Training Institution", y="Count"),
            use_container_width=True,
        )

        # New: District-wise Distribution
        st.subheader("District-wise Students")
        district_chart = filtered.groupby("District").size().reset_index(name="Count")
        st.plotly_chart(
            px.bar(district_chart, x="District", y="Count"), use_container_width=True
        )

        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("Training Status Distribution")
            st.plotly_chart(
                px.pie(filtered, names="Training Status"), use_container_width=True
            )

        with col_right:
            st.subheader("State-wise Distribution")
            st.plotly_chart(px.pie(filtered, names="State"), use_container_width=True)

        st.subheader("Institution vs Status")
        inst_status = (
            filtered.groupby(["Training Institution", "Training Status"])
            .size()
            .reset_index(name="Count")
        )
        st.plotly_chart(
            px.bar(
                inst_status,
                x="Training Institution",
                y="Count",
                color="Training Status",
                barmode="stack",
            ),
            use_container_width=True,
        )

        # Placement Section
        st.subheader("🏨 Placement Overview")

        placed = len(filtered[filtered["Placement Status"] == "Placed"])
        not_placed = len(filtered[filtered["Placement Status"] == "Not Placed"])

        col4, col5 = st.columns(2)
        col4.metric("Placed", placed)
        col5.metric("Not Placed", not_placed)

        if "Placement Hotel" in filtered.columns:
            hotel_data = filtered[filtered["Placement Status"] == "Placed"]
            if not hotel_data.empty:
                hotel_chart = hotel_data.groupby("Placement Hotel").size().reset_index(
                    name="Count"
                )
                if not hotel_chart.empty:
                    st.plotly_chart(
                        px.bar(hotel_chart, x="Placement Hotel", y="Count"),
                        use_container_width=True,
                    )

        # Backup Button
        st.download_button(
            "📥 Download Backup",
            filtered.to_csv(index=False).encode("utf-8"),
            "backup.csv",
            "text/csv",
        )
    else:
        st.info("📝 No data available. Add students to see the dashboard.")

# ---------------- ADD STUDENT ----------------
elif menu == "Add Student":
    st.title("➕ Add New Student")

    with st.form("student_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Student Name *")
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            address = st.text_area("Address")
            district = st.text_input("District *")
            state = st.text_input("State *")

        with col2:
            institution = st.text_input("Training Institution *")
            trade = st.text_input("Trade")
            status = st.selectbox("Training Status", ["Ongoing", "Completed", "Dropped"])
            start = st.date_input("Start Date")
            end = st.date_input("End Date")

        st.subheader("Placement Details")

        col3, col4 = st.columns(2)

        with col3:
            placement_hotel = st.text_input("Placement Hotel")
            placement_status = st.selectbox("Placement Status", ["Placed", "Not Placed"])

        with col4:
            placement_date = st.date_input("Placement Date")

        submitted = st.form_submit_button("💾 Save Student")

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
                    "Placement Date": str(placement_date),
                }

                new_data = pd.DataFrame([new_row])
                updated_df = pd.concat([df, new_data], ignore_index=True)

                if save_data(updated_df):
                    st.success("✅ Student added successfully!")
                    st.balloons()
                    # Clear cache to reload fresh data
                    st.cache_resource.clear()
                    st.rerun()
                else:
                    st.error("❌ Failed to save data. Please try again.")

# ---------------- VIEW ALL STUDENTS ----------------
elif menu == "View All Students":
    st.title("👥 All Students")

    if not df.empty:
        # Search functionality
        search = st.text_input("🔍 Search by name, district, or institution")

        if search:
            mask = df.apply(
                lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1
            )
            display_df = df[mask]
        else:
            display_df = df

        st.dataframe(
            display_df,
            use_container_width=True,
            height=600,
        )

        st.info(f"Showing {len(display_df)} of {len(df)} students")
    else:
        st.info("📝 No students added yet.")

# ---------------- DATA QUALITY ----------------
elif menu == "Data Quality":
    st.title("⚠️ Data Quality Check")

    if not df.empty:
        missing_status = df[df["Training Status"].isna() | (df["Training Status"] == "")]
        missing_inst = df[
            df["Training Institution"].isna() | (df["Training Institution"] == "")
        ]
        missing_district = df[df["District"].isna() | (df["District"] == "")]
        missing_state = df[df["State"].isna() | (df["State"] == "")]

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
