# Download-historical-Stock-data

# Importing Library


```python
from Pyzdata import pyzdata
```

###         Login Zerodha            


```python
zdata = pyzdata(userid="USERID", password="PASSWORD", totp=123456)
```

# Instrument token


```python
# Get instrument token for given trading symbol
instrument_token = zdata.get_instrument_token(tradingsymbol="SBIN", exchange="NSE")
```

# Monthly Data


```python
df = zdata.get_month_data(instrument_token, year=2023, month=2, interval=zdata.interval.minute1, oi=False)
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
      <td>SBIN</td>
      <td>2023-02-01 09:15:00</td>
      <td>561.40</td>
      <td>561.80</td>
      <td>557.80</td>
      <td>558.70</td>
      <td>362695</td>
    </tr>
    <tr>
      <th>1</th>
      <td>SBIN</td>
      <td>2023-02-01 09:16:00</td>
      <td>558.30</td>
      <td>559.50</td>
      <td>558.10</td>
      <td>559.05</td>
      <td>215450</td>
    </tr>
    <tr>
      <th>2</th>
      <td>SBIN</td>
      <td>2023-02-01 09:17:00</td>
      <td>558.65</td>
      <td>559.15</td>
      <td>558.20</td>
      <td>559.15</td>
      <td>171662</td>
    </tr>
    <tr>
      <th>3</th>
      <td>SBIN</td>
      <td>2023-02-01 09:18:00</td>
      <td>559.10</td>
      <td>560.20</td>
      <td>559.00</td>
      <td>560.05</td>
      <td>153677</td>
    </tr>
    <tr>
      <th>4</th>
      <td>SBIN</td>
      <td>2023-02-01 09:19:00</td>
      <td>560.00</td>
      <td>560.10</td>
      <td>559.70</td>
      <td>560.00</td>
      <td>131938</td>
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
      <th>7120</th>
      <td>SBIN</td>
      <td>2023-02-27 15:25:00</td>
      <td>527.50</td>
      <td>527.50</td>
      <td>527.40</td>
      <td>527.50</td>
      <td>38693</td>
    </tr>
    <tr>
      <th>7121</th>
      <td>SBIN</td>
      <td>2023-02-27 15:26:00</td>
      <td>527.50</td>
      <td>528.00</td>
      <td>527.00</td>
      <td>527.35</td>
      <td>128062</td>
    </tr>
    <tr>
      <th>7122</th>
      <td>SBIN</td>
      <td>2023-02-27 15:27:00</td>
      <td>527.20</td>
      <td>527.35</td>
      <td>526.90</td>
      <td>527.10</td>
      <td>77312</td>
    </tr>
    <tr>
      <th>7123</th>
      <td>SBIN</td>
      <td>2023-02-27 15:28:00</td>
      <td>527.10</td>
      <td>527.45</td>
      <td>527.05</td>
      <td>527.20</td>
      <td>47078</td>
    </tr>
    <tr>
      <th>7124</th>
      <td>SBIN</td>
      <td>2023-02-27 15:29:00</td>
      <td>527.50</td>
      <td>527.55</td>
      <td>527.30</td>
      <td>527.50</td>
      <td>83278</td>
    </tr>
  </tbody>
</table>
<p>7125 rows × 7 columns</p>
</div>


# Yearly Data


```python
df = zdata.get_year_data(instrument_token, year=2021, interval=zdata.interval.minute30)
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
      <td>SBIN</td>
      <td>2021-01-01 09:15:00</td>
      <td>274.90</td>
      <td>278.05</td>
      <td>274.50</td>
      <td>277.75</td>
      <td>4306013</td>
    </tr>
    <tr>
      <th>1</th>
      <td>SBIN</td>
      <td>2021-01-01 09:45:00</td>
      <td>277.75</td>
      <td>278.50</td>
      <td>277.20</td>
      <td>277.45</td>
      <td>2394262</td>
    </tr>
    <tr>
      <th>2</th>
      <td>SBIN</td>
      <td>2021-01-01 10:15:00</td>
      <td>277.40</td>
      <td>277.70</td>
      <td>276.75</td>
      <td>277.25</td>
      <td>1312581</td>
    </tr>
    <tr>
      <th>3</th>
      <td>SBIN</td>
      <td>2021-01-01 10:45:00</td>
      <td>277.20</td>
      <td>277.90</td>
      <td>277.20</td>
      <td>277.75</td>
      <td>854730</td>
    </tr>
    <tr>
      <th>4</th>
      <td>SBIN</td>
      <td>2021-01-01 11:15:00</td>
      <td>277.75</td>
      <td>278.20</td>
      <td>277.50</td>
      <td>277.70</td>
      <td>1133743</td>
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
      <td>SBIN</td>
      <td>2021-12-30 13:15:00</td>
      <td>453.65</td>
      <td>453.75</td>
      <td>452.10</td>
      <td>453.25</td>
      <td>455789</td>
    </tr>
    <tr>
      <th>3100</th>
      <td>SBIN</td>
      <td>2021-12-30 13:45:00</td>
      <td>453.25</td>
      <td>453.75</td>
      <td>451.55</td>
      <td>451.65</td>
      <td>520563</td>
    </tr>
    <tr>
      <th>3101</th>
      <td>SBIN</td>
      <td>2021-12-30 14:15:00</td>
      <td>451.65</td>
      <td>452.00</td>
      <td>448.55</td>
      <td>449.05</td>
      <td>1760595</td>
    </tr>
    <tr>
      <th>3102</th>
      <td>SBIN</td>
      <td>2021-12-30 14:45:00</td>
      <td>449.05</td>
      <td>452.80</td>
      <td>448.50</td>
      <td>452.50</td>
      <td>11066556</td>
    </tr>
    <tr>
      <th>3103</th>
      <td>SBIN</td>
      <td>2021-12-30 15:15:00</td>
      <td>452.45</td>
      <td>453.85</td>
      <td>451.10</td>
      <td>453.05</td>
      <td>8562346</td>
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
      <th>open_interest</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>SBIN</td>
      <td>2020-01-01</td>
      <td>334.70</td>
      <td>335.95</td>
      <td>332.15</td>
      <td>334.45</td>
      <td>17379320</td>
      <td>0</td>
    </tr>
    <tr>
      <th>1</th>
      <td>SBIN</td>
      <td>2020-01-02</td>
      <td>334.50</td>
      <td>339.85</td>
      <td>333.35</td>
      <td>339.30</td>
      <td>20324236</td>
      <td>0</td>
    </tr>
    <tr>
      <th>2</th>
      <td>SBIN</td>
      <td>2020-01-03</td>
      <td>337.95</td>
      <td>337.95</td>
      <td>332.00</td>
      <td>333.70</td>
      <td>21853208</td>
      <td>0</td>
    </tr>
    <tr>
      <th>3</th>
      <td>SBIN</td>
      <td>2020-01-06</td>
      <td>331.70</td>
      <td>331.70</td>
      <td>317.70</td>
      <td>319.00</td>
      <td>35645325</td>
      <td>0</td>
    </tr>
    <tr>
      <th>4</th>
      <td>SBIN</td>
      <td>2020-01-07</td>
      <td>324.45</td>
      <td>327.00</td>
      <td>315.40</td>
      <td>318.40</td>
      <td>50966826</td>
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
      <th>995</th>
      <td>SBIN</td>
      <td>2024-01-02</td>
      <td>641.35</td>
      <td>648.00</td>
      <td>633.85</td>
      <td>639.45</td>
      <td>15164482</td>
      <td>0</td>
    </tr>
    <tr>
      <th>996</th>
      <td>SBIN</td>
      <td>2024-01-03</td>
      <td>639.35</td>
      <td>648.00</td>
      <td>635.80</td>
      <td>643.45</td>
      <td>14571772</td>
      <td>0</td>
    </tr>
    <tr>
      <th>997</th>
      <td>SBIN</td>
      <td>2024-01-04</td>
      <td>642.50</td>
      <td>646.40</td>
      <td>638.65</td>
      <td>642.75</td>
      <td>13883388</td>
      <td>0</td>
    </tr>
    <tr>
      <th>998</th>
      <td>SBIN</td>
      <td>2024-01-05</td>
      <td>645.00</td>
      <td>651.75</td>
      <td>637.75</td>
      <td>641.95</td>
      <td>15984585</td>
      <td>0</td>
    </tr>
    <tr>
      <th>999</th>
      <td>SBIN</td>
      <td>2024-01-08</td>
      <td>640.00</td>
      <td>645.00</td>
      <td>625.05</td>
      <td>627.00</td>
      <td>14689705</td>
      <td>0</td>
    </tr>
  </tbody>
</table>
<p>1000 rows × 8 columns</p>
</div>
