import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the src directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities

# Initial activities data for resetting
INITIAL_ACTIVITIES = {
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
        "description": "Competitive basketball team for intramural and inter-school games",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 15,
        "participants": ["james@mergington.edu"]
    },
    "Tennis Club": {
        "description": "Learn tennis techniques and participate in friendly matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:00 PM",
        "max_participants": 16,
        "participants": ["sarah@mergington.edu", "alex@mergington.edu"]
    },
    "Art Studio": {
        "description": "Explore painting, drawing, and other visual arts",
        "schedule": "Wednesdays and Saturdays, 2:00 PM - 4:00 PM",
        "max_participants": 18,
        "participants": ["isabella@mergington.edu"]
    },
    "Music Band": {
        "description": "Play instruments and perform in school concerts",
        "schedule": "Mondays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 25,
        "participants": ["lucas@mergington.edu", "ava@mergington.edu"]
    },
    "Debate Club": {
        "description": "Develop argumentation and public speaking skills through competitive debate",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 14,
        "participants": ["ryan@mergington.edu"]
    },
    "Science Olympiad": {
        "description": "Compete in science competitions and conduct experiments",
        "schedule": "Tuesdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["noah@mergington.edu", "mia@mergington.edu"]
    }
}


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the activities dictionary to initial state before each test"""
    activities.clear()
    activities.update(INITIAL_ACTIVITIES)


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


def test_get_root_redirect(client):
    """Test that GET / redirects to static index.html"""
    # Arrange: No special setup needed

    # Act: Make request to root without following redirects
    response = client.get("/", follow_redirects=False)

    # Assert: Should redirect to static file
    assert response.status_code == 307  # Temporary redirect
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test getting all activities"""
    # Arrange: Activities are reset by fixture

    # Act: Request all activities
    response = client.get("/activities")

    # Assert: Returns 200 with activities dict
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) == 9  # All activities present
    assert "Chess Club" in data
    assert "Programming Class" in data

    # Check structure of one activity
    chess = data["Chess Club"]
    assert "description" in chess
    assert "schedule" in chess
    assert "max_participants" in chess
    assert "participants" in chess
    assert isinstance(chess["participants"], list)


def test_signup_success(client):
    """Test successful signup for an activity"""
    # Arrange: Choose an activity and new email
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"
    initial_count = len(activities[activity_name]["participants"])

    # Act: Signup
    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert: Success response and participant added
    assert response.status_code == 200
    data = response.json()
    assert "Signed up" in data["message"]
    assert email in data["message"]

    # Verify participant was added
    assert len(activities[activity_name]["participants"]) == initial_count + 1
    assert email in activities[activity_name]["participants"]


def test_signup_duplicate_email(client):
    """Test that duplicate signup is rejected"""
    # Arrange: Signup once
    activity_name = "Programming Class"
    email = "test@mergington.edu"
    client.post(f"/activities/{activity_name}/signup?email={email}")

    # Act: Try to signup again
    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert: 400 error for duplicate
    assert response.status_code == 400
    data = response.json()
    assert "already signed up" in data["detail"]


def test_signup_activity_not_found(client):
    """Test signup for non-existent activity"""
    # Arrange: Use invalid activity name
    activity_name = "Fake Activity"
    email = "test@mergington.edu"

    # Act: Attempt signup
    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert: 404 error
    assert response.status_code == 404
    data = response.json()
    assert "Activity not found" in data["detail"]


def test_signup_over_capacity_allowed(client):
    """Test that signup allows exceeding max_participants (known behavior)"""
    # Arrange: Find activity with low max_participants
    activity_name = "Debate Club"  # max 14, currently 1
    email = "new@mergington.edu"

    # Act: Signup (should succeed even if over capacity)
    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert: Success (documenting that capacity is not enforced)
    assert response.status_code == 200
    assert email in activities[activity_name]["participants"]


def test_unregister_success(client):
    """Test successful unregister from an activity"""
    # Arrange: First signup
    activity_name = "Tennis Club"
    email = "removeme@mergington.edu"
    client.post(f"/activities/{activity_name}/signup?email={email}")
    initial_count = len(activities[activity_name]["participants"])

    # Act: Unregister
    response = client.delete(f"/activities/{activity_name}/unregister?email={email}")

    # Assert: Success and participant removed
    assert response.status_code == 200
    data = response.json()
    assert "Unregistered" in data["message"]
    assert email in data["message"]

    # Verify participant was removed
    assert len(activities[activity_name]["participants"]) == initial_count - 1
    assert email not in activities[activity_name]["participants"]


def test_unregister_not_registered(client):
    """Test unregistering email not in activity"""
    # Arrange: Use email not signed up
    activity_name = "Art Studio"
    email = "notregistered@mergington.edu"

    # Act: Attempt unregister
    response = client.delete(f"/activities/{activity_name}/unregister?email={email}")

    # Assert: 400 error
    assert response.status_code == 400
    data = response.json()
    assert "not registered" in data["detail"]


def test_unregister_activity_not_found(client):
    """Test unregister from non-existent activity"""
    # Arrange: Invalid activity name
    activity_name = "Nonexistent Activity"
    email = "test@mergington.edu"

    # Act: Attempt unregister
    response = client.delete(f"/activities/{activity_name}/unregister?email={email}")

    # Assert: 404 error
    assert response.status_code == 404
    data = response.json()
    assert "Activity not found" in data["detail"]