import sys
import types
import importlib
import unittest

# Stub external dependencies so common.py can be imported without installing them
pymongo = types.ModuleType('pymongo')
class DummyCollection:
    def create_index(self, *a, **k):
        pass
    def find_one(self, *a, **k):
        return None
    def insert_one(self, *a, **k):
        pass
    def update_one(self, *a, **k):
        pass
class DummyDB:
    def __getitem__(self, name):
        return DummyCollection()
class DummyMongoClient:
    def __init__(self, *a, **k):
        pass
    def __getitem__(self, name):
        return DummyDB()

pymongo.MongoClient = DummyMongoClient
sys.modules['pymongo'] = pymongo

errors_mod = types.ModuleType('pymongo.errors')
errors_mod.PyMongoError = Exception
sys.modules['pymongo.errors'] = errors_mod

bson_mod = types.ModuleType('bson')
bson_mod.ObjectId = lambda *a, **k: None
sys.modules['bson'] = bson_mod

dotenv = types.ModuleType('dotenv')
dotenv.load_dotenv = lambda *a, **k: None
sys.modules['dotenv'] = dotenv

colorama = types.ModuleType('colorama')
colorama.just_fix_windows_console = lambda *a, **k: None
colorama.Fore = types.SimpleNamespace(WHITE='', CYAN='', YELLOW='', BLUE='', RED='', GREEN='', MAGENTA='')
colorama.Style = types.SimpleNamespace(RESET_ALL='')
sys.modules['colorama'] = colorama

twitter_account = types.ModuleType('twitter.account')
twitter_account.Account = object
twitter_account.Client = object
sys.modules['twitter.account'] = twitter_account

twitter_scraper = types.ModuleType('twitter.scraper')
twitter_scraper.Scraper = object
sys.modules['twitter.scraper'] = twitter_scraper

requests_mod = types.ModuleType('requests')
requests_mod.Session = lambda *a, **k: None
requests_mod.post = lambda *a, **k: types.SimpleNamespace(status_code=200)
sys.modules['requests'] = requests_mod

# Now import the module under test
common = importlib.import_module('common')
Utils = common.Utils

class TestExtractPostRestId(unittest.TestCase):
    def test_valid_link(self):
        link = "https://x.com/user/status/12345"
        self.assertEqual(Utils.extract_post_rest_id_from_post_link(link), 12345)

    def test_invalid_link(self):
        link = "invalid_link"
        self.assertFalse(Utils.extract_post_rest_id_from_post_link(link))

if __name__ == "__main__":
    unittest.main()
