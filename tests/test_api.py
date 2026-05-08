from datetime import date, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from app.database import get_connection
from app.main import create_app

USER_A_HEADERS = {"X-User-Id": "user-a"}
USER_B_HEADERS = {"X-User-Id": "user-b"}


def build_client(tmp_path: Path) -> TestClient:
    db_file = tmp_path / "test_foco.db"
    app = create_app(db_file)
    return TestClient(app)


def set_record_created_at(db_path: Path, record_id: int, created_at: datetime) -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            "UPDATE registros_foco SET criado_em = ? WHERE id = ?",
            (created_at.strftime("%Y-%m-%d %H:%M:%S"), record_id),
        )


def create_record(
    client: TestClient,
    headers: dict[str, str],
    nivel_foco: int,
    tempo_minutos: int,
    comentario: str,
    categoria: str,
) -> int:
    response = client.post(
        "/registro-foco",
        headers=headers,
        json={
            "nivel_foco": nivel_foco,
            "tempo_minutos": tempo_minutos,
            "comentario": comentario,
            "categoria": categoria,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_create_valid_record(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.post(
        "/registro-foco",
        headers=USER_A_HEADERS,
        json={
            "nivel_foco": 5,
            "tempo_minutos": 50,
            "comentario": "Implementação de endpoint",
            "categoria": "coding",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["user_id"] == "user-a"
    assert body["nivel_foco"] == 5
    assert body["tempo_minutos"] == 50
    assert body["categoria"] == "coding"
    assert "criado_em" in body


def test_rejects_missing_user_header(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.post(
        "/registro-foco",
        json={"nivel_foco": 3, "tempo_minutos": 20, "comentario": "Teste", "categoria": "geral"},
    )

    assert response.status_code == 422


def test_rejects_focus_level_out_of_range(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.post(
        "/registro-foco",
        headers=USER_A_HEADERS,
        json={"nivel_foco": 6, "tempo_minutos": 25, "comentario": "Teste", "categoria": "estudo"},
    )

    assert response.status_code == 422


def test_rejects_invalid_minutes(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.post(
        "/registro-foco",
        headers=USER_A_HEADERS,
        json={"nivel_foco": 3, "tempo_minutos": 0, "comentario": "Teste", "categoria": "estudo"},
    )

    assert response.status_code == 422


def test_rejects_empty_comment(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.post(
        "/registro-foco",
        headers=USER_A_HEADERS,
        json={"nivel_foco": 3, "tempo_minutos": 10, "comentario": "   ", "categoria": "estudo"},
    )

    assert response.status_code == 422


def test_empty_base_diagnosis(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.get("/diagnostico-produtividade", headers=USER_A_HEADERS)
    assert response.status_code == 200

    body = response.json()
    assert body["media_nivel_foco"] == 0.0
    assert body["tempo_total_focado"] == 0
    assert body["insights_por_categoria"] == []


def test_diagnosis_calculations_ranges_and_categories(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    create_record(client, USER_A_HEADERS, 2, 30, "Muitas interrupções", "reuniao")
    create_record(client, USER_A_HEADERS, 4, 45, "Tarefa estável", "coding")
    create_record(client, USER_A_HEADERS, 5, 60, "Fluxo alto", "coding")

    response = client.get("/diagnostico-produtividade", headers=USER_A_HEADERS)
    assert response.status_code == 200

    body = response.json()
    assert body["media_nivel_foco"] == 3.67
    assert body["tempo_total_focado"] == 135
    assert body["mensagem_feedback"] == "Produtividade estável. Pequenos ajustes de ambiente podem elevar seu foco."

    insights = {item["categoria"]: item for item in body["insights_por_categoria"]}
    assert insights["coding"]["media_foco"] == 4.5
    assert insights["coding"]["tempo_total"] == 105
    assert insights["reuniao"]["media_foco"] == 2.0
    assert insights["reuniao"]["tempo_total"] == 30


def test_diagnosis_isolated_by_user(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    create_record(client, USER_A_HEADERS, 5, 60, "A", "coding")
    create_record(client, USER_B_HEADERS, 1, 10, "B", "geral")

    response_a = client.get("/diagnostico-produtividade", headers=USER_A_HEADERS)
    response_b = client.get("/diagnostico-produtividade", headers=USER_B_HEADERS)

    assert response_a.status_code == 200
    assert response_b.status_code == 200
    assert response_a.json()["tempo_total_focado"] == 60
    assert response_b.json()["tempo_total_focado"] == 10


def test_real_sqlite_persistence(tmp_path: Path) -> None:
    db_file = tmp_path / "persistencia.db"
    app_a = create_app(db_file)
    client_a = TestClient(app_a)
    app_b = create_app(db_file)
    client_b = TestClient(app_b)

    create_response = client_a.post(
        "/registro-foco",
        headers=USER_A_HEADERS,
        json={"nivel_foco": 4, "tempo_minutos": 20, "comentario": "Sessão A", "categoria": "geral"},
    )
    assert create_response.status_code == 201

    diagnosis_response = client_b.get("/diagnostico-produtividade", headers=USER_A_HEADERS)
    assert diagnosis_response.status_code == 200
    assert diagnosis_response.json()["tempo_total_focado"] == 20


def test_dashboard_defaults_to_today(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.get("/dashboard-produtividade", headers=USER_A_HEADERS)
    assert response.status_code == 200

    body = response.json()
    assert body["periodo"]["timezone"] == "America/Sao_Paulo"
    assert body["periodo"]["from"] == body["periodo"]["to"]
    assert body["resumo"]["sessoes_total"] == 0
    assert body["score_consistencia"] == 0.0
    assert body["streak_dias"] == 0
    assert body["faixas_de_ouro"] == []
    assert body["comparativo_periodo_anterior"]["media_nivel_foco_delta"] == 0.0
    assert body["comparativo_periodo_anterior"]["tempo_total_focado_delta"] == 0
    assert body["comparativo_periodo_anterior"]["sessoes_total_delta"] == 0


def test_dashboard_rejects_invalid_date(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.get("/dashboard-produtividade?from=2026-13-40", headers=USER_A_HEADERS)
    assert response.status_code == 422


def test_dashboard_rejects_invalid_range_order(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.get("/dashboard-produtividade?from=2026-05-10&to=2026-05-01", headers=USER_A_HEADERS)
    assert response.status_code == 422
    body = response.json()
    assert "detail" in body


def test_dashboard_rejects_invalid_partial_range_order(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.get("/dashboard-produtividade?from=2099-01-01", headers=USER_A_HEADERS)
    assert response.status_code == 422


def test_dashboard_detects_focus_drop_and_category_extremes(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    db_file = tmp_path / "test_foco.db"

    base_date = date(2026, 5, 1)
    record_ids = [
        create_record(client, USER_A_HEADERS, 5, 30, "Deep work A", "coding"),
        create_record(client, USER_A_HEADERS, 5, 30, "Deep work B", "coding"),
        create_record(client, USER_A_HEADERS, 2, 30, "Distração A", "reuniao"),
        create_record(client, USER_A_HEADERS, 1, 30, "Distração B", "reuniao"),
    ]

    for idx, record_id in enumerate(record_ids):
        custom_datetime = datetime.combine(base_date + timedelta(days=idx), datetime.min.time()).replace(hour=10)
        set_record_created_at(db_file, record_id, custom_datetime)

    response = client.get("/dashboard-produtividade?from=2026-05-01&to=2026-05-07", headers=USER_A_HEADERS)
    assert response.status_code == 200

    body = response.json()
    assert 0.0 <= body["score_consistencia"] <= 100.0
    assert body["alerta_queda_foco"]["status"] is True
    assert body["alerta_queda_foco"]["variacao_percentual"] <= -15.0
    assert body["top_categoria"]["categoria"] == "coding"
    assert body["categoria_em_risco"]["categoria"] == "reuniao"
    assert body["streak_dias"] == 4
    assert len(body["faixas_de_ouro"]) >= 1
    assert "comparativo_periodo_anterior" in body
    assert 2 <= len(body["acoes_recomendadas"]) <= 3


def test_dashboard_without_relevant_drop_returns_no_alert(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    db_file = tmp_path / "test_foco.db"

    base_date = date(2026, 6, 1)
    record_ids = [
        create_record(client, USER_A_HEADERS, 3, 20, "Sessão 1", "geral"),
        create_record(client, USER_A_HEADERS, 3, 20, "Sessão 2", "geral"),
        create_record(client, USER_A_HEADERS, 3, 20, "Sessão 3", "geral"),
        create_record(client, USER_A_HEADERS, 3, 20, "Sessão 4", "geral"),
    ]

    for idx, record_id in enumerate(record_ids):
        custom_datetime = datetime.combine(base_date + timedelta(days=idx), datetime.min.time()).replace(hour=10)
        set_record_created_at(db_file, record_id, custom_datetime)

    response = client.get("/dashboard-produtividade?from=2026-06-01&to=2026-06-07", headers=USER_A_HEADERS)
    assert response.status_code == 200

    body = response.json()
    assert body["alerta_queda_foco"]["status"] is False
    assert body["alerta_queda_foco"]["variacao_percentual"] == 0.0


def test_dashboard_uses_timezone_from_environment(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DASHBOARD_TIMEZONE", "UTC")
    client = build_client(tmp_path)

    response = client.get("/dashboard-produtividade", headers=USER_A_HEADERS)
    assert response.status_code == 200
    assert response.json()["periodo"]["timezone"] == "UTC"


def test_dashboard_isolated_by_user(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    create_record(client, USER_A_HEADERS, 5, 60, "A", "coding")
    create_record(client, USER_B_HEADERS, 1, 10, "B", "geral")

    response_a = client.get("/dashboard-produtividade", headers=USER_A_HEADERS)
    response_b = client.get("/dashboard-produtividade", headers=USER_B_HEADERS)

    assert response_a.status_code == 200
    assert response_b.status_code == 200
    assert response_a.json()["resumo"]["tempo_total_focado"] == 60
    assert response_b.json()["resumo"]["tempo_total_focado"] == 10
