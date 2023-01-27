import pandas as pd


class Instrument:
    
    def __init__(self):
        self.instrument_data = pd.read_csv('https://api.kite.trade/instruments')
    
    def get_stock_instrument_token(self, tradingsymbol, exchange='NSE'):
        try:
            condition1 = (self.instrument_data['tradingsymbol'] == tradingsymbol)
            condition2 = (self.instrument_data['exchange'] == exchange)
            instrument_token = self.instrument_data[condition1 & condition2]['instrument_token'].iloc[0]
            return instrument_token
        except IndexError:
            print("No Scrip found On Zerodha")
            return None
