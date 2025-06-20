import sys
import time
import json
import argparse
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from colorama import Fore, Style, just_fix_windows_console

just_fix_windows_console()

DATABASE_NAME = "Database.sqlite3"
engine = create_engine(f"sqlite:///{DATABASE_NAME}", echo=False)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

class XTwitterAccount(Base):
    __tablename__ = "x_accounts"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    cookies_json = Column(Text, nullable=True)

Base.metadata.create_all(engine)


def print_color(txt, color):
    print(color + str(txt) + Style.RESET_ALL)


def selenium_login_and_save_cookies(username, password):
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=options)
    driver.get("https://twitter.com/login")
    time.sleep(4)
    # Username/email input
    user_box = driver.find_element(By.NAME, "text")
    user_box.send_keys(username)
    user_box.send_keys(Keys.RETURN)
    time.sleep(2)
    # Password input
    pwd_box = driver.find_element(By.NAME, "password")
    pwd_box.send_keys(password)
    pwd_box.send_keys(Keys.RETURN)
    print(Fore.YELLOW + "🔔 Waiting 10 seconds... Please solve any popups, complete verification, and wait for home timeline to load!" + Style.RESET_ALL)
    time.sleep(10)
    # Now refresh and wait to be sure session cookies are complete
    driver.refresh()
    print(Fore.CYAN + "🔁 Refreshed page. Waiting a few more seconds for all session cookies..." + Style.RESET_ALL)
    time.sleep(4)
    # Print cookies for debug
    cookies = driver.get_cookies()
    print(Fore.MAGENTA + "\n--- Session cookies ---")
    for c in cookies:
        print(f"{c['name']}: {c['value']}")
    print("--- End cookies ---\n" + Style.RESET_ALL)
    # Check login status
    if "login" in driver.current_url or "Log in" in driver.title:
        print(Fore.RED + "❌ Login failed! Still on login page." + Style.RESET_ALL)
        driver.quit()
        return None
    print(Fore.GREEN + "✅ Looks logged in! Saving cookies..." + Style.RESET_ALL)
    driver.quit()
    return cookies


def save_account(session, name, username, password, cookies):
    acc = XTwitterAccount(
        name=name,
        username=username,
        password=password,
        cookies_json=json.dumps(cookies)
    )
    session.add(acc)
    session.commit()


def add_account_interactive():
    name = input(Fore.YELLOW + "Account name (unique): " + Style.RESET_ALL).strip()
    username = input(Fore.YELLOW + "Twitter username/email: " + Style.RESET_ALL).strip()
    password = input(Fore.YELLOW + "Password: " + Style.RESET_ALL).strip()

    with SessionLocal() as session:
        cookies = selenium_login_and_save_cookies(username, password)
        if not cookies:
            print_color("Account not added (login failed).", Fore.RED)
            return
        key_cookies = ['auth_token', 'ct0', 'twid']
        found_keys = [c['name'] for c in cookies if c['name'] in key_cookies]
        if len(found_keys) < len(key_cookies):
            print_color("Warning: Not all key cookies found! You may not be fully logged in.", Fore.YELLOW)
        else:
            print_color("All key cookies present. Proceeding.", Fore.GREEN)
        save_account(session, name, username, password, cookies)
        print_color(f"Account '{name}' saved with cookies!", Fore.GREEN)


def list_accounts():
    with SessionLocal() as session:
        accounts = session.query(XTwitterAccount).all()
        if not accounts:
            print_color("No accounts found.", Fore.RED)
            return
        for acc in accounts:
            print(Fore.CYAN + f"Name: {acc.name}, Username: {acc.username}" + Style.RESET_ALL)


def del_account(name):
    with SessionLocal() as session:
        found = session.query(XTwitterAccount).filter_by(name=name).first()
        if not found:
            print_color("Account not found.", Fore.RED)
            return
        session.delete(found)
        session.commit()
        print_color(f"Account '{name}' deleted.", Fore.GREEN)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Twitter Selenium Cookie Bot")
    parser.add_argument("--add-account", action="store_true")
    parser.add_argument("--list-accounts", action="store_true")
    parser.add_argument("--del-account", type=str)
    args = parser.parse_args()

    if args.add_account:
        add_account_interactive()
    elif args.list_accounts:
        list_accounts()
    elif args.del_account:
        del_account(args.del_account)
    else:
        parser.print_help()
