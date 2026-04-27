import streamlit as st
import pandas as pd
from database import load_data, save_data, init_db
import os

st.set_page_config(page_title="Skill Development MIS", layout="wide")

# Initialize DB if not exists
if not os.path.exists("skill_program.db"):
    init_db()

df = load_data()

st.sidebar.title("Navigation")
menu = st.sidebar.radio("Go to", ["Dashboard", "Add Student", "Data Quality"])

# ---------------- Dashboard ----------------
if menu == "Dashboard":
    st.title("📊 Skill Development Dashboard")

    inst = st.sidebar.multiselect("Institution", df["Training Institution"].dropna().unique(), default=df["Training Institution"].dropna().unique())
    status = st.sidebar.multiselect("Status", df["Training Status"].dropna().unique(), default=df["Training Status"].dropna().unique())

    filtered = df[(df["Training Institution"].isin(inst)) & (df["Training Status"].isin(status))]

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Students", len(filtered))
    col2.metric("Ongoing", len(filtered[filtered["Training Status"]=="Ongoing"]))
    col3.metric("Completed", len(filtered[filtered["Training Status"]=="Completed"]))

    st.bar_chart(filtered["Training Institution"].value_counts())

# ---------------- Add Student ----------------
elif menu == "Add Student":
    st.title("➕ Add Student")

    with st.form("form"):
        name = st.text_input("Name")
        gender = st.selectbox("Gender", ["Male","Female","Other"])
        inst = st.text_input("Institution")
        trade = st.text_input("Trade")
        status = st.selectbox("Status", ["Ongoing","Completed","Dropped"])
        start = st.date_input("Start Date")
        end = st.date_input("End Date")
        batch = st.text_input("Batch")

        submit = st.form_submit_button("Save")

        if submit:
            new = pd.DataFrame([{
                "Student Name": name,
                "Gender": gender,
                "Training Institution": inst,
                "Trade": trade,
                "Training Status": status,
                "Start Date": start,
                "End Date": end,
                "Batch": batch
            }])

            df = pd.concat([df, new], ignore_index=True)
            save_data(df)
            st.success("Saved!")

# ---------------- Data Quality ----------------
elif menu == "Data Quality":
    st.title("⚠ Data Quality")

    st.write("Missing Status")
    st.dataframe(df[df["Training Status"]==""])

