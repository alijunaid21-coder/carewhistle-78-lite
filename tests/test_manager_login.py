import os
import sys
import importlib

# Ensure repository root is on the import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Ensure a fresh database for the test
if os.path.exists('carewhistle.db'):
    os.remove('carewhistle.db')

import app
importlib.reload(app)  # re-run init after potential DB removal
from fastapi.testclient import TestClient

client = TestClient(app.app)


def login(client, email, password):
    return client.post('/login', data={'email': email, 'password': password})


def test_manager_can_login():
    resp = login(client, 'manager@brightcare.com', 'manager1')
    assert resp.status_code == 200
    assert 'Overview' in resp.text
