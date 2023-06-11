# Download-historical-Stock-data-Free

# Importing Library


```python
from Pyzdata import pyzdata
```

###         Login Zerodha            


```python
# Method - 1
zdata = pyzdata(userid="userid", password="password", twofa="twofa", key_type="totp")
```


```python
# Method - 2
zdata = pyzdata(enctoken="enctoken")
```

# Instrument token


```python
# Get instrument token for given trading symbol
instrument_token = zdata.get_instrument_token(tradingsymbol="HDFC", exchange="NSE")
```

# Monthly Data


```python
df = zdata.get_month_data(instrument_token, year=2020, month=1, interval=zdata.interval.hour_1, oi=True)
display(df)
```


<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
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
      <th>open_interest</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>HDFC</td>
      <td>2020-01-01 09:15:00</td>
      <td>2418.00</td>
      <td>2423.90</td>
      <td>2409.00</td>
      <td>2412.55</td>
      <td>198613</td>
      <td>0</td>
    </tr>
    <tr>
      <th>1</th>
      <td>HDFC</td>
      <td>2020-01-01 10:15:00</td>
      <td>2412.55</td>
      <td>2429.80</td>
      <td>2410.00</td>
      <td>2424.70</td>
      <td>157818</td>
      <td>0</td>
    </tr>
    <tr>
      <th>2</th>
      <td>HDFC</td>
      <td>2020-01-01 11:15:00</td>
      <td>2424.80</td>
      <td>2425.60</td>
      <td>2420.00</td>
      <td>2424.75</td>
      <td>58640</td>
      <td>0</td>
    </tr>
    <tr>
      <th>3</th>
      <td>HDFC</td>
      <td>2020-01-01 12:15:00</td>
      <td>2424.75</td>
      <td>2429.90</td>
      <td>2424.00</td>
      <td>2426.55</td>
      <td>105438</td>
      <td>0</td>
    </tr>
    <tr>
      <th>4</th>
      <td>HDFC</td>
      <td>2020-01-01 13:15:00</td>
      <td>2426.50</td>
      <td>2433.80</td>
      <td>2425.00</td>
      <td>2430.40</td>
      <td>94888</td>
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
      <td>...</td>
    </tr>
    <tr>
      <th>149</th>
      <td>HDFC</td>
      <td>2020-01-30 11:15:00</td>
      <td>2424.05</td>
      <td>2424.90</td>
      <td>2408.05</td>
      <td>2413.00</td>
      <td>240059</td>
      <td>0</td>
    </tr>
    <tr>
      <th>150</th>
      <td>HDFC</td>
      <td>2020-01-30 12:15:00</td>
      <td>2413.10</td>
      <td>2422.40</td>
      <td>2408.70</td>
      <td>2411.40</td>
      <td>229149</td>
      <td>0</td>
    </tr>
    <tr>
      <th>151</th>
      <td>HDFC</td>
      <td>2020-01-30 13:15:00</td>
      <td>2411.35</td>
      <td>2417.00</td>
      <td>2406.35</td>
      <td>2410.45</td>
      <td>334411</td>
      <td>0</td>
    </tr>
    <tr>
      <th>152</th>
      <td>HDFC</td>
      <td>2020-01-30 14:15:00</td>
      <td>2410.45</td>
      <td>2427.75</td>
      <td>2407.90</td>
      <td>2411.55</td>
      <td>675028</td>
      <td>0</td>
    </tr>
    <tr>
      <th>153</th>
      <td>HDFC</td>
      <td>2020-01-30 15:15:00</td>
      <td>2411.60</td>
      <td>2413.60</td>
      <td>2409.45</td>
      <td>2411.00</td>
      <td>336853</td>
      <td>0</td>
    </tr>
  </tbody>
</table>
<p>154 rows × 8 columns</p>
</div>


# Yearly Data


```python
df = zdata.get_year_data(instrument_token, year=2021, interval=zdata.interval.minute_30)
display(df)
```


<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
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
      <td>2575.75</td>
      <td>2541.45</td>
      <td>2574.45</td>
      <td>294335</td>
    </tr>
    <tr>
      <th>1</th>
      <td>HDFC</td>
      <td>2021-01-01 09:45:00</td>
      <td>2575.65</td>
      <td>2593.30</td>
      <td>2574.25</td>
      <td>2583.00</td>
      <td>412409</td>
    </tr>
    <tr>
      <th>2</th>
      <td>HDFC</td>
      <td>2021-01-01 10:15:00</td>
      <td>2583.00</td>
      <td>2589.00</td>
      <td>2578.05</td>
      <td>2579.50</td>
      <td>146993</td>
    </tr>
    <tr>
      <th>3</th>
      <td>HDFC</td>
      <td>2021-01-01 10:45:00</td>
      <td>2579.60</td>
      <td>2582.00</td>
      <td>2570.00</td>
      <td>2572.10</td>
      <td>139784</td>
    </tr>
    <tr>
      <th>4</th>
      <td>HDFC</td>
      <td>2021-01-01 11:15:00</td>
      <td>2572.10</td>
      <td>2573.00</td>
      <td>2563.00</td>
      <td>2563.85</td>
      <td>110675</td>
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
      <th>3099</th>
      <td>HDFC</td>
      <td>2021-12-30 13:15:00</td>
      <td>2571.95</td>
      <td>2577.30</td>
      <td>2570.00</td>
      <td>2571.75</td>
      <td>101377</td>
    </tr>
    <tr>
      <th>3100</th>
      <td>HDFC</td>
      <td>2021-12-30 13:45:00</td>
      <td>2571.80</td>
      <td>2574.20</td>
      <td>2565.70</td>
      <td>2572.65</td>
      <td>77884</td>
    </tr>
    <tr>
      <th>3101</th>
      <td>HDFC</td>
      <td>2021-12-30 14:15:00</td>
      <td>2572.60</td>
      <td>2579.15</td>
      <td>2569.00</td>
      <td>2573.90</td>
      <td>101123</td>
    </tr>
    <tr>
      <th>3102</th>
      <td>HDFC</td>
      <td>2021-12-30 14:45:00</td>
      <td>2574.30</td>
      <td>2574.65</td>
      <td>2555.00</td>
      <td>2569.15</td>
      <td>335713</td>
    </tr>
    <tr>
      <th>3103</th>
      <td>HDFC</td>
      <td>2021-12-30 15:15:00</td>
      <td>2569.10</td>
      <td>2576.95</td>
      <td>2560.80</td>
      <td>2570.00</td>
      <td>259494</td>
    </tr>
  </tbody>
</table>
<p>3104 rows × 7 columns</p>
</div>


# Download data from given year to present time



```python
# csv file download at working directory
df = zdata.download_data_from_year(instrument_token, from_year=2020, interval=zdata.interval.day, print_statement=True)
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
    


<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
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
      <td>2020-01-01</td>
      <td>2418.00</td>
      <td>2438.50</td>
      <td>2409.00</td>
      <td>2433.95</td>
      <td>945874</td>
    </tr>
    <tr>
      <th>1</th>
      <td>HDFC</td>
      <td>2020-01-02</td>
      <td>2430.00</td>
      <td>2472.75</td>
      <td>2422.00</td>
      <td>2466.40</td>
      <td>1701396</td>
    </tr>
    <tr>
      <th>2</th>
      <td>HDFC</td>
      <td>2020-01-03</td>
      <td>2455.00</td>
      <td>2466.40</td>
      <td>2441.80</td>
      <td>2454.45</td>
      <td>1963923</td>
    </tr>
    <tr>
      <th>3</th>
      <td>HDFC</td>
      <td>2020-01-06</td>
      <td>2428.00</td>
      <td>2445.00</td>
      <td>2371.40</td>
      <td>2384.10</td>
      <td>2656731</td>
    </tr>
    <tr>
      <th>4</th>
      <td>HDFC</td>
      <td>2020-01-07</td>
      <td>2401.25</td>
      <td>2428.80</td>
      <td>2380.20</td>
      <td>2415.05</td>
      <td>3771992</td>
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
      <th>851</th>
      <td>HDFC</td>
      <td>2023-06-05</td>
      <td>2658.00</td>
      <td>2661.90</td>
      <td>2642.00</td>
      <td>2644.80</td>
      <td>4714971</td>
    </tr>
    <tr>
      <th>852</th>
      <td>HDFC</td>
      <td>2023-06-06</td>
      <td>2645.95</td>
      <td>2649.00</td>
      <td>2624.85</td>
      <td>2635.35</td>
      <td>4846536</td>
    </tr>
    <tr>
      <th>853</th>
      <td>HDFC</td>
      <td>2023-06-07</td>
      <td>2642.75</td>
      <td>2655.00</td>
      <td>2631.60</td>
      <td>2648.55</td>
      <td>2694134</td>
    </tr>
    <tr>
      <th>854</th>
      <td>HDFC</td>
      <td>2023-06-08</td>
      <td>2636.10</td>
      <td>2678.00</td>
      <td>2636.10</td>
      <td>2653.80</td>
      <td>2072748</td>
    </tr>
    <tr>
      <th>855</th>
      <td>HDFC</td>
      <td>2023-06-09</td>
      <td>2664.00</td>
      <td>2667.90</td>
      <td>2646.85</td>
      <td>2652.90</td>
      <td>4348281</td>
    </tr>
  </tbody>
</table>
<p>856 rows × 7 columns</p>
</div>



```python

```
