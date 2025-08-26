#!/usr/bin/env python3
"""
Local Chat Scraper & ETL (Selenium + BeautifulSoup + CSV + SQLite)

Demonstrates:
- Simulating user interactions with a chat UI (type, click/Enter)
- Extracting generated responses via HTML parsing
- Rate limiting between messages
- ETL: Transform and load data to CSV and SQLite
"""

import os
import time
import json
import random
from datetime import datetime
from typing import List, Dict

import pandas as pd
from bs4 import BeautifulSoup
from sqlalchemy import create_engine

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService

# ---------------- Configuration ----------------
BASE_URL = "http://127.0.0.1:5000/chat"
OUTPUT_DIR = "scraped_data"
CSV_PATH = os.path.join(OUTPUT_DIR, "chat_responses.csv")
DB_PATH = os.path.join(OUTPUT_DIR, "chat_responses.db")
TABLE_NAME = "chat_messages"
HEADLESS = False                  # set True for headless runs
MIN_DELAY, MAX_DELAY = 0.25, 0.5   # human-like delays between keystrokes
MIN_GAP, MAX_GAP = 3, 4       # rate limit between queries
WAIT_TIMEOUT = 10                 # explicit wait timeout
# ------------------------------------------------

def polite_sleep(a, b):
    time.sleep(random.uniform(a, b))

def setup_driver(headless: bool = HEADLESS):
    opts = Options()
    if headless:
        # Using new headless flag for modern Chrome
        opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1200,800")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--no-sandbox")
    # Honest UA string (do not pretend to be something you’re not)
    opts.add_argument("user-agent=LocalSeleniumDemo/1.0 (+https://example.local)")
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=opts)
    return driver

def open_chat(driver):
    driver.get(BASE_URL)
    # Wait for chat UI elements
    WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='chat-input']"))
    )
    WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='send-btn']"))
    )

def type_humanlike(element, text: str):
    for ch in text:
        element.send_keys(ch)
        polite_sleep(MIN_DELAY, MAX_DELAY)

def send_query_and_capture(driver, query: str) -> Dict:
    # Locate input and send message (press Enter)
    textarea = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='chat-input']"))
    )
    textarea.clear()
    type_humanlike(textarea, query)
    textarea.send_keys(Keys.ENTER)

    # Wait for a new bot message to appear
    # Strategy: wait until the last chat message has role 'bot' and contains content
    def bot_message_appeared(drv):
        soup = BeautifulSoup(drv.page_source, "html.parser")
        msgs = soup.select("[data-testid='chat-message']")
        if not msgs:
            return False
        last = msgs[-1]
        # heuristics: bot messages have EchoBot in this demo response
        content = last.select_one("[data-testid='chat-message-content']")
        if content and "EchoBot" in content.get_text(strip=True):
            return True
        return False

    WebDriverWait(driver, WAIT_TIMEOUT).until(bot_message_appeared)

    # Parse DOM for the latest pair (user & bot)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    all_msgs = soup.select("[data-testid='chat-message']")
    # Find last two: user then bot
    # (In this simple app the sequence is guaranteed; in real sites you'd match by timestamps/roles)
    last_user = None
    last_bot = None

    # Walk from end backwards to pick the most recent bot and the user before it
    for node in reversed(all_msgs):
        text = node.select_one("[data-testid='chat-message-content']")
        text = text.get_text(strip=True) if text else ""
        if "EchoBot" in text and last_bot is None:
            last_bot = text
        elif last_bot is not None and last_user is None:
            # previous message should belong to user
            last_user = text
            break

    ts = datetime.utcnow().isoformat() + "Z"
    return {
        "query": last_user or query,
        "response": last_bot or "",
        "timestamp_utc": ts,
        "response_len": len(last_bot or "")
    }

def transform(records: List[Dict]) -> pd.DataFrame:
    df = pd.DataFrame(records)
    # Example transform: split metadata from EchoBot response
    # Format: [EchoBot] You said: <query> | length=<n> | time=<iso>
    df["echo_ok"] = df["response"].str.contains(r"\[EchoBot\]", na=False)
    return df

def load_outputs(df: pd.DataFrame):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    # CSV
    df.to_csv(CSV_PATH, index=False, encoding="utf-8")
    # SQLite
    engine = create_engine(f"sqlite:///{DB_PATH}")
    df.to_sql(TABLE_NAME, engine, if_exists="replace", index=False)

def main():
    queries = [
        "What is AI?",
        "Explain supervised vs unsupervised learning.",
        "Give 3 use cases of Selenium."
    ]

    print("Launching browser…")
    driver = setup_driver(headless=HEADLESS)
    scraped: List[Dict] = []
    try:
        open_chat(driver)
        print("Chat page ready.")

        for i, q in enumerate(queries, 1):
            print(f"\n[{i}/{len(queries)}] Sending: {q}")
            try:
                record = send_query_and_capture(driver, q)
                scraped.append(record)
                print(f"  ✓ Got response ({record['response_len']} chars)")
            except TimeoutException:
                print("  ! Timed out waiting for response")
            # Rate limit between queries (polite)
            gap = random.uniform(MIN_GAP, MAX_GAP)
            print(f"  …sleeping {gap:.1f}s")
            time.sleep(gap)

        if scraped:
            df = transform(scraped)
            load_outputs(df)
            # Also save raw JSON if desired
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            with open(os.path.join(OUTPUT_DIR, "chat_responses.json"), "w", encoding="utf-8") as f:
                json.dump(scraped, f, ensure_ascii=False, indent=2)
            print(f"\nSaved:\n  - {CSV_PATH}\n  - {DB_PATH}\n  - {os.path.join(OUTPUT_DIR, 'chat_responses.json')}")
        else:
            print("No records scraped.")

    finally:
        driver.quit()
        print("Browser closed.")

if __name__ == "__main__":
    main()
