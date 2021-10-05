# requires dateparser package
import dateparser #version 2019 should be install therwise not work
import pytz
import json
import logging
from time import time, strftime, localtime,sleep
from operator import itemgetter
from datetime import datetime,timedelta
import requests
from threading import Thread,Event
import logging
#ENCODE
import  hmac
import hashlib
#from .exceptions import BinanceAPIException, BinanceRequestException, BinanceWithdrawException
#SAVE..........
from xml.etree.ElementTree import ElementTree, tostring
import xml.etree.ElementTree as ET
import  csv
#......
import pandas as pd
import numpy as np
import talib
#........
import os

class BinanceRequestException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        logging.info('BinanceRequestException: %s' % self.message)
        return 'BinanceRequestException: %s' % self.message



class BinanceAPIException(Exception):

    LISTENKEY_NOT_EXIST = '-1125'

    def __init__(self, response):
        self.status_code = 0
        try:
            json_res = response.json()
        except ValueError:
            logging.info('Invalid JSON error message from Binance: {}'.format(response.text))
            self.message = 'Invalid JSON error message from Binance: {}'.format(response.text)
        else:
            self.code = json_res['code']
            self.message = json_res['msg']
        self.status_code = response.status_code
        self.response = response
        self.request = getattr(response, 'request', None)

    def __str__(self):  # pragma: no cover
        logging.info( 'APIError(code=%s): %s' % (self.code, self.message))
        return 'APIError(code=%s): %s' % (self.code, self.message)



class BinanceKlines(object):

    API_URL = 'https://api.binance.com/api'
    WEBSITE_URL = 'https://www.binance.com'
    PUBLIC_API_VERSION = 'v1'
    PRIVATE_API_VERSION = 'v3'
    WITHDRAW_API_VERSION = 'v3'

    def __init__(self, api_key, api_secret, requests_params=None):
        """Binance API Client constructor

        :param api_key: Api Key
        :type api_key: str.
        :param api_secret: Api Secret
        :type api_secret: str.
        :param requests_params: optional - Dictionary of requests params to use for all calls
        :type requests_params: dict.

        """

        #...............
        self.Data_binance_500=None
        self.Kandle_time=None
        self.Kandle_type=None
        self.folder=None
        self.typefile=None
        self.symbol=None
        self.start_date=None
        self.end_date=None
        self.Dire=None
        #...............

        #..............
        '''
         thread1:get data binance(get kandle
           thread2(save csvfile)
           thread3(save xmlfile)
        '''
        #Process Kandle
        self.thread1 = None
        self.stop_thread1 = False
        #...
        #CSV WRITE FILE
        self.thread2 = None
        self.stop_thread2 = False
        #....
        #XML WRITE FILE
        self.thread3 = None
        self.stop_thread3= False
        #...

        #..............
        self.API_KEY = api_key
        self.API_SECRET = api_secret
        self.session = self._init_session()
        self._requests_params = requests_params

        # init DNS and SSL cert
        self.ping()


    def _init_session(self):
        session = requests.session()
        session.headers.update({'Accept': 'application/json',
                                'User-Agent': 'binance/python',
                                'X-MBX-APIKEY': self.API_KEY})
        return session
    def HeadFILE(self):
        header_Write_File = [
            'Open_time',  # Open time
            'Open',  # Open
            'High',  # High
            'Low',  # Low
            'Close',  # Close
            'Volume',  # Volume
            'Close_time',  # Close time
            'Quote_asset_volume',  # Quote asset volume
            'Number_of_trades',  # Number of trades
            'Taker_buy_base_asset_volume',  # Taker buy base asset volume
            'Taker_buy_quote_asset_volume',  # Taker buy quote asset volume
            'Can_be_ignored'  # Can be ignored
        ]
        return  header_Write_File

    def _generate_signature(self, data):

        ordered_data = self._order_params(data)
        query_string = '&'.join(["{}={}".format(d[0], d[1]) for d in ordered_data])
        m = hmac.new(self.API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256)
        return m.hexdigest()
    def _handle_response(self, response):
        """Internal helper for handling API responses from the Binance server.
        Raises the appropriate exceptions when necessary; otherwise, returns the
        response.
        """
        if not str(response.status_code).startswith('2'):
            raise BinanceAPIException(response)
        try:
            return response.json()
        except ValueError:
            raise BinanceRequestException('Invalid Response: %s' % response.text)
    def _order_params(self, data):
        """Convert params to list with signature as last element

        :param data:
        :return:

        """
        has_signature = False
        params = []
        for key, value in data.items():
            if key == 'signature':
                has_signature = True
            else:
                params.append((key, value))
        # sort parameters by key
        params.sort(key=itemgetter(0))
        if has_signature:
            params.append(('signature', data['signature']))
        return params


    def _request(self, method, uri, signed, force_params=False, **kwargs):

        # set default requests timeout
        kwargs['timeout'] = 100

        # add our global requests params
        if self._requests_params:
            kwargs.update(self._requests_params)

        data = kwargs.get('data', None)
        if data and isinstance(data, dict):
            kwargs['data'] = data
        if signed:
            # generate signature
            kwargs['data']['timestamp'] = int(time.time() * 1000)
            kwargs['data']['signature'] = self._generate_signature(kwargs['data'])

        # sort get and post params to match signature order
        if data:
            # find any requests params passed and apply them
            if 'requests_params' in kwargs['data']:
                # merge requests params into kwargs
                kwargs.update(kwargs['data']['requests_params'])
                del(kwargs['data']['requests_params'])

            # sort post params
            kwargs['data'] = self._order_params(kwargs['data'])

        # if get request assign data array to params value for requests lib
        if data and (method == 'get' or force_params):
            kwargs['params'] = kwargs['data']
            del(kwargs['data'])
        logging.info("kwargs or request End to binance: %s",kwargs)

        response = getattr(self.session, method)(uri, **kwargs)
        return self._handle_response(response)

    def _create_api_uri(self, path, signed=True, version=PUBLIC_API_VERSION):
        v = self.PRIVATE_API_VERSION if signed else version
        return self.API_URL + '/' + v + '/' + path

    def _request_api(self, method, path, signed=False, version=PUBLIC_API_VERSION, **kwargs):
        uri = self._create_api_uri(path, signed, version)
        return self._request(method, uri, signed, **kwargs)
    def _get(self, path, signed=False, version=PUBLIC_API_VERSION, **kwargs):
        return self._request_api('get', path, signed, version, **kwargs)

    def ping(self):
        """Test connectivity to the Rest API.

        https://github.com/binance-exchange/binance-official-api-docs/blob/master/rest-api.md#test-connectivity

        :returns: Empty array

        .. code-block:: python

            {}

        :raises: BinanceResponseException, BinanceAPIException

        """
        return self._get('ping')
    def get_klines(self, **params):
        """Kline/candlestick bars for a symbol. Klines are uniquely identified by their open time.

        https://github.com/binance-exchange/binance-official-api-docs/blob/master/rest-api.md#klinecandlestick-data

        :param symbol: required
        :type symbol: str
        :param interval: -
        :type interval: enum
        :param limit: - Default 500; max 500.
        :type limit: int
        :param startTime:
        :type startTime: int
        :param endTime:
        :type endTime: int

        :returns: API response

        .. code-block:: python

            [
                [
                    1499040000000,      # Open time
                    "0.01634790",       # Open
                    "0.80000000",       # High
                    "0.01575800",       # Low
                    "0.01577100",       # Close
                    "148976.11427815",  # Volume
                    1499644799999,      # Close time
                    "2434.19055334",    # Quote asset volume
                    308,                # Number of trades
                    "1756.87402397",    # Taker buy base asset volume
                    "28.46694368",      # Taker buy quote asset volume
                    "17928899.62484339" # Can be ignored
                ]
            ]

        :raises: BinanceResponseException, BinanceAPIException

        """
#        print("params:"+str(params))
        return self._get('klines', data=params)
    def date_to_milliseconds(self,date_str):
        """Convert UTC date to milliseconds
        If using offset strings add "UTC" to date string e.g. "now UTC", "11 hours ago UTC"
        See dateparse docs for formats http://dateparser.readthedocs.io/en/latest/
        :param date_str: date in readable format, i.e. "January 01, 2018", "11 hours ago UTC", "now UTC"
        :type date_str: str
        """
        '''
         an epoch is the date and time relative to which a computer's clock and timestamp values are determined.
        '''
        # get epoch value in UTC
        epoch = datetime.utcfromtimestamp(0).replace(tzinfo=pytz.utc)
        #...........................
        #UTC=datetime.utcnow()
        #Local=datetime.now()
        #print(UTC)
        #print(epoch)
        #print(Local)
        #print(date_str)
        #.................................
        #define epoch, the beginning of times in the UTC timestamp world
        # parse our date string
        #.........................
        #import time
        #current_milli=	int(round(time.time() * 1000))

        #...........................
        d = dateparser.parse(date_str)
        #print("function date to millisocond:"+str(d))
        #d = dateparser.parse('12 hour ago UTC') #THIS IS MY PROBLEM PROGRAM
        #print(d)
        #print(d)
        #........................
        '''
        if(d>UTC):
            diff_UTC_dateInput=d-UTC
        else:
            diff_UTC_dateInput = UTC-d
        print(diff_UTC_dateInput)
        if(not diff_UTC_dateInput):
            d = dateparser.parse(str(diff_UTC_dateInput)+' hours ago UTC')
        print(d)
        '''
        # if the date is not timezone aware apply UTC timezone
        if d.tzinfo is None or d.tzinfo.utcoffset(d) is None:
            d = d.replace(tzinfo=pytz.utc)

        # return the difference in time
        return int((d - epoch).total_seconds() * 1000.0)
        #return current_milli
    def milliseconds_to_date(self,milliseconds):
        s = milliseconds/ 1000.0
        dte = datetime.fromtimestamp(s).strftime('%Y-%m-%d %H:%M:%S.%f')
        return dte
    def interval_to_milliseconds(self,interval):
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
            "w": 7 * 24 * 60 * 60,
            "M": 30 * 24 * 60 * 60
        }

        unit = interval[-1]
        if unit in seconds_per_unit:
            try:
                ms = int(interval[:-1]) * seconds_per_unit[unit] * 1000
            except ValueError:
                pass
        return ms
# uses the date_to_milliseconds and interval_to_milliseconds functions
# https://gist.github.com/sammchardy/3547cfab1faf78e385b3fcb83ad86395
# https://gist.github.com/sammchardy/fcbb2b836d1f694f39bddd569d1c16fe


    def get_historical_klines(self,symbol, interval, start_str, end_str=None):
        """Get Historical Klines from Binance
        See dateparse docs for valid start and end string formats http://dateparser.readthedocs.io/en/latest/
        If using offset strings for dates add "UTC" to date string e.g. "now UTC", "11 hours ago UTC"
        :param symbol: Name of symbol pair e.g BNBBTC
        :type symbol: str
        :param interval: Biannce Kline interval
        :type interval: str
        :param start_str: Start date string in UTC format
        :type start_str: str
        :param end_str: optional - end date string in UTC format
        :type end_str: str
        :return: list of OHLCV values
        """
        # create the Binance client, no need for api key
       # client = Client("", "")

        # init our list
        output_data = []

        # setup the max limit (
        limit =500 #such as 1m: current time,current time-1m,current time-2m,current time-3m,,...????????

        # convert interval to useful value in seconds
        timeframe = self.interval_to_milliseconds(interval)

        # convert our date strings to milliseconds
        start_ts = self.date_to_milliseconds(start_str)
        # if an end time was passed convert it
        end_ts = None
        if end_str:
            end_ts = self.date_to_milliseconds(end_str)

        idx = 0
        #print("function his:"+ str(start_ts))
        #print(end_ts)
        # it can be difficult to know when a symbol was listed on Binance so allow start time to be before list date
        symbol_existed = False
        while True:
            # fetch the klines from start_ts up to max 500 entries or the end_ts if set
            temp_data = self.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit,
                startTime=start_ts,
                endTime=end_ts
            )
            if(temp_data==[] or temp_data==None):#limit=0
                break
#            print(self.milliseconds_to_date(temp_data[0][0]))
            #print("temp_data: "+str(temp_data))
            # handle the case where our start date is before the symbol pair listed on Binance
            if not symbol_existed and len(temp_data):
                symbol_existed = True

            if symbol_existed:
                # append this loops data to our output data
                output_data += temp_data

                # update our start timestamp using the last value in the array and add the interval timeframe
                start_ts = temp_data[len(temp_data) - 1][0] + timeframe
            else:
                # it wasn't listed yet, increment our start date
                start_ts += timeframe
            logging.info("idx %s",idx)
            idx += 1
            # check if we received less than the required limit and exit the loop
            if len(temp_data) < limit:
                # exit the while loop
                break

            # sleep after every 3rd call to be kind to the API
            if idx % 3 == 0:
                sleep(1)

        return output_data

    def Write_CsvFile(self,Data_binance_500,header,PathFile,writeFile):#Key:time,key:KLINE_INTERVAL_1MINUTE,,header:OHCL
        #logging.info("Thread %s: starting", 2)
        logging.info("Starting Write CSV File")
        '''
        :param Dire:
        :param Type:
        :param Data_binance_500:
        :param header:
        :param writeFile:
        :return:
        '''

        with open(PathFile, 'w', newline='') as output_file:
            list_writer = csv.writer(output_file)
            list_writer.writerow(header)
            logging.info("len Data candle : %s"  ,len(Data_binance_500))  #
            for one_minute_milli in Data_binance_500:
                #print(self.milliseconds_to_date(one_minute_milli[0]))  # convert milliseconds to date)
                list_writer.writerow(
                    [
                        self.milliseconds_to_date(one_minute_milli[0]),  # convert milliseconds to date
                        one_minute_milli[1],
                        one_minute_milli[2],
                        one_minute_milli[3],
                        one_minute_milli[4],
                        one_minute_milli[5],
                        self.milliseconds_to_date(one_minute_milli[6]),
                        one_minute_milli[7],
                        one_minute_milli[8],
                        one_minute_milli[9],
                        one_minute_milli[10],
                        one_minute_milli[11]
                    ])
            writeFile = True
        logging.info('Status File:%s' , str(writeFile))
        logging.info("Directory %s  End", PathFile)
        logging.info("..................")
        #self.stop(2)


    def Write_XMLFile(self,start_time,end_time,Key,key,Data_binance_500,PathFile,writeFile=False):#Key:time,key:KLINE_INTERVAL_1MINUTE,,header:OHCL
        #logging.info("Thread %s: starting", 3)
        logging.info("Staring Write Xml File \n")
#        data = ET.Element('data')  #<data></data>
        #tree = ET.parse('ADAUSDTbinance1year/BinanceData1year.xml')
        root = ET.Element("data")# <data></data>
        #root = tree.getroot()
        Kan = ET.SubElement(root, 'KANDLE')#<data><KANDLE></KANDLE></data>
        Kan.set("StartTime", start_time) #<KANDLE StartTime=""></KANDLE>
        Kan.set("EndTime", end_time)#<KANDLE EndTime=""></KANDLE>
        Kan.set("TypeKandle", Key) #<KANDLE TypeKandle=""></KANDLE>
        Kan.set("TypeTime", key)#<KANDLE TypeTime=""></KANDLE>
        logging.info("len %s : %s" , key,len(Data_binance_500))  #
        i=1
        for one_minute_milli in Data_binance_500:#problem analyse 1minute
            #print(self.milliseconds_to_date(one_minute_milli[0]))  # convert milliseconds to date)
            open_time = self.milliseconds_to_date(one_minute_milli[0])  # convert milliseconds to date
            close_time = self.milliseconds_to_date(one_minute_milli[6])  # convert milliseconds to date
            o_c_time = ET.SubElement(Kan, "Recorde"+str(i))  # <data><KANDLE><i></i></KANDLE></data>
            o_c_time.set("OpenTime", open_time)#<data><KANDLE><i OpenTime="" ></i></KANDLE></data>
            o_c_time.set("CloseTime", close_time)#<data><KANDLE><i CloseTime=""></i></KANDLE></data>
            o_c_time.text =str(one_minute_milli[1])+","+str(one_minute_milli[2])+","+str(one_minute_milli[3])+","+str(one_minute_milli[4])+","+str(one_minute_milli[5])+","+str(one_minute_milli[7])+","+str(one_minute_milli[8])+","+str(one_minute_milli[9])+","+str(one_minute_milli[10])+","+str(one_minute_milli[11])
            # create a new XML file with the results
            i+=1
        tree = ET.ElementTree(root)
        tree.write(PathFile )
        writeFile = True
        logging.info('Status File: %s' ,str(writeFile))
        logging.info("Directory  %s   End." , PathFile)
        #self.stop(3)
    def Write_json(self,symbol,start,end,Dire,interval,klines,writefile):
        # open a file with filename including symbol, interval and start and end converted to milliseconds
        with open(
            "Binance_{}_{}_{}-{}.json".format(
                symbol,
                interval,
                self.date_to_milliseconds(start),
                self.date_to_milliseconds(end)
            ),
            'w'  # set file write mode
        ) as f:
            f.write(json.dumps(klines))
        logging.info("WriteFile"+" "+str(writefile))
    #...................................................................
    #... thread and process kandle
    def run_Process_Kandle(self,objklines):#not work
        logging.info("Main    : before creating thread %s",1)
        self.stop_thread1=False
        self.thread1=Thread(target=self.Process_Kandle,args=(objklines,1,))
        logging.info("Main    : before running thread %s",1)
        self.thread1.start()
        logging.info("Main    : wait for the thread %s to finish",1)
        #self.thread1.join()
        logging.info("Thread  %s  : all done",1)
    #...................................................................
    #...................................................................
    def Process_Kandle(self,objklines,i):

        logging.info("Thread %s: starting", i)
        header_Write_File=objklines.HeadFILE()
        Data_binance_500= objklines.get_historical_klines(objklines.symbol,objklines.Kandle_time,objklines.start_date,objklines.end_date)

        if(Data_binance_500):
            logging.info("len candle return: %s",(len(Data_binance_500)))
            #output_file : C:\Miniconda3\Economic\ADAUSDTbinance\week\KLINE_INTERVAL_1WEEK.csv
            writeFile=False
            #PathDire=""

            #os.mkdir()
            PathFileCsv =objklines.folder + "/" +objklines.Dire  + "/" + objklines.Kandle_type + ".csv"
            if(objklines.typefile=="csv"):
                objklines.Write_CsvFile(Data_binance_500,header_Write_File,PathFileCsv,writeFile)
            elif(objklines.typefile=="xml"):
                PathFileXml = objklines.folder+ "/" +objklines.Dire  + "/" + objklines.Kandle_type + ".xml"
                objklines.Write_XMLFile(objklines.start_date,objklines.end_date,objklines.Dire,objklines.Kandle_type,Data_binance_500,PathFileXml,writeFile)#PROBLEM IS VERY MUCH LONG FETCH DATA #solution:thread
            elif(objklines.typefile=="json"):
                PathFileJson = objklines.folder+ "/" +objklines.Dire  + "/" + objklines.Kandle_type + ".xml"
                objklines.Write_json(objklines.start_date,objklines.end_date,objklines.Dire,objklines.Kandle_type,Data_binance_500,PathFileJson,writeFile)
            else:
                logging.info("not found.")




def main(dic_values):
    logging.info('IN THE NAME OF GOD .')
    logging.info(dic_values)
    print(dic_values)
    '''
    object class binance:
    arg1:API_KEY,arg2:SECRET_KEY
    '''
    ts=datetime.now()

    now_date,now_time=str(ts).split()
    logging.info(now_date)
    expire_time='2022-01-01'
    logging.info(expire_time)
    if(datetime.strptime(now_date,'%Y-%m-%d')<datetime.strptime(expire_time,"%Y-%m-%d")):
        logging.info("not expire")
        format = "%(asctime)s: %(message)s"
        logging.basicConfig(format=format, level=logging.INFO,
                             datefmt="%H:%M:%S")
        api_key=''
        secret_key=''
        objklines=BinanceKlines(api_key,secret_key)
        objklines.symbol=dic_values['request_values']['symbol']
        objklines.start_date=dic_values['request_values']['startDate'] #format date Y/MONTH/DAY
        objklines.end_date=dic_values['request_values']['endDate']
        objklines.Dire='minute'
        objklines.Kandle_time=dic_values['request_values']['interval']+dic_values['request_values']['time']#15m
        objklines.Kandle_type="KLINE_INTERVAL_"+objklines.Kandle_time
        objklines.folder="ADAUSDTbinanceRequest" #location save kandles
        objklines.typefile=dic_values['request_values']['typefile']#save kandles

        logging.info("start get Candles.")
        objklines.Process_Kandle(objklines,"not found")
        logging.info("End")
    else:
        logging.info("expire time app.please buy serial.")
