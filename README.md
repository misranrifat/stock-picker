# Stock Analysis Tool

![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![Selenium](https://img.shields.io/badge/Selenium-Automation-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

Automate the analysis of stock data with our Python-based tool. This project leverages Selenium to scrape historical stock prices from NASDAQ, evaluates them against Exponential Moving Averages (EMAs), and determines stock valuation.

## Table of Contents
- [Description](#description)
- [Getting Started](#getting-started)
  - [Dependencies](#dependencies)
  - [Installing](#installing)
  - [Setup](#setup)
- [Usage](#usage)
- [Features](#features)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Description

The Stock Analysis Tool is designed for investors and financial analysts to quickly and accurately assess stock valuations. By calculating the 20-day EMA, users can identify whether stocks are currently undervalued or overvalued.

## Getting Started

### Dependencies
- Python 3.x
- Pandas for data manipulation
- Selenium for web scraping
- Chrome WebDriver for Selenium

### Installing
First, make sure Python and pip are installed. Then, install the necessary Python packages:
```bash
pip install pandas selenium
