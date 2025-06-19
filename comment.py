from common import OperationInfo
from common import XTwitterAccount
from common import Terminal
from common import Utils
from common import GlobalSettings
from common import FileSystem
from twitter.account import Account

from common import random_comment_delay
from reply import send_reply
import os




def do_comment_by_account(account: dict, operation: OperationInfo, driver) -> bool:
    try:
        post_id:int = Utils.extract_post_rest_id_from_post_link(operation.media_post_link)

        if not isinstance(post_id , int):
            raise Exception("Post Not Found")


        Terminal.cyan("doing operation by these Info: ", show=True)
        Terminal.cyan(f"doing comment to post {post_id}", show=True)
        settings: dict = GlobalSettings.get_settings()
        try:
            if (account.get("today_comments") >= account.get("max_comments_per_day")):
                Terminal.yellow(f"Account {account.get('name')} has reached the maximum comments for today", show=True)
            elif settings.get("today_comments") >= settings.get("max_comments_per_day"):
                Terminal.yellow(f"Global Settings has reached the maximum comments for today", show=True)
            else:
                res = send_reply(
                    driver=driver,
                    reply_link=operation.media_post_link,
                    reply_text=operation.comment_to_make
                )
                if(res):
                    GlobalSettings.update_settings({
                        "today_comments": settings.get("today_comments") + 1,
                    })
                    XTwitterAccount.update(
                        account_id=account.get("_id"),
                        updates={
                            "today_comments": XTwitterAccount.get_by_username(account.get("username")).get("today_comments") + 1,
                        }
                    )
                    Terminal.green(f"Comment Replied Successfully ! :\n * Post Link : {operation.media_post_link} \n * Account Name: {account.get('name')}", show=True)
                    random_comment_delay()

                else:
                    print(f"Failed to reply comment on post {operation.media_post_link} using account {account.get('name')}")
        except Exception as e:
            Terminal.red(f"Error While Repling The Comment ! \n * Post Link : {operation.media_post_link} \n * Account Name: {account.get('name')}", show=True)
            Terminal.red(f"Error : {e}", show=True)

        Terminal.green(f"Operation Completed By Account Successfully\n * Account Name {account['name']}\n * Account Username : {account['username']} \n * Post Id : {post_id}", show=True)
    except Exception as e:
        Terminal.red(f"Failed to dowing operatin for post :\n * Post Link : {operation.media_post_link}\n * Account Name : {account['name']}\n * Account Username : {account['username']}", show=True)
        Terminal.red(f"Errors : {e}", show=True)
        return False



def do_comment_by_accounts(ac:XTwitterAccount, driver) -> None:
    try:
        base_dir:str = FileSystem.get_base_path()
        if not os.path.isfile(os.path.join(base_dir , "path.txt")):
            Terminal.red("path.txt file not exists , please create it , and paste operation JSON file PATH in it", show=True)
            quit()
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_name:str = open(os.path.join(base_dir , "path.txt"),"r").read()
        operation_file_path:str =  os.path.join(base_dir,file_name.strip())
        if not os.path.isfile(operation_file_path):
            Terminal.red(f"Operation file not exists at {operation_file_path}")
            quit()
        operations:list[OperationInfo] = FileSystem.get_media_posts_operations_from_file(operation_file_path)
        if not operations or not isinstance(operations , list) or len(operations) <= 0:
            Terminal.red("There is not operation in the operation file", show=True)
            Terminal.red("Probably The Format Of File is not correct", show=True)
            quit()    
        Terminal.cyan(f"{len(operations)} Operations Found ...", show=True)
        
        for op in operations:
            if (op.comment_to_make != ""):
                Terminal.cyan(f"Doing Operation on Link {op.media_post_link} ...", show=True)
                do_comment_by_account(ac,op,driver=driver)
            else:
                continue
        return
    except Exception as e:
        Terminal.red(f"Error While Reading Operation Json file at {operation_file_path} {e}", show=True)
        Terminal.red(f"Errors : {e}")
