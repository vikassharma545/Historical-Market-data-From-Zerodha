
# 📊 PyZData – Market Data Downloader from Zerodha

![GitHub repo size](https://img.shields.io/github/repo-size/vikassharma545/Historical-Market-data-From-Zerodha)
![GitHub last commit](https://img.shields.io/github/last-commit/vikassharma545/Historical-Market-data-From-Zerodha)
![GitHub issues](https://img.shields.io/github/issues/vikassharma545/Historical-Market-data-From-Zerodha)
![GitHub pull requests](https://img.shields.io/github/issues-pr/vikassharma545/Historical-Market-data-From-Zerodha)
![GitHub forks](https://img.shields.io/github/forks/vikassharma545/Historical-Market-data-From-Zerodha?style=social)
![GitHub stars](https://img.shields.io/github/stars/vikassharma545/Historical-Market-data-From-Zerodha?style=social)

> 💼 A lightweight, robust Python client to download **historical OHLC and Open Interest data** from Zerodha using login credentials and TOTP. Built with retry logic, efficient pagination, and developer-friendly design.

---

## 🚀 Features

- ✅ Fetch historical **1-minute to daily** data
- ✅ Supports **Open Interest (OI)** toggle
- ✅ Auto handles Zerodha login using **user_id + password + TOTP**
- ✅ Easy token lookup via symbol/exchange
- ✅ Efficient data download month-by-month
- ✅ Clean Pandas DataFrame output ready for ML/backtesting

---

## 🖥️ PyZData EXE for Non-Programmers

For non-programming users, a simple and clean Windows `.exe` GUI is available for easy data downloading:

### 🔐 Login Screen
![Login GUI](/assets/login.png)

### 📅 Download Screen
![Download GUI](/assets/download.png)

> Just open the executable and log in with your Zerodha credentials. Select your symbol, date range, and interval — and click **Download Data**.

---

## 📦 Installation

Install directly from GitHub:

```bash
pip install git+https://github.com/vikassharma545/Historical-Market-data-From-Zerodha.git
```

---

## 🧠 Usage

```python
from pyzdata import PyZData, Interval

# Option 1: Login using credentials
client = PyZData(user_id="your_id", password="your_password", totp=123456)

# Option 2: Login using enctoken
# client = PyZData(enctoken="your_enctoken")

# Fetch instrument token for NIFTY
token = client.get_instrument_token("NIFTY 50", "NSE")

# Download 1-minute OHLC + Volume + OI for Jan 2024
df = client.get_data(token, "2024-01-01", "2024-01-31", interval=Interval.MINUTE_1, oi=True, print_logs=True)

print(df.head())
```

---

## 📝 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙋‍♂️ Author

Developed with ❤️ by [Vikas Sharma](https://github.com/vikassharma545)
