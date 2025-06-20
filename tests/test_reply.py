import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from reply import create_driver_with_cookies


def test_create_driver_with_cookies_validation():
    with pytest.raises(ValueError):
        create_driver_with_cookies({"ct0": None, "auth_token": "abc"})
