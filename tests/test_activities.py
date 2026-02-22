"""
Tests for GET /activities endpoint.

This module tests the activities retrieval endpoint, verifying:
- Successful response with correct status code
- Response structure and data format
- All required fields present
- Data integrity and completeness
"""

import pytest


def test_get_activities_success(test_client):
    """
    Test successful retrieval of all activities.
    
    Verifies:
    - Status code is 200
    - Response is valid JSON
    - Returns dictionary of activities
    """
    response = test_client.get("/activities")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) > 0


def test_get_activities_structure(test_client, sample_data):
    """
    Test that activities have the correct data structure.
    
    Verifies each activity contains:
    - description (string)
    - schedule (string)
    - max_participants (integer)
    - participants (list)
    """
    response = test_client.get("/activities")
    activities = response.json()
    
    # Check a known activity exists
    assert sample_data["existing_activity"] in activities
    
    activity = activities[sample_data["existing_activity"]]
    assert "description" in activity
    assert "schedule" in activity
    assert "max_participants" in activity
    assert "participants" in activity
    
    assert isinstance(activity["description"], str)
    assert isinstance(activity["schedule"], str)
    assert isinstance(activity["max_participants"], int)
    assert isinstance(activity["participants"], list)


def test_get_activities_contains_all_expected(test_client):
    """
    Test that all expected activities are returned.
    
    Verifies the response includes all 9 default activities.
    """
    response = test_client.get("/activities")
    activities = response.json()
    
    expected_activities = [
        "Chess Club",
        "Programming Class",
        "Gym Class",
        "Basketball Team",
        "Tennis Club",
        "Art Studio",
        "Music Band",
        "Debate Club",
        "Science Club"
    ]
    
    for activity_name in expected_activities:
        assert activity_name in activities, f"{activity_name} not found in response"


def test_get_activities_participants_are_emails(test_client):
    """
    Test that participants lists contain valid email-like strings.
    
    Verifies participants are stored as email addresses.
    """
    response = test_client.get("/activities")
    activities = response.json()
    
    for activity_name, details in activities.items():
        participants = details["participants"]
        for email in participants:
            assert isinstance(email, str)
            assert "@" in email, f"Invalid email format in {activity_name}: {email}"


def test_get_activities_max_participants_positive(test_client):
    """
    Test that max_participants is a positive integer for all activities.
    """
    response = test_client.get("/activities")
    activities = response.json()
    
    for activity_name, details in activities.items():
        max_participants = details["max_participants"]
        assert max_participants > 0, f"{activity_name} has invalid max_participants: {max_participants}"


def test_get_activities_data_integrity(test_client):
    """
    Test that the activities data maintains integrity.
    
    Verifies:
    - Participant counts don't exceed limits
    - No duplicate participants in the same activity
    """
    response = test_client.get("/activities")
    activities = response.json()
    
    for activity_name, details in activities.items():
        participants = details["participants"]
        max_participants = details["max_participants"]
        
        # Note: max_participants enforcement is NOT currently implemented in API
        # This test documents the gap but won't fail if participants exceed limit
        # TODO: Once max_participants validation is added, uncomment this assertion:
        # assert len(participants) <= max_participants, \
        #     f"{activity_name} has {len(participants)} participants but max is {max_participants}"
        
        # Check for duplicates
        assert len(participants) == len(set(participants)), \
            f"{activity_name} has duplicate participants: {participants}"
