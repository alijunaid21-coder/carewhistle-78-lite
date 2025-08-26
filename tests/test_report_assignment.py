import os, sys, importlib, pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app

admin_client = None
manager_client = None


@pytest.fixture(autouse=True)
def fresh_db():
    global app, admin_client, manager_client
    if os.path.exists('carewhistle.db'):
        os.remove('carewhistle.db')
    importlib.reload(app)
    admin_client = app.app.test_client()
    manager_client = app.app.test_client()


def login(client, email, password):
    return client.post('/login', data={'email': email, 'password': password}, follow_redirects=True)

def test_manager_sees_assigned_report():
    login(admin_client, 'admin@admin.com', 'password')
    db = app.get_db()
    rid = db.execute('SELECT id FROM reports ORDER BY id LIMIT 1').fetchone()['id']
    mid = db.execute("SELECT id FROM users WHERE role='manager' ORDER BY id LIMIT 1").fetchone()['id']
    db.close()
    admin_client.post(f'/admin/report/{rid}', data={'action': 'assign_mgr', 'manager_id': mid}, follow_redirects=True)
    login(manager_client, 'manager@brightcare.com', 'manager1')
    resp = manager_client.get('/manager/messages')
    assert str(rid).encode() in resp.data


def test_manager_does_not_see_unassigned_report():
    login(admin_client, 'admin@admin.com', 'password')
    db = app.get_db()
    rid = db.execute('SELECT id FROM reports ORDER BY id LIMIT 1').fetchone()['id']
    db.close()
    login(manager_client, 'manager@brightcare.com', 'manager1')
    resp = manager_client.get('/manager/messages')
    html = resp.get_data(as_text=True)
    assert f'<td class="py-2">{rid}</td>' not in html
