import argparse
import json
import logging
import os
import shutil
import tempfile
import time
from dataclasses import asdict, dataclass
from urllib.parse import quote_plus, urlencode, urlparse

import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


@dataclass
class SearchResult:
    rank: int
    title: str
    snippet: str
    url: str
    domain: str


class SimpleGoogleScraper:
    def __init__(self, timeout: int = 10, lang: str = "en-US"):
        self.timeout = timeout
        self.lang = lang
        self.driver = None
        self.driver_path = None
        self._setup_driver_path()
        self.options = self._configure_chrome_options()

    def _setup_driver_path(self):
        system_driver = shutil.which("chromedriver")
        if system_driver:
            temp_dir = tempfile.mkdtemp(prefix="uc_driver_")
            self.driver_path = os.path.join(temp_dir, "chromedriver")
            shutil.copy2(system_driver, self.driver_path)
            os.chmod(self.driver_path, 0o755)
            logging.info(f"Using chromedriver from: {self.driver_path}")
        else:
            self.driver_path = None
            logging.info("System chromedriver not found, will download if needed")

    def _configure_chrome_options(self):
        opts = uc.ChromeOptions()

        opts.add_argument(f"--lang={self.lang}")

        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument(
            "--user-agent=Mozilla/5.0 (X11; Linux x86_64; rv:146.0) Gecko/20100101 Firefox/146.0"
        )
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-blink-features=AutomationControlled")

        return opts

    def start(self):
        """
        Start the Chrome WebDriver with proper configuration.
        """
        try:
            if self.driver_path:
                self.driver = uc.Chrome(
                    options=self.options,
                    driver_executable_path=self.driver_path,
                    use_subprocess=True,
                )
            else:
                self.driver = uc.Chrome(options=self.options)

            logging.info("WebDriver started successfully")

            if self.driver:
                size = self.driver.get_window_size()
                logging.info(f"Window size: {size['width']}x{size['height']}")

        except Exception as e:
            logging.error(f"Failed to start WebDriver: {e}")
            raise

    def stop(self):
        try:
            if self.driver:
                try:
                    self.driver.quit()
                    logging.info("WebDriver closed successfully")
                except Exception as e:
                    logging.warning(f"Error closing driver: {e}")
        finally:
            self.driver = None

            if self.driver_path and os.path.exists(self.driver_path):
                try:
                    driver_dir = os.path.dirname(self.driver_path)
                    if driver_dir.startswith(tempfile.gettempdir()):
                        shutil.rmtree(driver_dir, ignore_errors=True)
                        logging.debug(f"Cleaned up temp driver dir: {driver_dir}")
                except Exception as e:
                    logging.debug(f"Failed to clean up temp driver: {e}")

    def _direct_search_url(self, query: str) -> str:
        params = {"q": query, "hl": self.lang.split("-")[0]}
        if "-" in self.lang:
            params["gl"] = self.lang.split("-")[-1]
        return (
            f"https://www.google.com/search?{urlencode(params, quote_via=quote_plus)}"
        )

    def search(self, query: str, max_results: int = 10):
        url = self._direct_search_url(query)
        logging.info(f"Searching for: {query}")
        logging.debug(f"URL: {url}")

        self.driver.get(url)

        try:
            consent_btn = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.ID, "L2AGLb"))
            )
            consent_btn.click()
            logging.info("Accepted Google cookies.")
        except TimeoutException:
            logging.warning(
                "Timeout waiting for results. Saved screenshot to timeout_debug.png"
            )
        try:
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div#search, div#rso, div#main")
                )
            )
            logging.info("Search results loaded")
        except TimeoutException:
            logging.warning("Timeout waiting for results, allowing extra time")
            time.sleep(1.5)

        return self.extract_results(max_results=max_results)

    def extract_results(self, max_results: int = 10):
        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        search_root = soup.find("div", id="search") or soup

        candidates = search_root.select("div.MjjYud, div.g")
        logging.debug(f"Found {len(candidates)} candidate result containers")

        results = []
        rank = 1

        for cand in candidates:
            if rank > max_results:
                break

            a = cand.select_one("a")
            h3 = cand.select_one("h3")

            if not a or not h3:
                main = cand.select_one("div.yuRUbf a")
                if main:
                    a = main
                    h3 = main.select_one("h3")

            if not a or not h3:
                continue

            href = a.get("href", "")
            title = h3.get_text(strip=True)

            sn = cand.select_one(".IsZvec, .VwiC3b, span.aCOpRe, .s3v9rd, .st")
            snippet = sn.get_text(" ", strip=True) if sn else ""

            domain = urlparse(href).netloc

            results.append(
                SearchResult(
                    rank=rank, title=title, snippet=snippet, url=href, domain=domain
                )
            )
            rank += 1

        logging.info(f"Extracted {len(results)} search results")
        return results


def configure_logging(debug: bool = False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main():
    parser = argparse.ArgumentParser(
        description="Minimal Google scraper with headless support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search in normal mode
  python scrape_google.py --query "python tutorial" --max 5

  # Debug mode with detailed logging
  python scrape_google.py --query "python tutorial" --headless --debug
        """,
    )
    parser.add_argument("--query", "-q", required=True, help="Search query")
    parser.add_argument(
        "--max", type=int, default=10, help="Maximum results to extract (default: 10)"
    )
    parser.add_argument(
        "--lang", type=str, default="en-US", help="Preferred language (e.g. en-US)"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    configure_logging(debug=args.debug)

    logging.info("Starting Google scraper")
    scraper = SimpleGoogleScraper(timeout=10, lang=args.lang)

    try:
        scraper.start()
        results = scraper.search(args.query, max_results=args.max)

        out = {"results": [asdict(r) for r in results]}
        print(json.dumps(out, ensure_ascii=False, indent=2))

        logging.info(f"Search completed successfully ({len(results)} results)")
    except Exception as e:
        logging.error(f"Search failed: {e}")
        if args.debug:
            import traceback

            traceback.print_exc()
        raise
    finally:
        scraper.stop()


if __name__ == "__main__":
    main()
