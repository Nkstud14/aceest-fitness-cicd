"""Core domain logic for ACEest Fitness & Gym.

This module encapsulates the fitness business logic (training programs,
client management and workout tracking) in a framework-agnostic, fully
testable service layer. The data is held in memory which keeps the service
stateless across process restarts and trivial to run inside a container or
a CI environment where no external database is available.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date
from threading import Lock
from typing import Dict, List, Optional


class FitnessError(Exception):
    """Base error for predictable, client-facing domain failures."""


class ValidationError(FitnessError):
    """Raised when user supplied data fails validation."""


class NotFoundError(FitnessError):
    """Raised when a requested resource does not exist."""


class DuplicateError(FitnessError):
    """Raised when creating a resource that already exists."""


# Training programs preserved from the original ACEest desktop application.
PROGRAMS: Dict[str, Dict[str, str]] = {
    "Fat Loss": {
        "code": "FL",
        "workout": (
            "Mon: 5x5 Back Squat + AMRAP; Tue: EMOM 20min Assault Bike; "
            "Wed: Bench Press + 21-15-9; Thu: 10RFT Deadlifts/Box Jumps; "
            "Fri: 30min Active Recovery"
        ),
        "diet": "Grilled protein, complex carbs and greens. Target: 2,000 kcal",
    },
    "Muscle Gain": {
        "code": "MG",
        "workout": (
            "Mon: Squat 5x5; Tue: Bench 5x5; Wed: Deadlift 4x6; "
            "Thu: Front Squat 4x8; Fri: Incline Press 4x10; Sat: Barbell Rows 4x10"
        ),
        "diet": "High protein surplus with lean meats and rice. Target: 3,200 kcal",
    },
    "Beginner": {
        "code": "BG",
        "workout": "Circuit Training: Air Squats, Ring Rows, Push-ups. Focus: form mastery",
        "diet": "Balanced meals, 120g protein/day",
    },
}

WORKOUT_TYPES = ("Strength", "Hypertrophy", "Cardio", "Mobility")


@dataclass
class Workout:
    """A single logged workout session."""

    date: str
    workout_type: str
    duration_min: int
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Client:
    """A gym client with an optional assigned program and workout history."""

    name: str
    program: Optional[str] = None
    membership_status: str = "Active"
    workouts: List[Workout] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "program": self.program,
            "membership_status": self.membership_status,
            "workouts": [w.to_dict() for w in self.workouts],
        }


class FitnessService:
    """Thread-safe, in-memory service for clients, programs and workouts."""

    def __init__(self) -> None:
        self._clients: Dict[str, Client] = {}
        self._lock = Lock()

    # ----- Programs -------------------------------------------------------
    @staticmethod
    def list_programs() -> Dict[str, Dict[str, str]]:
        return PROGRAMS

    @staticmethod
    def get_program(name: str) -> Dict[str, str]:
        program = PROGRAMS.get(name)
        if program is None:
            raise NotFoundError(f"Program '{name}' not found")
        return program

    # ----- Clients --------------------------------------------------------
    def add_client(self, name: str, program: Optional[str] = None) -> Client:
        clean_name = (name or "").strip()
        if not clean_name:
            raise ValidationError("Client name must not be empty")

        if program is not None:
            program = program.strip()
            if program and program not in PROGRAMS:
                raise ValidationError(f"Unknown program '{program}'")
            program = program or None

        key = clean_name.lower()
        with self._lock:
            if key in self._clients:
                raise DuplicateError(f"Client '{clean_name}' already exists")
            client = Client(name=clean_name, program=program)
            self._clients[key] = client
        return client

    def get_client(self, name: str) -> Client:
        client = self._clients.get((name or "").strip().lower())
        if client is None:
            raise NotFoundError(f"Client '{name}' not found")
        return client

    def list_clients(self) -> List[Client]:
        return sorted(self._clients.values(), key=lambda c: c.name.lower())

    def assign_program(self, name: str, program: str) -> Client:
        if program not in PROGRAMS:
            raise ValidationError(f"Unknown program '{program}'")
        client = self.get_client(name)
        with self._lock:
            client.program = program
        return client

    # ----- Workouts -------------------------------------------------------
    def add_workout(
        self,
        name: str,
        workout_type: str,
        duration_min: int,
        workout_date: Optional[str] = None,
        notes: str = "",
    ) -> Workout:
        client = self.get_client(name)

        if workout_type not in WORKOUT_TYPES:
            raise ValidationError(
                f"Invalid workout type '{workout_type}'. "
                f"Expected one of {', '.join(WORKOUT_TYPES)}"
            )

        try:
            duration = int(duration_min)
        except (TypeError, ValueError):
            raise ValidationError("Duration must be an integer number of minutes")
        if duration <= 0:
            raise ValidationError("Duration must be a positive number of minutes")

        workout_date = (workout_date or date.today().isoformat()).strip()
        workout = Workout(
            date=workout_date,
            workout_type=workout_type,
            duration_min=duration,
            notes=(notes or "").strip(),
        )
        with self._lock:
            client.workouts.append(workout)
        return workout

    def list_workouts(self, name: str) -> List[Workout]:
        return list(self.get_client(name).workouts)

    # ----- Maintenance ----------------------------------------------------
    def reset(self) -> None:
        """Clear all stored state. Primarily used by the test suite."""
        with self._lock:
            self._clients.clear()
