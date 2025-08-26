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

def test_chatbot_empty_message():
    resp = client.post('/chatbot', json={})
    assert resp.get_json()['reply'] == 'Please say something.'


def test_chatbot_handles_invalid_json():
    resp = client.post('/chatbot', data='not json', content_type='application/json')
    assert resp.get_json()['reply'] == 'Please say something.'

def test_chatbot_history_and_no_key():
    resp = client.post('/chatbot', json={'message': 'Hello'})
    data = resp.get_json()
    assert data['reply'] == 'AI not configured.'
    with client.session_transaction() as sess:
        history = sess['chat_history']
        assert history[0]['role'] == 'system'


def test_chatbot_faq_response():
    resp = client.post('/chatbot', json={'message': 'How will my report be handled?'})
    data = resp.get_json()
    assert 'trained advisors compile a detailed concern report' in data['reply']
