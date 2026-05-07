from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class RegistroFocoCreate(BaseModel):
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


class RegistroFocoResponse(BaseModel):
    id: int
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
