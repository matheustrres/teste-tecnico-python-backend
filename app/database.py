import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "foco.db"


def init_db(db_path: str | Path = DEFAULT_DB_PATH) -> None:
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS registros_foco (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL DEFAULT 'anon-default',
                nivel_foco INTEGER NOT NULL,
                tempo_minutos INTEGER NOT NULL,
                comentario TEXT NOT NULL,
                categoria TEXT NOT NULL,
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        columns = conn.execute("PRAGMA table_info(registros_foco)").fetchall()
        has_user_id_column = any(column[1] == "user_id" for column in columns)
        if not has_user_id_column:
            conn.execute("ALTER TABLE registros_foco ADD COLUMN user_id TEXT NOT NULL DEFAULT 'anon-default'")

        conn.execute("CREATE INDEX IF NOT EXISTS idx_registros_foco_user_created ON registros_foco(user_id, criado_em)")
        conn.commit()
    finally:
        conn.close()


@contextmanager
def get_connection(db_path: str | Path = DEFAULT_DB_PATH) -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
