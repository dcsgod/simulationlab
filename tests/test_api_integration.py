"""
FastAPI REST API integration test suite covering all platform endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "X-Response-Time-Ms" in response.headers
    assert "X-Request-ID" in response.headers


def test_connectors_api(client):
    response = client.get("/api/connectors")
    assert response.status_code == 200
    connectors = response.json()
    assert len(connectors) >= 1
    assert any(c["source_id"] == "mock_lakehouse" for c in connectors)

    # Test sample table
    sample_resp = client.get(
        "/api/connectors/mock_lakehouse/sample",
        params={
            "catalog": "retail_lakehouse",
            "schema": "gold_analytics",
            "table": "daily_store_sales",
            "limit": 5,
        }
    )
    assert sample_resp.status_code == 200
    assert sample_resp.json()["row_count"] == 5


def test_discovery_and_ontology_api(client):
    disc_resp = client.post(
        "/api/discovery/run",
        json={"source_id": "mock_lakehouse", "catalog": "retail_lakehouse", "schema_name": "gold_analytics"}
    )
    assert disc_resp.status_code == 200
    data = disc_resp.json()
    assert data["status"] == "success"
    assert data["nodes_discovered"] > 0

    onto_resp = client.get("/api/ontology")
    assert onto_resp.status_code == 200
    onto_data = onto_resp.json()
    assert "gross_margin_usd" in onto_data["nodes"]


def test_dag_api(client):
    # Ensure graph is loaded
    client.post(
        "/api/discovery/run",
        json={"source_id": "mock_lakehouse", "catalog": "retail_lakehouse", "schema_name": "gold_analytics"}
    )
    resp = client.get("/api/dag")
    assert resp.status_code == 200
    dag_data = resp.json()
    assert dag_data["is_acyclic"] is True

    impact_resp = client.get("/api/dag/impact/gross_margin_usd")
    assert impact_resp.status_code == 200
    impact_data = impact_resp.json()
    assert "units_sold" in impact_data["upstream_drivers"] or "net_sales_usd" in impact_data["upstream_drivers"]


def test_scenario_and_simulation_api(client):
    # Get templates
    tmpl_resp = client.get("/api/scenarios/templates")
    assert tmpl_resp.status_code == 200
    templates = tmpl_resp.json()
    assert len(templates) >= 2
    scen_id = templates[0]["id"]

    # Run deterministic simulation
    sim_resp = client.post(
        "/api/simulations/run",
        json={"scenario_id": scen_id, "mode": "deterministic"}
    )
    assert sim_resp.status_code == 200
    sim_data = sim_resp.json()
    assert sim_data["status"] == "success"
    assert "gross_margin_usd" in sim_data["metrics"]

    # Run Monte Carlo simulation
    mc_resp = client.post(
        "/api/simulations/run",
        json={"scenario_id": scen_id, "mode": "monte_carlo", "num_iterations": 200}
    )
    assert mc_resp.status_code == 200
    mc_data = mc_resp.json()
    assert "units_sold" in mc_data["distributions"]


def test_optimization_api(client):
    # Solve template retail allocation
    opt_resp = client.post(
        "/api/optimization/solve",
        json={"template_name": "retail_promo_allocation"}
    )
    assert opt_resp.status_code == 200
    opt_data = opt_resp.json()
    assert opt_data["is_optimal"] is True
    assert opt_data["objective_value"] > 0
    assert "promo_beverages" in opt_data["variable_values"]

    # Solve energy dispatch template
    opt_resp_energy = client.post(
        "/api/optimization/solve",
        json={"template_name": "energy_dispatch_least_cost"}
    )
    assert opt_resp_energy.status_code == 200
    assert opt_resp_energy.json()["is_optimal"] is True


def test_explainability_waterfall_api(client):
    tmpl_resp = client.get("/api/scenarios/templates")
    scen_id = tmpl_resp.json()[0]["id"]

    waterfall_resp = client.post(
        "/api/explainability/waterfall",
        json={"scenario_id": scen_id, "target_metric": "gross_margin_usd"}
    )
    assert waterfall_resp.status_code == 200
    contributions = waterfall_resp.json()
    assert len(contributions) > 0


def test_chat_copilot_api(client):
    chat_resp = client.post(
        "/api/chat",
        json={"message": "What happens to gross margin if promotional discount increases by 5%?"}
    )
    assert chat_resp.status_code == 200
    data = chat_resp.json()
    assert "envelope" in data
    assert "gross_margin_usd" in data["envelope"]["metric_deltas"]
    assert "gross_margin_usd" in data["reply"]
