"""
Test suite for the Snake Game API.

Run with:
    pytest -v

Run with coverage (used in CI):
    pytest -v --cov=app --cov-report=term-missing
"""


class TestHealth:
    def test_health_returns_ok(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["redis"] == "up"

    def test_ready_returns_200_when_redis_up(self, client):
        resp = client.get("/api/ready")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ready"

    def test_root_lists_service_info(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["service"] == "snake-game-api"


class TestSubmitScore:
    def test_submit_valid_score(self, client):
        resp = client.post("/api/score", json={"player": "Ali", "score": 120})
        assert resp.status_code == 201
        body = resp.json()
        assert body == {"player": "Ali", "submitted_score": 120, "best_score": 120}

    def test_lower_score_does_not_overwrite_best(self, client):
        client.post("/api/score", json={"player": "Ali", "score": 120})
        resp = client.post("/api/score", json={"player": "Ali", "score": 50})
        assert resp.status_code == 201
        assert resp.json()["best_score"] == 120

    def test_higher_score_overwrites_previous_best(self, client):
        client.post("/api/score", json={"player": "Ali", "score": 120})
        resp = client.post("/api/score", json={"player": "Ali", "score": 300})
        assert resp.status_code == 201
        assert resp.json()["best_score"] == 300

    def test_player_name_is_trimmed(self, client):
        resp = client.post("/api/score", json={"player": "  Sara  ", "score": 10})
        assert resp.status_code == 201
        assert resp.json()["player"] == "Sara"

    def test_rejects_empty_player_name(self, client):
        resp = client.post("/api/score", json={"player": "", "score": 50})
        assert resp.status_code == 422

    def test_rejects_whitespace_only_player_name(self, client):
        resp = client.post("/api/score", json={"player": "   ", "score": 50})
        assert resp.status_code == 422

    def test_rejects_negative_score(self, client):
        resp = client.post("/api/score", json={"player": "Bob", "score": -5})
        assert resp.status_code == 422

    def test_rejects_score_above_max(self, client):
        resp = client.post("/api/score", json={"player": "Bob", "score": 10_000_000})
        assert resp.status_code == 422

    def test_rejects_player_name_too_long(self, client):
        resp = client.post("/api/score", json={"player": "x" * 21, "score": 10})
        assert resp.status_code == 422

    def test_rejects_missing_fields(self, client):
        resp = client.post("/api/score", json={"player": "Bob"})
        assert resp.status_code == 422


class TestLeaderboard:
    def test_empty_leaderboard(self, client):
        resp = client.get("/api/leaderboard")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_leaderboard_ordered_descending(self, client):
        client.post("/api/score", json={"player": "Ali", "score": 100})
        client.post("/api/score", json={"player": "Sara", "score": 300})
        client.post("/api/score", json={"player": "Omar", "score": 200})

        resp = client.get("/api/leaderboard")
        assert resp.status_code == 200
        board = resp.json()

        assert [e["player"] for e in board] == ["Sara", "Omar", "Ali"]
        assert [e["rank"] for e in board] == [1, 2, 3]
        assert [e["score"] for e in board] == [300, 200, 100]

    def test_leaderboard_respects_limit(self, client):
        for i in range(5):
            client.post("/api/score", json={"player": f"player{i}", "score": i * 10})

        resp = client.get("/api/leaderboard?limit=2")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_leaderboard_limit_cannot_exceed_max(self, client):
        client.post("/api/score", json={"player": "Ali", "score": 100})
        resp = client.get("/api/leaderboard?limit=99999")
        assert resp.status_code == 200
        # should be capped internally, not error out
        assert isinstance(resp.json(), list)

    def test_leaderboard_deduplicates_by_player(self, client):
        client.post("/api/score", json={"player": "Ali", "score": 50})
        client.post("/api/score", json={"player": "Ali", "score": 150})
        client.post("/api/score", json={"player": "Ali", "score": 90})

        resp = client.get("/api/leaderboard")
        board = resp.json()
        assert len(board) == 1
        assert board[0]["score"] == 150
