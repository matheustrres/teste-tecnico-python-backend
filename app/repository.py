from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.database import DEFAULT_DB_PATH, get_connection


@dataclass
class FocusRecord:
    id: int
    nivel_foco: int
    tempo_minutos: int
    comentario: str
    categoria: str
    criado_em: datetime


class FocusRecordRepository:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        self.db_path = db_path

    def create(self, nivel_foco: int, tempo_minutos: int, comentario: str, categoria: str) -> FocusRecord:
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO registros_foco (nivel_foco, tempo_minutos, comentario, categoria)
                VALUES (?, ?, ?, ?)
                """,
                (nivel_foco, tempo_minutos, comentario, categoria),
            )
            inserted_id = cursor.lastrowid
            row = conn.execute(
                """
                SELECT id, nivel_foco, tempo_minutos, comentario, categoria, criado_em
                FROM registros_foco
                WHERE id = ?
                """,
                (inserted_id,),
            ).fetchone()
        return self._row_to_entity(row)

    def list_all(self) -> list[FocusRecord]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT id, nivel_foco, tempo_minutos, comentario, categoria, criado_em
                FROM registros_foco
                ORDER BY id ASC
                """
            ).fetchall()
        return [self._row_to_entity(row) for row in rows]

    @staticmethod
    def _row_to_entity(row) -> FocusRecord:
        return FocusRecord(
            id=row["id"],
            nivel_foco=row["nivel_foco"],
            tempo_minutos=row["tempo_minutos"],
            comentario=row["comentario"],
            categoria=row["categoria"],
            criado_em=datetime.fromisoformat(row["criado_em"]),
        )
