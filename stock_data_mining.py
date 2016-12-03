import pandas as pd
import numpy as np
import urllib
import datetime, time

from bs4 import BeautifulSoup
from datetime import datetime
from dateutil.parser import parse
from pandas import DataFrame, Series
from pandas_datareader import data, wb
from urllib.request import urlopen

# 주식명 웹입력
stock_name = 'LG'

# 주식 등록종목 코드확인
stock_reg_file = './data/total.xls'
stock_reg_df =pd.read_excel(stock_reg_file)
stock_reg_info = stock_reg_df[[stock_reg_df.columns[1], stock_reg_df.columns[2], stock_reg_df.columns[4]]]

code = stock_reg_info[stock_reg_info['기업명'] == stock_name]['종목코드'].values[0]
stockItem = str(code).zfill(6)
print(stock_name, stockItem)
#stockItem = '005930'

# 구글 파이낸스에서 해당 종목 정보 받기
columns = ['Open', 'High', 'Low', 'Close', 'Volume']
start_date = datetime(2003, 1, 1)

df = data.DataReader(
    "KRX" + ":" + stockItem, 
    "google", 
    start_date,
    #datetime(2003, 1, 3) #TEST
    datetime.now()
)

import datetime, time

d = df.index[-1]
end_date = datetime.date(d.year, d.month, d.day) + datetime.timedelta(days=1)
today = datetime.date.today()

# 부족한 데이터 날짜 범위 구하기
delta = today - end_date
need_web_scrap = True

if delta.days == 0 :
    need_web_scrap = False
    delta_dates = pd.date_range(end_date.strftime('%Y/%m/%d'), periods=1)
else:
    delta_dates = pd.date_range(end_date.strftime('%Y/%m/%d'), periods=delta.days)

# 스크랩핑 정보 담을 DataFrame 생성
add_data = np.empty((len(delta_dates), len(columns)))
add_data[:] = np.NAN # NaN 값으로 초기화
add_df = DataFrame(add_data, index=delta_dates ,columns=columns)

if(need_web_scrap):
    # 네이버에서 부족한 날짜에 해당하는 정보 Web 스크랩핑
    url = 'http://finance.naver.com/item/sise_day.nhn?code='+ stockItem
    html = urlopen(url)  
    source = BeautifulSoup(html.read(), "html.parser")

    maxPage=source.find_all("table",align="center")

    mp = maxPage[0].find_all("td",class_="pgRR")
    mpNum = int(mp[0].a.get('href').split("page=")[1])


    # 스크랩핑 정보 DataFrame 추가하기
    stop_date = datetime.date(delta_dates[0].year, delta_dates[0].month, delta_dates[0].day).strftime('%Y.%m.%d')

    for page in range(1, mpNum+1):
        url = 'http://finance.naver.com/item/sise_day.nhn?code=' + stockItem +'&page='+ str(page)
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
                    add_df.ix[date, columns[3]] = close
                except:
                    #add_df = add_df.drop(date, 0)
                    continue

                x = srlists[i].find_all("td",class_="num")
                add_df.ix[date, columns[0]] = x[2].text
                add_df.ix[date, columns[1]] = x[3].text
                add_df.ix[date, columns[2]] = x[4].text
                add_df.ix[date, columns[4]] = x[5].text
                #print(date, close)

        if (status):
            break

# NaN 컬럼 삭제 및 오름차순 정렬
add_df = add_df.dropna().sort_index()
df = df.append(add_df)

# csv 파일 저장
df.to_csv('./data/KRX_' + stockItem + '.csv')
