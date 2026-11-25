"""Shared Pytest fixtures for the ACEest Fitness & Gym test suite."""
import pytest

from aceest_fitness import create_app
from aceest_fitness.service import FitnessService


@pytest.fixture()
def service():
    """A fresh, isolated service instance per test."""
    return FitnessService()


@pytest.fixture()
def app(service):
    flask_app = create_app(service=service)
    flask_app.config.update(TESTING=True)
    return flask_app


@pytest.fixture()
def client(app):
    return app.test_client()
