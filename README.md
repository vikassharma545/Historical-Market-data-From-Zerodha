# Download-historical-Stock-data-Free

# Importing Library


```python
from login import Login
from stockdata import StockData
```

# Login Zerodha Account


```python
"""         Login Zerodha            """

userid = None
pwd = None

zerodha = Login(user_id=userid, password=pwd)
```

    [WDM] - Downloading: 100%|████████████████████████████████████████████████████████| 6.79M/6.79M [00:00<00:00, 11.7MB/s]
    

    Login Successfull :)
    

# Initiate Stock data


```python
stdata = StockData(zerodha.get_enc_cookie())
tradingsymbol = "HDFC"
```

# Monthly Data


```python
df = stdata.get_month_data(tradingsymbol, year=2020, month=1, interval=stdata.interval.minute_5)
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
      <td>HDFC</td>
      <td>2020-01-01 09:15:00</td>
      <td>2418.00</td>
      <td>2423.00</td>
      <td>2412.50</td>
      <td>2421.00</td>
      <td>47534</td>
    </tr>
    <tr>
      <th>1</th>
      <td>HDFC</td>
      <td>2020-01-01 09:20:00</td>
      <td>2421.00</td>
      <td>2422.75</td>
      <td>2416.20</td>
      <td>2421.00</td>
      <td>23113</td>
    </tr>
    <tr>
      <th>2</th>
      <td>HDFC</td>
      <td>2020-01-01 09:25:00</td>
      <td>2420.00</td>
      <td>2423.90</td>
      <td>2418.00</td>
      <td>2421.30</td>
      <td>23143</td>
    </tr>
    <tr>
      <th>3</th>
      <td>HDFC</td>
      <td>2020-01-01 09:30:00</td>
      <td>2421.00</td>
      <td>2421.95</td>
      <td>2417.35</td>
      <td>2417.35</td>
      <td>13116</td>
    </tr>
    <tr>
      <th>4</th>
      <td>HDFC</td>
      <td>2020-01-01 09:35:00</td>
      <td>2418.00</td>
      <td>2420.00</td>
      <td>2416.00</td>
      <td>2418.00</td>
      <td>12686</td>
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
      <th>1720</th>
      <td>HDFC</td>
      <td>2020-01-31 15:05:00</td>
      <td>2415.70</td>
      <td>2416.65</td>
      <td>2411.50</td>
      <td>2414.80</td>
      <td>124660</td>
    </tr>
    <tr>
      <th>1721</th>
      <td>HDFC</td>
      <td>2020-01-31 15:10:00</td>
      <td>2414.30</td>
      <td>2415.50</td>
      <td>2411.50</td>
      <td>2414.20</td>
      <td>119434</td>
    </tr>
    <tr>
      <th>1722</th>
      <td>HDFC</td>
      <td>2020-01-31 15:15:00</td>
      <td>2413.75</td>
      <td>2414.15</td>
      <td>2409.00</td>
      <td>2409.10</td>
      <td>125146</td>
    </tr>
    <tr>
      <th>1723</th>
      <td>HDFC</td>
      <td>2020-01-31 15:20:00</td>
      <td>2409.10</td>
      <td>2410.90</td>
      <td>2405.00</td>
      <td>2410.35</td>
      <td>128606</td>
    </tr>
    <tr>
      <th>1724</th>
      <td>HDFC</td>
      <td>2020-01-31 15:25:00</td>
      <td>2410.35</td>
      <td>2418.80</td>
      <td>2409.85</td>
      <td>2416.40</td>
      <td>72053</td>
    </tr>
  </tbody>
</table>
<p>1725 rows × 7 columns</p>
</div>


# Yearly Data


```python
df = stdata.get_year_data(tradingsymbol, year=2021)
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
      <td>HDFC</td>
      <td>2021-01-01 09:15:00</td>
      <td>2549.00</td>
      <td>2554.50</td>
      <td>2541.45</td>
      <td>2544.00</td>
      <td>20203</td>
    </tr>
    <tr>
      <th>1</th>
      <td>HDFC</td>
      <td>2021-01-01 09:16:00</td>
      <td>2545.00</td>
      <td>2553.30</td>
      <td>2543.95</td>
      <td>2551.00</td>
      <td>17885</td>
    </tr>
    <tr>
      <th>2</th>
      <td>HDFC</td>
      <td>2021-01-01 09:17:00</td>
      <td>2551.10</td>
      <td>2553.00</td>
      <td>2549.45</td>
      <td>2551.80</td>
      <td>13379</td>
    </tr>
    <tr>
      <th>3</th>
      <td>HDFC</td>
      <td>2021-01-01 09:18:00</td>
      <td>2550.80</td>
      <td>2553.00</td>
      <td>2549.90</td>
      <td>2552.20</td>
      <td>9797</td>
    </tr>
    <tr>
      <th>4</th>
      <td>HDFC</td>
      <td>2021-01-01 09:19:00</td>
      <td>2552.05</td>
      <td>2552.65</td>
      <td>2548.00</td>
      <td>2550.00</td>
      <td>9716</td>
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
      <th>92528</th>
      <td>HDFC</td>
      <td>2021-12-31 15:25:00</td>
      <td>2587.55</td>
      <td>2587.55</td>
      <td>2585.30</td>
      <td>2585.30</td>
      <td>14941</td>
    </tr>
    <tr>
      <th>92529</th>
      <td>HDFC</td>
      <td>2021-12-31 15:26:00</td>
      <td>2585.05</td>
      <td>2587.25</td>
      <td>2585.05</td>
      <td>2586.95</td>
      <td>8485</td>
    </tr>
    <tr>
      <th>92530</th>
      <td>HDFC</td>
      <td>2021-12-31 15:27:00</td>
      <td>2587.00</td>
      <td>2587.20</td>
      <td>2586.95</td>
      <td>2587.15</td>
      <td>12485</td>
    </tr>
    <tr>
      <th>92531</th>
      <td>HDFC</td>
      <td>2021-12-31 15:28:00</td>
      <td>2587.20</td>
      <td>2588.05</td>
      <td>2583.05</td>
      <td>2583.75</td>
      <td>14830</td>
    </tr>
    <tr>
      <th>92532</th>
      <td>HDFC</td>
      <td>2021-12-31 15:29:00</td>
      <td>2585.00</td>
      <td>2588.00</td>
      <td>2583.70</td>
      <td>2587.00</td>
      <td>6883</td>
    </tr>
  </tbody>
</table>
<p>92533 rows × 7 columns</p>
</div>


# Download data from given year to present time



```python
# csv file download at working directory
df = stdata.download_data_from_year(tradingsymbol, from_year=2020, print_statement=True)
display(df)
```

    Downloading...
    HDFC data from 2020-01-01 to 2020-01-31 Fetched :)
    HDFC data from 2020-02-01 to 2020-02-29 Fetched :)
    HDFC data from 2020-03-01 to 2020-03-31 Fetched :)
    HDFC data from 2020-04-01 to 2020-04-30 Fetched :)
    HDFC data from 2020-05-01 to 2020-05-31 Fetched :)
    HDFC data from 2020-06-01 to 2020-06-30 Fetched :)
    HDFC data from 2020-07-01 to 2020-07-31 Fetched :)
    HDFC data from 2020-08-01 to 2020-08-31 Fetched :)
    HDFC data from 2020-09-01 to 2020-09-30 Fetched :)
    HDFC data from 2020-10-01 to 2020-10-31 Fetched :)
    HDFC data from 2020-11-01 to 2020-11-30 Fetched :)
    HDFC data from 2020-12-01 to 2020-12-31 Fetched :)
    HDFC data from 2021-01-01 to 2021-01-31 Fetched :)
    HDFC data from 2021-02-01 to 2021-02-28 Fetched :)
    HDFC data from 2021-03-01 to 2021-03-31 Fetched :)
    HDFC data from 2021-04-01 to 2021-04-30 Fetched :)
    HDFC data from 2021-05-01 to 2021-05-31 Fetched :)
    HDFC data from 2021-06-01 to 2021-06-30 Fetched :)
    HDFC data from 2021-07-01 to 2021-07-31 Fetched :)
    HDFC data from 2021-08-01 to 2021-08-31 Fetched :)
    HDFC data from 2021-09-01 to 2021-09-30 Fetched :)
    HDFC data from 2021-10-01 to 2021-10-31 Fetched :)
    HDFC data from 2021-11-01 to 2021-11-30 Fetched :)
    HDFC data from 2021-12-01 to 2021-12-31 Fetched :)
    HDFC data from 2022-01-01 to 2022-01-31 Fetched :)
    HDFC data from 2022-02-01 to 2022-02-28 Fetched :)
    HDFC data from 2022-03-01 to 2022-03-31 Fetched :)
    HDFC data from 2022-04-01 to 2022-04-30 Fetched :)
    HDFC data from 2022-05-01 to 2022-05-31 Fetched :)
    HDFC data from 2022-06-01 to 2022-06-30 Fetched :)
    HDFC data from 2022-07-01 to 2022-07-31 Fetched :)
    HDFC data from 2022-08-01 to 2022-08-31 Fetched :)
    HDFC data from 2022-09-01 to 2022-09-30 Fetched :)
    HDFC data from 2022-10-01 to 2022-10-31 Fetched :)
    HDFC data from 2022-11-01 to 2022-11-30 Fetched :)
    HDFC data from 2022-12-01 to 2022-12-31 Fetched :)
    HDFC data from 2023-01-01 to 2023-01-31 Fetched :)
    HDFC data from 2023-02-01 to 2023-02-28 Fetched :)
    HDFC data from 2023-03-01 to 2023-03-31 Fetched :)
    HDFC data from 2023-04-01 to 2023-04-30 Fetched :)
    HDFC data from 2023-05-01 to 2023-05-31 Fetched :)
    HDFC data from 2023-06-01 to 2023-06-30 Fetched :)
    HDFC data from 2023-07-01 to 2023-07-31 Fetched :)
    HDFC data from 2023-08-01 to 2023-08-31 Fetched :)
    HDFC data from 2023-09-01 to 2023-09-30 Fetched :)
    HDFC data from 2023-10-01 to 2023-10-31 Fetched :)
    HDFC data from 2023-11-01 to 2023-11-30 Fetched :)
    HDFC data from 2023-12-01 to 2023-12-31 Fetched :)
    


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
      <td>HDFC</td>
      <td>2020-01-01 09:15:00</td>
      <td>2418.00</td>
      <td>2421.70</td>
      <td>2414.25</td>
      <td>2415.95</td>
      <td>14155</td>
    </tr>
    <tr>
      <th>1</th>
      <td>HDFC</td>
      <td>2020-01-01 09:16:00</td>
      <td>2415.95</td>
      <td>2417.65</td>
      <td>2413.05</td>
      <td>2414.20</td>
      <td>10688</td>
    </tr>
    <tr>
      <th>2</th>
      <td>HDFC</td>
      <td>2020-01-01 09:17:00</td>
      <td>2413.60</td>
      <td>2415.75</td>
      <td>2412.50</td>
      <td>2415.75</td>
      <td>7366</td>
    </tr>
    <tr>
      <th>3</th>
      <td>HDFC</td>
      <td>2020-01-01 09:18:00</td>
      <td>2415.05</td>
      <td>2421.40</td>
      <td>2415.05</td>
      <td>2421.40</td>
      <td>8600</td>
    </tr>
    <tr>
      <th>4</th>
      <td>HDFC</td>
      <td>2020-01-01 09:19:00</td>
      <td>2421.00</td>
      <td>2423.00</td>
      <td>2419.80</td>
      <td>2421.00</td>
      <td>6725</td>
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
      <th>291137</th>
      <td>HDFC</td>
      <td>2023-01-27 15:25:00</td>
      <td>2665.00</td>
      <td>2665.90</td>
      <td>2663.95</td>
      <td>2664.85</td>
      <td>12430</td>
    </tr>
    <tr>
      <th>288546</th>
      <td>HDFC</td>
      <td>2023-01-27 15:26:00</td>
      <td>2664.40</td>
      <td>2664.65</td>
      <td>2662.15</td>
      <td>2663.20</td>
      <td>11335</td>
    </tr>
    <tr>
      <th>288547</th>
      <td>HDFC</td>
      <td>2023-01-27 15:27:00</td>
      <td>2663.25</td>
      <td>2669.00</td>
      <td>2662.00</td>
      <td>2666.70</td>
      <td>15732</td>
    </tr>
    <tr>
      <th>286820</th>
      <td>HDFC</td>
      <td>2023-01-27 15:28:00</td>
      <td>2668.00</td>
      <td>2669.40</td>
      <td>2662.75</td>
      <td>2665.90</td>
      <td>9753</td>
    </tr>
    <tr>
      <th>291141</th>
      <td>HDFC</td>
      <td>2023-01-27 15:29:00</td>
      <td>2665.90</td>
      <td>2669.40</td>
      <td>2662.15</td>
      <td>2665.00</td>
      <td>4108</td>
    </tr>
  </tbody>
</table>
<p>286390 rows × 7 columns</p>
</div>



```python

```
