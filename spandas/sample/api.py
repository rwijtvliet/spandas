#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
                         index=si, rc=['sd', ('ao', 'd')])
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