
# 📊 PyZData – Historical Market Data Downloader from Zerodha

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

## 📦 Installation

Install directly from GitHub:

```bash
pip install git+https://github.com/vikassharma545/Historical-Market-data-From-Zerodha.git
```

---

## 🧠 Usage

```python
from pyzdata import PyZData, Interval

# Login
client = PyZData(user_id="your_id", password="your_password", totp=123456)

# Fetch instrument token for NIFTY
token = client.get_instrument_token("NIFTY", "NSE")

# Download 1-minute OHLC + Volume + OI for Jan 2024
df = client.get_data(token, "2024-01-01", "2024-01-31", interval=Interval.MINUTE_1, oi=True)

print(df.head())
```

---

## 📂 Project Structure

```
pyzdata/
│   ├── __init__.py       # Exports the PyZData interface
│   └── pyzdata.py        # Core logic: login, retry, fetch, parse
notebooks/
│   └── Jupyter_file.ipynb  # Example usage with plots (WIP)
setup.py
README.md
LICENSE
```

---

## 🔐 Authentication

This tool logs in using **enctoken** via:
- `user_id`
- `password`
- `TOTP` (Google Authenticator 6-digit)

It **does not use the official Zerodha KiteConnect token**.

---

## 📈 Popularity (Live badges)

- **Repo Stars**: ![Stars](https://img.shields.io/github/stars/vikassharma545/Historical-Market-data-From-Zerodha?style=social)
- **Forks**: ![Forks](https://img.shields.io/github/forks/vikassharma545/Historical-Market-data-From-Zerodha?style=social)
- **Clone Count** (manually track with GitHub Insights or shield.io custom badges)

---

## 👨‍💻 Contributing

Pull requests and issues are welcome!

1. Fork this repo
2. Make your changes
3. Submit a PR

---

## 📝 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙋‍♂️ Author

Developed with ❤️ by [Vikas Sharma](https://github.com/vikassharma545)
