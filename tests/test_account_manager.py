import os
import sys
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import account_manager


def test_save_account(tmp_path):
    db_file = tmp_path / "temp.sqlite"
    engine = create_engine(f"sqlite:///{db_file}")
    Session = sessionmaker(bind=engine)
    account_manager.Base.metadata.create_all(engine)
    session = Session()

    cookies = [{"name": "auth_token", "value": "abc"}]
    account_manager.save_account(session, "acc1", "user", "pass", cookies)

    stored = session.query(account_manager.XTwitterAccount).filter_by(name="acc1").first()
    assert stored is not None
    assert json.loads(stored.cookies_json)[0]["value"] == "abc"
