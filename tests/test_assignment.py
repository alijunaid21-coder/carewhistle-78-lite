import os
import sys
import importlib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Ensure a fresh database for the test
if os.path.exists('carewhistle.db'):
    os.remove('carewhistle.db')

import app
importlib.reload(app)
from fastapi.testclient import TestClient

client = TestClient(app.app)


def login(client, email, password):
    return client.post('/login', data={'email': email, 'password': password})


def test_reports_visible_only_after_assignment():
    # Manager should not see unassigned reports
    login(client, 'manager@brightcare.com', 'manager1')
    resp = client.get('/manager/messages')
    assert 'Open' not in resp.text

    # Admin assigns report to manager
    login(client, 'admin@admin.com', 'password')
    db = app.get_db()
    row = db.execute("SELECT id, company_id FROM users WHERE email='manager@brightcare.com'").fetchone()
    mid, cid = row["id"], row["company_id"]
    rid = db.execute("SELECT id FROM reports WHERE company_id=? LIMIT 1", (cid,)).fetchone()["id"]
    db.close()
    client.post(f'/admin/report/{rid}', data={'action': 'assign', 'manager_id': mid})

    # Manager can now see the report
    login(client, 'manager@brightcare.com', 'manager1')
    resp = client.get('/manager/messages')
    assert 'Open' in resp.text

