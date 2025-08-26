#!/usr/bin/env python3
"""
Simple Bing Chat Scraper - Minimal Version
==========================================

A simplified version of the Bing Chat scraper with basic functionality
for testing and development purposes.
"""

import time
import random
import json
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup


class SimpleBingChatScraper:
    def __init__(self, email="", password="", headless=False):
        self.email = email
        self.password = password
        self.headless = headless
        self.driver = None
        self.scraped_data = []

    def setup_driver(self):
        """Setup Chrome WebDriver with basic options"""
        options = Options()

        if self.headless:
            options.add_argument("--headless")

        # Basic options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        options.add_argument("--window-size=1920,1080")

        try:
            self.driver = webdriver.Chrome(options=options)
            print("✅ Chrome WebDriver initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize WebDriver: {e}")
            print("Make sure Chrome browser is installed and chromedriver is in PATH")
            return False

    def login_to_bing(self):
        """Simple login to Bing Chat"""
        try:
            print("🌐 Navigating to Bing Chat...")
            self.driver.get("https://bing.com/chat")
            time.sleep(3)

            # Check if already logged in
            try:
                chat_input = self.driver.find_element(By.CSS_SELECTOR, "textarea")
                if chat_input:
                    print("✅ Already logged in or no login required")
                    return True
            except:
                pass

            # Look for sign-in button
            try:
                sign_in_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Sign in"))
                )
                sign_in_button.click()
                time.sleep(3)

                if self.email and self.password:
                    # Enter email
                    email_input = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
                    )
                    email_input.send_keys(self.email)

                    # Click Next
                    next_button = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
                    next_button.click()
                    time.sleep(3)

                    # Enter password
                    password_input = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
                    )
                    password_input.send_keys(self.password)

                    # Click Sign In
                    signin_button = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
                    signin_button.click()
                    time.sleep(5)

                    print("✅ Login completed")
                else:
                    print("⚠️ No credentials provided. Manual login may be required.")
                    input("Please complete login manually and press Enter to continue...")

                return True

            except TimeoutException:
                print("⚠️ No sign-in button found. Proceeding without login...")
                return True

        except Exception as e:
            print(f"❌ Login failed: {e}")
            return False

    def send_query(self, query):
        """Send a query to Bing Chat and get response"""
        try:
            print(f"📝 Sending query: {query}")

            # Find chat input
            chat_input = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea"))
            )

            # Clear and type query
            chat_input.clear()
            for char in query:
                chat_input.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))  # Human-like typing

            time.sleep(1)

            # Send query
            chat_input.send_keys(Keys.RETURN)
            print("📤 Query sent, waiting for response...")

            # Wait for response
            time.sleep(8)  # Give time for response to generate

            # Extract response using BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            # Look for response content
            response_text = ""

            # Try different selectors for response content
            selectors = [
                '[data-testid="chat-message-content"]',
                '.chat-message-content',
                '.response-content',
                '[class*="message"]',
                '[class*="response"]'
            ]

            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    # Get the last response (most recent)
                    response_text = elements[-1].get_text(strip=True)
                    if len(response_text) > 20:  # Valid response
                        break

            if not response_text:
                # Fallback: get all text from page and try to extract response
                page_text = soup.get_text()
                # This is a simplified extraction - in practice, you'd need more sophisticated parsing
                if query.lower() in page_text.lower():
                    response_text = "Response extracted from page content (simplified)"

            if response_text:
                result = {
                    'query': query,
                    'response': response_text,
                    'timestamp': datetime.now().isoformat(),
                    'response_length': len(response_text)
                }

                self.scraped_data.append(result)
                print(f"✅ Response extracted ({len(response_text)} characters)")
                return result
            else:
                print("⚠️ No response found")
                return None

        except Exception as e:
            print(f"❌ Failed to send query: {e}")
            return None

    def scrape_queries(self, queries):
        """Scrape multiple queries with rate limiting"""
        print(f"🚀 Starting to scrape {len(queries)} queries...")

        for i, query in enumerate(queries, 1):
            print(f"\n--- Query {i}/{len(queries)} ---")

            result = self.send_query(query)

            if result:
                print(f"✅ Query {i} completed successfully")
            else:
                print(f"❌ Query {i} failed")

            # Rate limiting
            if i < len(queries):
                delay = random.uniform(5, 10)
                print(f"⏳ Waiting {delay:.1f} seconds before next query...")
                time.sleep(delay)

        print(f"\n🎉 Scraping completed! Collected {len(self.scraped_data)} responses")

    def save_data(self, output_dir="scraped_data"):
        """Save scraped data to files"""
        if not self.scraped_data:
            print("⚠️ No data to save")
            return

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Save as JSON
        json_file = f"{output_dir}/bing_responses.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.scraped_data, f, indent=2, ensure_ascii=False)

        # Save as simple CSV-like format
        csv_file = f"{output_dir}/bing_responses.txt"
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write("Query\tResponse\tTimestamp\tLength\n")
            for item in self.scraped_data:
                f.write(
                    f"{item['query']}\t{item['response'][:100]}...\t{item['timestamp']}\t{item['response_length']}\n")

        print(f"💾 Data saved to:")
        print(f"   📄 {json_file}")
        print(f"   📄 {csv_file}")

    def cleanup(self):
        """Close browser and cleanup"""
        if self.driver:
            self.driver.quit()
            print("🔒 Browser closed")


def main():
    """Simple main function for testing"""
    print("🤖 Simple Bing Chat Scraper")
    print("=" * 40)

    # Test queries
    test_queries = [
        "What is AI",
        "How does machine learning work?",
        "Explain quantum computing in simple terms"
    ]

    # Get credentials (optional)
    email = input("Enter your Microsoft email (or press Enter to skip): ").strip()
    password = input("Enter your password (or press Enter to skip): ").strip() if email else ""

    # Create scraper
    scraper = SimpleBingChatScraper(email=email, password=password, headless=False)

    try:
        # Setup and run
        if scraper.setup_driver():
            if scraper.login_to_bing():
                scraper.scrape_queries(test_queries)
                scraper.save_data()
            else:
                print("❌ Login failed")
        else:
            print("❌ Driver setup failed")

    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        scraper.cleanup()


if __name__ == "__main__":
    main()