import os
import sys
import pymongo
import mongomock
import pytest
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

pymongo.MongoClient = mongomock.MongoClient
os.environ.setdefault("MONGO_URI", "mongodb://localhost")
os.environ.setdefault("DATABASE_NAME", "testdb")
os.environ.setdefault("ACCOUNTS_COLLECTION", "accounts")
os.environ.setdefault("SETTINGS_COLLECTION", "settings")

import common


def test_backend_unreachable(monkeypatch):
    account = {"username": "test", "email": "a@b.com", "password": "12345678"}

    def mock_head(*args, **kwargs):
        raise requests.exceptions.ConnectionError("unreachable")

    monkeypatch.setattr(requests, "head", mock_head)

    # post should not be called if head fails, but patch it just in case
    monkeypatch.setattr(requests, "post", lambda *a, **k: None)

    assert common.test_and_save_account_by_info(account) is False
