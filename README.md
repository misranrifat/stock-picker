# Stock Analysis Tool

![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![Selenium](https://img.shields.io/badge/Selenium-Automation-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

Automate the analysis of stock data with our Python-based tool. This project leverages Selenium to scrape historical stock prices from NASDAQ, evaluates them against Exponential Moving Averages (EMAs), and determines stock valuation. The tool uses multithreading to process multiple stocks concurrently for improved performance.

## Table of Contents
- [Description](#description)
- [Getting Started](#getting-started)
  - [Dependencies](#dependencies)
  - [Installing](#installing)
  - [Setup](#setup)
- [Usage](#usage)
- [Features](#features)

## Description

The Stock Analysis Tool is designed for investors and financial analysts to quickly and accurately assess stock valuations. By calculating the 20-day EMA, users can identify whether stocks are currently undervalued or overvalued. The tool processes multiple stocks concurrently, making it efficient for analyzing large portfolios.

## Getting Started

### Dependencies
- Python 3.x
- Chrome browser and ChromeDriver
- Required Python packages:
  - pandas
  - selenium
  - requests
  - tenacity
  - fake-useragent
  - undetected-chromedriver

### Installing

1. Install the required packages:
```bash
pip install -r requirements.txt
```

### Setup

1. Prepare your stock tickers file:
   - Create a CSV file named `stock_tickers.csv`
   - Include a column named "Ticker" with the stock symbols you want to analyze

2. Ensure Chrome browser is installed on your system

## Usage

1. Run the analysis:
```bash
python stock_analysis.py
```

2. The script will:
   - Process multiple stocks concurrently (10 stocks at a time by default)
   - Download historical data for each stock
   - Calculate 20-day EMAs
   - Determine if each stock is overvalued or undervalued
   - Save results to `results.txt`

## Features

- Concurrent processing of multiple stocks
- Automated web scraping with retry mechanism
- EMA-based stock valuation
- Anti-detection measures for web scraping
