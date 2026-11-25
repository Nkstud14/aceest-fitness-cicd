"""Integration tests for the ACEest Fitness & Gym Flask HTTP endpoints."""


def test_index_page_renders(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"ACEest Fitness" in resp.data


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_list_programs_endpoint(client):
    resp = client.get("/api/programs")
    assert resp.status_code == 200
    assert "Fat Loss" in resp.get_json()


def test_get_single_program(client):
    resp = client.get("/api/programs/Muscle Gain")
    assert resp.status_code == 200
    assert resp.get_json()["code"] == "MG"


def test_get_unknown_program_returns_404(client):
    resp = client.get("/api/programs/Unknown")
    assert resp.status_code == 404
    assert "error" in resp.get_json()


def test_add_and_get_client(client):
    resp = client.post("/api/clients", json={"name": "Alice", "program": "Fat Loss"})
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["name"] == "Alice"
    assert body["program"] == "Fat Loss"

    resp = client.get("/api/clients/Alice")
    assert resp.status_code == 200
    assert resp.get_json()["name"] == "Alice"


def test_add_client_missing_name_returns_400(client):
    resp = client.post("/api/clients", json={"name": ""})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_add_duplicate_client_returns_409(client):
    client.post("/api/clients", json={"name": "Bob"})
    resp = client.post("/api/clients", json={"name": "Bob"})
    assert resp.status_code == 409


def test_list_clients_endpoint(client):
    client.post("/api/clients", json={"name": "Carol"})
    resp = client.get("/api/clients")
    assert resp.status_code == 200
    names = [c["name"] for c in resp.get_json()]
    assert "Carol" in names


def test_assign_program_endpoint(client):
    client.post("/api/clients", json={"name": "Dave"})
    resp = client.post("/api/clients/Dave/program", json={"program": "Beginner"})
    assert resp.status_code == 200
    assert resp.get_json()["program"] == "Beginner"


def test_add_and_list_workouts(client):
    client.post("/api/clients", json={"name": "Eve"})
    resp = client.post(
        "/api/clients/Eve/workouts",
        json={"workout_type": "Strength", "duration_min": 60, "notes": "Squats"},
    )
    assert resp.status_code == 201

    resp = client.get("/api/clients/Eve/workouts")
    assert resp.status_code == 200
    workouts = resp.get_json()
    assert len(workouts) == 1
    assert workouts[0]["workout_type"] == "Strength"


def test_add_workout_invalid_type_returns_400(client):
    client.post("/api/clients", json={"name": "Frank"})
    resp = client.post(
        "/api/clients/Frank/workouts",
        json={"workout_type": "Zumba", "duration_min": 30},
    )
    assert resp.status_code == 400


def test_add_workout_unknown_client_returns_404(client):
    resp = client.post(
        "/api/clients/Ghost/workouts",
        json={"workout_type": "Cardio", "duration_min": 20},
    )
    assert resp.status_code == 404


def test_add_client_via_form_data(client):
    resp = client.post("/api/clients", data={"name": "Grace"})
    assert resp.status_code == 201
    assert resp.get_json()["name"] == "Grace"
