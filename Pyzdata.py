import pyotp
import datetime
import requests
import pandas as pd
from enum import Enum

class interval(Enum):
    
    minute1 = 'minute'
    minute2 = '2minute'
    minute3 = '3minute'
    minute4 = '4minute'
    minute5 = '5minute'
    minute10 = '10minute'
    minute15 = '15minute'
    minute30 = '30minute'
    hour1 = '60minute'
    hour2 = '2hour'
    hour3 = '3hour'
    hour4 = '4hour'
    day = 'day'

class pyzdata:
    
    __root_url = "https://kite.zerodha.com/oms"
    __market_historical_url = "/instruments/historical/{instrument_token}/{interval}"

    def __init__(self, userid:str, password:str, totp:int):
        """
        Initialise a new pykite client instance.

        :param userid: Kite userId
        :param password: kite password
        :param twofa: Totp/PIN/TotpKey
        :param key_type: {'totp','pin','totpkey'}, default 'totp'

        """

        self.__session = requests.session()
        self.__login_url = "https://kite.zerodha.com/api"

        # login
        data = {"user_id": userid, "password": password}
        response = self.__session.post(f"{self.__login_url}/login", data=data)
        if response.status_code != 200:
            raise Exception(response.json())

        data = {
            "request_id": response.json()['data']['request_id'],
            "twofa_value": totp,
            "user_id": response.json()['data']['user_id']
        }

        response = self.__session.post(f"{self.__login_url}/twofa", data=data)

        if response.status_code != 200:
            raise Exception(response.json())

        self.__enctoken = response.cookies.get('enctoken')

        if self.__enctoken is None:
            raise Exception("Invalid detail. !!!")

        self.__header = {"Authorization": f"enctoken {self.__enctoken}"}
        self.interval = interval
        self.instrument_data = pd.read_csv("https://api.kite.trade/instruments")

    def get_instrument_token(self, tradingsymbol:str, exchange:str):

        try:
            condition1 = (self.instrument_data['tradingsymbol'] == tradingsymbol)
            condition2 = (self.instrument_data['exchange'] == exchange)
            instrument_token = self.instrument_data[condition1 & condition2]['instrument_token'].iloc[0]
            return instrument_token
        except:
            raise Exception("instrument token not found !!!")

    def __get_trading_symbol(self, instrument_token:int):
        try:
            tradingsymbol = self.instrument_data[self.instrument_data['instrument_token'] == instrument_token]['tradingsymbol'].iloc[0]
            return tradingsymbol
        except:
            raise Exception("Instrument token not found !!!")


    def get_month_data(self, instrument_token:int, year:int, month:int, interval:interval, oi=False, print_statement=False):

        """
            Retrieve historical data (candles) for an instrument.
            - `instrument_token` is the instrument identifier (retrieved from the kite.instruments) call.
            - `year` is the year of data.
            - `month` is the month of data.
            - `interval` is the candle interval (minute, day, 5 minute etc.).
            - `continuous` is a boolean flag to get continuous data for futures and options instruments.
            - `oi` is a boolean flag to get open interest.
        """

        tradingsymbol = self.__get_trading_symbol(instrument_token)

        from_date = pd.to_datetime(f"{year}-{month}", format="%Y-%m")
        to_date = pd.to_datetime(f"{year}-{month}-{from_date.days_in_month}", format='%Y-%m-%d')

        date_string_format = "%Y-%m-%d %H:%M:%S"
        from_date_string = from_date.strftime(date_string_format)
        to_date_string = to_date.strftime(date_string_format)

        params = {
            "from": from_date_string,
            "to": to_date_string,
            "oi": int(oi)
        }
        
        URL = f"{self.__root_url}{self.__market_historical_url.format(instrument_token=instrument_token, interval=interval.value)}"
        response = self.__session.get(URL, params=params, headers=self.__header).json()

        if response['status'] == 'success':
            data = pd.DataFrame(response['data']['candles'])

            if not data.empty:

                if oi:
                    columns = ['datetime', 'open', 'high', 'low', 'close', 'volume', 'open_interest']
                else:
                    columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']

                data.columns = columns
                data['tradingsymbol'] = tradingsymbol
                data['datetime'] = pd.to_datetime(data['datetime'])
                data['datetime'] = data['datetime'].apply(lambda x: pd.Timestamp.combine(x.date(), x.time()))
                data = data.reindex(columns=['tradingsymbol'] + columns)

                if print_statement:
                    print(f"{tradingsymbol} data from {str(from_date)[:10]} to {str(to_date)[:10]} Fetched :)")

                return data

        else:
            return pd.DataFrame()

    def get_year_data(self, instrument_token:int, year:int, interval:interval, continuous=False, oi=False, print_statement=False):
        data = pd.DataFrame()

        for month in range(1, 13):
            monthly_data = self.get_month_data(instrument_token, year, month, interval, oi, print_statement)
            data = pd.concat([data, monthly_data], ignore_index=True)

        return data

    def download_data_from_year(self, instrument_token:int, from_year:int, interval:interval, oi=False, print_statement=False):
        print('Downloading...')
        to_year, data = pd.Timestamp.now().year, pd.DataFrame()

        for year in range(from_year, to_year + 1):
            year_data = self.get_year_data(instrument_token, year, interval, oi, print_statement)
            data = pd.concat([data, year_data], ignore_index=True)

        data.sort_values(by=['datetime'], inplace=True)
        data.drop_duplicates(inplace=True)
        data = data[data['datetime'] < pd.Timestamp.combine(pd.Timestamp.now().date(), datetime.time(15, 30))]
        data.to_csv(f'{self.__get_trading_symbol(instrument_token)} {from_year} to {to_year}.csv', index=False)

        return data
