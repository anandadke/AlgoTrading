# pip install fyers-apiv2
# pip install selenium
# pip install webdriver-manager

from fyers_api.Websocket import ws
from fyers_api import fyersModel
from fyers_api import accessToken
import datetime
import time
import document_file
import requests
import json
import pyotp
import talib as ta
import pandas as pd
import sys
from urllib.parse import parse_qs,urlparse

log_path = document_file.log_path
client_id = document_file.client_id
secret_key = document_file.secret_key
redirect_url = document_file.redirect_url
response_type = document_file.response_type
grant_type = document_file.grant_type
username = document_file.username
password = document_file.password
pin1 = document_file.pin1
pin2 = document_file.pin2
pin3 = document_file.pin3
pin4 = document_file.pin4

APP_ID =  "TYCMM54OOQ" # App ID from myapi dashboard is in the form appId-appType. Example - EGNI8CE27Q-100, In this code EGNI8CE27Q will be APP_ID and 100 will be the APP_TYPE
APP_TYPE = "100"
SECRET_KEY = 'BNP2JTCR9Z'
client_id= f'{APP_ID}-{APP_TYPE}'

FY_ID = "XA38106"  # Your fyers ID
APP_ID_TYPE = "2"  # Keep default as 2, It denotes web login
TOTP_KEY = "CSMGTRPPJBS2FRM7RHJAPVXNB4HPEJ6W"  # TOTP secret is generated when we enable 2Factor TOTP from myaccount portal
PIN = "9296"  # User pin for fyers account

REDIRECT_URI = "http://localhost:8080/apis/broker/login/fyers"  # Redirect url from the app.

BASE_URL = "https://api-t2.fyers.in/vagator/v2"
BASE_URL_2 = "https://api.fyers.in/api/v2"
URL_SEND_LOGIN_OTP = BASE_URL + "/send_login_otp"   #/send_login_otp_v2
URL_VERIFY_TOTP = BASE_URL + "/verify_otp"
URL_VERIFY_PIN = BASE_URL + "/verify_pin"
URL_TOKEN = BASE_URL_2 + "/token"
URL_VALIDATE_AUTH_CODE = BASE_URL_2 + "/validate-authcode"
SUCCESS = 1
ERROR = -1

def send_login_otp(fy_id, app_id):
    try:
        result_string = requests.post(url=URL_SEND_LOGIN_OTP, json= {"fy_id": fy_id, "app_id": app_id })
        if result_string.status_code != 200:
            return [ERROR, result_string.text]
        result = json.loads(result_string.text)
        request_key = result["request_key"]
        return [SUCCESS, request_key]
    except Exception as e:
        return [ERROR, e]

def verify_totp(request_key, totp):
    try:
        result_string = requests.post(url=URL_VERIFY_TOTP, json={"request_key": request_key,"otp": totp})
        if result_string.status_code != 200:
            return [ERROR, result_string.text]
        result = json.loads(result_string.text)
        request_key = result["request_key"]
        return [SUCCESS, request_key]
    except Exception as e:
        return [ERROR, e]

session = accessToken.SessionModel(client_id=client_id, secret_key=SECRET_KEY, redirect_uri=REDIRECT_URI,
                            response_type='code', grant_type='authorization_code')

urlToActivate = session.generate_authcode()
print(f'URL to activate APP:  {urlToActivate}')



# Step 1 - Retrieve request_key from send_login_otp API

send_otp_result = send_login_otp(fy_id=FY_ID, app_id=APP_ID_TYPE)

if send_otp_result[0] != SUCCESS:
    print(f"send_login_otp failure - {send_otp_result[1]}")
    sys.exit()
else:
    print("send_login_otp success")


# Step 2 - Verify totp and get request key from verify_otp API
for i in range(1,3):
    request_key = send_otp_result[1]
    verify_totp_result = verify_totp(request_key=request_key, totp=pyotp.TOTP(TOTP_KEY).now())
    if verify_totp_result[0] != SUCCESS:
        print(f"verify_totp_result failure - {verify_totp_result[1]}")
        time.sleep(1)
    else:
        print(f"verify_totp_result success {verify_totp_result}")
        break

request_key_2 = verify_totp_result[1]

# Step 3 - Verify pin and send back access token
ses = requests.Session()
payload_pin = {"request_key":f"{request_key_2}","identity_type":"pin","identifier":f"{PIN}","recaptcha_token":""}
res_pin = ses.post('https://api-t2.fyers.in/vagator/v2/verify_pin', json=payload_pin).json()
print(res_pin['data'])
ses.headers.update({
    'authorization': f"Bearer {res_pin['data']['access_token']}"
})



authParam = {"fyers_id":FY_ID,"app_id":APP_ID,"redirect_uri":REDIRECT_URI,"appType":APP_TYPE,"code_challenge":"","state":"None","scope":"","nonce":"","response_type":"code","create_cookie":True}
authres = ses.post('https://api.fyers.in/api/v2/token', json=authParam).json()
print(authres)
url = authres['Url']
print(url)
parsed = urlparse(url)
auth_code = parse_qs(parsed.query)['auth_code'][0]



session.set_token(auth_code)
response = session.generate_token()
access_token= response["access_token"]
print(access_token)

script_list = ["HDFCBANK-EQ","SBIN-EQ","INFY-EQ","ICICIBANK-EQ","AXISBANK-EQ","MARUTI-EQ","WIPRO-EQ","BHARTIARTL-EQ","ASIANPAINT-EQ","DIVISLAB-EQ","HDFC-EQ","HCLTECH-EQ","TECHM-EQ","KOTAKBANK-EQ","TITAN-EQ","TATACONSUM-EQ","LT-EQ","UPL-EQ","ITC-EQ","EICHERMOT-EQ","TCS-EQ","ADANIPORTS-EQ","CIPLA-EQ","SBILIFE-EQ","DRREDDY-EQ","RELIANCE-EQ","ULTRACEMCO-EQ","M&M-EQ","BAJAJFINSV-EQ","GRASIM-EQ","NESTLEIND-EQ","INDUSINDBK-EQ","HEROMOTOCO-EQ","POWERGRID-EQ","NTPC-EQ","BRITANNIA-EQ","SUNPHARMA-EQ","BAJAJ-AUTO-EQ","BAJFINANCE-EQ","HINDALCO-EQ","BPCL-EQ","SHREECEM-EQ","TATASTEEL-EQ","JSWSTEEL-EQ","HDFCLIFE-EQ","COALINDIA-EQ","HINDUNILVR-EQ","TATAMOTORS-EQ","IOC-EQ","ONGC-EQ"]

exchange = "NSE"
quantity = int(100)
timeframe = "15"
from_date = "2023-03-10"
today = datetime.datetime.now().strftime('%Y-%m-%d') #"2022-03-14"
rsi_overbought = 80
rsi_oversold = 20
buy_traded_stock = []
sell_traded_stock = []
ma_short = 13
ma_long = 22

def getTime():
	return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def placeOrder(script, order):
	if order == "BUY":
		order = fyers.place_order({"symbol":f"{exchange}:{script}","qty":quantity,"type":"2","side":"1","productType":"INTRADAY","limitPrice":"0","stopPrice":"0","disclosedQty":"0","validity":"DAY","offlineOrder":"False","stopLoss":"0","takeProfit":"0"})
		print(f"Buy Order Placed for {script} at time: {getTime()}")
	else:
		order = fyers.place_order({"symbol":f"{exchange}:{script}","qty":quantity,"type":"2","side":"-1","productType":"INTRADAY","limitPrice":"0","stopPrice":"0","disclosedQty":"0","validity":"DAY","offlineOrder":"False","stopLoss":"0","takeProfit":"0"})
		print(f"Buy Order Placed for {script} at time: {getTime()}")

def maAlgorithm():
	for script in script_list:
		data = {"symbol":f"{exchange}:{script}","resolution": timeframe,"date_format":"1","range_from": from_date,"range_to": today,"cont_flag":"0"}
		try:
			hist_data = fyers.history(data)
		except Exception as e:
			raise e
		df = pd.DataFrame(hist_data["candles"], columns=['date', 'open', 'high', 'low', 'close', 'volume'])
		df['date'] = pd.to_datetime(df['date'], unit = "s", utc=True)
		df['date'] = df['date'].dt.tz_convert('Asia/Kolkata')
		df["rsi"] = ta.RSI(df["close"], timeperiod=14).round(2)
		df["ema_long"] = ta.EMA(df["close"], timeperiod=ma_long).round(2)
		df["ema_short"] = ta.EMA(df["close"], timeperiod=ma_short).round(2)
		df.dropna(inplace=True)
		if not df.empty:
			print(df)
			if (df.ema_short.values[-1] > df.ema_long.values[-1]) and (df.ema_short.values[-2] < df.ema_long.values[-2]) and (script not in sell_traded_stock):
				sell_traded_stock.append(script)
				placeOrder(script, "SELL")

			if (df.ema_short.values[-1] < df.ema_long.values[-1]) and (df.ema_short.values[-2] > df.ema_long.values[-2]) and (script not in buy_traded_stock):
				buy_traded_stock.append(script)
				placeOrder(script, "BUY")

def main():
	global fyers
	fyers = fyersModel.FyersModel(token=access_token, log_path="C:/Data/Anand", client_id=client_id)
	fyers.token = access_token


	closingtime = int(15) * 60 + int(10)
	orderplacetime = int(9) * 60 + int(20)
	timenow = (datetime.datetime.now().hour * 60 + datetime.datetime.now().minute)
	print(f"Waiting for 9.20 AM , Time Now:{getTime()}")

	while timenow < orderplacetime:
		time.sleep(0.2)
		timenow = (datetime.datetime.now().hour * 60 + datetime.datetime.now().minute)
	print(f"Ready for trading, Time Now:{getTime()}")

	while timenow < closingtime:
		maAlgorithm()

if __name__ == "__main__":
	main()
