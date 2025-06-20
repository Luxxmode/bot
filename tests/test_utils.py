import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from common import Utils


def test_extract_post_rest_id_valid():
    link = "https://x.com/user/status/1234567890123456789/photo/1"
    assert Utils.extract_post_rest_id_from_post_link(link) == 1234567890123456789


def test_extract_post_rest_id_invalid():
    link = "https://x.com/user/1234567890123456789"
    assert Utils.extract_post_rest_id_from_post_link(link) is False
