from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.database import DEFAULT_DB_PATH, get_connection


@dataclass
class FocusRecord:
    id: int
    user_id: str
    nivel_foco: int
    tempo_minutos: int
    comentario: str
    categoria: str
    created_at: datetime


class FocusRecordRepository:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        self.db_path = db_path

    def create(self, user_id: str, nivel_foco: int, tempo_minutos: int, comentario: str, categoria: str) -> FocusRecord:
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO registros_foco (user_id, nivel_foco, tempo_minutos, comentario, categoria)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, nivel_foco, tempo_minutos, comentario, categoria),
            )
            inserted_id = cursor.lastrowid
            row = conn.execute(
                """
                SELECT id, user_id, nivel_foco, tempo_minutos, comentario, categoria, criado_em
                FROM registros_foco
                WHERE id = ?
                """,
                (inserted_id,),
            ).fetchone()
        return self._row_to_entity(row)

    def list_all(self, user_id: str) -> list[FocusRecord]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT id, user_id, nivel_foco, tempo_minutos, comentario, categoria, criado_em
                FROM registros_foco
                WHERE user_id = ?
                ORDER BY id ASC
                """,
                (user_id,),
            ).fetchall()
        return [self._row_to_entity(row) for row in rows]

    def list_by_local_date_range(self, user_id: str, start_date: date, end_date: date, timezone: str) -> list[FocusRecord]:
        zone = ZoneInfo(timezone)
        records = self.list_all(user_id)
        filtered: list[FocusRecord] = []
        for record in records:
            local_date = record.created_at.astimezone(zone).date()
            if start_date <= local_date <= end_date:
                filtered.append(record)
        return filtered

    @staticmethod
    def _row_to_entity(row) -> FocusRecord:
        return FocusRecord(
            id=row["id"],
            user_id=row["user_id"],
            nivel_foco=row["nivel_foco"],
            tempo_minutos=row["tempo_minutos"],
            comentario=row["comentario"],
            categoria=row["categoria"],
            created_at=FocusRecordRepository._parse_datetime(row["criado_em"]),
        )

    @staticmethod
    def _parse_datetime(raw_value: str) -> datetime:
        normalized = raw_value.replace(" ", "T")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
