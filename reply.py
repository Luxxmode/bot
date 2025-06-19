import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
        StaleElementReferenceException,
        NoSuchElementException,
        ElementClickInterceptedException,
    )
import random
# ===== Utility =====
def strip_non_bmp(text):
    return ''.join(c for c in text if c <= '\uFFFF')


# ===== Function: Setup driver and set cookies once =====
def create_driver_with_cookies(cookies_dict):
    options = Options()
    options.add_argument('--disable-notifications')
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(options=options)
    driver.get("https://x.com")

    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    for name, value in cookies_dict.items():
        driver.add_cookie({
            "name": name,
            "value": value,
            "domain": ".x.com",
            "path": "/",
            "secure": True,
            "httpOnly": True,
            "sameSite": "Lax"
        })
    
    driver.get("https://x.com/home")
    time.sleep(5)
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    try:
        return driver
    except:
        driver.quit()
        return None


# ===== Function: Use driver to send reply =====
def send_reply(driver, reply_link, reply_text):
    try:
        driver.get(reply_link)
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(5)

        for _ in range(5):
            driver.execute_script("window.scrollBy(0, 300);")
            time.sleep(1.5)

        try:
            reply_btn = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@data-testid="reply"] | //button[@data-testid="reply"]'))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", reply_btn)
            time.sleep(2)
            driver.execute_script("arguments[0].click();", reply_btn)
            print("✅ Reply button clicked")
        except Exception as e:
            print("❌ Couldn't click reply button:", str(e))
            driver.save_screenshot("click_fail.png")
            with open("page_source_click_fail.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            return False

        try:
            reply_box = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, '//div[@data-testid="tweetTextarea_0"]'))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", reply_box)
            time.sleep(1.5)
            reply_box.click()
            time.sleep(1.5)
            reply_box.send_keys(strip_non_bmp(reply_text))
        except Exception as e:
            print("❌ Failed to type reply:", str(e))
            driver.save_screenshot("reply_typing_fail.png")
            with open("page_source_reply_fail.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            return False

        try:
            send_btn = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@data-testid="tweetButtonInline"] | //button[@data-testid="tweetButton"]'))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", send_btn)
            time.sleep(1.5)
            send_btn.click()
            print("✅ Reply sent successfully!")
            return True
        except Exception as e:
            print("❌ Failed to send reply:", str(e))
            driver.save_screenshot("send_fail.png")
            with open("page_source_send_fail.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            return False

    finally:
        print("Closing request...")

def like_comments_under_tweet(driver, tweet_url, comments_to_like, max_scrolls=20):

    driver.get(tweet_url)
    time.sleep(5)

    liked = 0
    scrolls = 0
    seen_hashes = set()

    print("📥 Scrolling and liking comments on the go...")

    while liked < comments_to_like and scrolls < max_scrolls:
        comment_blocks = driver.find_elements(By.CSS_SELECTOR, '[data-testid="cellInnerDiv"]')
        print(f"🔎 Found {len(comment_blocks)} comment blocks")

        for i, block in enumerate(comment_blocks):
            try:
                comment_text = block.text.strip()
                comment_hash = hash(comment_text)

                if comment_hash in seen_hashes:
                    continue
                seen_hashes.add(comment_hash)

                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", block)
                time.sleep(random.uniform(1.0, 1.5))

                print(f"\n📝 Comment {i+1}: {comment_text[:100]}...")

                # Like button
                like_btn = block.find_element(By.XPATH, './/*[@data-testid="like"]')

                try:
                    svg = like_btn.find_element(By.TAG_NAME, "svg")
                    fill = svg.get_attribute("fill")

                    if fill and ("red" in fill.lower() or fill == "currentColor"):
                        print("❤️ Already liked or ambiguous. Skipping.")
                        continue

                except Exception as e:
                    print(f"⚠️ SVG read issue: {e}")
                    continue

                try:
                    driver.execute_script("arguments[0].click();", like_btn)
                    liked += 1
                    print(f"✅ Liked comment #{liked}")
                except ElementClickInterceptedException:
                    print("⚠️ Could not click like button.")
                    continue

                time.sleep(random.uniform(2.0, 2.5))

                if liked >= comments_to_like:
                    break

            except (StaleElementReferenceException, NoSuchElementException) as e:
                print(f"⚠️ Skipped due to exception: {type(e).__name__}")
                continue

        scrolls += 1
        driver.execute_script("window.scrollBy(0, 1500);")
        time.sleep(random.uniform(2.5, 3.5))

    print(f"\n🎉 Finished. Total comments liked: {liked} / {comments_to_like}")
    return liked
