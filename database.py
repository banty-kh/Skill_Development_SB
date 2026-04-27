from sqlalchemy import create_engine
import pandas as pd

engine = create_engine("sqlite:///skill_program.db")

def init_db():
    df = pd.DataFrame(columns=[
        "Student Name","Gender","Training Institution","Trade",
        "Training Status","Start Date","End Date","Batch"
    ])
    df.to_sql("students", engine, if_exists="replace", index=False)

def load_data():
    try:
        return pd.read_sql("SELECT * FROM students", engine)
    except:
        return pd.DataFrame()

def save_data(df):
    df.to_sql("students", engine, if_exists="replace", index=False)
