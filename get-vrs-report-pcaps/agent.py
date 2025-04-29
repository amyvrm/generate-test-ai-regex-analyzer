"""
AI Agent for Trend Micro VRS Portal Automation
---------------------------------------------
Use Case: Automate login, search, and file download for a given TSL ID from the Trend Micro TIS portal.

Features:
- Robust element waits and error handling
- Modular agent class for extensibility
- CLI usability for easy integration
"""

import os
import time
import tempfile
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

class VRSPortalAIAgent:
    """
    AI Agent for automating Trend Micro TIS portal tasks.
    Use Case: Downloading resources after login and search.
    """
    RESOURCE_LABELS = [
        "Vulnerability Report PDF",
        "Vulnerability Baseline PCAP",
        "Vulnerability Attack PCAP"
    ]

    def __init__(self, portal_url, user_id, subscriber, password, tsl_id, download_dir):
        self.portal_url = portal_url
        self.user_id = user_id
        self.subscriber = subscriber
        self.password = password
        self.tsl_id = tsl_id
        self.download_dir = download_dir
        self.driver = None
        self.wait = None

    def setup(self):
        """Set up Selenium WebDriver with best practices for headless automation."""
        chrome_options = Options()
        chrome_options.binary_location = "/usr/bin/chromium"
        chrome_options.add_experimental_option("prefs", {
            "download.default_directory": os.path.abspath(self.download_dir),
            "download.prompt_for_download": False,
            "plugins.always_open_pdf_externally": True
        })
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--headless=new')
        user_data_dir = tempfile.mkdtemp(dir="/tmp")
        chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
        service = Service("/usr/bin/chromedriver")
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)

    def robust_find(self, by, value, alternatives=None, retries=3, wait_time=2):
        """
        Try to find an element using the main selector, then alternatives, with retries and adaptive backoff.
        """
        for attempt in range(retries):
            try:
                return self.wait.until(EC.presence_of_element_located((by, value)))
            except Exception as e:
                if alternatives:
                    for alt_by, alt_value in alternatives:
                        try:
                            return self.wait.until(EC.presence_of_element_located((alt_by, alt_value)))
                        except Exception:
                            continue
                if attempt < retries - 1:
                    time.sleep(wait_time * (attempt + 1))
                else:
                    print(f"[AI Agent] Failed to find element by {by}='{value}'. Error: {e}")
                    raise

    def login(self):
        self.driver.get(self.portal_url)
        self.robust_find(By.ID, "user_username").send_keys(self.user_id)
        self.robust_find(By.ID, "user_subscriber_number").send_keys(self.subscriber)
        self.robust_find(By.ID, "user_password").send_keys(self.password)
        login_btn = self.robust_find(
            By.XPATH,
            "//input[@type='submit' and @name='commit' and @value='Log In']",
            alternatives=[
                (By.XPATH, "//input[@type='submit' and contains(@value, 'Log') and @name='commit']"),
                (By.XPATH, "//button[contains(., 'Log In')]")
            ]
        )
        self.driver.execute_script("arguments[0].scrollIntoView(true);", login_btn)
        try:
            login_btn.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", login_btn)
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    def search_tsl(self):
        search_box = self.robust_find(By.ID, "kw")
        search_box.clear()
        search_box.send_keys(self.tsl_id)
        search_button = self.robust_find(
            By.XPATH,
            "//input[@type='submit' and @value='Search']",
            alternatives=[
                (By.XPATH, "//input[@type='submit' and contains(@value, 'Search')]")
            ]
        )
        search_button.click()
        tsl_link = self.robust_find(
            By.XPATH,
            f"//a[starts-with(normalize-space(text()), '{self.tsl_id}') or contains(normalize-space(text()), '{self.tsl_id}')]",
            alternatives=[
                (By.PARTIAL_LINK_TEXT, self.tsl_id)
            ]
        )
        tsl_link.click()
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    def download_resources(self):
        for label in self.RESOURCE_LABELS:
            try:
                resources_table = self.driver.find_element(
                    By.XPATH,
                    "//td[normalize-space(text())='Resources']/following-sibling::td[1]/table[contains(@class, 'widescreen')]"
                )
                resource_row = resources_table.find_element(
                    By.XPATH,
                    f".//tr[normalize-space(td[1])=\"{label}\"]"
                )
                links = resource_row.find_elements(
                    By.XPATH,
                    ".//td[2]//a[@title='Download']"
                )
                if not links:
                    print(f"No download link found for resource '{label}' (row exists but no file available).")
                    continue
                download_link = links[0]
                file_url = download_link.get_attribute("href")
                self.driver.execute_script("window.open(arguments[0]);", file_url)
                print(f"Download started for resource '{label}' at URL: {file_url}")
                time.sleep(2)
            except Exception as e:
                print(f"Resource '{label}' not found for TSL ID {self.tsl_id}. Error: {e}")

    def run(self):
        try:
            self.setup()
            self.login()
            self.search_tsl()
            self.download_resources()
            print("Download process completed. Check your download directory.")
        finally:
            if self.driver:
                self.driver.quit()

# --- CLI Usability Example ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Agent for TIS Portal downloads.")
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--subscriber", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--tsl-id", required=True, help="Comma-separated TSL IDs.")
    parser.add_argument("--download-dir", default="downloads")
    portal_url = os.environ.get("PORTAL_URL")
    if not portal_url:
        raise ValueError("The environment variable 'PORTAL_URL' must be set.")
    args = parser.parse_args()
    os.makedirs(args.download_dir, exist_ok=True)
    tsl_ids = [tid.strip() for tid in args.tsl_id.split(",") if tid.strip()]
    for tsl_id in tsl_ids:
        tsl_dir = os.path.join(args.download_dir, tsl_id)
        os.makedirs(tsl_dir, exist_ok=True)
        agent = VRSPortalAIAgent(portal_url, args.user_id, args.subscriber, args.password, tsl_id, tsl_dir)
        agent.run()
        print(f"Completed processing for TSL ID: {tsl_id}")

"""
# Use Case Example:
# Automate the download of all resources for given TSL IDs from the Trend Micro TIS portal.
# Usage:
# python agent.py --user-id myuser --subscriber mysub --password mypass --tsl-id TSL20230504-07,TSL20230505-08 --download-dir downloads
"""
