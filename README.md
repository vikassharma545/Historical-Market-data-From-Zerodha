# Download-historical-Stock-data-Free

# Importing Library


```python
from Pyzdata import PyZData, Interval
```

###         Login Zerodha            


```python
zdata = PyZData(userid="USERID", password="PASSWORD", totp=123456)
```

# Instrument token


```python
# Get instrument token for given trading symbol
instrument_token = zdata.get_instrument_token(tradingsymbol="NIFTY 50", exchange="NSE")
```

# Monthly Data


```python
df = zdata.get_month_data(instrument_token, year=2024, month=2, interval=Interval.MINUTE_1, oi=False, print_logs=True)
display(df)
```

    NIFTY 50 data fetched: 2024-02-01 - 2024-02-29.
    


<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>tradingsymbol</th>
      <th>datetime</th>
      <th>open</th>
      <th>high</th>
      <th>low</th>
      <th>close</th>
      <th>volume</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>NIFTY 50</td>
      <td>2024-02-01 09:15:00</td>
      <td>21780.65</td>
      <td>21788.35</td>
      <td>21719.05</td>
      <td>21736.10</td>
      <td>0</td>
    </tr>
    <tr>
      <th>1</th>
      <td>NIFTY 50</td>
      <td>2024-02-01 09:16:00</td>
      <td>21734.25</td>
      <td>21756.35</td>
      <td>21733.70</td>
      <td>21746.40</td>
      <td>0</td>
    </tr>
    <tr>
      <th>2</th>
      <td>NIFTY 50</td>
      <td>2024-02-01 09:17:00</td>
      <td>21744.05</td>
      <td>21753.60</td>
      <td>21741.15</td>
      <td>21741.60</td>
      <td>0</td>
    </tr>
    <tr>
      <th>3</th>
      <td>NIFTY 50</td>
      <td>2024-02-01 09:18:00</td>
      <td>21742.40</td>
      <td>21747.80</td>
      <td>21716.90</td>
      <td>21725.65</td>
      <td>0</td>
    </tr>
    <tr>
      <th>4</th>
      <td>NIFTY 50</td>
      <td>2024-02-01 09:19:00</td>
      <td>21724.95</td>
      <td>21729.10</td>
      <td>21706.55</td>
      <td>21718.80</td>
      <td>0</td>
    </tr>
    <tr>
      <th>...</th>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
    </tr>
    <tr>
      <th>7870</th>
      <td>NIFTY 50</td>
      <td>2024-02-29 15:25:00</td>
      <td>22042.25</td>
      <td>22049.60</td>
      <td>22041.35</td>
      <td>22048.40</td>
      <td>0</td>
    </tr>
    <tr>
      <th>7871</th>
      <td>NIFTY 50</td>
      <td>2024-02-29 15:26:00</td>
      <td>22048.75</td>
      <td>22057.55</td>
      <td>22047.65</td>
      <td>22056.50</td>
      <td>0</td>
    </tr>
    <tr>
      <th>7872</th>
      <td>NIFTY 50</td>
      <td>2024-02-29 15:27:00</td>
      <td>22055.65</td>
      <td>22060.55</td>
      <td>22051.45</td>
      <td>22055.75</td>
      <td>0</td>
    </tr>
    <tr>
      <th>7873</th>
      <td>NIFTY 50</td>
      <td>2024-02-29 15:28:00</td>
      <td>22053.10</td>
      <td>22056.20</td>
      <td>22043.25</td>
      <td>22050.40</td>
      <td>0</td>
    </tr>
    <tr>
      <th>7874</th>
      <td>NIFTY 50</td>
      <td>2024-02-29 15:29:00</td>
      <td>22050.65</td>
      <td>22050.65</td>
      <td>22037.00</td>
      <td>22042.05</td>
      <td>0</td>
    </tr>
  </tbody>
</table>
<p>7875 rows × 7 columns</p>
</div>


# Yearly Data


```python
df = zdata.get_year_data(instrument_token, year=2021, interval=Interval.MINUTE_1)
display(df)
```


<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>tradingsymbol</th>
      <th>datetime</th>
      <th>open</th>
      <th>high</th>
      <th>low</th>
      <th>close</th>
      <th>volume</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>NIFTY 50</td>
      <td>2021-01-01 09:15:00</td>
      <td>13996.10</td>
      <td>14019.50</td>
      <td>13994.85</td>
      <td>14013.15</td>
      <td>0</td>
    </tr>
    <tr>
      <th>1</th>
      <td>NIFTY 50</td>
      <td>2021-01-01 09:16:00</td>
      <td>14014.85</td>
      <td>14018.55</td>
      <td>14008.15</td>
      <td>14009.05</td>
      <td>0</td>
    </tr>
    <tr>
      <th>2</th>
      <td>NIFTY 50</td>
      <td>2021-01-01 09:17:00</td>
      <td>14008.05</td>
      <td>14013.10</td>
      <td>14005.05</td>
      <td>14012.70</td>
      <td>0</td>
    </tr>
    <tr>
      <th>3</th>
      <td>NIFTY 50</td>
      <td>2021-01-01 09:18:00</td>
      <td>14013.65</td>
      <td>14019.10</td>
      <td>14013.65</td>
      <td>14016.20</td>
      <td>0</td>
    </tr>
    <tr>
      <th>4</th>
      <td>NIFTY 50</td>
      <td>2021-01-01 09:19:00</td>
      <td>14015.45</td>
      <td>14017.80</td>
      <td>14011.95</td>
      <td>14015.45</td>
      <td>0</td>
    </tr>
    <tr>
      <th>...</th>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
    </tr>
    <tr>
      <th>92433</th>
      <td>NIFTY 50</td>
      <td>2021-12-31 15:25:00</td>
      <td>17357.90</td>
      <td>17358.50</td>
      <td>17353.75</td>
      <td>17356.30</td>
      <td>0</td>
    </tr>
    <tr>
      <th>92434</th>
      <td>NIFTY 50</td>
      <td>2021-12-31 15:26:00</td>
      <td>17356.10</td>
      <td>17359.65</td>
      <td>17355.55</td>
      <td>17359.25</td>
      <td>0</td>
    </tr>
    <tr>
      <th>92435</th>
      <td>NIFTY 50</td>
      <td>2021-12-31 15:27:00</td>
      <td>17358.85</td>
      <td>17360.50</td>
      <td>17356.20</td>
      <td>17359.80</td>
      <td>0</td>
    </tr>
    <tr>
      <th>92436</th>
      <td>NIFTY 50</td>
      <td>2021-12-31 15:28:00</td>
      <td>17359.75</td>
      <td>17360.90</td>
      <td>17351.10</td>
      <td>17353.55</td>
      <td>0</td>
    </tr>
    <tr>
      <th>92437</th>
      <td>NIFTY 50</td>
      <td>2021-12-31 15:29:00</td>
      <td>17353.45</td>
      <td>17365.45</td>
      <td>17353.10</td>
      <td>17364.25</td>
      <td>0</td>
    </tr>
  </tbody>
</table>
<p>92438 rows × 7 columns</p>
</div>


# Download data from given year to present time



```python
# csv file download at working directory
df = zdata.download_data_from_year(instrument_token, from_year=2024, interval=Interval.DAY, print_logs=True)
display(df)
```

    Downloading data...
    NIFTY 50 data fetched: 2024-01-01 - 2024-01-31.
    NIFTY 50 data fetched: 2024-02-01 - 2024-02-29.
    NIFTY 50 data fetched: 2024-03-01 - 2024-03-31.
    NIFTY 50 data fetched: 2024-04-01 - 2024-04-30.
    NIFTY 50 data fetched: 2024-05-01 - 2024-05-31.
    NIFTY 50 data fetched: 2024-06-01 - 2024-06-30.
    NIFTY 50 data fetched: 2024-07-01 - 2024-07-31.
    NIFTY 50 data fetched: 2024-08-01 - 2024-08-31.
    NIFTY 50 data fetched: 2024-09-01 - 2024-09-30.
    NIFTY 50 data fetched: 2024-10-01 - 2024-10-31.
    NIFTY 50 data fetched: 2024-11-01 - 2024-11-30.
    NIFTY 50 data fetched: 2024-12-01 - 2024-12-31.
    Data for the year 2024 fetched successfully.
    NIFTY 50 data fetched: 2025-01-01 - 2025-01-31.
    NIFTY 50 data fetched: 2025-02-01 - 2025-02-28.
    NIFTY 50 data fetched: 2025-03-01 - 2025-03-31.
    NIFTY 50 data fetched: 2025-04-01 - 2025-04-30.
    NIFTY 50 data fetched: 2025-05-01 - 2025-05-31.
    NIFTY 50 data fetched: 2025-06-01 - 2025-06-30.
    NIFTY 50 data fetched: 2025-07-01 - 2025-07-31.
    NIFTY 50 data fetched: 2025-08-01 - 2025-08-31.
    NIFTY 50 data fetched: 2025-09-01 - 2025-09-30.
    NIFTY 50 data fetched: 2025-10-01 - 2025-10-31.
    NIFTY 50 data fetched: 2025-11-01 - 2025-11-30.
    NIFTY 50 data fetched: 2025-12-01 - 2025-12-31.
    Data for the year 2025 fetched successfully.
    Data downloaded and saved to NIFTY 50_2024_to_2025_day.csv
    


<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>tradingsymbol</th>
      <th>datetime</th>
      <th>open</th>
      <th>high</th>
      <th>low</th>
      <th>close</th>
      <th>volume</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>NIFTY 50</td>
      <td>2024-01-01</td>
      <td>21727.75</td>
      <td>21834.35</td>
      <td>21680.85</td>
      <td>21741.90</td>
      <td>0</td>
    </tr>
    <tr>
      <th>1</th>
      <td>NIFTY 50</td>
      <td>2024-01-02</td>
      <td>21751.35</td>
      <td>21755.60</td>
      <td>21555.65</td>
      <td>21665.80</td>
      <td>0</td>
    </tr>
    <tr>
      <th>2</th>
      <td>NIFTY 50</td>
      <td>2024-01-03</td>
      <td>21661.10</td>
      <td>21677.00</td>
      <td>21500.35</td>
      <td>21517.35</td>
      <td>0</td>
    </tr>
    <tr>
      <th>3</th>
      <td>NIFTY 50</td>
      <td>2024-01-04</td>
      <td>21605.80</td>
      <td>21685.65</td>
      <td>21564.55</td>
      <td>21658.60</td>
      <td>0</td>
    </tr>
    <tr>
      <th>4</th>
      <td>NIFTY 50</td>
      <td>2024-01-05</td>
      <td>21705.75</td>
      <td>21749.60</td>
      <td>21629.20</td>
      <td>21710.80</td>
      <td>0</td>
    </tr>
    <tr>
      <th>...</th>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
    </tr>
    <tr>
      <th>261</th>
      <td>NIFTY 50</td>
      <td>2025-01-17</td>
      <td>23277.10</td>
      <td>23292.10</td>
      <td>23100.35</td>
      <td>23203.20</td>
      <td>0</td>
    </tr>
    <tr>
      <th>262</th>
      <td>NIFTY 50</td>
      <td>2025-01-20</td>
      <td>23290.40</td>
      <td>23391.10</td>
      <td>23170.65</td>
      <td>23344.75</td>
      <td>0</td>
    </tr>
    <tr>
      <th>263</th>
      <td>NIFTY 50</td>
      <td>2025-01-21</td>
      <td>23421.65</td>
      <td>23426.30</td>
      <td>22976.85</td>
      <td>23024.65</td>
      <td>0</td>
    </tr>
    <tr>
      <th>264</th>
      <td>NIFTY 50</td>
      <td>2025-01-22</td>
      <td>23099.15</td>
      <td>23169.55</td>
      <td>22981.30</td>
      <td>23155.35</td>
      <td>0</td>
    </tr>
    <tr>
      <th>265</th>
      <td>NIFTY 50</td>
      <td>2025-01-23</td>
      <td>23128.30</td>
      <td>23270.80</td>
      <td>23090.65</td>
      <td>23245.70</td>
      <td>0</td>
    </tr>
  </tbody>
</table>
<p>266 rows × 7 columns</p>
</div>



```python

```
