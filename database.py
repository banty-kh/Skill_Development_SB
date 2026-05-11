import sqlite3
import pandas as pd

DB_PATH = "skill_program.db"
TABLE_NAME = "students"

DEFAULT_COLUMNS = [
    "Student Name", "Gender", "Training Institution", "Trade",
    "Training Status", "Start Date", "End Date", "Batch",
    "Placement Hotel", "Placement Status", "Placement Date"
]


def init_db() -> None:
    """Create table if it doesn't exist."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            f'''
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                "Student Name" TEXT,
                "Gender" TEXT,
                "Training Institution" TEXT,
                "Trade" TEXT,
                "Training Status" TEXT,
                "Start Date" TEXT,
                "End Date" TEXT,
                "Batch" TEXT,
                "Placement Hotel" TEXT,
                "Placement Status" TEXT,
                "Placement Date" TEXT
            )
            '''
        )


def load_data() -> pd.DataFrame:
    init_db()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            return pd.read_sql_query(f"SELECT * FROM {TABLE_NAME}", conn)
    except Exception:
        return pd.DataFrame(columns=DEFAULT_COLUMNS)


def save_data(df: pd.DataFrame) -> None:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        df.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)
