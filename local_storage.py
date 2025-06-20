import json
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
ACCOUNTS_FILE = os.path.join(DATA_DIR, "accounts.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

DEFAULT_SETTINGS = {
    "max_likes_per_day":    100,
    "max_comments_per_day": 100,
    "like_min_delay":       10,
    "like_max_delay":       10,
    "comment_min_delay":    30,
    "comment_max_delay":    90,
    "today_likes":          0,
    "today_comments":       0,
    "last_reset_date":      datetime.now().date().isoformat(),
    "created_at":           int(datetime.now().timestamp()),
}


def _load(path, default):
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default


def _save(path, data):
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ----- Settings -----
def get_settings():
    return _load(SETTINGS_FILE, DEFAULT_SETTINGS.copy())


def update_settings(updates):
    settings = get_settings()
    settings.update(updates)
    _save(SETTINGS_FILE, settings)


# ----- Accounts -----
def _get_accounts():
    return _load(ACCOUNTS_FILE, [])


def _save_accounts(accs):
    _save(ACCOUNTS_FILE, accs)


def insert_account(account):
    accs = _get_accounts()
    accs.append(account)
    _save_accounts(accs)
    return True


def get_account(username):
    for acc in _get_accounts():
        if acc.get("username") == username:
            return acc
    return None


def get_all_accounts():
    return _get_accounts()


def delete_account(username):
    accs = _get_accounts()
    new_accs = [a for a in accs if a.get("username") != username]
    if len(new_accs) != len(accs):
        _save_accounts(new_accs)
        return True
    return False


def update_account(username, updates):
    accs = _get_accounts()
    for acc in accs:
        if acc.get("username") == username:
            acc.update(updates)
            _save_accounts(accs)
            return True
    return False
