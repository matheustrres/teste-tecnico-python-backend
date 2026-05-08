from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator, model_validator


class FocusRecordCreate(BaseModel):
    nivel_foco: int = Field(ge=1, le=5)
    tempo_minutos: int = Field(gt=0)
    comentario: str
    categoria: str = "geral"

    @field_validator("comentario", "categoria")
    @classmethod
    def validate_not_empty(cls, value: str) -> str:
        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError("não pode ser vazio")
        return cleaned_value


class FocusRecordResponse(BaseModel):
    id: int
    user_id: str
    nivel_foco: int
    tempo_minutos: int
    comentario: str
    categoria: str
    criado_em: datetime


class CategoryInsight(BaseModel):
    categoria: str
    media_foco: float
    tempo_total: int
    recomendacao: str


class DiagnosisResponse(BaseModel):
    media_nivel_foco: float
    tempo_total_focado: int
    mensagem_feedback: str
    insights_por_categoria: list[CategoryInsight]


class PeriodQuery(BaseModel):
    from_date: date | None = Field(default=None, alias="from")
    to_date: date | None = Field(default=None, alias="to")

    @model_validator(mode="after")
    def validate_date_order(self) -> "PeriodQuery":
        if self.from_date is not None and self.to_date is not None and self.from_date > self.to_date:
            raise ValueError("'from' deve ser menor ou igual a 'to'")
        return self


class PeriodResponse(BaseModel):
    from_date: date = Field(alias="from")
    to_date: date = Field(alias="to")
    timezone: str


class DashboardSummary(BaseModel):
    sessoes_total: int
    tempo_total_focado: int
    media_nivel_foco: float


class FocusDropAlert(BaseModel):
    status: bool
    variacao_percentual: float
    mensagem: str


class CategorySummary(BaseModel):
    categoria: str
    media_foco: float
    tempo_total: int


class PreviousPeriodComparison(BaseModel):
    media_nivel_foco_delta: float
    tempo_total_focado_delta: int
    sessoes_total_delta: int


class ProductivityDashboardResponse(BaseModel):
    periodo: PeriodResponse
    resumo: DashboardSummary
    score_consistencia: float
    alerta_queda_foco: FocusDropAlert
    top_categoria: CategorySummary | None
    categoria_em_risco: CategorySummary | None
    streak_dias: int
    faixas_de_ouro: list[str]
    comparativo_periodo_anterior: PreviousPeriodComparison
    acoes_recomendadas: list[str]
