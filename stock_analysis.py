import glob
import os
import platform
import subprocess
import time
import logging
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_chromedriver_path():
    system_os = platform.system()
    script_directory = os.path.dirname(os.path.realpath(__file__))
    if system_os == "Linux":
        logging.info(f'Operating system is {system_os}')
        return os.path.join(script_directory, "chromedriver", "chromedriver-linux64", "chromedriver")
    elif system_os == "Windows":
        logging.info(f'Operating system is {system_os}')
        return os.path.join(script_directory, "chromedriver", "chromedriver-win64", "chromedriver.exe")
    elif system_os == "Darwin":
        logging.info(f'Operating system is {system_os}')
        return os.path.join(script_directory, "chromedriver", "chromedriver-mac-arm64", "chromedriver")
    else:
        raise ValueError("Unsupported operating system.")


def log_chromedriver_version(driver_path):
    try:
        result = subprocess.run([driver_path, '--version'], capture_output=True, text=True)
        version_info = result.stdout.strip()
        logging.info(f"ChromeDriver version: {version_info}")
    except Exception as e:
        logging.error(f"Failed to log ChromeDriver version: {e}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    current_directory = os.getcwd()
    download_directory = os.path.join(current_directory, 'download_directory')
    think_time = 60

    options = ChromeOptions()
    options.add_argument("--disable-blink-features")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--log-level=3")
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument('window-size=2560x1440')
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    options.add_argument('--disable-gpu')
    prefs = {
        "download.default_directory": download_directory,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)

    try:
        stock_tickers_df = pd.read_csv('stock_tickers.csv')
        stock_tickers = stock_tickers_df['Ticker'].tolist()
    except Exception as e:
        logging.error(f"Error reading stock tickers: {e}")
        exit(1)

    chromedriver_path = get_chromedriver_path()
    service = ChromeService(executable_path=chromedriver_path)
    log_chromedriver_version(chromedriver_path)

    with open('results.txt', 'w') as f:
        pass

    for ticker in stock_tickers:
        browser = None
        try:
            browser = webdriver.Chrome(service=service, options=options)
            logging.info(f"Starting processing for {ticker}")

            browser.get(f"https://www.nasdaq.com/market-activity/stocks/{ticker}/historical")
            logging.info(f"Opening {browser.current_url}")

            one_year_filter = WebDriverWait(browser, think_time).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'1Y')]"))
            )
            one_year_filter.click()

            download_data = WebDriverWait(browser, think_time).until(
                EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='DOWNLOAD DATA']"))
            )
            download_data.click()

            time.sleep(1)
            logging.info(f"Data downloaded for {ticker}")
        except Exception as e:
            logging.error(f"Error processing {ticker}: {e}")
        finally:
            if browser:
                browser.quit()
                logging.info(f'Browser closed')

        try:
            file_path = glob.glob(f'{download_directory}/HistoricalData_*.csv')[0]
            df = pd.read_csv(file_path, usecols=['Date', 'Close/Last'])
            df['Date'] = pd.to_datetime(df['Date'])
            df['Close/Last'] = df['Close/Last'].replace('[\$,]', '', regex=True).astype(float)

            ema_span = 20
            df['EMA'] = df['Close/Last'].ewm(span=ema_span, adjust=False).mean()

            latest_close = df.iloc[-1]['Close/Last']
            latest_ema = df.iloc[-1]['EMA']
            valuation = 'undervalued' if latest_close < latest_ema else 'overvalued'
            result_string = f"{ticker}: The stock is currently {valuation}. Close: {latest_close:.2f}, EMA: {latest_ema:.2f}\n"

            with open('results.txt', 'a') as results_file:
                results_file.write(result_string)

            os.remove(file_path)
            logging.info(f"Processed and removed file for {ticker}")
        except Exception as e:
            logging.error(f"Error post-processing {ticker}: {e}")

    logging.info("All stock valuations have been saved to results.txt")
