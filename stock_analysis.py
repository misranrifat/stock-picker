import glob
import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

if __name__ == '__main__':

    current_directory = os.getcwd()
    download_directory = os.path.join(current_directory, 'download_directory')
    think_time = 60

    options = ChromeOptions()
    options.add_argument("--disable-blink-features")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--log-level=3")

    prefs = {
        "download.default_directory": download_directory,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)

    stock_tickers_df = pd.read_csv('stock_tickers.csv')
    stock_tickers = stock_tickers_df['Ticker'].tolist()

    with open('results.txt', 'w') as f:
        pass

    with open('results.txt', 'a') as results_file:
        for ticker in stock_tickers:
            browser = webdriver.Chrome(options=options)
            browser.implicitly_wait(think_time)
            browser.set_page_load_timeout(think_time)

            browser.get(f"https://www.nasdaq.com/market-activity/stocks/{ticker}/historical")

            one_year_filter = WebDriverWait(browser, think_time).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'1Y')]"))
            )
            one_year_filter.click()

            download_data = WebDriverWait(browser, think_time).until(
                EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='DOWNLOAD DATA']"))
            )
            download_data.click()

            time.sleep(1)
            browser.quit()

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

            results_file.write(result_string)

            os.remove(file_path)
            print(f"Processed and removed file: {file_path}")

    print(f"All stock valuations have been saved to {'results.txt'}")
