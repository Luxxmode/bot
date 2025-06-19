from common import OperationInfo
from common import XTwitterAccount
from common import Terminal
from common import GlobalSettings
from common import TRM_HELP
from common import ask_account_info
from common import test_and_save_account_by_info
from common import accounts_collection
from common import Validator
from common import FileSystem
from comment import do_comment_by_accounts
from like import do_like_by_accounts
from argparse import ArgumentParser
import sys
from common import get_session_of_account
from common import get_session_of_account
from reply import create_driver_with_cookies
from common import Utils
import json
import os
import time

if __name__ == "__main__":
    if len(sys.argv) <= 1 or sys.argv[1].lower() in ["--h", "-h", "--help", "-help"]:
        print(TRM_HELP)
        quit()

    # Ensure settings exist
    GlobalSettings.get_settings()

    parser = ArgumentParser(description="XTwitter Bot V1", add_help=False)

    parser.add_argument("--add-account" , action="store_true")
    parser.add_argument("--del-account")
    parser.add_argument("--accounts" , action="store_true")
    parser.add_argument("--list-accounts" , action="store_true")
    parser.add_argument("--list-account" , action="store_true")

    parser.add_argument("--min-like-delay")
    parser.add_argument("--max-like-delay")
    parser.add_argument("--min-comment-delay")
    parser.add_argument("--max-comment-delay")
    parser.add_argument("--settings" , action="store_true")
    parser.add_argument("--setting" , action="store_true")

    parser.add_argument("--do-operation" , action="store_true")
    parser.add_argument("--do-linklist")

    args = parser.parse_args()

    if args.add_account:
        acc_info:dict = ask_account_info()
        test_and_save_account_by_info(acc_info)
        quit()
    elif args.del_account:
        if accounts_collection.count_documents({"username": str(args.del_account).strip()}) > 0:
            result = XTwitterAccount.delete_by_username(str(args.del_account))
            if result:
                Terminal.green(f"Account {args.del_account} Deleted Successfully!", show=True)
            else:
                Terminal.red(f"Error deleting account {args.del_account}", show=True)
        else:
            Terminal.red(f"Account {args.del_account} not found in the database!", show=True)
    elif args.min_like_delay:
        if not Validator.is_int(args.min_like_delay) or int(args.min_like_delay) <= 0:
            Terminal.red("Invalid Min Like Delay - must be positive integer", show=True)
            quit()
        GlobalSettings.update_settings({"like_min_delay": int(args.min_like_delay)})
        Terminal.green(f"Min Like delay updated to {args.min_like_delay} seconds!", show=True)
        quit()
    elif args.max_like_delay:
        if not Validator.is_int(args.max_like_delay) or int(args.max_like_delay) <= 0:
            Terminal.red("Invalid Max Like Delay - must be positive integer", show=True)
            quit()
        GlobalSettings.update_settings({"like_max_delay": int(args.max_like_delay)})
        Terminal.green(f"Max Like delay updated to {args.max_like_delay} seconds!", show=True)
        quit()
    elif args.min_comment_delay:
        if not Validator.is_int(args.min_comment_delay) or int(args.min_comment_delay) <= 0:
            Terminal.red("Invalid Min Comment Delay - must be positive integer", show=True)
            quit()
        GlobalSettings.update_settings({"comment_min_delay": int(args.min_comment_delay)})
        Terminal.green(f"Min Comment delay updated to {args.min_comment_delay} seconds!", show=True)
        quit()
    elif args.max_comment_delay:
        if not Validator.is_int(args.max_comment_delay) or int(args.max_comment_delay) <= 0:
            Terminal.red("Invalid Max Comment Delay - must be positive integer", show=True)
            quit()
        GlobalSettings.update_settings({"comment_max_delay": int(args.max_comment_delay)})
        Terminal.green(f"Max Comment delay updated to {args.max_comment_delay} seconds!", show=True)
        quit()
    elif args.settings:
        settings = GlobalSettings.get_settings()
        Terminal.cyan("*** Settings ***" , show=True)
        Terminal.cyan("---------------------------")
        Terminal.cyan(f"min like delay : {settings['like_min_delay']}s", show=True)
        Terminal.cyan(f"max like delay : {settings['like_max_delay']}s", show=True)
        Terminal.cyan(f"min comment delay : {settings['comment_min_delay']}s", show=True)
        Terminal.cyan(f"max comment delay : {settings['comment_max_delay']}s", show=True)
        Terminal.cyan("---------------------------", show=True)
        quit()
    elif args.accounts or args.list_accounts or args.list_account:
        accs = XTwitterAccount.get_all()
        if not isinstance(accs , list) or len(accs) <= 0:
            Terminal.red("No accounts found in database", show=True)
            quit()
        
        Terminal.cyan("Listing Accounts ....", show=True)
        for acc in accs:
            print(f"""
{Terminal.yellow("-----------------------------")}
Account Name: {acc['name']}
Account Username: {acc['username']}
Account Email: {acc['email']}
Account Password: {acc['password']}
{Terminal.yellow("-----------------------------")}
""")
    elif args.do_linklist:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        link_file = args.do_linklist
        link_path = link_file if os.path.isabs(link_file) else os.path.join(base_dir, link_file)
        if not os.path.isfile(link_path):
            Terminal.red(f"Links file not exists at {link_path}", show=True)
            quit()
        with open(link_path, "r", encoding="utf-8") as f:
            links = [ln.strip() for ln in f if ln.strip()]
        operations = []
        for link in links:
            if not Validator.is_twitter_post_status_link(link):
                Terminal.red(f"Invalid link skipped: {link}", show=True)
                continue
            rest_id = Utils.extract_post_rest_id_from_post_link(link)
            if not rest_id:
                Terminal.red(f"Could not extract post id from {link}", show=True)
                continue
            username = link.split("/status")[0].split("/")[-1]
            operations.append({
                "rest_id": str(rest_id),
                "username": username,
                "media_post_link": link,
                "comment_to_make": "that is perfect! \ud83c\udf39\u2764",
                "comments_to_like": 12
            })
        if len(operations) == 0:
            Terminal.red("No valid links to process", show=True)
            quit()
        unique_name = f"operation_{int(time.time())}.json"
        output_path = os.path.join(base_dir, unique_name)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(operations, f, indent=4)
        with open(os.path.join(base_dir, "path.txt"), "w", encoding="utf-8") as f:
            f.write(unique_name)
        Terminal.green(f"Operation file created at {unique_name}", show=True)
        quit()
    elif args.do_operation:
        accs:list[dict] = XTwitterAccount.get_all()
        if not isinstance(accs , list) or len(accs) <= 0:
            Terminal.red(f"Accounts List is Empty For Doing Operation", show=True)
            quit()
        for ac in accs:
            session=get_session_of_account(account=ac)
            ct = session.cookies.get("ct0")
            auth_token = session.cookies.get("auth_token")
            driver = create_driver_with_cookies(cookies_dict={"ct0": ct, "auth_token": auth_token,})
            if not driver:
                Terminal.red(f"Failed to create driver with cookies for account {ac.get('username')}", show=True)
                continue
            Terminal.cyan(f"Doing Operation using account {ac.get('username')} ...", show=True)
            do_comment_by_accounts(ac,driver=driver)  
            do_like_by_accounts(ac, driver=driver)
            driver.quit()
        Terminal.cyan("All Operations Completed !", show=True)        
        Terminal.green("Operation Completed !", show=True)

