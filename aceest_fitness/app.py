"""Flask application factory and HTTP routes for ACEest Fitness & Gym."""
from __future__ import annotations

from flask import Flask, jsonify, render_template, request

from aceest_fitness.service import (
    DuplicateError,
    FitnessError,
    FitnessService,
    NotFoundError,
    ValidationError,
)


def create_app(service: FitnessService | None = None) -> Flask:
    """Create and configure the Flask application.

    Accepting an optional service lets tests inject an isolated instance.
    """
    app = Flask(__name__)
    app.config["SERVICE"] = service or FitnessService()

    def svc() -> FitnessService:
        return app.config["SERVICE"]

    # ----- Error handling -------------------------------------------------
    @app.errorhandler(ValidationError)
    def _handle_validation(err: ValidationError):
        return jsonify(error=str(err)), 400

    @app.errorhandler(DuplicateError)
    def _handle_duplicate(err: DuplicateError):
        return jsonify(error=str(err)), 409

    @app.errorhandler(NotFoundError)
    def _handle_not_found(err: NotFoundError):
        return jsonify(error=str(err)), 404

    @app.errorhandler(FitnessError)
    def _handle_generic(err: FitnessError):
        return jsonify(error=str(err)), 400

    # ----- Views ----------------------------------------------------------
    @app.get("/")
    def index():
        return render_template(
            "index.html",
            programs=svc().list_programs(),
            clients=svc().list_clients(),
        )

    @app.get("/health")
    def health():
        return jsonify(status="ok", service="ACEest Fitness & Gym")

    # ----- Programs API ---------------------------------------------------
    @app.get("/api/programs")
    def api_programs():
        return jsonify(svc().list_programs())

    @app.get("/api/programs/<name>")
    def api_program(name: str):
        return jsonify(svc().get_program(name))

    # ----- Clients API ----------------------------------------------------
    @app.get("/api/clients")
    def api_list_clients():
        return jsonify([c.to_dict() for c in svc().list_clients()])

    @app.post("/api/clients")
    def api_add_client():
        data = request.get_json(silent=True) or request.form
        client = svc().add_client(
            name=data.get("name", ""),
            program=data.get("program"),
        )
        return jsonify(client.to_dict()), 201

    @app.get("/api/clients/<name>")
    def api_get_client(name: str):
        return jsonify(svc().get_client(name).to_dict())

    @app.post("/api/clients/<name>/program")
    def api_assign_program(name: str):
        data = request.get_json(silent=True) or request.form
        client = svc().assign_program(name, data.get("program", ""))
        return jsonify(client.to_dict())

    # ----- Workouts API ---------------------------------------------------
    @app.get("/api/clients/<name>/workouts")
    def api_list_workouts(name: str):
        return jsonify([w.to_dict() for w in svc().list_workouts(name)])

    @app.post("/api/clients/<name>/workouts")
    def api_add_workout(name: str):
        data = request.get_json(silent=True) or request.form
        workout = svc().add_workout(
            name=name,
            workout_type=data.get("workout_type", ""),
            duration_min=data.get("duration_min", 0),
            workout_date=data.get("date"),
            notes=data.get("notes", ""),
        )
        return jsonify(workout.to_dict()), 201

    return app
