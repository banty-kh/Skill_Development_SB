import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Skill Development MIS", layout="wide")

from database import load_data, save_data

# ---------------- PUBLIC ACCESS ----------------
# Authentication has been removed to make the app publicly accessible.

# ---------------- LOAD DATA ----------------
df = load_data()

# ---------------- ROLE BASED MENU ----------------
menu = st.sidebar.radio("Navigation", ["Dashboard", "Add Student", "Data Quality"])

# ---------------- DASHBOARD ----------------
if menu == "Dashboard":

    st.title("📊 Skill Development Dashboard")

    inst_filter = st.sidebar.multiselect(
        "Institution",
        df["Training Institution"].dropna().unique(),
        default=df["Training Institution"].dropna().unique()
    )

    status_filter = st.sidebar.multiselect(
        "Training Status",
        df["Training Status"].dropna().unique(),
        default=df["Training Status"].dropna().unique()
    )

    filtered = df[
        (df["Training Institution"].isin(inst_filter)) &
        (df["Training Status"].isin(status_filter))
    ]

    # KPIs
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Students", len(filtered))
    col2.metric("Ongoing", len(filtered[filtered["Training Status"]=="Ongoing"]))
    col3.metric("Completed", len(filtered[filtered["Training Status"]=="Completed"]))

    # Charts
    st.subheader("Institution-wise Students")
    inst_chart = filtered.groupby("Training Institution").size().reset_index(name="Count")
    st.plotly_chart(px.bar(inst_chart, x="Training Institution", y="Count"), use_container_width=True)

    st.subheader("Training Status Distribution")
    st.plotly_chart(px.pie(filtered, names="Training Status"), use_container_width=True)

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
        hotel_chart = filtered[filtered["Placement Status"]=="Placed"] \
            .groupby("Placement Hotel").size().reset_index(name="Count")

        if not hotel_chart.empty:
            st.plotly_chart(px.bar(hotel_chart, x="Placement Hotel", y="Count"), use_container_width=True)

    # Backup Button
    st.download_button(
        "Download Backup",
        filtered.to_csv(index=False),
        "backup.csv"
    )

# ---------------- ADD STUDENT ----------------
elif menu == "Add Student":

    st.title("➕ Add New Student")

    with st.form("student_form"):
        name = st.text_input("Student Name")
        gender = st.selectbox("Gender", ["Male","Female","Other"])
        institution = st.text_input("Training Institution")
        trade = st.text_input("Trade")
        status = st.selectbox("Training Status", ["Ongoing","Completed","Dropped"])
        start = st.date_input("Start Date")
        end = st.date_input("End Date")
        batch = st.text_input("Batch")

        # Placement
        placement_hotel = st.text_input("Placement Hotel")
        placement_status = st.selectbox("Placement Status", ["Placed","Not Placed"])
        placement_date = st.date_input("Placement Date")

        submitted = st.form_submit_button("Save")

        if submitted:
            if not name or not institution:
                st.error("Name and Institution are required")
            elif end < start:
                st.error("End date cannot be before start date")
            else:
                new_data = pd.DataFrame([{
                    "Student Name": name,
                    "Gender": gender,
                    "Training Institution": institution,
                    "Trade": trade,
                    "Training Status": status,
                    "Start Date": start,
                    "End Date": end,
                    "Batch": batch,
                    "Placement Hotel": placement_hotel,
                    "Placement Status": placement_status,
                    "Placement Date": placement_date
                }])

                df = pd.concat([df, new_data], ignore_index=True)
                save_data(df)

                st.success("Student added successfully!")

# ---------------- DATA QUALITY ----------------
elif menu == "Data Quality":

    st.title("⚠️ Data Quality Check")

    missing_status = df[df["Training Status"].isna() | (df["Training Status"]=="")]
    missing_inst = df[df["Training Institution"].isna() | (df["Training Institution"]=="")]

    st.subheader("Missing Training Status")
    st.dataframe(missing_status)

    st.subheader("Missing Institution")
    st.dataframe(missing_inst)

    st.warning(f"{len(missing_status)} records missing status")
    st.warning(f"{len(missing_inst)} records missing institution")
