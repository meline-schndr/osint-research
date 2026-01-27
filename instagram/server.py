import time

import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from minimal_server import minimal_server
from selenium.webdriver.common.by import By


class GetResults:
    def __init__(self):
        self.options = uc.ChromeOptions()

        self.options.add_argument("--headless=new")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-gpu")

        self.options.add_argument(
            "--user-agent=Mozilla/5.0 (X11; Linux x86_64; rv:146.0) Gecko/20100101 Firefox/146.0"
        )

        self.options.add_argument("--window-size=1920,1080")

        self.options.add_argument(
            "--no-first-run --no-service-autorun --password-store=basic"
        )
        self.options.add_argument("--disable-blink-features=AutomationControlled")

        self.driver = None

    def open_google(self):
        self.driver.get("https://www.google.com")
        time.sleep(5)
        self.accept_cookies()

    def accept_cookies(self):
        try:
            time.sleep(2)
            consent_button = self.driver.find_element(By.ID, "L2AGLb")
            consent_button.click()
        except:
            print("Consent button not found or already accepted.")

    def search_query(self, query="zumba"):
        search_box = self.driver.find_element(By.ID, "APjFqb")
        search_box.click()
        for char in query:
            search_box.send_keys(char)
            time.sleep(0.3)

        time.sleep(1)
        try:
            search_button = self.driver.find_element(
                By.NAME, "btnK"
            search_button.click()
        except:
            try:
                search_button = self.driver.find_element(By.CLASS_NAME, "gNO89b")
                search_button.click()
            except:
                print("Search button not found.")
        time.sleep(3)

    def extract_results(self):
        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        search_div = soup.find("div", id="search")

        if not search_div:
            print("Kein <div id='search'> gefunden.")
            return []

        results_tab = []
        results = search_div.select("div.MjjYud, div.g")
        for result in results:
            if result.find("div", class_="yuRUbf") or result.find("h3"):
                h3 = result.find("h3")
                span = result.select_one(".VwiC3b, .st, span")
                a = result.find("a")

                title = h3.get_text(strip=True) if h3 else "—"
                snippet = span.get_text(strip=True) if span else "—"
                link = a["href"] if a and a.has_attr("href") else "—"

                results_tab.append([title, snippet, link])

        return results_tab

    def run(self):
        self.driver = uc.Chrome(options=self.options)
        try:
            self.open_google()
            self.search_query("zumba")
            tab = self.extract_results()
        finally:
            self.driver.quit()
        return tab


if __name__ == "__main__":
    obj = GetResults()
    minimal_server(obj, host="localhost", port=4444)
