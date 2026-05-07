from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def build_client(tmp_path: Path) -> TestClient:
    db_file = tmp_path / "test_foco.db"
    app = create_app(db_file)
    return TestClient(app)


def test_create_valid_record(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.post(
        "/registro-foco",
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
    assert body["nivel_foco"] == 5
    assert body["tempo_minutos"] == 50
    assert body["categoria"] == "coding"
    assert "criado_em" in body


def test_rejects_focus_level_out_of_range(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.post(
        "/registro-foco",
        json={"nivel_foco": 6, "tempo_minutos": 25, "comentario": "Teste", "categoria": "estudo"},
    )

    assert response.status_code == 422


def test_rejects_invalid_minutes(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.post(
        "/registro-foco",
        json={"nivel_foco": 3, "tempo_minutos": 0, "comentario": "Teste", "categoria": "estudo"},
    )

    assert response.status_code == 422


def test_rejects_empty_comment(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.post(
        "/registro-foco",
        json={"nivel_foco": 3, "tempo_minutos": 10, "comentario": "   ", "categoria": "estudo"},
    )

    assert response.status_code == 422


def test_empty_base_diagnosis(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.get("/diagnostico-produtividade")
    assert response.status_code == 200

    body = response.json()
    assert body["media_nivel_foco"] == 0.0
    assert body["tempo_total_focado"] == 0
    assert body["insights_por_categoria"] == []


def test_diagnosis_calculations_ranges_and_categories(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    client.post(
        "/registro-foco",
        json={"nivel_foco": 2, "tempo_minutos": 30, "comentario": "Muitas interrupções", "categoria": "reuniao"},
    )
    client.post(
        "/registro-foco",
        json={"nivel_foco": 4, "tempo_minutos": 45, "comentario": "Tarefa estável", "categoria": "coding"},
    )
    client.post(
        "/registro-foco",
        json={"nivel_foco": 5, "tempo_minutos": 60, "comentario": "Fluxo alto", "categoria": "coding"},
    )

    response = client.get("/diagnostico-produtividade")
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


def test_real_sqlite_persistence(tmp_path: Path) -> None:
    db_file = tmp_path / "persistencia.db"
    app_a = create_app(db_file)
    client_a = TestClient(app_a)
    app_b = create_app(db_file)
    client_b = TestClient(app_b)

    create_response = client_a.post(
        "/registro-foco",
        json={"nivel_foco": 4, "tempo_minutos": 20, "comentario": "Sessão A", "categoria": "geral"},
    )
    assert create_response.status_code == 201

    diagnosis_response = client_b.get("/diagnostico-produtividade")
    assert diagnosis_response.status_code == 200
    assert diagnosis_response.json()["tempo_total_focado"] == 20
