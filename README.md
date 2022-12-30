# Download-historical-Stock-data-Free

# Importing Library


```python
from login import login
from stock_data import stock_data
```

# Login Zerodha Account


```python
"""         Login Zerodha            """

userid = ""
pwd = ""

zerodha = login(user_id=userid, password=pwd)
```

    Login Successfull :)
    

# Initiate Stock data


```python
z_data = stock_data(zerodha.enc_cookies)
stock_name = "HDFC"
```

# Monthly Data


```python
df = z_data.get_month_data(stock_name, year=2020, month=1)
display(df)
```

<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Scrip</th>
      <th>Date Time</th>
      <th>Open</th>
      <th>High</th>
      <th>Low</th>
      <th>Close</th>
      <th>Volume</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>HDFC</td>
      <td>2020-01-01 09:15:00</td>
      <td>2417.00</td>
      <td>2420.70</td>
      <td>2414.15</td>
      <td>2415.30</td>
      <td>516</td>
    </tr>
    <tr>
      <th>1</th>
      <td>HDFC</td>
      <td>2020-01-01 09:16:00</td>
      <td>2415.30</td>
      <td>2417.55</td>
      <td>2414.10</td>
      <td>2415.00</td>
      <td>555</td>
    </tr>
    <tr>
      <th>2</th>
      <td>HDFC</td>
      <td>2020-01-01 09:17:00</td>
      <td>2415.00</td>
      <td>2415.75</td>
      <td>2414.95</td>
      <td>2415.00</td>
      <td>331</td>
    </tr>
    <tr>
      <th>3</th>
      <td>HDFC</td>
      <td>2020-01-01 09:18:00</td>
      <td>2415.00</td>
      <td>2421.40</td>
      <td>2415.00</td>
      <td>2421.00</td>
      <td>191</td>
    </tr>
    <tr>
      <th>4</th>
      <td>HDFC</td>
      <td>2020-01-01 09:19:00</td>
      <td>2421.00</td>
      <td>2422.70</td>
      <td>2420.95</td>
      <td>2420.95</td>
      <td>14</td>
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
      <th>8620</th>
      <td>HDFC</td>
      <td>2020-01-31 15:25:00</td>
      <td>2409.75</td>
      <td>2411.75</td>
      <td>2409.75</td>
      <td>2411.20</td>
      <td>483</td>
    </tr>
    <tr>
      <th>8621</th>
      <td>HDFC</td>
      <td>2020-01-31 15:26:00</td>
      <td>2411.20</td>
      <td>2412.55</td>
      <td>2410.25</td>
      <td>2411.00</td>
      <td>599</td>
    </tr>
    <tr>
      <th>8622</th>
      <td>HDFC</td>
      <td>2020-01-31 15:27:00</td>
      <td>2411.00</td>
      <td>2418.40</td>
      <td>2411.00</td>
      <td>2418.40</td>
      <td>870</td>
    </tr>
    <tr>
      <th>8623</th>
      <td>HDFC</td>
      <td>2020-01-31 15:28:00</td>
      <td>2418.40</td>
      <td>2418.75</td>
      <td>2415.75</td>
      <td>2418.05</td>
      <td>733</td>
    </tr>
    <tr>
      <th>8624</th>
      <td>HDFC</td>
      <td>2020-01-31 15:29:00</td>
      <td>2418.05</td>
      <td>2418.05</td>
      <td>2416.00</td>
      <td>2416.90</td>
      <td>14</td>
    </tr>
  </tbody>
</table>
<p>8625 rows × 7 columns</p>
</div>


# Yearly Data


```python
df = z_data.get_year_data(stock_name, year=2021)
display(df)
```


<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Scrip</th>
      <th>Date Time</th>
      <th>Open</th>
      <th>High</th>
      <th>Low</th>
      <th>Close</th>
      <th>Volume</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>HDFC</td>
      <td>2021-01-01 09:15:00</td>
      <td>2545.00</td>
      <td>2554.20</td>
      <td>2541.30</td>
      <td>2542.05</td>
      <td>590</td>
    </tr>
    <tr>
      <th>1</th>
      <td>HDFC</td>
      <td>2021-01-01 09:16:00</td>
      <td>2546.45</td>
      <td>2552.65</td>
      <td>2544.95</td>
      <td>2552.40</td>
      <td>562</td>
    </tr>
    <tr>
      <th>2</th>
      <td>HDFC</td>
      <td>2021-01-01 09:17:00</td>
      <td>2552.40</td>
      <td>2553.50</td>
      <td>2550.00</td>
      <td>2553.50</td>
      <td>443</td>
    </tr>
    <tr>
      <th>3</th>
      <td>HDFC</td>
      <td>2021-01-01 09:18:00</td>
      <td>2553.50</td>
      <td>2553.50</td>
      <td>2549.65</td>
      <td>2551.60</td>
      <td>234</td>
    </tr>
    <tr>
      <th>4</th>
      <td>HDFC</td>
      <td>2021-01-01 09:19:00</td>
      <td>2551.60</td>
      <td>2551.95</td>
      <td>2548.50</td>
      <td>2549.95</td>
      <td>123</td>
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
      <th>92764</th>
      <td>HDFC</td>
      <td>2021-12-31 15:25:00</td>
      <td>2588.55</td>
      <td>2588.55</td>
      <td>2586.20</td>
      <td>2587.00</td>
      <td>115</td>
    </tr>
    <tr>
      <th>92765</th>
      <td>HDFC</td>
      <td>2021-12-31 15:26:00</td>
      <td>2585.30</td>
      <td>2585.30</td>
      <td>2585.30</td>
      <td>2585.30</td>
      <td>66</td>
    </tr>
    <tr>
      <th>92766</th>
      <td>HDFC</td>
      <td>2021-12-31 15:27:00</td>
      <td>2585.30</td>
      <td>2588.00</td>
      <td>2585.30</td>
      <td>2588.00</td>
      <td>11</td>
    </tr>
    <tr>
      <th>92767</th>
      <td>HDFC</td>
      <td>2021-12-31 15:28:00</td>
      <td>2588.00</td>
      <td>2588.00</td>
      <td>2582.30</td>
      <td>2582.30</td>
      <td>197</td>
    </tr>
    <tr>
      <th>92768</th>
      <td>HDFC</td>
      <td>2021-12-31 15:29:00</td>
      <td>2582.30</td>
      <td>2588.40</td>
      <td>2582.30</td>
      <td>2587.65</td>
      <td>7</td>
    </tr>
  </tbody>
</table>
<p>92769 rows × 7 columns</p>
</div>


# Download data from given year to present time


```python
# csv file download at working directory
df = z_data.download_data_from_year(stock_name, year=2020)
display(df)
```

    Downloading...
    


<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Scrip</th>
      <th>Date Time</th>
      <th>Open</th>
      <th>High</th>
      <th>Low</th>
      <th>Close</th>
      <th>Volume</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>HDFC</td>
      <td>2020-01-01 09:15:00</td>
      <td>2417.00</td>
      <td>2420.70</td>
      <td>2414.15</td>
      <td>2415.30</td>
      <td>516</td>
    </tr>
    <tr>
      <th>1</th>
      <td>HDFC</td>
      <td>2020-01-01 09:16:00</td>
      <td>2415.30</td>
      <td>2417.55</td>
      <td>2414.10</td>
      <td>2415.00</td>
      <td>555</td>
    </tr>
    <tr>
      <th>2</th>
      <td>HDFC</td>
      <td>2020-01-01 09:17:00</td>
      <td>2415.00</td>
      <td>2415.75</td>
      <td>2414.95</td>
      <td>2415.00</td>
      <td>331</td>
    </tr>
    <tr>
      <th>3</th>
      <td>HDFC</td>
      <td>2020-01-01 09:18:00</td>
      <td>2415.00</td>
      <td>2421.40</td>
      <td>2415.00</td>
      <td>2421.00</td>
      <td>191</td>
    </tr>
    <tr>
      <th>4</th>
      <td>HDFC</td>
      <td>2020-01-01 09:19:00</td>
      <td>2421.00</td>
      <td>2422.70</td>
      <td>2420.95</td>
      <td>2420.95</td>
      <td>14</td>
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
      <th>279510</th>
      <td>HDFC</td>
      <td>2022-12-30 15:25:00</td>
      <td>2642.10</td>
      <td>2645.00</td>
      <td>2641.35</td>
      <td>2642.35</td>
      <td>185</td>
    </tr>
    <tr>
      <th>279511</th>
      <td>HDFC</td>
      <td>2022-12-30 15:26:00</td>
      <td>2642.35</td>
      <td>2642.40</td>
      <td>2642.35</td>
      <td>2642.40</td>
      <td>5</td>
    </tr>
    <tr>
      <th>279512</th>
      <td>HDFC</td>
      <td>2022-12-30 15:27:00</td>
      <td>2642.40</td>
      <td>2644.45</td>
      <td>2640.55</td>
      <td>2640.55</td>
      <td>106</td>
    </tr>
    <tr>
      <th>279513</th>
      <td>HDFC</td>
      <td>2022-12-30 15:28:00</td>
      <td>2640.55</td>
      <td>2644.00</td>
      <td>2640.25</td>
      <td>2640.25</td>
      <td>26</td>
    </tr>
    <tr>
      <th>279514</th>
      <td>HDFC</td>
      <td>2022-12-30 15:29:00</td>
      <td>2640.25</td>
      <td>2641.15</td>
      <td>2640.05</td>
      <td>2640.45</td>
      <td>61</td>
    </tr>
  </tbody>
</table>
<p>279515 rows × 7 columns</p>
</div>