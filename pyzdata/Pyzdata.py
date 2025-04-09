import requests
import datetime
import pandas as pd
from enum import Enum
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

class Interval(Enum):
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
    
    ROOT_URL = "https://kite.zerodha.com/oms"
    LOGIN_URL = "https://kite.zerodha.com/api/login"
    TWOFA_URL = "https://kite.zerodha.com/api/twofa"
    INSTRUMENTS_URL = "https://api.kite.trade/instruments"
    HISTORICAL_ENDPOINT = "/instruments/historical/{instrument_token}/{interval}"

    def __init__(self, user_id: str, password: str, totp: int):
        
        self.session = requests.Session()
        self._init_retry_strategy()
        self._login(user_id, password, totp)
        self.instrument_data = self._load_instrument_data()
        
    def _init_retry_strategy(self):
        retry_strategy = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _login(self, user_id: str, password: str, totp: int):
        
        response = self.session.post(self.LOGIN_URL, data={"user_id": user_id, "password": password})
        response.raise_for_status()

        data = response.json()['data']
        twofa_data = {
            "request_id": data['request_id'],
            "twofa_value": totp,
            "user_id": data['user_id']
        }

        response = self.session.post(self.TWOFA_URL, data=twofa_data)
        response.raise_for_status()

        enctoken = response.cookies.get('enctoken')
        if not enctoken:
            raise ValueError("Login failed: enctoken not found.")

        self.headers = {"Authorization": f"enctoken {enctoken}"}
        print(f"\n✅ Logged in successfully\n")
        
    def _load_instrument_data(self) -> pd.DataFrame:
        print("Loading instrument data from", self.INSTRUMENTS_URL)
        return pd.read_csv(self.INSTRUMENTS_URL)

    def get_instrument_token(self, tradingsymbol: str, exchange: str) -> int:
        
        condition = (
            (self.instrument_data['tradingsymbol'] == tradingsymbol) &
            (self.instrument_data['exchange'] == exchange)
        )
        result = self.instrument_data[condition]
        if result.empty:
            raise ValueError("Instrument token not found for the given symbol and exchange.")
        return int(result.iloc[0]['instrument_token'])

    def _get_trading_symbol(self, instrument_token: int) -> str:
        result = self.instrument_data[self.instrument_data['instrument_token'] == instrument_token]
        if result.empty:
            raise ValueError("Trading symbol not found for the given instrument token.")
        return result.iloc[0]['tradingsymbol']

    def _get_month_data(self, instrument_token: int, year: int, month: int, interval: Interval, oi: bool = False, print_logs: bool = False) -> pd.DataFrame:
        
        tradingsymbol = self._get_trading_symbol(instrument_token)
        from_date = pd.to_datetime(f"{year}-{month}-01")
        to_date = pd.to_datetime(f"{year}-{month}-{from_date.days_in_month}")
        to_date_extended = to_date + datetime.timedelta(days=5)

        params = {
            "from": from_date.strftime("%Y-%m-%d %H:%M:%S"),
            "to": to_date_extended.strftime("%Y-%m-%d %H:%M:%S"),
            "oi": int(oi)
        }

        url = f"{self.ROOT_URL}{self.HISTORICAL_ENDPOINT.format(instrument_token=instrument_token, interval=interval.value)}"
        response = self.session.get(url, params=params, headers=self.headers)

        if response.ok:
            response_json = response.json()
            if response_json.get('status') == 'success':
                data = pd.DataFrame(response_json['data']['candles'])
                if not data.empty:
                    columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
                    if oi:
                        columns.append('open_interest')
                    data.columns = columns
                    data['tradingsymbol'] = tradingsymbol
                    data['datetime'] = pd.to_datetime(data['datetime'])
                    data['datetime'] = data['datetime'].apply(lambda x: pd.Timestamp.combine(x.date(), x.time()))
                    data = data[['tradingsymbol'] + columns]
                    data = data[(data['datetime'].dt.date >= from_date.date()) & (data['datetime'].dt.date <= to_date.date())]
                    data.drop_duplicates(inplace=True)
                    data.reset_index(drop=True, inplace=True)

                    if print_logs:
                        print(f"{tradingsymbol} data fetched: {from_date.date()} - {to_date.date()}")

                    return data
        else:
            if print_logs:
                print(f"Failed to fetch {tradingsymbol} data: {from_date.date()} - {to_date.date()}")

        return pd.DataFrame()

    def get_data(self, instrument_token, start_date, end_date, interval: Interval, oi: bool = False, print_logs: bool = False ) -> pd.DataFrame:

        from_date = pd.to_datetime(start_date)
        to_date = pd.to_datetime(end_date)

        all_data = []
        
        current = from_date.replace(day=1)
        while current <= to_date:
            
            year, month = current.year, current.month
            
            df = self._get_month_data(instrument_token=instrument_token, year=year, month=month, interval=interval, oi=oi, print_logs=print_logs)

            if not df.empty:
                df = df[(df['datetime'].dt.date >= from_date.date()) & (df['datetime'].dt.date <= to_date.date())]
                all_data.append(df)

            current = pd.Timestamp(year=current.year, month=current.month, day=1)
            current = current + pd.Timedelta(days=current.days_in_month)

        if all_data:
            final_df = pd.concat(all_data, ignore_index=True)
            final_df.drop_duplicates(inplace=True)
            final_df.reset_index(drop=True, inplace=True)
            return final_df

        return pd.DataFrame()