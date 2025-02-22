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

default_data = np.empty((1, len(columns)))
default_data[:] = np.NAN

def get_idx_today():
    check_hour = dtdt.now().hour
    check_min = dtdt.now().minute

    print(str(check_hour) + ':' + str(check_min))

    if check_hour == 15:
        if (check_min > 30):
            today = dt.date.today()
    elif check_hour > 15:
        today = dt.date.today()
    else:
        today = dt.date.today() - dt.timedelta(days=1)
    return today

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

def get_gold_cross_info():
    df = pd.read_csv('./data/csv/daily/gold_cross.csv', index_col="Date")
    return df

def get_deal_trend_info(category):
    df = pd.read_csv('./data/csv/daily/' + category + '_deal_trend.csv', index_col='Date')
    return df

def check_csv_file(category, item):
    if os.path.isdir("./data/csv"):
        if os.path.isfile("./data/csv/" + category + '_' + item + '.csv'):
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

def create_investor_deal_trend(category, num=0):
    columns = ['Date', '개인', '외국인', '기관계',
                '금융투자', '보험', '투신', '은행',
                '기타금융기관', '연기금', '기타법인']

    df = pd.DataFrame(default_data, columns=columns)

    date = get_idx_today().strftime('%Y%m%d')
    url = 'http://finance.naver.com/sise/investorDealTrendDay.nhn?bizdate=' + date + '&sosok='
    if category == 'kospi':
        url = url+'01'
    else:
        url = url+'02'

    html = urlopen(url)
    source = BeautifulSoup(html.read(), "html.parser")

    s_table=source.find_all("table", class_="type_1")
    s_td = s_table[0].find_all("td")

    maxPage = source.find_all("table", align="center")
    mp = maxPage[0].find_all("td",class_="pgRR")

    try:
        mpNum = int(mp[0].a.get('href').split("page=")[1])
    except:
        mpNum = 1

    if num != 0:
        mpNum = num

    idx=0
    for page in range(1, mpNum+1):
        html = urlopen(url +'&page='+ str(page))
        source = BeautifulSoup(html.read(), "html.parser")
        srlists=source.find_all("tr")
        isCheckNone = None

        status = False
        #print(idx)
        for i in range(1,len(srlists)-1):
            #endlist = srlists[i].find_all("td",class_="blank_09")[0].text
            dealTrend = srlists[i].find_all("td")
            num = len(dealTrend)
            if (num-1) == i:
                break

            if (num == len(columns)):
                for j in range(num):
                    if j == 0:
                        date = dealTrend[j].text.split('.')
                        year = 2000 + int(date[0])
                        mon =  int(date[1])
                        day =  int(date[2])
                        df.ix[idx, columns[j]] = dt.date(year, mon, day).strftime('%Y.%m.%d')
                    else:
                        df.ix[idx, columns[j]] = dealTrend[j].text
                idx += 1

            else:
                continue
    df.to_csv('./data/csv/daily/' + category + '_deal_trend.csv', index=False)
    return df

def create_gold_cross_items():
    columns = ['Date', '종목코드', '현재가', '상승폭',
               '등락률', '거래량', '시가', '고가',
               ' 저가', 'PER', 'ROE']
    df = pd.DataFrame(default_data, columns=columns)
    date = get_idx_today().strftime('%Y.%m.%d')

    url = 'http://finance.naver.com/sise/item_gold.nhn'
    html = urlopen(url)
    source = BeautifulSoup(html.read(), "html.parser")

    s_table=source.find_all("table", class_="type_5")
    s_td = s_table[0].find_all("td")
    s_number = s_table[0].find_all("td", class_="number")

    code = []
    for td in s_td:
        try:
            code.append(td.a.get('href').split("code=")[1])
        except:
            continue

    #default_data = np.empty((mp_num, len(columns)))
    #default_data[:] = np.NAN

    total_item_num = int(len(s_number) / 9)
    print(total_item_num)
    for i in range(total_item_num):
        df.ix[i, columns[0]] = date
        df.ix[i, columns[1]] = code[i]
        if i == 0:
            for j in range(len(columns)-2):
                df.ix[i, columns[j+2]] = s_number[j].text.strip()
        else:
             for j in range(len(columns)-2):
                df.ix[i, columns[j+2]] = s_number[(i*9)+j].text.strip()

    df.to_csv('./data/csv/daily/gold_cross.csv', index=False)

def init_stock_data(kospi, kosdaq):  
    create_stock_csv_file(kospi, "KRX", len(kospi))
    create_stock_csv_file(kosdaq, "KOSDAQ", len(kosdaq))

def update_stock_data(item, kospi, kosdaq):
    try:
        code = kospi[kospi['기업명'] == item]['종목코드'].values[0]
        category = 'KRX'
    except:

        try:
            code = kosdaq[kosdaq['기업명'] == item]['종목코드'].values[0]
            category = 'KOSDAQ'
        except:
            sys.exit("ERROR - Unregisterd Stock!")

    stock_item = str(code).zfill(6)
    print(category, item, stock_item)

    # 조회 종목 CSV 파일 확인
    file_path = './data/csv/' 
    file_name = category + '_' + stock_item + '.csv'

    csv_file = True
    if check_csv_file(category, stock_item):
        print ("Exist csv file:" + file_name)
        try:
            df = pd.read_csv(file_path + file_name, index_col='Unnamed: 0')
        except:
            df = pd.read_csv(file_path + file_name, index_col='Date')
            df = df.drop(df[-10:].index) # TEST1
            #df = df.drop(['2016.12.06', '2016.12.07', '2016.12.08']) # TEST2
    else:
        df = DataFrame(default_data ,columns=columns, index=['1980.1.1'])
        csv_file = False

    df.index.name = 'Date'
    # CSV 파일의 최종 날짜 정보와 조회시점의 정보 누락분 확인
    #print("Check delta date")
    d = [int(x) for x in df.index[-1].split('.')]
    end_date = dtdt(d[0], d[1], d[2])
    print(end_date)

    check_hour = dtdt.now().hour
    check_min = dtdt.now().minute

    print(str(check_hour) + ':' + str(check_min))
    market_closed = True

    if check_hour == 15:
        if (check_min > 30):
            today = dt.date.today()
    elif check_hour > 15:
        today = dt.date.today()
    else:
        market_closed = False
        today = dt.date.today() - dt.timedelta(days=1)

    delta = dtdt(today.year, today.month, today.day) - end_date

    # 구글 파이낸스에서 해당 종목 정보 받기
    print("delta days:" + str(delta.days))
    if delta.days <= 0 :
        delta_dates = pd.date_range(end_date.strftime('%Y.%m.%d'), periods=1)
    else:
        delta_dates = pd.date_range(end_date.strftime('%Y.%m.%d'), periods=delta.days)
    need_web_scrap = True
    add_df = DataFrame(default_data, columns=columns)

    if csv_file:
        if delta.days > 30:
            try:
                add_df = data.DataReader(
                    category + ":" + stock_item,
                    "google",
                    end_date,
                    dtdt(today.year, today.month, today.day)
                )
                add_df.index =  pd.to_datetime(add_df.index).strftime('%Y.%m.%d')

                need_web_scrap = False
            except:
                print ("Exception to get info via GOOGLE")


    if(need_web_scrap):
        add_df = get_info_with_web_scrap(stock_item, add_df, delta_dates)
        add_df = add_df.dropna().sort_index()
        if (market_closed):
            print("Market closed")
        else:
            add_df.drop(add_df[-1:].index)
        print("Complete to get stock info via NAVER")

    if delta.days > 0 :
        df = df.append(add_df).dropna()
        #if not os.path.isfile(file_path+file_name):
        df.to_csv(file_path+file_name)
        #else:
        #    df.to_csv(file_path+file_name, mode='a',header=True, index=True, index_label='Date')