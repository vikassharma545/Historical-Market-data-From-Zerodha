import requests
import datetime
import pandas as pd
from time import sleep

class stock_data:
    __scrip_data = None
    __enc_cookies = None

    def __init__(self, enc_cookies):

        self.__enc_cookies = enc_cookies
        self.__scrip_data = pd.read_csv('https://api.kite.trade/instruments')

    def get_month_data(self, stock_name, year, month):

        try:
            token = self.__scrip_data[self.__scrip_data['tradingsymbol'] == stock_name]['instrument_token'].iloc[0]
        except:
            raise Exception("No Scrip found On Zerodha")

        for _ in range(3):
            try:
                from_date = pd.to_datetime(f"{year}-{month}", format="%Y-%m")
                to_date = pd.to_datetime(f"{year}-{month}-{from_date.days_in_month}", format='%Y-%m-%d')

                url = f"https://kite.zerodha.com/oms/instruments/historical/{token}/minute?user_id=1234&oi={1}&from={str(from_date)[:10]}&to={str(to_date)[:10]}"
                headers = {
                    'authorization': f"enctoken {self.__enc_cookies}"
                }
                response = requests.get(url, headers=headers)
                response = response.json()
                if response['status'] == 'success':
                    data = pd.DataFrame(response['data']['candles'])
                    if not data.empty:
                        data.drop([6], inplace=True, axis=1)
                        data.columns = ['Date Time', 'Open', 'High', 'Low', 'Close', 'Volume']
                        data['Scrip'] = stock_name
                        data['Date Time'] = pd.to_datetime(data['Date Time'])
                        data['Date Time'] = data['Date Time'].apply(lambda x: pd.Timestamp.combine(x.date(), x.time()))
                        data = data.reindex(columns=['Scrip', 'Date Time', 'Open', 'High', 'Low', 'Close', 'Volume'])

                    return data

            except Exception as e:
                print('wait ...', e)
                sleep(3)

        raise Exception("Try From Start Again !!! :(")

    def get_year_data(self, stock_name, year):
        data = pd.DataFrame()
        for month in range(1, 13):
            monthly_data = self.get_month_data(stock_name, year, month)
            data = pd.concat([data, monthly_data], ignore_index=True)
        return data

    def download_data_from_year(self, stock_name, year):
        print('Downloading...')
        data = pd.DataFrame()
        from_year = year
        to_year = pd.Timestamp.now().year
        for year in range(from_year, to_year + 1):
            year_data = self.get_year_data(stock_name, year)
            data = pd.concat([data, year_data], ignore_index=True)

        data.sort_values(by=['date_time'], inplace=True)
        data.drop_duplicates(inplace=True)
        data = data[data.date_time < pd.Timestamp.combine(pd.Timestamp.now().date(), datetime.time(15, 30))]
        data.to_csv(f'{stock_name} {from_year} to {to_year}.csv', index=False)
        return data