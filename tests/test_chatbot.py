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


def test_chatbot_faq_response():
    resp = client.post('/chatbot', json={'message': 'How do I file a report?'})
    assert 'Go to the Make a Report page' in resp.get_json()['reply']


def test_chatbot_empty_message():
    resp = client.post('/chatbot', json={})
    assert resp.get_json()['reply'] == 'Please say something.'


def test_chatbot_handles_invalid_json():
    resp = client.post('/chatbot', data='not json', content_type='application/json')
    assert resp.get_json()['reply'] == 'Please say something.'


def test_chatbot_unknown_question():
    question = "What's the weather?"
    resp = client.post('/chatbot', json={'message': question})
    reply = resp.get_json()['reply']
    assert 'whistleblowing' in reply.lower()
    assert question in reply
