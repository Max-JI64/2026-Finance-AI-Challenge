from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_scope_endpoint_keeps_prediction_boundary() -> None:
    response = client.get("/scope")
    payload = response.json()

    assert response.status_code == 200
    assert payload["geography"] == "Seoul"
    assert payload["predicts"] == "다음 분기 상권·업종 매출환경 악화 위험"
    assert "개별 점포 폐업확률" in payload["does_not_predict"]
    assert payload["separates"] == ["상권환경 위험", "사업체 금융부담"]

