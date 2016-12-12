#!/usr/local/bin/python
#-*- coding: utf-8 -*-

import stock_data_getter as sdg
#sdg = __import__('stock_data_getter')

# 생성 데이터 확인
sdg.init_stock_data(df_kospi, df_kosdaq)

# 관심 종목 입력
