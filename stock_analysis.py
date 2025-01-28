import glob
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from urllib.parse import urljoin

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tenacity import retry, stop_after_attempt, wait_exponential
from tqdm import tqdm

class Config:
    """Configuration class for stock analysis."""
    BASE_URL = "https://www.nasdaq.com/market-activity/stocks"
    THINK_TIME = 60
    EMA_SPAN = 20
    MAX_RETRIES = 3
    
    def __init__(self):
        self.current_directory = Path.cwd()
        self.download_directory = self.current_directory / 'download_directory'
        self.screenshots_dir = self.current_directory / 'screen_shots'
        self.results_file = self.current_directory / 'results.txt'
        self.stock_tickers_file = self.current_directory / 'stock_tickers.csv'
        
        # Create necessary directories
        self.download_directory.mkdir(exist_ok=True)
        self.screenshots_dir.mkdir(exist_ok=True)

class ChromeDriverManager:
    """Manages Chrome WebDriver setup and configuration."""
    
    @staticmethod
    def get_chrome_options(download_directory: Path) -> ChromeOptions:
        options = ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_argument("--no-sandbox")
        options.add_argument('--disable-gpu')
        options.add_argument('window-size=2560x1440')
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
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
        
        options.add_argument("--verbose")
        prefs = {
            "download.default_directory": str(download_directory),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        options.add_experimental_option("prefs", prefs)
        return options

class StockAnalyzer:
    """Main class for analyzing stock data."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def load_stock_tickers(self) -> List[str]:
        """Load stock tickers from CSV file."""
        try:
            stock_tickers_df = pd.read_csv(self.config.stock_tickers_file)
            return stock_tickers_df['Ticker'].tolist()
        except Exception as e:
            self.logger.error(f"Error reading stock tickers: {e}")
            raise
    
    def clean_screenshots(self) -> None:
        """Clean existing screenshots."""
        try:
            for file in self.config.screenshots_dir.glob('*'):
                file.unlink()
                self.logger.info(f"Deleted {file}")
        except Exception as e:
            self.logger.error(f"Error cleaning screenshots: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def process_stock_data(self, ticker: str, browser: webdriver.Chrome) -> Optional[str]:
        """Process stock data for a given ticker with retry mechanism."""
        try:
            url = urljoin(f"{Config.BASE_URL}/", f"{ticker}/historical")
            browser.get(url)
            self.logger.info(f"Opening {browser.current_url}")
            
            # Take screenshot
            screenshot_path = self.config.screenshots_dir / f"{ticker}_screenshot.png"
            browser.save_screenshot(str(screenshot_path))
            self.logger.info(f"Screenshot saved at {screenshot_path}")
            
            # Click 1Y filter
            one_year_filter = WebDriverWait(browser, Config.THINK_TIME).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'1Y')]"))
            )
            one_year_filter.click()
            
            # Download data
            download_data = WebDriverWait(browser, Config.THINK_TIME).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Download')]"))
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
            file_path = next(self.config.download_directory.glob('HistoricalData_*.csv'))
            df = pd.read_csv(file_path, usecols=['Date', 'Close/Last'])
            df['Date'] = pd.to_datetime(df['Date'])
            df['Close/Last'] = df['Close/Last'].replace(r'[\$,]', '', regex=True).astype(float)
            
            # Calculate EMA
            df['EMA'] = df['Close/Last'].ewm(span=Config.EMA_SPAN, adjust=False).mean()
            
            latest_close = df.iloc[-1]['Close/Last']
            latest_ema = df.iloc[-1]['EMA']
            valuation = 'undervalued' if latest_close < latest_ema else 'overvalued'
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result = f"{ticker}: The stock is currently {valuation}. Close: {latest_close:.2f}, EMA: {latest_ema:.2f} ({timestamp})\n\n"
            
            file_path.unlink()
            return result
        except Exception as e:
            self.logger.error(f"Error analyzing data for {ticker}: {e}")
            return None

    def run_analysis(self):
        """Main method to run the stock analysis."""
        stock_tickers = self.load_stock_tickers()
        self.clean_screenshots()
        
        # Clear results file
        self.config.results_file.write_text('')
        
        chrome_options = ChromeDriverManager.get_chrome_options(self.config.download_directory)
        
        for ticker in tqdm(stock_tickers):
            browser = None
            try:
                browser = webdriver.Chrome(options=chrome_options)
                self.logger.info(f"Starting processing for {ticker}")
                
                result = self.process_stock_data(ticker, browser)
                if result:
                    with open(self.config.results_file, 'a') as f:
                        f.write(result)
                
            finally:
                if browser:
                    browser.quit()
                    self.logger.info('Browser closed')

def main():
    """Main entry point of the script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        config = Config()
        analyzer = StockAnalyzer(config)
        analyzer.run_analysis()
        logging.info("All stock valuations have been saved to results.txt")
    except Exception as e:
        logging.error(f"Fatal error in main execution: {e}")
        raise

if __name__ == '__main__':
    main()