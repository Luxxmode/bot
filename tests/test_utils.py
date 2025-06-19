import os
import sys
import pymongo
import mongomock
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

pymongo.MongoClient = mongomock.MongoClient
os.environ.setdefault("MONGO_URI", "mongodb://localhost")
os.environ.setdefault("DATABASE_NAME", "testdb")
os.environ.setdefault("ACCOUNTS_COLLECTION", "accounts")
os.environ.setdefault("SETTINGS_COLLECTION", "settings")

from common import Utils


def test_extract_post_rest_id_valid():
    link = "https://x.com/user/status/1234567890123456789/photo/1"
    assert Utils.extract_post_rest_id_from_post_link(link) == 1234567890123456789


def test_extract_post_rest_id_invalid():
    link = "https://x.com/user/1234567890123456789"
    assert Utils.extract_post_rest_id_from_post_link(link) is False
