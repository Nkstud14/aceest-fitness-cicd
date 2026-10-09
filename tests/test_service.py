"""Unit tests for the ACEest Fitness & Gym domain service layer."""
import pytest

from aceest_fitness.service import (
    DuplicateError,
    FitnessService,
    NotFoundError,
    ValidationError,
)


def test_list_programs_contains_core_programs(service):
    programs = service.list_programs()
    assert set(programs) == {"Fat Loss", "Muscle Gain", "Beginner"}
    assert programs["Fat Loss"]["code"] == "FL"


def test_get_program_unknown_raises(service):
    with pytest.raises(NotFoundError):
        service.get_program("Nonexistent")


def test_add_client_success(service):
    client = service.add_client("Alice", "Muscle Gain")
    assert client.name == "Alice"
    assert client.program == "Muscle Gain"
    assert client.membership_status == "Active"


def test_add_client_trims_whitespace(service):
    client = service.add_client("  Bob  ")
    assert client.name == "Bob"
    assert client.program is None


@pytest.mark.parametrize("bad_name", ["", "   ", None])
def test_add_client_empty_name_rejected(service, bad_name):
    with pytest.raises(ValidationError):
        service.add_client(bad_name)


def test_add_client_unknown_program_rejected(service):
    with pytest.raises(ValidationError):
        service.add_client("Carol", "Powerlifting")


def test_add_duplicate_client_rejected_case_insensitive(service):
    service.add_client("Dave")
    with pytest.raises(DuplicateError):
        service.add_client("dave")


def test_get_client_not_found(service):
    with pytest.raises(NotFoundError):
        service.get_client("Ghost")


def test_list_clients_sorted(service):
    service.add_client("Zoe")
    service.add_client("Amy")
    names = [c.name for c in service.list_clients()]
    assert names == ["Amy", "Zoe"]


def test_assign_program(service):
    service.add_client("Eve")
    client = service.assign_program("Eve", "Fat Loss")
    assert client.program == "Fat Loss"


def test_assign_unknown_program_rejected(service):
    service.add_client("Frank")
    with pytest.raises(ValidationError):
        service.assign_program("Frank", "CrossFit Open")


def test_add_workout_success(service):
    service.add_client("Grace")
    workout = service.add_workout("Grace", "Strength", 45, "2026-01-01", "Leg day")
    assert workout.workout_type == "Strength"
    assert workout.duration_min == 45
    assert workout.notes == "Leg day"
    assert service.list_workouts("Grace") == [workout]


def test_add_workout_defaults_date(service):
    service.add_client("Heidi")
    workout = service.add_workout("Heidi", "Cardio", 30)
    assert workout.date  # today's date is filled in automatically


def test_add_workout_invalid_type_rejected(service):
    service.add_client("Ivan")
    with pytest.raises(ValidationError):
        service.add_workout("Ivan", "Yoga", 30)


@pytest.mark.parametrize("bad_duration", [0, -10, "abc", None])
def test_add_workout_invalid_duration_rejected(service, bad_duration):
    service.add_client("Judy")
    with pytest.raises(ValidationError):
        service.add_workout("Judy", "Mobility", bad_duration)


def test_add_workout_unknown_client_rejected(service):
    with pytest.raises(NotFoundError):
        service.add_workout("Nobody", "Strength", 30)


def test_reset_clears_state(service):
    service.add_client("Ken")
    service.reset()
    assert service.list_clients() == []


def test_isolated_service_instances():
    a = FitnessService()
    b = FitnessService()
    a.add_client("Shared")
    assert a.list_clients()
    assert b.list_clients() == []
