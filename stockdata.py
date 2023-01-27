import datetime
import requests
import pandas as pd
from time import sleep

from interval import Interval
from instrument import Instrument


class StockData:
    
    def __init__(self, enc_cookies):
        self.interval = Interval()
        self.instrument = Instrument()
        self.__enc_cookies = enc_cookies

    def get_month_data(self, tradingsymbol, year, month, interval=Interval.minute_1, print_statement=False):
        
        instrument_token = self.instrument.get_stock_instrument_token(tradingsymbol)
        
        if instrument_token is None:
            return pd.DataFrame()

        for _ in range(3):
            try:
                from_date = pd.to_datetime(f"{year}-{month}", format="%Y-%m")
                to_date = pd.to_datetime(f"{year}-{month}-{from_date.days_in_month}", format='%Y-%m-%d')

                url = f"https://kite.zerodha.com/oms/instruments/historical/{instrument_token}/{interval}" \
                      f"?user_id=1234&oi=1&from={str(from_date)[:10]}&to={str(to_date)[:10]}"
                response = requests.get(url, headers={'authorization': f"enctoken {self.__enc_cookies}"})
                response = response.json()
                if response['status'] == 'success':
                    data = pd.DataFrame(response['data']['candles'])
                    if not data.empty:
                        data = data.loc[:,:5]
                        data.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
                        data['tradingsymbol'] = tradingsymbol
                        data['datetime'] = pd.to_datetime(data['datetime'])
                        data['datetime'] = data['datetime'].apply(lambda x: pd.Timestamp.combine(x.date(), x.time()))
                        columns = ['tradingsymbol', 'datetime', 'open', 'high', 'low', 'close', 'volume']
                        data = data.reindex(columns=columns)
                    
                        if print_statement:
                            print(f"{tradingsymbol} data from {str(from_date)[:10]} to {str(to_date)[:10]} Fetched :)")

                    return data

            except Exception as e:
                print('wait ...', e)
                sleep(3)

        print("Try From Start Again !!! :(")
        
    def get_year_data(self, stock_name, year, interval=Interval.minute_1, print_statement=False):
        data = pd.DataFrame()
        for month in range(1, 13):
            monthly_data = self.get_month_data(stock_name, year, month, interval, print_statement)
            data = pd.concat([data, monthly_data], ignore_index=True)
        return data

    def download_data_from_year(self, stock_name, from_year, interval=Interval.minute_1, print_statement=False):
        print('Downloading...')
        to_year, data = pd.Timestamp.now().year, pd.DataFrame()
        
        for year in range(from_year, to_year + 1):
            year_data = self.get_year_data(stock_name, year, interval, print_statement)
            data = pd.concat([data, year_data], ignore_index=True)

        data.sort_values(by=['datetime'], inplace=True)
        data.drop_duplicates(inplace=True)
        data = data[data['datetime'] < pd.Timestamp.combine(pd.Timestamp.now().date(), datetime.time(15, 30))]
        data.to_csv(f'{stock_name} {from_year} to {to_year}.csv', index=False)
        return data