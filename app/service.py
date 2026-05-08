from collections import defaultdict
from datetime import date, datetime
from math import sqrt
from os import getenv
from zoneinfo import ZoneInfo

from app.repository import FocusRecord, FocusRecordRepository


class DiagnosisService:
    DEFAULT_DASHBOARD_TIMEZONE = "America/Sao_Paulo"
    DASHBOARD_TIMEZONE_ENV_VAR = "DASHBOARD_TIMEZONE"
    ALERT_DROP_THRESHOLD = -15.0

    def __init__(self, repository: FocusRecordRepository, dashboard_timezone: str | None = None) -> None:
        self.repository = repository
        self.dashboard_timezone = self._resolve_dashboard_timezone(dashboard_timezone)

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

    def generate_dashboard(self, from_date: date | None, to_date: date | None) -> dict:
        period_start, period_end = self._resolve_period(from_date, to_date)
        records = self.repository.list_by_local_date_range(period_start, period_end, self.dashboard_timezone)
        summary = self._build_summary(records)
        consistency_score = self._build_consistency_score(records, period_start, period_end)
        focus_alert = self._build_focus_drop_alert(records)
        top_category, risk_category = self._extract_category_extremes(records)
        actions = self._build_recommended_actions(consistency_score, focus_alert["status"], risk_category)

        return {
            "periodo": {
                "from": period_start,
                "to": period_end,
                "timezone": self.dashboard_timezone,
            },
            "resumo": summary,
            "score_consistencia": consistency_score,
            "alerta_queda_foco": focus_alert,
            "top_categoria": top_category,
            "categoria_em_risco": risk_category,
            "acoes_recomendadas": actions,
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

    def _resolve_period(self, from_date: date | None, to_date: date | None) -> tuple[date, date]:
        timezone = ZoneInfo(self.dashboard_timezone)
        today = datetime.now(timezone).date()
        period_start = from_date or today
        period_end = to_date or today

        if period_start > period_end:
            raise ValueError("'from' deve ser menor ou igual a 'to'")

        return period_start, period_end

    @staticmethod
    def _build_summary(records: list[FocusRecord]) -> dict:
        if not records:
            return {
                "sessoes_total": 0,
                "tempo_total_focado": 0,
                "media_nivel_foco": 0.0,
            }

        return {
            "sessoes_total": len(records),
            "tempo_total_focado": sum(item.tempo_minutos for item in records),
            "media_nivel_foco": round(sum(item.nivel_foco for item in records) / len(records), 2),
        }

    def _build_consistency_score(self, records: list[FocusRecord], period_start: date, period_end: date) -> float:
        if not records:
            return 0.0

        timezone = ZoneInfo(self.dashboard_timezone)
        total_days = (period_end - period_start).days + 1
        active_days = {item.created_at.astimezone(timezone).date() for item in records}
        regularity_score = (len(active_days) / total_days) * 100

        focus_values = [item.nivel_foco for item in records]
        average_focus = sum(focus_values) / len(focus_values)
        variance = sum((value - average_focus) ** 2 for value in focus_values) / len(focus_values)
        std_deviation = sqrt(variance)
        stability_score = max(0.0, 100 - ((std_deviation / 2) * 100))

        score = (regularity_score * 0.6) + (stability_score * 0.4)
        return round(max(0.0, min(100.0, score)), 2)

    @classmethod
    def _resolve_dashboard_timezone(cls, explicit_timezone: str | None) -> str:
        candidate = explicit_timezone or getenv(cls.DASHBOARD_TIMEZONE_ENV_VAR) or cls.DEFAULT_DASHBOARD_TIMEZONE
        try:
            ZoneInfo(candidate)
            return candidate
        except Exception:
            return cls.DEFAULT_DASHBOARD_TIMEZONE

    @classmethod
    def _build_focus_drop_alert(cls, records: list[FocusRecord]) -> dict:
        if len(records) < 4:
            return {
                "status": False,
                "variacao_percentual": 0.0,
                "mensagem": "Dados insuficientes para detectar tendência de queda de foco.",
            }

        ordered_records = sorted(records, key=lambda item: item.created_at)
        split_index = len(ordered_records) // 2
        older_half = ordered_records[:split_index]
        recent_half = ordered_records[split_index:]

        if not older_half or not recent_half:
            return {
                "status": False,
                "variacao_percentual": 0.0,
                "mensagem": "Dados insuficientes para detectar tendência de queda de foco.",
            }

        old_average = sum(item.nivel_foco for item in older_half) / len(older_half)
        recent_average = sum(item.nivel_foco for item in recent_half) / len(recent_half)

        if old_average == 0:
            variation = 0.0
        else:
            variation = round(((recent_average - old_average) / old_average) * 100, 2)

        has_alert = variation <= cls.ALERT_DROP_THRESHOLD
        message = (
            "Queda de foco detectada no período recente; revise interrupções e tamanho dos blocos."
            if has_alert
            else "Sem queda relevante de foco no período analisado."
        )

        return {
            "status": has_alert,
            "variacao_percentual": variation,
            "mensagem": message,
        }

    @staticmethod
    def _extract_category_extremes(records: list[FocusRecord]) -> tuple[dict | None, dict | None]:
        if not records:
            return None, None

        grouped: dict[str, dict[str, float]] = defaultdict(lambda: {"focus_sum": 0.0, "count": 0.0, "time": 0.0})
        for item in records:
            category_data = grouped[item.categoria]
            category_data["focus_sum"] += item.nivel_foco
            category_data["count"] += 1
            category_data["time"] += item.tempo_minutos

        category_stats: list[dict] = []
        for category, values in grouped.items():
            category_stats.append(
                {
                    "categoria": category,
                    "media_foco": round(values["focus_sum"] / values["count"], 2),
                    "tempo_total": int(values["time"]),
                }
            )

        top_category = max(category_stats, key=lambda item: (item["media_foco"], item["tempo_total"]))
        risk_category = min(category_stats, key=lambda item: (item["media_foco"], -item["tempo_total"]))
        return top_category, risk_category

    @staticmethod
    def _build_recommended_actions(
        consistency_score: float, has_focus_drop_alert: bool, risk_category: dict | None
    ) -> list[str]:
        actions: list[str] = []

        if consistency_score < 60:
            actions.append("Defina horário fixo diário para sessões de foco e reduza variações de rotina.")
        else:
            actions.append("Mantenha sua cadência atual de sessões e revise semanalmente seu padrão de foco.")

        if has_focus_drop_alert:
            actions.append("Faça pausas curtas a cada bloco e silencie notificações durante tarefas críticas.")

        if risk_category is not None:
            actions.append(
                f"Crie um plano de melhoria para a categoria '{risk_category['categoria']}' com blocos menores e objetivos claros."
            )

        return actions[:3]
