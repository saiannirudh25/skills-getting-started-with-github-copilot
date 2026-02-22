"""
Tests for DELETE /activities/{activity_name}/unregister endpoint.

This module tests the student unregister functionality, including:
- Successful unregistration scenarios
- Error cases (invalid activity, student not registered)
- Edge cases (last participant, special characters)
- Data integrity after unregistration
"""

import pytest
from src.app import activities


def test_unregister_success(test_client, sample_data):
    """
    Test successful student unregistration from an activity.
    
    Verifies:
    - Status code is 200
    - Success message returned
    - Student removed from participants list
    """
    activity_name = sample_data["existing_activity"]
    email = sample_data["existing_student"]
    
    # Verify student is initially registered
    assert email in activities[activity_name]["participants"]
    initial_count = len(activities[activity_name]["participants"])
    
    response = test_client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email in data["message"]
    assert activity_name in data["message"]
    
    # Verify student was removed
    assert email not in activities[activity_name]["participants"]
    assert len(activities[activity_name]["participants"]) == initial_count - 1


def test_unregister_activity_not_found(test_client, sample_data):
    """
    Test unregister fails when activity doesn't exist.
    
    Verifies:
    - Status code is 404
    - Appropriate error message returned
    """
    response = test_client.delete(
        f"/activities/{sample_data['nonexistent_activity']}/unregister",
        params={"email": sample_data["existing_student"]}
    )
    
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


def test_unregister_student_not_registered(test_client, sample_data):
    """
    Test unregister fails when student is not registered for the activity.
    
    Verifies:
    - Status code is 400
    - Appropriate error message returned
    """
    activity_name = sample_data["existing_activity"]
    email = sample_data["new_student"]
    
    # Verify student is not registered
    assert email not in activities[activity_name]["participants"]
    
    response = test_client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "not registered" in data["detail"].lower()


def test_unregister_last_participant(test_client, sample_data):
    """
    Test unregister works when removing the last participant.
    
    Verifies:
    - Can remove the last participant
    - Activity remains with empty participants list
    """
    activity_name = sample_data["activity_with_one"]
    
    # Get the single participant
    participants = activities[activity_name]["participants"]
    assert len(participants) == 1
    email = participants[0]
    
    response = test_client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    
    assert response.status_code == 200
    assert len(activities[activity_name]["participants"]) == 0


def test_unregister_with_special_characters(test_client):
    """
    Test unregister with activity names containing special characters.
    
    Verifies URL encoding and special character handling.
    """
    # Art Studio has a space in the name
    activity_name = "Art Studio"
    
    # Get an existing participant
    participants = activities[activity_name]["participants"]
    assert len(participants) > 0
    email = participants[0]
    
    response = test_client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    
    assert response.status_code == 200
    assert email not in activities[activity_name]["participants"]


def test_unregister_data_integrity(test_client, sample_data):
    """
    Test that unregister only removes the specified student.
    
    Verifies:
    - Only the specified student is removed
    - Other participants remain unchanged
    """
    activity_name = sample_data["activity_with_many"]
    
    # Get participants
    participants_before = activities[activity_name]["participants"].copy()
    assert len(participants_before) >= 2
    
    email_to_remove = participants_before[0]
    email_to_keep = participants_before[1]
    
    response = test_client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email_to_remove}
    )
    
    assert response.status_code == 200
    
    # Verify only specified student removed
    assert email_to_remove not in activities[activity_name]["participants"]
    assert email_to_keep in activities[activity_name]["participants"]
    assert len(activities[activity_name]["participants"]) == len(participants_before) - 1


def test_unregister_doesnt_affect_other_activities(test_client, sample_data):
    """
    Test that unregister doesn't affect other activities.
    
    Verifies:
    - Only the specified activity is modified
    - Other activities remain unchanged
    - Same email in other activities is preserved
    """
    # sophia@mergington.edu is in both Programming Class and Debate Club
    email = "sophia@mergington.edu"
    activity_to_modify = "Programming Class"
    activity_to_preserve = "Debate Club"
    
    # Verify student is in both
    assert email in activities[activity_to_modify]["participants"]
    assert email in activities[activity_to_preserve]["participants"]
    
    # Store state of activity to preserve
    preserve_participants_before = activities[activity_to_preserve]["participants"].copy()
    
    # Unregister from one activity
    response = test_client.delete(
        f"/activities/{activity_to_modify}/unregister",
        params={"email": email}
    )
    
    assert response.status_code == 200
    
    # Verify removed from specified activity
    assert email not in activities[activity_to_modify]["participants"]
    
    # Verify still in other activity (unchanged)
    assert email in activities[activity_to_preserve]["participants"]
    assert activities[activity_to_preserve]["participants"] == preserve_participants_before


def test_unregister_multiple_times_fails(test_client, sample_data):
    """
    Test that unregistering the same student twice fails.
    
    Verifies:
    - First unregister succeeds
    - Second unregister returns 400
    """
    activity_name = sample_data["existing_activity"]
    email = sample_data["existing_student"]
    
    # First unregister - should succeed
    response1 = test_client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    assert response1.status_code == 200
    
    # Second unregister - should fail
    response2 = test_client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    assert response2.status_code == 400
    data = response2.json()
    assert "not registered" in data["detail"].lower()


def test_unregister_then_signup_again(test_client, sample_data):
    """
    Test that a student can signup again after unregistering.
    
    Verifies:
    - Unregister succeeds
    - Signup succeeds after unregister
    - Student is back in participants list
    """
    activity_name = sample_data["existing_activity"]
    email = sample_data["existing_student"]
    
    # Unregister
    response1 = test_client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    assert response1.status_code == 200
    assert email not in activities[activity_name]["participants"]
    
    # Signup again
    response2 = test_client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    assert response2.status_code == 200
    assert email in activities[activity_name]["participants"]


def test_unregister_preserves_activity_metadata(test_client, sample_data):
    """
    Test that unregister doesn't modify activity metadata.
    
    Verifies:
    - Description unchanged
    - Schedule unchanged
    - Max participants unchanged
    """
    activity_name = sample_data["existing_activity"]
    email = sample_data["existing_student"]
    
    # Store metadata before
    description_before = activities[activity_name]["description"]
    schedule_before = activities[activity_name]["schedule"]
    max_before = activities[activity_name]["max_participants"]
    
    # Unregister
    response = test_client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    assert response.status_code == 200
    
    # Verify metadata unchanged
    assert activities[activity_name]["description"] == description_before
    assert activities[activity_name]["schedule"] == schedule_before
    assert activities[activity_name]["max_participants"] == max_before
