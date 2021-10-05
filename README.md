سلام 

گرفتن داده های ارز های دیجیتال از وب سایت بایننس


سوال: چگونه برنامه را اجرا کنم؟

جواب: 

ابتدا در مسیر برنامه کامند لاین را باز کنید و کامند زیر را وارد کنید :
python GUIrequest.py

![1](https://user-images.githubusercontent.com/61306250/136050245-3efd03f2-ff3e-4c30-9eed-dd778c346e1f.JPG)


سپس برنامه به شکل زیر اجرا می شود .

![2](https://user-images.githubusercontent.com/61306250/136050369-577d7fed-838c-4e55-8e25-31e977189352.JPG)


#-----
سوال :برنامه چه کار می کند ؟

جواب :
 
 1- گرفتن داده های ارز های دیجیتال به صورت تایم فریم های زیر

KLINE_INTERVAL_1MINUTE = '1m'

KLINE_INTERVAL_3MINUTE = '3m'

KLINE_INTERVAL_5MINUTE = '5m'

KLINE_INTERVAL_15MINUTE = '15m'

KLINE_INTERVAL_30MINUTE = '30m'

KLINE_INTERVAL_1HOUR = '1h'

KLINE_INTERVAL_2HOUR = '2h'

KLINE_INTERVAL_4HOUR = '4h'

KLINE_INTERVAL_6HOUR = '6h'

KLINE_INTERVAL_8HOUR = '8h'

KLINE_INTERVAL_12HOUR = '12h'

KLINE_INTERVAL_1DAY = '1d'

KLINE_INTERVAL_3DAY = '3d'

KLINE_INTERVAL_1WEEK = '1w'

KLINE_INTERVAL_1MONTH = '1M'


2- ذخیره داده به 3 فرمت

XML 

JSON

CSV


#-----
سوال: نیازمندی های برنامه برای اجرا چیست؟

جواب:

1- ساخت اکانت بایننس 

2- گرفتن دو مقدار 
api_key ,secret 
از وب سایت بایننس 

3-  این دومقدار در فایل 
GetHistoricalCandle.py
خط 591و 592 جلوی دومقداریا دومتغیر قرار دهید .
#----

سوال: چگونه با برنامه کار کنم ؟

ورودی زیر را نگاه کنید 

![3](https://user-images.githubusercontent.com/61306250/136052644-13bcd823-bfc7-478b-9859-234d10931b57.JPG)

با این کانفیگ خروجی برنامه  شما چیست؟

1- ارز کاردانو /تتر

2- تاریخ شروع 
2021/4/19

3- تاریخ پایان
2021/5/19

4-کندل های 5 دقیقه ای 

5- به صورت فایل سی اس وی 
به برمی گرداند .


موفق باشید
به امید خدا 
#----
# GetDataCryptoBinance
Get Data Crypto by exchange Binance
 
