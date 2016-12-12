#!/usr/local/bin/python
#-*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from datetime import datetime as dtdt
from dateutil.parser import parse
from pandas import DataFrame, Series
from pandas_datareader import data, wb
from urllib.request import urlopen

import datetime as dt
import time
import numpy as np
import os
import pandas as pd
import sys
import urllib

stock_reg_kospi = './data/KOSPI.xls'
stock_reg_kosdaq = './data/KOSDAQ.xls'

columns = ['Open', 'High', 'Low', 'Close', 'Volume']

def get_info_with_web_scrap(item, df, idx_date):
    print("Get stock info using web scraping..")
    
    # 네이버에서 부족한 날짜에 해당하는 정보 Web 스크랩핑
    url = 'http://finance.naver.com/item/sise_day.nhn?code='+ item
    html = urlopen(url)  
    source = BeautifulSoup(html.read(), "html.parser")
    
    maxPage=source.find_all("table",align="center")
    mp = maxPage[0].find_all("td",class_="pgRR")
    
    try:
        mpNum = int(mp[0].a.get('href').split("page=")[1])
    except:
        mpNum = 1
    
    # 스크랩핑 정보 DataFrame 추가하기
    stop_date = dt.date(idx_date[0].year, idx_date[0].month, idx_date[0].day).strftime('%Y.%m.%d')

    for page in range(1, mpNum+1):
        url = 'http://finance.naver.com/item/sise_day.nhn?code=' + item +'&page='+ str(page)
        html = urlopen(url)
        source = BeautifulSoup(html.read(), "html.parser")
        srlists=source.find_all("tr") 
        isCheckNone = None

        status = False

        for i in range(1,len(srlists)-1):
            if(srlists[i].span != isCheckNone):
                date = srlists[i].find_all("td",align="center")[0].text
                close = srlists[i].find_all("td",class_="num")[0].text
                #print(stop_date, date)
                if stop_date >= date:
                    status = True
                    break

                try:
                    df.ix[date, columns[3]] = close
                except:
                    #add_df = add_df.drop(date, 0)
                    continue

                x = srlists[i].find_all("td",class_="num")
                df.ix[date, columns[0]] = x[2].text
                df.ix[date, columns[1]] = x[3].text
                df.ix[date, columns[2]] = x[4].text
                df.ix[date, columns[4]] = x[5].text
                #print(date, close)

        if (status):
            break
    df.index.name = 'Date'
    return df

def check_csv_file(cat, item):
    if os.path.isdir("./data/csv"):
        if os.path.isfile("./data/csv/" + cat + '_' + item + '.csv'):
            return True
    return False

def create_stock_csv_file(df, category, num=10):
    print("Start to create init stock data - " + category)
    
    start_date = dtdt(1980, 1, 1)
    
    for i in range(num):
        # 순서대로 종목 stock_item 가져오기
        try:
            code = str(df.ix[i]['종목코드']).zfill(6)

        except:
            print("ERROR - Unregisterd Stock!")
            continue
        
        if check_csv_file(category, code):
            print("Already exist: " + category + '_' + code + '.csv')
            continue
        
        stock_item = str(code).zfill(6)
        print(category, stock_item)
        start_idx_dates = pd.date_range(start_date.strftime('%Y/%m/%d'), periods=1)
        
        init_data = np.empty((1, len(columns)))
        init_data[:] = np.NAN # NaN 값으로 초기화
        init_df = DataFrame(init_data, index=start_idx_dates ,columns=columns)
        
        get_df = get_info_with_web_scrap(stock_item, init_df, start_idx_dates)
        get_df = get_df.dropna().sort_index()
        get_df.to_csv('./data/csv/' + category + '_' + stock_item + '.csv')

    print("Complete to create init stock data!")

def init_stock_data(df_kospi, df_kosdaq):  
    create_stock_csv_file(df_kospi, "KRX", len(df_kospi))
    create_stock_csv_file(df_kosdaq, "KOSDAQ", len(df_kosdaq))

# 전체 주식 데이터 생성 (최초 1회 수행)
#init_stock_data(df_kospi, df_kosdaq)
