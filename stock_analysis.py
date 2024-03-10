import glob
import os
import time
import logging
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

if __name__ == '__main__':
    try:
        current_directory = os.getcwd()
        download_directory = os.path.join(current_directory, 'download_directory')
        think_time = 60
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
            logging.info('reading stock_tickers.csv')
        except Exception as e:
            logging.info(f"Error reading stock tickers: {e}")
            exit(1)

        stock_tickers = stock_tickers_df['Ticker'].tolist()

        with open('results.txt', 'w') as f:
            pass

        with open('results.txt', 'a') as results_file:
            for ticker in stock_tickers:
                try:
                    browser = webdriver.Chrome(options=options)
                    browser.implicitly_wait(think_time)
                    browser.set_page_load_timeout(think_time)
                    logging.info(
                        f"window resolution: {browser.get_window_size()['width']}x{browser.get_window_size()['height']}")

                    browser.get(f"https://www.nasdaq.com/market-activity/stocks/{ticker}/historical")
                    logging.info(f'page title {browser.title}')

                    one_year_filter = WebDriverWait(browser, think_time).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'1Y')]"))
                    )
                    one_year_filter.click()
                    logging.info('one_year_filter clicked')

                    download_data = WebDriverWait(browser, think_time).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='DOWNLOAD DATA']"))
                    )
                    download_data.click()
                    logging.info('download_data clicked')

                    time.sleep(1)
                except Exception as e:
                    logging.info(f"Error processing {ticker}: {e}")
                finally:
                    browser.quit()
                    logging.info('browser closed')

                try:
                    file_path = glob.glob(f'{download_directory}/HistoricalData_*.csv')[0]
                    logging.info(f'searching for csv file in {download_directory}')
                    df = pd.read_csv(file_path, usecols=['Date', 'Close/Last'])
                    logging.info(f'reading csv file in {file_path}')

                    df['Date'] = pd.to_datetime(df['Date'])
                    df['Close/Last'] = df['Close/Last'].replace('[\$,]', '', regex=True).astype(float)

                    ema_span = 20
                    df['EMA'] = df['Close/Last'].ewm(span=ema_span, adjust=False).mean()

                    latest_close = df.iloc[-1]['Close/Last']
                    latest_ema = df.iloc[-1]['EMA']

                    valuation = 'undervalued' if latest_close < latest_ema else 'overvalued'
                    result_string = f"{ticker}: The stock is currently {valuation}. Close: {latest_close:.2f}, EMA: {latest_ema:.2f}\n"
                    logging.info(
                        f"{ticker}: The stock is currently {valuation}. Close: {latest_close:.2f}, EMA: {latest_ema:.2f}")

                    results_file.write(result_string)
                    logging.info(f'written result_string to results.txt')

                    os.remove(file_path)
                    logging.info(f"Processed and removed file: {file_path}")
                except Exception as e:
                    logging.info(f"Error post-processing {ticker}: {e}")

        logging.info(f"All stock valuations have been saved to {'results.txt'}")
    except Exception as e:
        logging.info(f"Critical error occurred: {e}")
