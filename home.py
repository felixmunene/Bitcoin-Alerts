from flask import Flask, request, render_template
import requests as req
import dateparser
import pytz
import json
import time
import pandas as pd
from datetime import datetime
app = Flask(__name__)
transactionsurl = "https://api.whale-alert.io/v1/transactions/"
transactionurl = "https://api.whale-alert.io/v1/transaction/"
statusurl = "https://api.whale-alert.io/v1/status"
api_key = "Dt2SXrzJA5VJ780xJtFMFdcW8JVkTS32"
response_dict={}
@app.route('/')
def hello_world():    
    df = pd.DataFrame()
    # r = transactionsquery(api_key,500000,'15 Minutes ago UTC')
    # data = r.json()
    # result_str=json.dumps(data)
    # result_tuple = json.loads(result_str)
    # if result_tuple.get('result') == 'success':
    #     transaction_list=result_tuple['transactions']
    #     for i in transaction_list:
    #        response = transactionquery(i['blockchain'],i['hash'],api_key)
    #        print(respponse.content)
    
    try:
        r = transactionsquery(api_key,500000,'10 Minutes ago UTC')
    except:
        print('transactions query failed')
    try:
       result =  parseresponse(r)
    except:
        print('parse response failed')
    try:
        if result.get('result')=='success':
            transaction_list=result['transactions']
            for i in transaction_list:
                try:
                    response = transactionquery(i['blockchain'],i['hash'],api_key)
                except:
                    print('transactionquery execution failure')
                try:
                    transactionresults = parseresponse(response)                    
                except:
                    print('Error parsing the transaction query result')
                if transactionresults.get('result')=='success':
                    transaction_data = transactionresults['transactions']
                    for i in transaction_data:
                        i.pop('from')
                        i.pop('to')
                        for key in i:
                            set_key(response_dict,key,i[key])
                        #print(type(i))
                        
    except:
        print(result)
    df = pd.DataFrame.from_dict(response_dict)
    return render_template('simple.html',  tables=[df.to_html(classes='data')], titles=df.columns.values)
def set_key(dictionary,key,value):
    if key not in dictionary:
        dictionary[key]= value
    elif type(dictionary[key]) == list:
        dictionary[key].append(value)
    else:
        dictionary[key] = [dictionary[key],value]
def statuscheck(api_key):
    #takes a parameter of api key 
    PARAMS = {'api_key:api_key'}
    r = req.get(url=statusurl,params=PARAMS)
    return r
def parseresponse(r):
    try:
        data = r.json()
    except ValueError as e:
        print(e)
    try:
        result_str= json.dumps(data)
        result_tuple = json.loads(result_str)
    except ValueError as e:
        print(e)
    return result_tuple

def transactionquery(blockchain,hash,api_key):
    #takes parameters as follows
    #blockchain --string --The blockchain to search for the specific hash (lowercase)
    #hash --string --The hash of the transaction to return
    PARAMS = {'api_key':api_key}
    r = req.get(url=(transactionurl+blockchain+'/'+hash),params=PARAMS)
    return r
def transactionsquery(api_key,min_value,start_str,end_str=None):
    #takes parameters as follows
    #start--unix --int timestamp for retrieving transactions from timestamp (exclusive)
    #end --unix --int timestamp for retrieving transactions to timestamp (inclusive)
    #cursor --string --Pagination key from the previous response. Recommended when retrieving transactions in intervals
    #min_value --int -- Minimum USD value of transactions returned (value at time of transaction). Allowed minimum value varies per plan ($500k for Personal, $100k for Personal).
    #limit --int --Maximum number of results returned. Default 100, max 100.
    # currency --string --Returns transactions for a specific currency code. Returns all currencies by default.
    starttime = date_to_milliseconds(start_str) 
    #print(starttime)
    if end_str:
        endtime = date_to_milliseconds(end_str)
    else:
        endtime = None
    PARAMS = {'api_key':api_key,'min_value':min_value,'start':starttime,'end':endtime,'min_value':min_value}
    r = req.get(url=transactionsurl,params=PARAMS)
    return r
def date_to_milliseconds(date_str):
    #""":parameter date in redable format i.e "January 01, 2018  "January 01, 2018", "11 hours ago UTC", "now UTC"
     #  :type date_str:str
      #  :example usage : print(date_to_milliseconds("now UTC"))
       # print(date_to_milliseconds("January 01, 2018"))
        #print(date_to_milliseconds("11 hours ago UTC"))
    #""""

    #get epoch time in UTC
    epoch = datetime.utcfromtimestamp(0).replace(tzinfo=pytz.utc)
    #pass our date string
    d = dateparser.parse(date_str)

    # if the date is not timezone aware apply UTC timezone
    if d.tzinfo is None or d.tzinfo.utcoffset(d) is None:
        d = d.replace(tzinfo=pytz.utc)
    # return the difference in time
    return int((d - epoch).total_seconds() * 1.0)

def interval_to_milliseconds(interval):
    """Convert a Binance interval string to milliseconds
    :param interval: Binance interval string 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w
    :type interval: str
    :return:
         None if unit not one of m, h, d or w
         None if string not in correct format
         int value of interval in milliseconds
    """
    ms = None
    seconds_per_unit = {
        "m": 60,
        "h": 60 * 60,
        "d": 24 * 60 * 60,
        "w": 7 * 24 * 60 * 60
    }

    unit = interval[-1]
    if unit in seconds_per_unit:
        try:
            ms = int(interval[:-1]) * seconds_per_unit[unit] * 1000
        except ValueError:
            pass
    return ms
