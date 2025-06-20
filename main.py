from common import OperationInfo
from common import XTwitterAccount
from common import Terminal
from common import GlobalSettings
from common import TRM_HELP
from common import ask_account_info
from common import test_and_save_account_by_info
from common import Validator
from common import FileSystem
from comment import do_comment_by_accounts
from like import do_like_by_accounts
from argparse import ArgumentParser
import sys
from common import get_session_of_account
from reply import create_driver_with_cookies

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

    args = parser.parse_args()

    if args.add_account:
        acc_info:dict = ask_account_info()
        test_and_save_account_by_info(acc_info)
        quit()
    elif args.del_account:
        if XTwitterAccount.get_by_username(str(args.del_account).strip()):
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
            acc_name = acc.get('name') or acc.get('username')
            print(
                f"""
{Terminal.yellow("-----------------------------")}
Account Name: {acc_name}
Account Username: {acc.get('username')}
Account Email: {acc.get('email')}
Account Password: {acc.get('password')}
{Terminal.yellow("-----------------------------")}
"""
            )
    elif args.do_operation:
        accs:list[dict] = XTwitterAccount.get_all()
        if not isinstance(accs , list) or len(accs) <= 0:
            Terminal.red(f"Accounts List is Empty For Doing Operation", show=True)
            quit()
        for ac in accs:
            session = get_session_of_account(account=ac)
            ct = session.cookies.get("ct0") if session else None
            auth_token = session.cookies.get("auth_token") if session else None

            if not ct or not auth_token:
                Terminal.red(
                    f"Account {ac.get('username')} is missing required cookies; skipping",
                    show=True,
                )
                continue

            driver = create_driver_with_cookies({"ct0": ct, "auth_token": auth_token})
            if not driver:
                Terminal.red(
                    f"Failed to create driver with cookies for account {ac.get('username')}",
                    show=True,
                )
                continue

            Terminal.cyan(
                f"Doing Operation using account {ac.get('username')} ...",
                show=True,
            )
            do_comment_by_accounts(ac, driver=driver)
            do_like_by_accounts(ac, driver=driver)
            driver.quit()
        Terminal.cyan("All Operations Completed !", show=True)
        Terminal.green("Operation Completed !", show=True)

