"""
AI Agent for Trend Micro TIS Portal Automation
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

class TISPortalAIAgent:
    """
    AI Agent for automating Trend Micro TIS portal tasks.
    Use Case: Downloading resources after login and search.
    """
    RESOURCE_LABELS = [
        "Vulnerability Report PDF",
        "Vulnerability Baseline PCAP",
        "Vulnerability Attack PCAP"
    ]

    def __init__(self, user_id, subscriber, password, tsl_id, download_dir):
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

    def login(self):
        """Automate login using robust waits and direct selectors."""
        self.driver.get("https://tisportal.trendmicro.com/")
        self.wait.until(EC.presence_of_element_located((By.ID, "user_username"))).send_keys(self.user_id)
        self.wait.until(EC.presence_of_element_located((By.ID, "user_subscriber_number"))).send_keys(self.subscriber)
        self.wait.until(EC.presence_of_element_located((By.ID, "user_password"))).send_keys(self.password)
        login_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and @name='commit' and @value='Log In']")))
        self.driver.execute_script("arguments[0].scrollIntoView(true);", login_btn)
        try:
            login_btn.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", login_btn)
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    def search_tsl(self):
        """Search for the TSL ID and navigate to its details page."""
        search_box = self.wait.until(EC.presence_of_element_located((By.ID, "kw")))
        search_box.clear()
        search_box.send_keys(self.tsl_id)
        search_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and @value='Search']")))
        search_button.click()
        tsl_link = self.wait.until(EC.element_to_be_clickable((By.XPATH, f"//a[starts-with(normalize-space(text()), '{self.tsl_id}') or contains(normalize-space(text()), '{self.tsl_id}')]")))
        tsl_link.click()
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    def download_resources(self):
        """Download all required resources from the TSL details page."""
        for label in self.RESOURCE_LABELS:
            try:
                # Find the <tr> whose first <td> matches the label
                resource_row = self.driver.find_element(
                    By.XPATH,
                    f"//table[contains(@class, 'widescreen')]//tr[td[1][contains(normalize-space(), '{label}')]]"
                )
                # Find the download link in the second <td>
                download_link = resource_row.find_element(
                    By.XPATH,
                    ".//td[2]//a[@title='Download']"
                )
                file_url = download_link.get_attribute("href")
                self.driver.execute_script("window.open(arguments[0]);", file_url)
                print(f"Download started for resource '{label}' at URL: {file_url}")
                time.sleep(2)
            except Exception as e:
                print(f"Resource '{label}' not found for TSL ID {self.tsl_id}. Error: {e}")

    def run(self):
        """Run the full agent workflow."""
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
    parser.add_argument("--tsl-id", required=True)
    parser.add_argument("--download-dir", default="downloads")
    args = parser.parse_args()
    os.makedirs(args.download_dir, exist_ok=True)
    agent = TISPortalAIAgent(args.user_id, args.subscriber, args.password, args.tsl_id, args.download_dir)
    agent.run()

"""
# Use Case Example:
# Automate the download of all resources for a given TSL ID from the Trend Micro TIS portal.
# Usage:
# python agent.py --user-id myuser --subscriber mysub --password mypass --tsl-id TSL20230504-07 --download-dir downloads
"""
