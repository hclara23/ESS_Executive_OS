#!/usr/bin/env python3
"""Smoke test script for local Elio / WisCore API.

Runs simple checks against health, public endpoints, and the public assistant.
"""
import sys
import json
from urllib import request, parse

BASE = 'http://127.0.0.1:8001'


def post(path, data):
    url = BASE + path
    body = json.dumps(data).encode('utf-8')
    req = request.Request(url, data=body, headers={'Content-Type': 'application/json'})
    try:
        with request.urlopen(req, timeout=10) as r:
            return r.getcode(), r.read().decode('utf-8')
    except Exception as e:
        return None, str(e)


def get(path):
    url = BASE + path
    try:
        with request.urlopen(url, timeout=10) as r:
            return r.getcode(), r.read().decode('utf-8')
    except Exception as e:
        return None, str(e)


def run():
    print('Health ->', get('/health'))
    print('API info ->', get('/api'))

    # Public RFQ
    rfq_payload = {"name": "Smoke", "company": "TestCo", "email": "smoke@example.com", "description": "Smoke test", "items": [{"sku": "X", "qty": 1}]}
    print('RFQ ->', post('/wiscore/rfq', rfq_payload))

    # Public emergency
    em_payload = {"name": "Smoke", "company": "TestCo", "email": "smoke@example.com", "description": "Emergency test", "message": "Test"}
    print('Emergency ->', post('/wiscore/emergency', em_payload))

    # Public assistant
    assist = {"message": "Find cable trays"}
    print('Assistant public ->', post('/wiscore/assistant_public', assist))


if __name__ == '__main__':
    run()
