from common import (
    OperationInfo,
    XTwitterAccount,
    Terminal,
    Utils,
    GlobalSettings,
    FileSystem,
    get_session_of_account,
    random_like_delay,
)
from reply import like_comments_under_tweet, create_driver_with_cookies
import os





def do_like_by_account(account: dict, operation: OperationInfo, driver) -> bool:
    try:
        post_id:int = Utils.extract_post_rest_id_from_post_link(operation.media_post_link)

        if not isinstance(post_id , int):
            raise Exception("Post Not Found")


        Terminal.cyan("doing operation by these Info: ", show=True)
        Terminal.cyan(f"doing like to post {post_id } in comments", show=True)
        settings: dict = GlobalSettings.get_settings()
        try:
            max_likes_for_acc = account.get("max_likes_per_day", settings.get("max_likes_per_day"))
            if account.get("today_likes", 0) >= max_likes_for_acc:
                Terminal.yellow(
                    f"Account {account['username']} has reached the maximum likes for today",
                    show=True,
                )
                return True




            elif settings.get("today_likes") >= settings.get("max_likes_per_day"):
                Terminal.yellow(f"Global Settings has reached the maximum likes for today", show=True)
            else:
                res = like_comments_under_tweet(
                    driver=driver,
                    tweet_url=operation.media_post_link,
                    comments_to_like=operation.comments_to_like,
                    max_scrolls=account.get("max_likes_per_day", 20)  # Default to 10 if not specified
                )
                if res:
                    GlobalSettings.update_settings(
                        {"today_likes": settings.get("today_likes", 0) + res}
                    )
                    XTwitterAccount.update(
                        account_id=account.get("_id"),
                        updates={
                            "today_likes": XTwitterAccount.get_by_username(account.get("username")).get("today_likes") + res,
                        }
                    )
                    Terminal.green(f"Comment Liked Successfully ! :\n * Post Link : {operation.media_post_link} \n * Account Name: {account.get('name')}", show=True)
                    random_like_delay()
                else:
                    print(f"Failed to like comment on post {operation.media_post_link} using account {account.get('name')}")
        except Exception as e:
            Terminal.red(f"Error While Liking The Comment ! \n * Post Link : {operation.media_post_link} \n * Account Name: {account.get('name')}", show=True)
            Terminal.red(f"Error : {e}", show=True)

        Terminal.green(f"Operation Completed By Account Successfully\n * Account Name {account['name']}\n * Account Username : {account['username']} \n * Post Id : {post_id}", show=True)
    except Exception as e:
        Terminal.red(f"Failed to doing operation for post :\n * Post Link : {operation.media_post_link}\n * Account Name : {account['name']}\n * Account Username : {account['username']}", show=True)
        Terminal.red(f"Errors : {e}", show=True)
        return False


def do_like_by_accounts(ac:XTwitterAccount, driver) -> None:
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
        session=get_session_of_account(account=ac)
        ct = session.cookies.get("ct0")
        auth_token = session.cookies.get("auth_token")
        driver = create_driver_with_cookies(cookies_dict={"ct0": ct, "auth_token": auth_token,})
        if not driver:
            Terminal.red(f"Failed to create driver with cookies for account {ac.get('username')}", show=True)
            return
        for op in operations:
            if (op.comments_to_like != 0 and op.media_post_link):
                Terminal.cyan(f"Doing Operation on Link {op.media_post_link} ...", show=True)
                do_like_by_account(ac,op,driver=driver)
            else:
                continue
        return
    except Exception as e:
        Terminal.red(f"Error While Reading Operation Json file at {operation_file_path} {e}", show=True)
        Terminal.red(f"Errors : {e}")
