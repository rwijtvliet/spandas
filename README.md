# Spandas

Working with timeseries using `pandas`, I kept running into the same limitations of the `DatetimeIndex` (no 'duration' associated with datapoint) and `PeriodIndex` (no timezone support), so I'm trying to roll my own.

## Concept

Data is kept in `SpanSeries` objects (which are collected in `SpanDataFrame` objects).

These have two defining properties that differentiate them from the usual `Series` (and `DataFrame`) objects:

* A `SpanIndex`, which is an index where each element is a time span.

  A time span is a left-closed interval with a (possibly timezone aware) timestamp on each end.

  Time spans in a `SpanIndex` do not have to be of uniform spacing; neither with a fixed timedelta (i.e. 1h) nor with a fixed 'natural' length (i.e., one month).

* A `.rc` property on each column, that defines their "nature" and resample characteristic. 

### Example 1

As an example, starting with this `SpanDataFrame`, with taxi cab data: 

| index    | n    | d    | v    | r    | rs   |
| -------- | ---- | ---- | ---- | ---- | ---- |
| [t0, t1) | 14   | 200  | 45   | 500  | 2.5  |
| [t1, t2) | 15   | 331  | 51   | 621  | 1.88 |
| [t2, t3) | 21   | 255  | 48   | 553  | 2.17 |

With columns `d`: distance driven [km], `n `: number of trips, `v`: average velocity [km/h], `r`: revenue (i.e., income) [Eur], `sr`: specific revenue, i.e., in [Eur/km].

When resampling, these quantities are treated differently, depending on their "resample chararcteristic". 

##### Downsampling

To combine the three rows into one time span, the following rules were applied:

| index    | n    | d    | v     | r    | rs   |
| -------- | ---- | ---- | ----- | ---- | ---- |
| [t0, t3) | 50   | 786  | 48.75 | 1674 | 2.13 |

* `d`, `n`, `r`: sum of values in subspans
* `v`: average, weighted by subspan duration (`timedelta` property)
* `rs`: average, weighted by subspan distance (value in column `d`)

##### Upsampling

To split the first time span into two: [t0, t'), [t', t1), with t' at the 60% point between t0 and t1:

| index    | d    | n    | v    | r    | rs   |
| -------- | ---- | ---- | ---- | ---- | ---- |
| [t0, t') | 180  | 8.4  | 45   | 300  | 2.5  |
| [t', t1) | 120  | 5.6  | 45   | 200  | 2.5  |

* `d`, `n`, `r`: superspan value distributed over subspans in proportion to their duration (`timedelta` property)
* `v`, `rs`: superspan value copied over into each subspan

### Example 2

Another example is in this `SpanDataFrame`, with stock price data:

| index    | q    | ps    | po   | ph   | pl   | pc   |
| -------- | ---- | ----- | ---- | ---- | ---- | ---- |
| [t0, t1) | 2234 | 14.01 | 43   | 52   | 42   | 45   |
| [t1, t2) | 3213 | 15.48 | 46   | 58   | 37   | 40   |
| [t2, t3) | 1826 | 21.21 | 38   | 42   | 30   | 41   |

With `q`: number of shares traded in each timespan, `ps`: settlement price (i.e., average trading price) [Eur], and the other columns the open, high, low, and closing prices [Eur].

##### Downsampling

| index    | q    | ps    | po   | ph   | pl   | pc   |
| -------- | ---- | ----- | ---- | ---- | ---- | ---- |
| [t0, t3) | 7273 | 16.46 | 43   | 58   | 30   | 41   |

* `q`: sum of values in subspans
* `ps`: average, weighted by subspan trading volume (value in column  `q`)
* `po`: value of left-most (i.e., first) subspan
* `ph`: max of values in subspans
* `pl`: min of values in subspans
* `pc`: value of right-most (i.e. last) subspan 

##### Upsampling

Same t' as before:

| index    | q      | ps    | po   | ph   | pl   | pc   |
| -------- | ------ | ----- | ---- | ---- | ---- | ---- |
| [t0, t') | 1345.8 | 16.46 | 43   | na   | na   | na   |
| [t', t1) | 897.2  | 16.46 | na   | na   | na   | 45   |

* `q`: superspan value distributed over subspans in proportion to their duration (`timedelta` property)
* `ps`: superspan value copied over into each subspan
* `po`: superspan value copied over into left-most subspan; `na` in others
* `ph`: `na` (at least one of subspans will have superspan's `ph` value, but it's unknowable, which)
* `pl`: `na` (same)
* `pc`: superspan value copied over into right-most subspan: `na` in others

## Resampling characteristic

The following values for the resampling characteristic are available. Note that, when downsampling, the original time spans are the 'subspans' that are being combined into a new, longer 'superspan'; when upsampling, each original time span is a 'superspan' that is being turned into multiple shorter 'subspans'.

|      |                                 | Downsampling behaviour: superspan value equals...            | Upsampling behaviour: subspan values equal...                |
| ---- | ------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| `sd` | "sum; duration-weighted split"  | ...sum of subspan values                                     | ...fraction of superspan value, in proportion to their duration |
| `su` | "sum; unweighted split"         | ...sum of subspan values                                     | ...equal part of superspan value (i.e., each subspan gets same value) |
| `ad` | "average, weighted by duration" | ...average of subspan values, weighted by their duration (`timedelta` property) | ...superspan value                                           |
| `au` | "average, unweighted"           | ...average of subspan values, equal weights                  | ...superspan value                                           |
| `ao` | "average, weighted by other"    | ...average of subspan values, weighted by other column's values | ...superspan value                                           |
| `po` | "opening price"                 | ...value of left-most (i.e., first) subspan                  | ...superspan value for left-most subspan; `na` for all others |
| `ph` | "high price"                    | ...maximum subspan value                                     | `na`                                                         |
| `pl` | "low price"                     | ...minimum subspan value                                     | `na`                                                         |
| `pc` | "closing price"                 | ...value of right-most (i.e., last) subspan                  | ...superspan value for right-most subspan: `na` for all others |
|      |                                 |                                                              |                                                              |

With a superspan with value *V*, and *n* subspans with durations *d<sub>i</sub>* and values *v<sub>i</sub>*:
$$
\begin{aligned}
V=\sum v_i  & & \left\{ \begin{aligned} 
v_i  =& \frac{d_i}{\sum{d_i}} V \\  
v_i  =& \frac{1}{n} V
\end{aligned} \right. \\

\left. \begin{aligned} 
V  =& \frac{\sum{d_i vi}}{\sum d_i} \\  
V  =& \frac{1}{n} \sum v_i \\ 
V  =& \frac{\sum o_i v_i}{\sum o_i}
\end{aligned} \right\} & & v_i = V
\end{aligned} \\

v_i = \left\{\begin{aligned} V \text{ if $i=0$}\\\text{na if $i\neq0$}\end{aligned} \right.
$$

## Api, sample usage

```python
"""
Sample api usage.
"""

import spandas as spd

si = spd.span_range(['2020-01-01', '2020-01-03 12:00', '2020-01-07', '2020-01-10'])
#SpanIndex([('2020-01-01 00:00:00', '2020-01-03 12:00:00'),
#           ('2020-01-03 12:00:00', '2020-01-07 00:00:00'), 
#           ('2020-01-07 00:00:00', '2020-01-10 00:00:00')]
si.to_timedelta()
#TimedeltaIndex(['1 day, 12 hours', '3 days, 12 hours', '3 days'],
#               dtype='timedelta64[ns]', freq=None)

customers = spd.SpanSeries([14, 15, 21], index=si, name='n', rc='sd')
customers.aggregate()
#50
velocity = spd.SpanSeries([45, 51, 48], index=si, name='v', rc='ad')
velocity.aggregate()
#48.75

taxi = spd.SpanDataFrame({'d': [200, 331, 255], 'rs': [2.5, 1.88, 2.17]}, 
                         index=si, rc=['sd', ('so', 'd')])
taxi.aggregate()
#d     780.00
#rs      2.13
#dtype: float64

#resample characteristic can be determined from combination
taxi['r'] = taxi['d'] * taxi['rs']
taxi['r']
#0    500.00
#1    622.28
#2    553.35
#dtype: float64, rc='sd'
taxi['error'] = taxi['d'] + taxi['rs']
#ValueError: addition invalid operation between columns with resample characteristics 'sd' and 'ao'.
```

