from pathlib import Path

from fastapi import FastAPI

from app.database import init_db
from app.repository import FocusRecordRepository
from app.schemas import DiagnosisResponse, RegistroFocoCreate, RegistroFocoResponse
from app.service import DiagnosisService


def create_app(db_path: str | Path | None = None) -> FastAPI:
    app = FastAPI(title="API de Foco e Produtividade", version="1.0.0")

    db_target = db_path if db_path is not None else None
    init_db(db_target) if db_target is not None else init_db()
    repository = FocusRecordRepository(db_target) if db_target is not None else FocusRecordRepository()
    service = DiagnosisService(repository)

    @app.post("/registro-foco", response_model=RegistroFocoResponse, status_code=201)
    def create_record(payload: RegistroFocoCreate) -> RegistroFocoResponse:
        record = service.register_focus(
            nivel_foco=payload.nivel_foco,
            tempo_minutos=payload.tempo_minutos,
            comentario=payload.comentario,
            categoria=payload.categoria,
        )
        return RegistroFocoResponse.model_validate(record.__dict__)

    @app.get("/diagnostico-produtividade", response_model=DiagnosisResponse)
    def get_diagnosis() -> DiagnosisResponse:
        return DiagnosisResponse.model_validate(service.generate_diagnosis())

    return app


criar_app = create_app
app = create_app()
