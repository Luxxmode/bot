import os
import time
import random
import pathlib
import re
import json
import traceback
import typing
from datetime import datetime 
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bson import ObjectId
from dotenv import load_dotenv
load_dotenv("./.env", override=True)

# ========================================================================================================================
# pip packages

import colorama
from  twitter.account import Account
from twitter.account import Client
from twitter.scraper import Scraper
import requests


# ========================================================================================================================
# constants

colorama.just_fix_windows_console()

# MongoDB configuration
MONGO_URI = os.environ.get("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")
ACCOUNTS_COLLECTION = os.getenv("ACCOUNTS_COLLECTION")
SETTINGS_COLLECTION = os.getenv("SETTINGS_COLLECTION")
BACKEND_URL = "https://x-backend-i606.onrender.com"
# Initialize MongoDB
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DATABASE_NAME]
accounts_collection = db[ACCOUNTS_COLLECTION]
settings_collection = db[SETTINGS_COLLECTION]

# Create indexes
accounts_collection.create_index("username", unique=True)
accounts_collection.create_index("email", unique=True)

ACC_TEST_MAX_TRIES: int = 10

# ====================================================================================================
# errors

class XTwitterExceptions(Exception):
    pass

class InvalidOperationFilePath(XTwitterExceptions):
    pass

class InvalidOperationFile(XTwitterExceptions):
    pass

# ====================================================================================================
# MongoDB Models

class GlobalSettings:
    @staticmethod
    def get_settings():
        """Fetch the one-and-only settings doc and zero counters once per calendar day."""
        now_ts = int(time.time())
        today_iso = datetime.now().date().isoformat()

        settings = settings_collection.find_one({})
        if not settings:
            # first‐time setup
            settings = {
                "max_likes_per_day":    100,
                "max_comments_per_day": 100,
                "like_min_delay":       10,
                "like_max_delay":       10,
                "comment_min_delay":    30,
                "comment_max_delay":    90,
                "today_likes":          0,
                "today_comments":       0,
                "last_reset_date":      today_iso,
                "created_at":           now_ts
            }
            settings_collection.insert_one(settings)
            return settings

        # if we haven’t reset _today_ yet, zero out both counters:
        if settings.get("last_reset_date") != today_iso:
            settings_collection.update_one({}, {"$set": {
                "today_likes":     0,
                "today_comments":  0,
                "last_reset_date": today_iso
            }})
            # also reflect it in our in-memory copy
            settings["today_likes"]     = 0
            settings["today_comments"]  = 0
            settings["last_reset_date"] = today_iso

        return settings

    @staticmethod
    def update_settings(updates):
        settings_collection.update_one(
            {}, 
            {"$set": updates},
            upsert=True
        )
    
    @staticmethod
    def is_edited_today():
        settings = GlobalSettings.get_settings()
        edited_at_ts = settings.get("edited_at")
        if not edited_at_ts:
            return False

        edited_date = datetime.fromtimestamp(edited_at_ts).date()
        today = datetime.now().date()

        return edited_date == today

class XTwitterAccount:
    @staticmethod
    def create(account_data):
        account_data["last_used_at"] = int(time.time())
        account_data["created_at"] = int(time.time())
        account_data["edited_at"] = int(time.time())
        
        # Set default values
        defaults = {
            "x_followers_count": 0,
            "x_friends_count": 0,
            "x_media_count": 0,
            "x_statuses_count": 0,
            "x_verified": False,
            "x_is_blue_verified": False,
            "x_birthdate_year": 0,
            "x_birthdate_month": 0,
            "x_birthdate_day": 0,
            "today_likes": 0,
            "today_comments": 0,
            "max_likes_per_day": 10,
            "max_comments_per_day": 10,
        }
        
        # Merge defaults with provided data
        account_data = {**defaults, **account_data}
        
        try:
            result = accounts_collection.insert_one(account_data)
            return result.inserted_id
        except PyMongoError as e:
            Terminal.red(f"Error creating account: {e}", show=True)
            return None

    @staticmethod
    def get_by_username(username):
        """Fetch the account and zero its daily counters once per calendar day."""
        acct = accounts_collection.find_one({"username": username})
        if not acct:
            return None

        today_iso = datetime.now().date().isoformat()
        if acct.get("last_reset_date") != today_iso:
            # zero it out
            accounts_collection.update_one(
                {"username": username},
                {"$set": {
                    "today_likes":     0,
                    "today_comments":  0,
                    "last_reset_date": today_iso
                }}
            )
            acct["today_likes"]     = 0
            acct["today_comments"]  = 0
            acct["last_reset_date"] = today_iso

        return acct

    @staticmethod
    def get_all():
        return list(accounts_collection.find({}))

    @staticmethod
    def delete_by_username(username):
        result = accounts_collection.delete_one({"username": username})
        return result.deleted_count > 0

    @staticmethod
    def update(account_id, updates):
        updates["edited_at"] = int(time.time())
        print(f"Updating account {account_id} with updates: {updates}")
        accounts_collection.update_one(
            {"_id": ObjectId(account_id)},
            {"$set": updates}
        )   

# ====================================================================================================
# terminal helpers

class Terminal:
    @staticmethod
    def white(txt: str, show: bool = False, ask: bool = False) -> str | typing.Any:
        o = str(colorama.Fore.WHITE) + str(txt) + str(colorama.Style.RESET_ALL)
        if show:
            print(o)
            return
        if ask:
            return input(o)
        return o

    @staticmethod
    def cyan(txt: str, show: bool = False, ask: bool = False) -> str | typing.Any:
        o = str(colorama.Fore.CYAN) + str(txt) + str(colorama.Style.RESET_ALL)
        if show:
            print(o)
            return
        if ask:
            return input(o)
        return o

    @staticmethod
    def yellow(txt: str, show: bool = False, ask: bool = False) -> str | typing.Any:
        o = str(colorama.Fore.YELLOW) + str(txt) + str(colorama.Style.RESET_ALL)
        if show:
            print(o)
            return
        if ask:
            return input(o)
        return o

    @staticmethod
    def blue(txt: str, show: bool = False, ask: bool = False) -> str | typing.Any:
        o = str(colorama.Fore.BLUE) + str(txt) + str(colorama.Style.RESET_ALL)
        if show:
            print(o)
            return
        if ask:
            return input(o)
        return o

    @staticmethod
    def red(txt: str, show: bool = False, ask: bool = False) -> str | typing.Any:
        o = str(colorama.Fore.RED) + str(txt) + str(colorama.Style.RESET_ALL)
        if show:
            print(o)
            return
        if ask:
            return input(o)
        return o

    @staticmethod
    def green(txt: str, show: bool = False, ask: bool = False) -> str | typing.Any:
        o = str(colorama.Fore.GREEN) + str(txt) + str(colorama.Style.RESET_ALL)
        if show:
            print(o)
            return
        if ask:
            return input(o)
        return o

    @staticmethod
    def magenta(txt: str, show: bool = False, ask: bool = False) -> str | typing.Any:
        o = str(colorama.Fore.MAGENTA) + str(txt) + str(colorama.Style.RESET_ALL)
        if show:
            print(o)
            return
        if ask:
            return input(o)
        return o

# ====================================================================================================
# validators class to validate values

class Validator:
    @staticmethod
    def is_int(val: typing.Any) -> bool:
        try:
            if isinstance(val, int):
                return True
            int(val)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_float(val: typing.Any) -> bool:
        try:
            if isinstance(val, float):
                return True
            float(val)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_twitter_username(val: typing.Any) -> bool:
        try:
            return len(re.findall(r"^@?(\w){1,15}$", str(val))) > 0
        except:
            return False

    @staticmethod
    def is_twitter_email(val: typing.Any) -> bool:
        try:
            return len(re.findall(r"^[^@]+@[^@]+\.[^@]+$", str(val))) > 0
        except:
            return False

    @staticmethod
    def is_twitter_password(val: typing.Any) -> bool:
        try:
            return isinstance(val, str) and len(str(val.strip())) >= 8
        except:
            return False

    @staticmethod
    def is_twitter_post_status_link(val: typing.Any) -> bool:
        try:
            rgx = r"^[H|h][T|t][T|t][P|p][S|s]?\:\/\/[X|x]\.[C|c][O|o][M|m]\/\w+\/[S|s][T|t][A|a][T|t][U|u][S|s]\/\d+\/(\w*\/?\d?)$"
            return len(re.findall(rgx, str(val))) > 0
        except:
            return False

# ====================================================================================================

class OperationInfo:
    rest_id: int | str = None
    username: str = None
    media_post_link: str = None
    comment_to_make: str = None
    comments_to_like: int = 10

    def __init__(
        self,
        rest_id: int | str = None,
        username: str = None,
        media_post_link: str = None,
        comment_to_make: str = None,
        comments_to_like: int = 10,
    ):
        self.rest_id = rest_id
        self.username = username
        self.media_post_link = media_post_link
        self.comment_to_make = comment_to_make
        self.comments_to_like = comments_to_like

def random_like_delay():
    settings = GlobalSettings.get_settings()
    delay = random.uniform(settings.get("like_min_delay"), settings.get("like_max_delay"))
    Terminal.yellow(f"Sleeping {delay:.2f} seconds before liking...")
    time.sleep(delay)

def random_comment_delay():
    settings = GlobalSettings.get_settings()
    delay = random.uniform(settings.get("comment_min_delay"), settings.get("comment_max_delay"))
    Terminal.yellow(f"Sleeping {delay:.2f} seconds before commenting...")
    time.sleep(delay)
# ====================================================================================================
# filesystem utils

class FileSystem:
    @staticmethod
    def get_base_path() -> str:
        return pathlib.Path(__file__).parent.__str__()

    @staticmethod
    def get_media_posts_operations_from_file(file_path: str) -> list[OperationInfo]:
        if not os.path.isfile(file_path):
            raise InvalidOperationFilePath(f"Invalid [Operation File] Path '{file_path}' , not exists")

        contents: list[dict] = {}
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                contents = json.load(file)
        except json.JSONDecodeError:
            raise InvalidOperationFile(f"Invalid Json [Operation File] Path '{file_path}'")

        invalid_operation_infos_count: int = 0
        valid_operations_infos_count: int = 0

        operations: list[OperationInfo] = []
        added_posts: list[str] = []

        if isinstance(contents, list):
            for op in contents:
                if not isinstance(op, dict):
                    invalid_operation_infos_count += 1
                    continue
                if "rest_id" not in op:
                    invalid_operation_infos_count += 1
                    continue
                if "username" not in op:
                    invalid_operation_infos_count += 1
                    continue
                if "media_post_link" not in op:
                    invalid_operation_infos_count += 1
                    continue
                if "comment_to_make" not in op:
                    op["comment_to_make"]=""
                    continue
                if not isinstance(op["username"], str) or not isinstance(op["media_post_link"], str) or not isinstance(op["comment_to_make"], str):
                    invalid_operation_infos_count += 1
                    continue

                if op["media_post_link"] in added_posts:
                    continue
                added_posts.append(op["media_post_link"])

                opinfo: OperationInfo = OperationInfo(
                    rest_id=op["rest_id"],
                    username=str(op["username"]).strip(),
                    media_post_link=str(op["media_post_link"]).strip(),
                    comment_to_make=str(op["comment_to_make"]).strip(),
                    comments_to_like = ((10 if int(op["comments_to_like"]) > 10 else int(op["comments_to_like"]) ) if "comments_to_like" in op and Validator.is_int(op["comments_to_like"]) else 0)
                )

                operations.append(opinfo)
                valid_operations_infos_count += 1

        return operations

    @staticmethod
    def fill_comments_randomly(operation_file: str, comments_file: str, output_file: str | None = None) -> None:
        """Populate each operation's comment_to_make field with a random comment.

        Parameters
        ----------
        operation_file : str
            Path to the operations JSON file.
        comments_file : str
            Path to the JSON file containing a list of comments.
        output_file : str | None, optional
            If provided, the updated operations are written to this path.
            Otherwise ``operation_file`` is overwritten.
        """

        if not os.path.isfile(operation_file):
            raise InvalidOperationFilePath(f"Invalid [Operation File] Path '{operation_file}' , not exists")
        if not os.path.isfile(comments_file):
            raise InvalidOperationFilePath(f"Invalid [Comments File] Path '{comments_file}' , not exists")

        try:
            with open(comments_file, "r", encoding="utf-8") as f:
                comments = json.load(f)
        except json.JSONDecodeError:
            raise InvalidOperationFile(f"Invalid Json [Comments File] Path '{comments_file}'")

        if not isinstance(comments, list) or len(comments) == 0:
            raise InvalidOperationFile("Comments file must contain a non-empty list")

        try:
            with open(operation_file, "r", encoding="utf-8") as f:
                operations = json.load(f)
        except json.JSONDecodeError:
            raise InvalidOperationFile(f"Invalid Json [Operation File] Path '{operation_file}'")

        if isinstance(operations, list):
            for op in operations:
                if isinstance(op, dict):
                    op["comment_to_make"] = random.choice(comments).strip()

        target = output_file if output_file else operation_file
        with open(target, "w", encoding="utf-8") as f:
            json.dump(operations, f, indent=4)

# ====================================================================================================
# utils

class Utils:
    @staticmethod
    def extract_post_rest_id_from_post_link(post_link: str) -> int | bool:
        try:
            if not Validator.is_twitter_post_status_link(post_link):
                return False
            spl1: list[str] = post_link.split("/status/")
            rest_id: str = spl1[1].split("/")[0].strip()
            return int(rest_id)
        except:
            return False

# ====================================================================================================
# functions

def ask_account_info() -> dict:
    o: dict = {
        "username": None,
        "email": None,
        "password": None,
        "secret_key": None,
    }

    while True:
        if o["username"] == None:
            ask_username: str = Terminal.yellow("Please Enter Account Username: ", ask=True)
            if not isinstance(ask_username, str) or not Validator.is_twitter_username(ask_username.strip()):
                Terminal.red("Invalid X Account Username , it must be valid username", show=True)
                continue
            if accounts_collection.find_one({"username": ask_username.strip()}):
                Terminal.red("Error , This Account Username is taken for another account in the database", show=True)
                continue
            o["username"] = ask_username.strip()

        if o["email"] == None:
            ask_email: str = Terminal.yellow("Please Enter Account Email: ", ask=True)
            if not isinstance(ask_email, str) or not Validator.is_twitter_email(ask_email.strip()):
                Terminal.red("Invalid X-Account Email , it must be valid email !", show=True)
                continue
            o["email"] = ask_email.strip()

        if o["password"] == None:
            ask_password: str = Terminal.yellow("Please Enter Account Password: ", ask=True)
            if not isinstance(ask_password, str) or not Validator.is_twitter_password(ask_password):
                Terminal.red("Invalid X-Account Password , it must be valid password , and it least 8 chars !", show=True)
                continue
            o["password"] = ask_password
        if o["secret_key"] == None:
            ask_secret_key: str = Terminal.yellow("Please Enter Account Secret Key (2FA): if enabled: ", ask=True)
            o["secret_key"] = ask_secret_key.strip()    

        break

    return o

def test_and_save_account_by_info(account_info: dict) -> bool:
    global ACC_TEST_MAX_TRIES
    try:
        if not isinstance(account_info, dict) or "username" not in account_info:
            return

        Terminal.cyan(f"Trying to Test Account {account_info['username']}", show=True)

        t_acc: Account = None
        t_scp: Scraper = None
        logged_in: bool = False
        last_error: Exception = None

        for i in range(ACC_TEST_MAX_TRIES):
            try:
                print("[*] Sending login request...")
                response = requests.post(f"{BACKEND_URL}/login", json=account_info, timeout=180)
                response.raise_for_status()  # Raise exception if HTTP error occurred

                res_json = response.json()
                if res_json.get("success") is False:
                    raise Exception("Login failed, account session is None")
                t_acc = res_json.get("cookies")
                print(f"[*] Login successful, cookies received: {t_acc}")
                logged_in = True
                break
            except Exception as e:
                print(f"Error while logging in to account {account_info['username']} (Attempt {i + 1}/{ACC_TEST_MAX_TRIES}): {e}")
                last_error = e

        if logged_in:
            Terminal.green(f"Account Logged in after {i} Tries !", show=True)
            Terminal.green(f"Account Test Was Successfull !", show=True)
        else:
            Terminal.red(f"Account Test Fails After {i} Tries !", show=True)
            Terminal.red(f"Error :{last_error}")
            return False

        Terminal.cyan(f"Trying to save Account into database ...", show=True)
        cookies = {**t_acc, **account_info}

        # Create a session object
        session = requests.Session()

        # Inject cookies into the session
        for key, value in cookies.items():
            session.cookies.set(key, value)        
        print(session.cookies)
        t_scp = Scraper(session=session)
        acc_info: list[dict] = t_scp.users([account_info["username"]])
        print(f"Account Info Scrapped: {acc_info}")
        if not isinstance(acc_info, list) or len(acc_info) <= 0 or "data" not in acc_info[0] or "user" not in acc_info[0]["data"] or "result" not in acc_info[0]["data"]["user"]:
            Terminal.red("Saving Account Fails !", show=True)
            Terminal.red(f"Error: Invalid Account Scrapped Info !", show=True)
            return

        acc_real_info: dict = acc_info[0]["data"]["user"]["result"]

        account_doc = {
            "name": acc_real_info["legacy"]["name"],
            "username": account_info["username"],
            "email": account_info["email"],
            "password": account_info["password"],
            "x_cookies_json": json.dumps(cookies),
            "last_used_at": int(time.time()),
            "created_at": int(time.time()),
            "edited_at": int(time.time())
        }

        if "rest_id" in acc_real_info:
            account_doc["x_id"] = acc_real_info["rest_id"]
            account_doc["x_rest_id"] = acc_real_info["rest_id"]

        if "is_blue_verified" in acc_real_info:
            account_doc["x_is_blue_verified"] = bool(acc_real_info["is_blue_verified"])

        if "legacy" in acc_real_info:
            legacy = acc_real_info["legacy"]
            if "screen_name" in legacy:
                account_doc["x_profile_name"] = legacy["screen_name"]
            if "profile_image_url_https" in legacy and isinstance(legacy["profile_image_url_https"], str):
                account_doc["x_profile_image_url_https"] = legacy["profile_image_url_https"]
            if "followers_count" in legacy:
                account_doc["x_followers_count"] = legacy["followers_count"]
            if "friends_count" in legacy:
                account_doc["x_friends_count"] = legacy["friends_count"]
            if "media_count" in legacy:
                account_doc["x_media_count"] = legacy["media_count"]

            if "legacy_extended_profile" in legacy:
                legacy_extended_profile = legacy["legacy_extended_profile"]
                if "birthdate" in legacy_extended_profile:
                    birthdate = legacy_extended_profile["birthdate"]
                    account_doc.update({
                        "x_birthdate_year": birthdate.get("year", 0),
                        "x_birthdate_month": birthdate.get("month", 0),
                        "x_birthdate_day": birthdate.get("day", 0)
                    })

            if "verified" in legacy:
                account_doc["x_verified"] = bool(legacy["verified"])

        result = XTwitterAccount.create(account_doc)
        
        if result:
            Terminal.green(f"Account {account_info['username']} Saved Successfully!", show=True)
            return True
        else:
            Terminal.red("Error While Saving Account to MongoDB!", show=True)
            return False

    except Exception as e:
        Terminal.red("Error While Testing and Saving Account!", show=True)
        Terminal.red(f"Errors: {e}", show=True)
        return False

def get_session_of_account(account: dict) ->Client | bool:
    try:
        if not isinstance(account, dict):
            return False

        cookies: dict = {}
        if isinstance(account.get("x_cookies_json"), str):
            cookies = json.loads(account["x_cookies_json"])

        client: Client = Client()
        client.cookies.update(cookies)

        return client
    except Exception as e:
        Terminal.red("Error while creating account session", show=True)
        Terminal.red(f"Error : {e}", show=True)
        return False

def get_comments_ids(account: dict, tweet_id: int, max_len: int = 10) -> list[int] | bool:
    try:
        if not isinstance(account, dict):
            return False

        ss = get_session_of_account(account=account)

        t_scrapper: Scraper = Scraper(session=ss)

        tweet_details: list[dict] = t_scrapper.tweets_details(tweet_ids=[tweet_id])

        if not isinstance(tweet_details, list) or len(tweet_details) <= 0:
            return []

        tweet_detail: dict = tweet_details[0]
        if "data" not in tweet_detail or "threaded_conversation_with_injections_v2" not in tweet_detail["data"] or "instructions" not in tweet_detail["data"]["threaded_conversation_with_injections_v2"]:
            return []

        tweet_instructions: list[dict] = tweet_detail["data"]["threaded_conversation_with_injections_v2"]["instructions"]

        if not isinstance(tweet_instructions, list) or len(tweet_instructions) <= 0 or not isinstance(tweet_instructions[0], dict):
            return []

        tweet_ins: dict = tweet_instructions[0]
        if "entries" not in tweet_ins or not isinstance(tweet_ins["entries"], list) or len(tweet_ins["entries"]) <= 0:
            return []
        
        out: list[int] = []
        for tweet_entry in tweet_ins["entries"]:
            if len(out) >= max_len:
                break
            if not isinstance(tweet_entry, dict):
                continue
            if "content" not in tweet_entry or not isinstance(tweet_entry["content"], dict) or "items" not in tweet_entry["content"] or not isinstance(tweet_entry["content"]["items"], list) or len(tweet_entry["content"]["items"]) <= 0:
                continue
            tweet_item: dict = tweet_entry["content"]["items"][0]
            if not isinstance(tweet_item, dict):
                continue
            if "item" not in tweet_item or not isinstance(tweet_item["item"], dict) or "itemContent" not in tweet_item["item"] or not isinstance(tweet_item["item"]["itemContent"], dict):
                continue
            tweet_item_content: dict = tweet_item["item"]["itemContent"]
            if not isinstance(tweet_item_content, dict) or "tweet_results" not in tweet_item_content:
                continue
            tweet_item_content_results: dict | list = tweet_item_content["tweet_results"]
            if not isinstance(tweet_item_content_results, list) and not isinstance(tweet_item_content_results, dict):
                continue
            if isinstance(tweet_item_content_results, dict):
                if "result" in tweet_item_content_results and isinstance(tweet_item_content_results["result"], dict):
                    if "__typename" in tweet_item_content_results["result"] and tweet_item_content_results["result"]["__typename"] == "Tweet":
                        if "rest_id" in tweet_item_content_results["result"]:
                            comment_id = tweet_item_content_results["result"]["rest_id"]
                            if Validator.is_int(comment_id):
                                comment_id_int: int = int(comment_id)
                                if comment_id_int not in out:
                                    out.append(comment_id_int)
                                    continue

        return out

    except Exception as e:
        fc = traceback.format_exc()
        quit()
        Terminal.red(f"Error While Getting Comments From the post {tweet_id}", show=True)
        Terminal.red(f"Errors: {e}" , show=True)
        return False

# ====================================================================================================
# texts

TRM_HELP: str = (
    "Welcome to XTwitterBot V1\n"
    + Terminal.cyan("-------------------------------") + "\n\n"

    + Terminal.cyan("* NOTE 1:") + "\n"
    + Terminal.white(
        "To work with files, place the operation file path into 'path.txt', which is located next to 'main.py'.\n"
    ) + "\n"

    + Terminal.cyan("* NOTE 2:") + "\n"
    + Terminal.white(
        "Some operations require delays to complete.\n"
        "Please wait until the script finishes processing.\n"
    ) + "\n"

    + Terminal.cyan("-------------------------------") + "\n\n"

    + Terminal.cyan("python main.py ") + Terminal.yellow("--add-account") + "\n"
    "    * Add a new account to the script's database.\n"
    "    * The script will prompt you for the name, username, email, and password of the X account.\n\n"

    + Terminal.cyan("python main.py ") + Terminal.yellow('--del-account="NAME"') + "\n"
    "    * Replace NAME with the account name you wish to delete.\n"
    "    * This command will remove the account from the database.\n\n"

    + Terminal.cyan("python main.py ") + Terminal.yellow("--list-accounts") + "\n"
    "    * Lists all X accounts currently stored in the database.\n\n"

    + Terminal.cyan("python main.py ") + Terminal.yellow("--min-like-delay=DELAY") + "\n"
    "    * Set the minimum delay (in seconds) between likes per account.\n"
    "    * Example: --min-like-delay=2\n\n"

    + Terminal.cyan("python main.py ") + Terminal.yellow("--max-like-delay=DELAY") + "\n"
    "    * Set the maximum delay (in seconds) between likes per account.\n"
    "    * Example: --max-like-delay=4\n\n"

    + Terminal.cyan("python main.py ") + Terminal.yellow("--min-comment-delay=DELAY") + "\n"
    "    * Set the minimum delay (in seconds) between comments per account.\n"
    "    * Example: --min-comment-delay=2\n\n"

    + Terminal.cyan("python main.py ") + Terminal.yellow("--max-comment-delay=DELAY") + "\n"
    "    * Set the maximum delay (in seconds) between comments per account.\n"
    "    * Example: --max-comment-delay=4\n\n"

    + Terminal.cyan("python main.py ") + Terminal.yellow("--settings") + "\n"
    "    * View the current script settings including delay configurations and more.\n\n"

    + Terminal.cyan("python main.py ") + Terminal.yellow("--do-operation") + "\n"
    "    * Executes operations defined in the operation.json file.\n"
    "    * The script reads the path from 'path.txt' to locate the operation file.\n"
    "    * Bot will display progress in the terminal.\n"
    "    * All accounts will be rotated automatically to perform the operations.\n\n"
    + Terminal.cyan("python main.py ") + Terminal.yellow("--do-linklist=FILE") + "\n"
    "    * Create an operation JSON from tweet links listed in FILE.\n"
    "    * Each line in FILE should contain a tweet URL.\n\n"

    + Terminal.cyan("-------------------------------") + "\n"
)