from collections import defaultdict

from app.repository import FocusRecord, FocusRecordRepository


class DiagnosisService:
    def __init__(self, repository: FocusRecordRepository) -> None:
        self.repository = repository

    def register_focus(self, nivel_foco: int, tempo_minutos: int, comentario: str, categoria: str) -> FocusRecord:
        return self.repository.create(nivel_foco, tempo_minutos, comentario, categoria)

    def generate_diagnosis(self) -> dict:
        records = self.repository.list_all()
        if not records:
            return {
                "media_nivel_foco": 0.0,
                "tempo_total_focado": 0,
                "mensagem_feedback": "Sem registros ainda. Inicie uma sessão para gerar diagnóstico.",
                "insights_por_categoria": [],
            }

        average_focus = round(sum(item.nivel_foco for item in records) / len(records), 2)
        total_time = sum(item.tempo_minutos for item in records)

        return {
            "media_nivel_foco": average_focus,
            "tempo_total_focado": total_time,
            "mensagem_feedback": self._build_feedback_message(average_focus),
            "insights_por_categoria": self._build_category_insights(records),
        }

    @staticmethod
    def _build_feedback_message(average_focus: float) -> str:
        if average_focus < 3.0:
            return "Seu foco está baixo. Faça pausas mais longas e reduza notificações."
        if average_focus <= 4.0:
            return "Produtividade estável. Pequenos ajustes de ambiente podem elevar seu foco."
        return "Você está em uma maratona produtiva de alto nível!"

    def _build_category_insights(self, records: list[FocusRecord]) -> list[dict]:
        grouped: dict[str, dict[str, float]] = defaultdict(lambda: {"focus_sum": 0.0, "count": 0.0, "time": 0.0})

        for item in records:
            bucket = grouped[item.categoria]
            bucket["focus_sum"] += item.nivel_foco
            bucket["count"] += 1
            bucket["time"] += item.tempo_minutos

        insights: list[dict] = []
        for category, values in grouped.items():
            average_focus = round(values["focus_sum"] / values["count"], 2)
            total_time = int(values["time"])
            insights.append(
                {
                    "categoria": category,
                    "media_foco": average_focus,
                    "tempo_total": total_time,
                    "recomendacao": self._build_category_recommendation(average_focus),
                }
            )

        return sorted(insights, key=lambda item: item["categoria"])

    @staticmethod
    def _build_category_recommendation(average_focus: float) -> str:
        if average_focus < 3.0:
            return "Blocos menores e menos interrupções podem ajudar nesta categoria."
        if average_focus <= 4.0:
            return "Você está consistente; experimente metas mais objetivas por sessão."
        return "Excelente desempenho; mantenha esse padrão de execução."
