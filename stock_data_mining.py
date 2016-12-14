#!/usr/local/bin/python
#-*- coding: utf-8 -*-

import stock_data_getter as sdg
#sdg = __import__('stock_data_getter')

item = 'LG'

category = ''
df_kospi = sdg.pd.read_excel(sdg.stock_reg_kospi)
df_kosdaq = sdg.pd.read_excel(sdg.stock_reg_kosdaq)

# 주식 생성 데이터 확인
sdg.init_stock_data(df_kospi, df_kosdaq)

# 주식 데이터 업데이트
sdg.update_stock_data(item, df_kospi, df_kosdaq)
