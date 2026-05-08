from sqlalchemy import create_engine, text
import pandas as pd

DB_PATH = "sqlite:///skill_program.db"
TABLE_NAME = "students"

engine = create_engine(DB_PATH)

DEFAULT_COLUMNS = [
    "Student Name", "Gender", "Training Institution", "Trade",
    "Training Status", "Start Date", "End Date", "Batch",
    "Placement Hotel", "Placement Status", "Placement Date"
]


def init_db() -> None:
    """Create table if it doesn't exist."""
    with engine.begin() as conn:
        conn.execute(text(
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
        ))


def load_data() -> pd.DataFrame:
    init_db()
    try:
        return pd.read_sql(f"SELECT * FROM {TABLE_NAME}", engine)
    except Exception:
        return pd.DataFrame(columns=DEFAULT_COLUMNS)


def save_data(df: pd.DataFrame) -> None:
    init_db()
    df.to_sql(TABLE_NAME, engine, if_exists="replace", index=False)
