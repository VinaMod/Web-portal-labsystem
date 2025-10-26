#!/usr/bin/env python
"""
Simple test script to demonstrate API usage
NOTE: This requires Google OAuth credentials to be configured
"""

import requests
import json

BASE_URL = "http://localhost:5000"


def test_health():
    """Test the health endpoint"""
    print("\n=== Testing Health Endpoint ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_courses():
    """Test getting all courses"""
    print("\n=== Testing Courses Endpoint ===")
    response = requests.get(f"{BASE_URL}/courses")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_dashboard_unauthorized():
    """Test dashboard without authentication"""
    print("\n=== Testing Dashboard (Unauthorized) ===")
    response = requests.get(f"{BASE_URL}/dashboard")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_dashboard_authorized(token):
    """Test dashboard with authentication"""
    print("\n=== Testing Dashboard (Authorized) ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/dashboard", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_register_lab(token, course_id):
    """Test lab registration"""
    print(f"\n=== Testing Lab Registration (Course ID: {course_id}) ===")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {"course_id": course_id}
    response = requests.post(f"{BASE_URL}/register-lab", json=data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json() if response.status_code == 201 else None


def test_websocket_connection():
    """Information about WebSocket testing"""
    print("\n=== WebSocket Connection ===")
    print("To test WebSocket functionality, use a WebSocket client:")
    print("")
    print("Example using socketio-client library:")
    print("```python")
    print("import socketio")
    print("")
    print("sio = socketio.Client()")
    print("")
    print("@sio.on('connection_response')")
    print("def on_connect_response(data):")
    print("    print('Connected:', data)")
    print("")
    print("@sio.on('output')")
    print("def on_output(data):")
    print("    print('Output:', data['message'])")
    print("")
    print("sio.connect('http://localhost:5000')")
    print("sio.emit('authenticate', {'token': 'YOUR_JWT_TOKEN'})")
    print("sio.emit('start_lab', {'lab_id': 1})")
    print("```")


if __name__ == "__main__":
    print("=" * 60)
    print("Labtainer Backend API Test Script")
    print("=" * 60)
    
    test_health()
    test_courses()
    test_dashboard_unauthorized()
    
    print("\n" + "=" * 60)
    print("NOTE: To test authenticated endpoints, you need to:")
    print("1. Configure Google OAuth credentials")
    print("2. Complete OAuth login flow")
    print("3. Use the JWT token returned")
    print("=" * 60)
    
    test_websocket_connection()
    
    print("\n" + "=" * 60)
    print("API Documentation available in README.md")
    print("=" * 60)
