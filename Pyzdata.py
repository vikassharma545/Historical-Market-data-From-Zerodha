import pyotp
import datetime
import requests
import pandas as pd
from enum import Enum
from time import sleep


class Interval(Enum):
    """Enumeration for time intervals."""
    MINUTE_1 = 'minute'
    MINUTE_2 = '2minute'
    MINUTE_3 = '3minute'
    MINUTE_4 = '4minute'
    MINUTE_5 = '5minute'
    MINUTE_10 = '10minute'
    MINUTE_15 = '15minute'
    MINUTE_30 = '30minute'
    HOUR_1 = '60minute'
    HOUR_2 = '2hour'
    HOUR_3 = '3hour'
    HOUR_4 = '4hour'
    DAY = 'day'


class PyZData:
    """Client for fetching historical market data from Zerodha Kite API."""

    __ROOT_URL = "https://kite.zerodha.com/oms"
    __MARKET_HISTORICAL_URL = "/instruments/historical/{instrument_token}/{interval}"

    def __init__(self, userid: str, password: str, totp: int):
        """
        Initialize a new PyZData client instance.

        :param userid: Kite user ID
        :param password: Kite password
        :param totp: TOTP for two-factor authentication
        """
        self.__session = requests.Session()
        self.__login_url = "https://kite.zerodha.com/api"

        # Login to the API
        self.__login(userid, password, totp)

        # Load instrument data
        self.instrument_data = pd.read_csv("https://api.kite.trade/instruments")

    def __login(self, userid: str, password: str, totp: int):
        """Handles the login process to the Kite API."""
        data = {"user_id": userid, "password": password}
        response = self.__session.post(f"{self.__login_url}/login", data=data)

        if response.status_code != 200:
            raise Exception("Login failed: " + str(response.json()))

        data = {
            "request_id": response.json()['data']['request_id'],
            "twofa_value": totp,
            "user_id": response.json()['data']['user_id']
        }

        response = self.__session.post(f"{self.__login_url}/twofa", data=data)

        if response.status_code != 200:
            raise Exception("Two-factor authentication failed: " + str(response.json()))

        self.__enctoken = response.cookies.get('enctoken')

        if self.__enctoken is None:
            raise Exception("Invalid login details.")

        self.__header = {"Authorization": f"enctoken {self.__enctoken}"}

    def get_instrument_token(self, tradingsymbol: str, exchange: str) -> int:
        """
        Retrieve the instrument token for a given trading symbol and exchange.

        :param tradingsymbol: The trading symbol of the instrument
        :param exchange: The exchange where the instrument is listed
        :return: The instrument token
        """
        try:
            condition1 = (self.instrument_data['tradingsymbol'] == tradingsymbol)
            condition2 = (self.instrument_data['exchange'] == exchange)
            instrument_token = self.instrument_data[condition1 & condition2]['instrument_token'].iloc[0]
            return instrument_token
        except IndexError:
            raise Exception("Instrument token not found for the given trading symbol and exchange.")

    def __get_trading_symbol(self, instrument_token: int) -> str:
        """
        Retrieve the trading symbol for a given instrument token.

        :param instrument_token: The instrument token
        :return: The trading symbol
        """
        try:
            tradingsymbol = self.instrument_data[self.instrument_data['instrument_token'] == instrument_token]['tradingsymbol'].iloc[0]
            return tradingsymbol
        except IndexError:
            raise Exception("Trading symbol not found for the given instrument token.")

    def get_month_data(self, instrument_token: int, year: int, month: int, interval: Interval, oi: bool = False, print_logs: bool = False) -> pd.DataFrame:
        """
        Retrieve historical data (candles) for an instrument for a specific month.

        :param instrument_token: The instrument identifier
        :param year: The year of data
        :param month: The month of data
        :param interval: The candle interval
        :param oi: Flag to include open interest
        :param print_logs: Flag to print logs after fetching data
        :return: DataFrame containing historical data
        """
        tradingsymbol = self.__get_trading_symbol(instrument_token)

        from_date = pd.to_datetime(f"{year}-{month}-01")
        to_date = pd.to_datetime(f"{year}-{month}-{from_date.days_in_month}")
        to_date2 = to_date + datetime.timedelta(days=5)

        params = {
            "from": from_date.strftime("%Y-%m-%d %H:%M:%S"),
            "to": to_date2.strftime("%Y-%m-%d %H:%M:%S"),
            "oi": int(oi)
        }

        url = f"{self.__ROOT_URL}{self.__MARKET_HISTORICAL_URL.format(instrument_token=instrument_token, interval=interval.value)}"
        response = self.__session.get(url, params=params, headers=self.__header)
        
        if response.ok:
            response = response.json()
            
            if response.get('status') == 'success':
                data = pd.DataFrame(response['data']['candles'])

                if not data.empty:
                    columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
                    if oi:
                        columns.append('open_interest')

                    data.columns = columns
                    data['tradingsymbol'] = tradingsymbol
                    data['datetime'] = pd.to_datetime(data['datetime'])
                    data['datetime'] = data['datetime'].apply(lambda x: pd.Timestamp.combine(x.date(), x.time()))
                    data = data.reindex(columns=['tradingsymbol'] + columns)
                    data = data[(data['datetime'].dt.date >= from_date.date()) & (data['datetime'].dt.date <= to_date.date())]
                    data.drop_duplicates(inplace=True)
                    data.reset_index(drop=True, inplace=True)

                    if print_logs:
                        print(f"{tradingsymbol} data fetched: {from_date.date()} - {to_date.date()}.")

                    return data
        else:
            if print_logs:
                print(f"Could not fetch {tradingsymbol} data: {from_date.date()} - {to_date.date()}.")

        return pd.DataFrame()

    def get_year_data(self, instrument_token: int, year: int, interval: Interval, oi: bool = False, print_logs: bool = False) -> pd.DataFrame:
        """
        Retrieve historical data for an entire year.
        """
        
        monthly_data_list = []
        for month in range(1, 13):
            monthly_data = self.get_month_data(instrument_token, year, month, interval, oi, print_logs)
            monthly_data_list.append(monthly_data)

        # Concatenate all monthly data into a single DataFrame
        data = pd.concat(monthly_data_list, ignore_index=True) if monthly_data_list else pd.DataFrame()
        data.drop_duplicates(inplace=True)

        if print_logs and monthly_data_list:
            print(f"Data for the year {year} fetched successfully.")

        return data

    def download_data_from_year(self, instrument_token: int, from_year: int, interval: Interval, oi: bool = False, print_logs: bool = False) -> pd.DataFrame:
        """
        Download historical data from a specified starting year to the current year.
        """
        
        print('Downloading data...')
        to_year = pd.Timestamp.now().year
        data = pd.DataFrame()

        yearly_data_list = []
        for year in range(from_year, to_year + 1):
            yearly_data = self.get_year_data(instrument_token, year, interval, oi, print_logs)
            yearly_data_list.append(yearly_data)

        data = pd.concat(yearly_data_list, ignore_index=True)
        data.drop_duplicates(inplace=True)
        filename = f"{self.__get_trading_symbol(instrument_token)}_{from_year}_to_{to_year}_{interval.value}.csv"
        data.to_csv(filename, index=False)

        if print_logs:
            print(f"Data downloaded and saved to {filename}")

        return data
