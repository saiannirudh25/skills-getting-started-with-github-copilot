"""
Shared pytest fixtures for FastAPI backend tests.

This module provides common test fixtures including:
- test_client: FastAPI TestClient for making API requests
- reset_activities: Fixture to restore activities data to known state
- sample_data: Predictable test data for assertions
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


# Store original activities data for reset
ORIGINAL_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Competitive basketball practice and games",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 15,
        "participants": ["james@mergington.edu"]
    },
    "Tennis Club": {
        "description": "Tennis lessons and friendly matches",
        "schedule": "Saturdays, 10:00 AM - 12:00 PM",
        "max_participants": 16,
        "participants": ["isabella@mergington.edu"]
    },
    "Art Studio": {
        "description": "Painting, drawing, and visual arts exploration",
        "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
        "max_participants": 18,
        "participants": ["grace@mergington.edu", "lucas@mergington.edu"]
    },
    "Music Band": {
        "description": "Learn instruments and perform in the school band",
        "schedule": "Mondays and Thursdays, 4:00 PM - 5:00 PM",
        "max_participants": 25,
        "participants": ["noah@mergington.edu"]
    },
    "Debate Club": {
        "description": "Develop critical thinking and public speaking skills",
        "schedule": "Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 14,
        "participants": ["sophia@mergington.edu", "liam@mergington.edu"]
    },
    "Science Club": {
        "description": "Explore STEM through experiments and projects",
        "schedule": "Fridays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["ava@mergington.edu"]
    }
}


@pytest.fixture
def test_client():
    """
    Provides a FastAPI TestClient instance for making API requests.
    
    Returns:
        TestClient: Configured test client for the FastAPI app
    """
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """
    Automatically resets the activities dictionary to its original state
    before each test to ensure test isolation and prevent side effects.
    
    This fixture runs automatically before every test due to autouse=True.
    """
    # Deep copy to restore original state
    activities.clear()
    for name, details in ORIGINAL_ACTIVITIES.items():
        activities[name] = {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": details["participants"].copy()  # Copy list to avoid mutation
        }
    yield
    # Cleanup after test if needed
    activities.clear()
    for name, details in ORIGINAL_ACTIVITIES.items():
        activities[name] = {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": details["participants"].copy()
        }


@pytest.fixture
def sample_data():
    """
    Provides sample test data for predictable assertions.
    
    Returns:
        dict: Test data including activity names and student emails
    """
    return {
        "existing_activity": "Chess Club",
        "nonexistent_activity": "Underwater Basket Weaving",
        "new_student": "test.student@mergington.edu",
        "existing_student": "michael@mergington.edu",
        "activity_with_one": "Basketball Team",
        "activity_with_many": "Programming Class"
    }
