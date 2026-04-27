import streamlit as st
import pandas as pd
import plotly.express as px
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
import os

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Skill Development MIS", layout="wide")

DATA_FILE = "data.csv"

# ---------------- LOAD AUTH ----------------
with open("config.yaml") as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"]
)

name, authentication_status, username = authenticator.login("Login", "main")

# ---------------- AUTH CHECK ----------------
if authentication_status is False:
    st.error("Invalid credentials")

elif authentication_status is None:
    st.warning("Enter login details")

elif authentication_status:

    authenticator.logout("Logout", "sidebar")
    st.sidebar.write(f"Welcome {name}")

    # ---------------- LOAD DATA ----------------
    def load_data():
        if os.path.exists(DATA_FILE):
            return pd.read_csv(DATA_FILE)
        else:
            return pd.DataFrame(columns=[
                "Student Name","Gender","Training Institution","Trade",
                "Training Status","Start Date","End Date","Batch"
            ])

    def save_data(df):
        df.to_csv(DATA_FILE, index=False)

    df = load_data()

    # ---------------- MENU ----------------
    menu = st.sidebar.radio("Navigation", ["Dashboard", "Add Student", "Data Quality"])

    # ================= DASHBOARD =================
    if menu == "Dashboard":

        st.title("📊 Skill Development Dashboard")

        # Filters
        inst_filter = st.sidebar.multiselect(
            "Institution", df["Training Institution"].dropna().unique(),
            default=df["Training Institution"].dropna().unique()
        )

        status_filter = st.sidebar.multiselect(
            "Status", df["Training Status"].dropna().unique(),
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

        st.subheader("Status Distribution")
        st.plotly_chart(px.pie(filtered, names="Training Status"), use_container_width=True)

        st.subheader("Institution vs Status")
        inst_status = filtered.groupby(["Training Institution","Training Status"]).size().reset_index(name="Count")
        st.plotly_chart(px.bar(inst_status, x="Training Institution", y="Count", color="Training Status", barmode="stack"), use_container_width=True)

        st.dataframe(filtered)

    # ================= ADD STUDENT =================
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

            submitted = st.form_submit_button("Save")

            if submitted:
                new_data = pd.DataFrame([{
                    "Student Name": name,
                    "Gender": gender,
                    "Training Institution": institution,
                    "Trade": trade,
                    "Training Status": status,
                    "Start Date": start,
                    "End Date": end,
                    "Batch": batch
                }])

                df = pd.concat([df, new_data], ignore_index=True)
                save_data(df)

                st.success("Student added successfully!")

    # ================= DATA QUALITY =================
    elif menu == "Data Quality":

        st.title("⚠️ Data Quality Check")

        missing_status = df[df["Training Status"].isna() | (df["Training Status"]=="")]
        missing_inst = df[df["Training Institution"].isna() | (df["Training Institution"]=="")]

        st.subheader("Missing Training Status")
        st.write(missing_status)

        st.subheader("Missing Institution")
        st.write(missing_inst)

        st.warning(f"{len(missing_status)} records missing status")
        st.warning(f"{len(missing_inst)} records missing institution")
