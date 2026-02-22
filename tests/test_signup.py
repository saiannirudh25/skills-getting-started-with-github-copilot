"""
Tests for POST /activities/{activity_name}/signup endpoint.

This module tests the student signup functionality, including:
- Successful signup scenarios
- Error cases (invalid activity, duplicate signup)
- Edge cases (special characters, URL encoding)
- Data integrity after signup
"""

import pytest
from src.app import activities


def test_signup_success(test_client, sample_data):
    """
    Test successful student signup for an activity.
    
    Verifies:
    - Status code is 200
    - Success message returned
    - Student added to participants list
    """
    activity_name = sample_data["existing_activity"]
    email = sample_data["new_student"]
    
    # Get initial participant count
    initial_count = len(activities[activity_name]["participants"])
    
    response = test_client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email in data["message"]
    assert activity_name in data["message"]
    
    # Verify student was added
    assert email in activities[activity_name]["participants"]
    assert len(activities[activity_name]["participants"]) == initial_count + 1


def test_signup_activity_not_found(test_client, sample_data):
    """
    Test signup fails when activity doesn't exist.
    
    Verifies:
    - Status code is 404
    - Appropriate error message returned
    """
    response = test_client.post(
        f"/activities/{sample_data['nonexistent_activity']}/signup",
        params={"email": sample_data["new_student"]}
    )
    
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


def test_signup_duplicate_prevention(test_client, sample_data):
    """
    Test that duplicate signups are prevented.
    
    Verifies:
    - First signup succeeds
    - Second signup with same email returns 400
    - Participant not added twice
    """
    activity_name = sample_data["existing_activity"]
    email = sample_data["new_student"]
    
    # First signup - should succeed
    response1 = test_client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    assert response1.status_code == 200
    
    # Get participant count after first signup
    count_after_first = len(activities[activity_name]["participants"])
    
    # Second signup - should fail
    response2 = test_client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    assert response2.status_code == 400
    data = response2.json()
    assert "detail" in data
    assert "already signed up" in data["detail"].lower()
    
    # Verify participant count didn't change
    assert len(activities[activity_name]["participants"]) == count_after_first


def test_signup_existing_student_duplicate(test_client, sample_data):
    """
    Test that existing students can't sign up again.
    
    Verifies duplicate prevention for pre-existing participants.
    """
    activity_name = sample_data["existing_activity"]
    email = sample_data["existing_student"]
    
    # Get initial count
    initial_count = len(activities[activity_name]["participants"])
    
    # Try to signup existing student
    response = test_client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "already signed up" in data["detail"].lower()
    
    # Verify count didn't change
    assert len(activities[activity_name]["participants"]) == initial_count


def test_signup_with_special_characters(test_client):
    """
    Test signup with activity names containing special characters.
    
    Verifies URL encoding and special character handling.
    """
    # Art Studio has a space in the name
    activity_name = "Art Studio"
    email = "special.test@mergington.edu"
    
    response = test_client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    
    assert response.status_code == 200
    assert email in activities[activity_name]["participants"]


def test_signup_email_format_variations(test_client, sample_data):
    """
    Test signup accepts various valid email formats.
    
    Note: API currently does not validate email format.
    This test documents existing behavior.
    """
    activity_name = sample_data["existing_activity"]
    
    # Various email formats
    emails = [
        "simple@mergington.edu",
        "first.last@mergington.edu",
        "first+tag@mergington.edu",
        "first_last@mergington.edu"
    ]
    
    for email in emails:
        response = test_client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        assert email in activities[activity_name]["participants"]


def test_signup_data_integrity(test_client, sample_data):
    """
    Test that signup doesn't affect other activities.
    
    Verifies:
    - Only the specified activity is modified
    - Other activities remain unchanged
    """
    activity_name = sample_data["existing_activity"]
    other_activity = sample_data["activity_with_one"]
    email = sample_data["new_student"]
    
    # Store state of other activity
    other_participants_before = activities[other_activity]["participants"].copy()
    
    # Signup for one activity
    response = test_client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    assert response.status_code == 200
    
    # Verify other activity unchanged
    assert activities[other_activity]["participants"] == other_participants_before
    assert email not in activities[other_activity]["participants"]


def test_signup_multiple_activities(test_client, sample_data):
    """
    Test that a student can sign up for multiple different activities.
    
    Verifies:
    - Same student can be in multiple activities
    - Each signup is independent
    """
    email = sample_data["new_student"]
    activity1 = sample_data["existing_activity"]
    activity2 = sample_data["activity_with_one"]
    
    # Signup for first activity
    response1 = test_client.post(
        f"/activities/{activity1}/signup",
        params={"email": email}
    )
    assert response1.status_code == 200
    
    # Signup for second activity
    response2 = test_client.post(
        f"/activities/{activity2}/signup",
        params={"email": email}
    )
    assert response2.status_code == 200
    
    # Verify student is in both
    assert email in activities[activity1]["participants"]
    assert email in activities[activity2]["participants"]


def test_signup_max_participants_not_enforced(test_client):
    """
    Test documenting that max_participants limit is NOT enforced.
    
    Note: This is a known gap in the current implementation.
    The API allows signups even when max_participants is reached.
    
    TODO: Update this test when max_participants validation is implemented.
    """
    # Find an activity and fill it to max
    activity_name = "Basketball Team"
    max_participants = activities[activity_name]["max_participants"]
    
    # Sign up students until we exceed max
    for i in range(max_participants + 5):
        email = f"student{i}@mergington.edu"
        response = test_client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Currently, API allows exceeding max_participants
        # When validation is added, this should fail after reaching max
        if i < max_participants:
            assert response.status_code == 200
        # else:
        #     # Uncomment when max_participants validation is implemented
        #     assert response.status_code == 400
