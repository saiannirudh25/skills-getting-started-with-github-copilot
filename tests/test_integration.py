"""
Integration tests for the activities API.

This module tests end-to-end scenarios involving multiple API calls,
verifying that different endpoints work together correctly.
"""

import pytest
from src.app import activities


def test_full_lifecycle_signup_verify_unregister(test_client, sample_data):
    """
    Test complete lifecycle: signup -> verify in list -> unregister -> verify removed.
    
    This simulates the typical user flow through the application.
    """
    activity_name = sample_data["existing_activity"]
    email = sample_data["new_student"]
    
    # Step 1: Get initial activities list
    response1 = test_client.get("/activities")
    assert response1.status_code == 200
    initial_data = response1.json()
    initial_participants = initial_data[activity_name]["participants"].copy()
    assert email not in initial_participants
    
    # Step 2: Signup for activity
    response2 = test_client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    assert response2.status_code == 200
    
    # Step 3: Verify student appears in activities list
    response3 = test_client.get("/activities")
    assert response3.status_code == 200
    after_signup_data = response3.json()
    assert email in after_signup_data[activity_name]["participants"]
    
    # Step 4: Unregister from activity
    response4 = test_client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    assert response4.status_code == 200
    
    # Step 5: Verify student removed from activities list
    response5 = test_client.get("/activities")
    assert response5.status_code == 200
    after_unregister_data = response5.json()
    assert email not in after_unregister_data[activity_name]["participants"]


def test_multiple_students_same_activity(test_client, sample_data):
    """
    Test multiple students signing up for the same activity.
    
    Verifies that the system correctly handles multiple concurrent participants.
    """
    activity_name = sample_data["existing_activity"]
    students = [
        "alice@mergington.edu",
        "bob@mergington.edu",
        "charlie@mergington.edu"
    ]
    
    initial_count = len(activities[activity_name]["participants"])
    
    # Sign up all students
    for email in students:
        response = test_client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
    
    # Verify all students are registered
    response = test_client.get("/activities")
    data = response.json()
    participants = data[activity_name]["participants"]
    
    for email in students:
        assert email in participants
    
    assert len(participants) == initial_count + len(students)


def test_one_student_multiple_activities(test_client):
    """
    Test one student signing up for multiple different activities.
    
    Verifies that a student can participate in multiple activities simultaneously.
    """
    email = "multi.activity@mergington.edu"
    activities_to_join = ["Chess Club", "Programming Class", "Science Club"]
    
    # Sign up for multiple activities
    for activity_name in activities_to_join:
        response = test_client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
    
    # Verify student is in all activities
    response = test_client.get("/activities")
    data = response.json()
    
    for activity_name in activities_to_join:
        assert email in data[activity_name]["participants"]


def test_signup_unregister_signup_cycle(test_client, sample_data):
    """
    Test multiple cycles of signup and unregister for the same student.
    
    Verifies that data remains consistent through multiple operations.
    """
    activity_name = sample_data["existing_activity"]
    email = sample_data["new_student"]
    
    # Cycle 1: Signup -> Unregister
    response1 = test_client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    assert response1.status_code == 200
    assert email in activities[activity_name]["participants"]
    
    response2 = test_client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    assert response2.status_code == 200
    assert email not in activities[activity_name]["participants"]
    
    # Cycle 2: Signup -> Unregister
    response3 = test_client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    assert response3.status_code == 200
    assert email in activities[activity_name]["participants"]
    
    response4 = test_client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    assert response4.status_code == 200
    assert email not in activities[activity_name]["participants"]


def test_complex_scenario_multiple_students_activities(test_client):
    """
    Test complex scenario with multiple students and multiple activities.
    
    Simulates a realistic usage pattern with various operations.
    """
    # Student-activity mappings
    student_activities = {
        "test1@mergington.edu": ["Chess Club", "Programming Class"],
        "test2@mergington.edu": ["Chess Club", "Science Club"],
        "test3@mergington.edu": ["Programming Class", "Art Studio"]
    }
    
    # Sign up all students for their activities
    for email, activity_list in student_activities.items():
        for activity_name in activity_list:
            response = test_client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
    
    # Verify all signups via GET
    response = test_client.get("/activities")
    data = response.json()
    
    for email, activity_list in student_activities.items():
        for activity_name in activity_list:
            assert email in data[activity_name]["participants"]
    
    # Unregister one student from one activity
    response = test_client.delete(
        "/activities/Chess Club/unregister",
        params={"email": "test1@mergington.edu"}
    )
    assert response.status_code == 200
    
    # Verify selective unregister
    response = test_client.get("/activities")
    data = response.json()
    
    assert "test1@mergington.edu" not in data["Chess Club"]["participants"]
    assert "test1@mergington.edu" in data["Programming Class"]["participants"]
    assert "test2@mergington.edu" in data["Chess Club"]["participants"]


def test_error_handling_in_workflow(test_client, sample_data):
    """
    Test that errors in workflow don't corrupt data state.
    
    Verifies that failed operations don't leave the system in an inconsistent state.
    """
    activity_name = sample_data["existing_activity"]
    email = sample_data["new_student"]
    
    # Get initial state
    initial_participants = activities[activity_name]["participants"].copy()
    
    # Try to unregister non-existent student (should fail)
    response1 = test_client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    assert response1.status_code == 400
    
    # Verify state unchanged after failed unregister
    assert activities[activity_name]["participants"] == initial_participants
    
    # Successful signup
    response2 = test_client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    assert response2.status_code == 200
    
    # Try to signup again (should fail)
    response3 = test_client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    assert response3.status_code == 400
    
    # Verify student only appears once
    participant_count = activities[activity_name]["participants"].count(email)
    assert participant_count == 1


def test_activity_availability_changes(test_client):
    """
    Test that activity availability updates correctly as students signup/unregister.
    
    Verifies that the available spots calculation is accurate.
    """
    activity_name = "Tennis Club"
    
    # Get initial availability
    response1 = test_client.get("/activities")
    data1 = response1.json()
    max_participants = data1[activity_name]["max_participants"]
    initial_count = len(data1[activity_name]["participants"])
    initial_spots = max_participants - initial_count
    
    # Add a student
    email = "availability.test@mergington.edu"
    response2 = test_client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    assert response2.status_code == 200
    
    # Check availability decreased
    response3 = test_client.get("/activities")
    data3 = response3.json()
    new_count = len(data3[activity_name]["participants"])
    new_spots = max_participants - new_count
    
    assert new_spots == initial_spots - 1
    assert new_count == initial_count + 1
    
    # Remove the student
    response4 = test_client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    assert response4.status_code == 200
    
    # Check availability increased back
    response5 = test_client.get("/activities")
    data5 = response5.json()
    final_count = len(data5[activity_name]["participants"])
    final_spots = max_participants - final_count
    
    assert final_spots == initial_spots
    assert final_count == initial_count


def test_all_activities_operations(test_client):
    """
    Test that operations work correctly across all activities.
    
    Verifies system-wide consistency.
    """
    email = "system.wide@mergington.edu"
    
    # Get all activities
    response = test_client.get("/activities")
    assert response.status_code == 200
    all_activities = response.json()
    
    # Sign up for each activity
    for activity_name in all_activities.keys():
        response = test_client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
    
    # Verify in all activities
    response = test_client.get("/activities")
    data = response.json()
    
    for activity_name in all_activities.keys():
        assert email in data[activity_name]["participants"]
    
    # Unregister from all activities
    for activity_name in all_activities.keys():
        response = test_client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
    
    # Verify removed from all
    response = test_client.get("/activities")
    data = response.json()
    
    for activity_name in all_activities.keys():
        assert email not in data[activity_name]["participants"]
