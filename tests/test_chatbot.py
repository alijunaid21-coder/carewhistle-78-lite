import os
import sys
import importlib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Ensure a fresh database for the test
if os.path.exists('carewhistle.db'):
    os.remove('carewhistle.db')

import app
importlib.reload(app)

client = app.app.test_client()

CONTACT_MSG = (
    "Please contact us on info@carewhistle.com for further assistance."
)


def test_chatbot_constant_response():
    resp = client.post('/chatbot', json={'message': 'Hello'})
    assert resp.get_json()['reply'] == CONTACT_MSG


def test_chatbot_empty_message():
    resp = client.post('/chatbot', json={})
    assert resp.get_json()['reply'] == CONTACT_MSG


def test_chatbot_handles_invalid_json():
    resp = client.post(
        '/chatbot', data='not json', content_type='application/json'
    )
    assert resp.get_json()['reply'] == CONTACT_MSG
