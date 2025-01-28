import glob
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tenacity import retry, stop_after_attempt, wait_exponential


class Config:
    """Configuration class for stock analysis."""

    BASE_URL = "https://www.nasdaq.com/market-activity/stocks"
    THINK_TIME = 60
    EMA_SPAN = 20
    MAX_RETRIES = 3

    def __init__(self):
        self.current_directory = Path.cwd()
        self.download_directory = self.current_directory / "download_directory"
        self.results_file = self.current_directory / "results.txt"
        self.stock_tickers_file = self.current_directory / "stock_tickers.csv"

        # Create necessary directories
        self.download_directory.mkdir(exist_ok=True)


class ChromeDriverManager:
    """Manages Chrome WebDriver setup and configuration."""

    @staticmethod
    def get_chrome_options(download_directory: Path) -> ChromeOptions:
        options = ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("window-size=2560x1440")
        options.add_argument("--disable-blink-features")

        # Enable headless mode
        options.add_argument("--headless=new")

        # Fix WebGL errors
        options.add_argument("--enable-unsafe-swiftshader")
        options.add_argument("--ignore-gpu-blocklist")

        # Fix SSL errors
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--ignore-ssl-errors")
        options.add_argument("--allow-insecure-localhost")

        # Automation Detection Mitigation
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
        )

        options.add_argument("--verbose")
        prefs = {
            "download.default_directory": str(download_directory),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        }
        options.add_experimental_option("prefs", prefs)
        return options


class StockAnalyzer:
    """Main class for analyzing stock data."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.results_queue = queue.Queue()  # Thread-safe queue for results

    def clean_download_directory(self) -> None:
        """Clean all files in the download directory."""
        try:
            for file in self.config.download_directory.glob("*"):
                file.unlink()
                self.logger.info(f"Deleted {file}")
        except Exception as e:
            self.logger.error(f"Error cleaning download directory: {e}")
            raise

    def load_stock_tickers(self) -> List[str]:
        """Load stock tickers from CSV file."""
        try:
            stock_tickers_df = pd.read_csv(self.config.stock_tickers_file)
            return stock_tickers_df["Ticker"].tolist()
        except Exception as e:
            self.logger.error(f"Error reading stock tickers: {e}")
            raise

    def clean_screenshots(self) -> None:
        """Clean existing screenshots."""
        # Remove this method as it's no longer needed
        pass

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def process_stock_data(
        self, ticker: str, browser: webdriver.Chrome
    ) -> Optional[str]:
        """Process stock data for a given ticker with retry mechanism."""
        try:
            url = urljoin(f"{Config.BASE_URL}/", f"{ticker}/historical")
            browser.get(url)
            self.logger.info(f"Opening {browser.current_url}")

            # Click 1Y filter
            one_year_filter = WebDriverWait(browser, Config.THINK_TIME).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(),'1Y')]")
                )
            )
            one_year_filter.click()

            # Download data
            download_data = WebDriverWait(browser, Config.THINK_TIME).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//span[contains(text(),'Download')]")
                )
            )
            download_data.click()
            time.sleep(1)

            return self.analyze_downloaded_data(ticker)

        except TimeoutException:
            self.logger.error(f"Timeout waiting for elements for {ticker}")
            raise
        except Exception as e:
            self.logger.error(f"Error processing {ticker}: {e}")
            raise

    def analyze_downloaded_data(self, ticker: str) -> Optional[str]:
        """Analyze downloaded stock data."""
        try:
            file_path = next(
                self.config.download_directory.glob("HistoricalData_*.csv")
            )
            df = pd.read_csv(file_path, usecols=["Date", "Close/Last"])
            df["Date"] = pd.to_datetime(df["Date"])
            df["Close/Last"] = (
                df["Close/Last"].replace(r"[\$,]", "", regex=True).astype(float)
            )

            # Calculate EMA
            df["EMA"] = df["Close/Last"].ewm(span=Config.EMA_SPAN, adjust=False).mean()

            latest_close = df.iloc[0]["Close/Last"]
            latest_ema = df.iloc[-1]["EMA"]
            valuation = "undervalued" if latest_close < latest_ema else "overvalued"

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result = f"{ticker}: The stock is currently {valuation}. Close: {latest_close:.2f}, EMA: {latest_ema:.2f} ({timestamp})\n\n"

            file_path.unlink()
            return result
        except Exception as e:
            self.logger.error(f"Error analyzing data for {ticker}: {e}")
            return None

    def process_single_stock(self, ticker: str) -> None:
        """Process a single stock with its own browser instance."""
        chrome_options = ChromeDriverManager.get_chrome_options(
            self.config.download_directory
        )
        browser = None
        try:
            browser = webdriver.Chrome(options=chrome_options)
            self.logger.info(f"Starting processing for {ticker}")

            result = self.process_stock_data(ticker, browser)
            if result:
                self.results_queue.put(result)

        finally:
            if browser:
                browser.quit()
                self.logger.info(f"Browser closed for {ticker}")

    def run_analysis(self):
        """Main method to run the stock analysis with multithreading."""
        # Clean download directory before starting
        self.clean_download_directory()

        stock_tickers = self.load_stock_tickers()
        total_stocks = len(stock_tickers)

        # Clear results file
        self.config.results_file.write_text("")

        # Use ThreadPoolExecutor to process stocks concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Submit all tasks
            future_to_ticker = {
                executor.submit(self.process_single_stock, ticker): ticker
                for ticker in stock_tickers
            }

            # Show progress for completed tasks
            completed = 0
            self.logger.info(f"Starting analysis of {total_stocks} stocks...")

            for future in as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    future.result()  # This will raise any exceptions that occurred
                    completed += 1
                    if (
                        completed % 5 == 0 or completed == total_stocks
                    ):  # Log every 5 stocks or at completion
                        self.logger.info(
                            f"Progress: {completed}/{total_stocks} stocks processed ({(completed/total_stocks)*100:.1f}%)"
                        )
                except Exception as e:
                    self.logger.error(f"Error processing {ticker}: {e}")
                    completed += 1

            # Write all results from queue to file
            with open(self.config.results_file, "a") as f:
                while not self.results_queue.empty():
                    f.write(self.results_queue.get())


def main():
    """Main entry point of the script."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    try:
        start_time = time.time()
        config = Config()
        analyzer = StockAnalyzer(config)
        analyzer.run_analysis()

        # Calculate execution time
        execution_time = time.time() - start_time
        minutes = int(execution_time // 60)
        seconds = int(execution_time % 60)

        logging.info("All stock valuations have been saved to results.txt")
        logging.info(f"Total execution time: {minutes} minutes and {seconds} seconds")
    except Exception as e:
        logging.error(f"Fatal error in main execution: {e}")
        raise


if __name__ == "__main__":
    main()
