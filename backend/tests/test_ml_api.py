from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_ml_category_model_endpoint():
    r = client.get("/api/ml/category-model")
    assert r.status_code == 200
    data = r.json()
    assert "trained" in data


def test_ml_predict_category_accepts_post():
    r = client.post("/api/ml/predict-category", json={"description": "uber para o aeroporto"})
    assert r.status_code == 200
    data = r.json()
    assert "model_trained" in data
    assert "top_categories" in data
