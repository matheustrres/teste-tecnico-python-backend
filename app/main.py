from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from pydantic import ValidationError

from app.database import init_db
from app.repository import FocusRecordRepository
from app.schemas import (
    DiagnosisResponse,
    FocusRecordCreate,
    FocusRecordResponse,
    PeriodQuery,
    ProductivityDashboardResponse,
)
from app.service import DiagnosisService


def create_app(db_path: str | Path | None = None) -> FastAPI:
    app = FastAPI(title="API de Foco e Produtividade", version="1.0.0")

    db_target = db_path if db_path is not None else None
    init_db(db_target) if db_target is not None else init_db()
    repository = FocusRecordRepository(db_target) if db_target is not None else FocusRecordRepository()
    service = DiagnosisService(repository)

    @app.post("/registro-foco", response_model=FocusRecordResponse, status_code=201)
    def create_record(payload: FocusRecordCreate) -> FocusRecordResponse:
        record = service.register_focus(
            nivel_foco=payload.nivel_foco,
            tempo_minutos=payload.tempo_minutos,
            comentario=payload.comentario,
            categoria=payload.categoria,
        )
        return FocusRecordResponse.model_validate(
            {
                "id": record.id,
                "nivel_foco": record.nivel_foco,
                "tempo_minutos": record.tempo_minutos,
                "comentario": record.comentario,
                "categoria": record.categoria,
                "criado_em": record.created_at,
            }
        )

    @app.get("/diagnostico-produtividade", response_model=DiagnosisResponse)
    def get_diagnosis() -> DiagnosisResponse:
        return DiagnosisResponse.model_validate(service.generate_diagnosis())

    @app.get("/dashboard-produtividade", response_model=ProductivityDashboardResponse)
    def get_productivity_dashboard(
        from_date: date | None = Query(default=None, alias="from"),
        to_date: date | None = Query(default=None, alias="to"),
    ) -> ProductivityDashboardResponse:
        try:
            period_query = PeriodQuery.model_validate({"from": from_date, "to": to_date})
        except ValidationError as exc:
            messages = [error["msg"] for error in exc.errors()]
            raise HTTPException(status_code=422, detail=messages) from exc

        try:
            dashboard = service.generate_dashboard(period_query.from_date, period_query.to_date)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        return ProductivityDashboardResponse.model_validate(dashboard)

    return app


app = create_app()
