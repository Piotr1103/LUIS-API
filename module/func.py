from django.conf import settings

from linebot import LineBotApi
from linebot.models import TextSendMessage

import requests
import twder  #匯率套件
try:
    import xml.etree.cElementTree as et
except ImportError:
    import xml.etree.ElementTree as et

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)

user_key = "CWB-4F1E78C6-CD21-4332-A767-0BE5254A00FA"
doc_name = "F-C0032-001"

cities = ["臺北","新北","桃園","臺中","臺南","高雄","基隆","新竹","嘉義"]  #市
counties = ["苗栗","彰化","南投","雲林","嘉義","屏東","宜蘭","花蓮","臺東","澎湖","金門","連江"]  #縣
currencies = {'美金':'USD','美元':'USD','港幣':'HKD','英鎊':'GBP','澳幣':'AUD','加拿大幣':'CAD',\
              '加幣':'CAD','新加坡幣':'SGD','新幣':'SGD','瑞士法郎':'CHF','瑞郎':'CHF','日圓':'JPY',\
              '日幣':'JPY','南非幣':'ZAR','瑞典幣':'SEK','紐元':'NZD','紐幣':'NZD','泰幣':'THB',\
              '泰銖':'THB','菲國比索':'PHP','菲律賓幣':'PHP','印尼幣':'IDR','歐元':'EUR','韓元':'KRW',\
              '韓幣':'KRW','越南盾':'VND','越南幣':'VND','馬來幣':'MYR','人民幣':'CNY' }  #幣別字典
keys = currencies.keys()

def sendUse(event):  #使用說明
    try:
        text1 ='''
查詢天氣：輸入「XXXX天氣如何?」，例如「高雄天氣如何?」
        輸入「XXXX有下雨嗎?」，例如「台中有下雨嗎?」

查詢匯率：輸入「XXXX匯率為多少?」，例如「美金匯率為多少?」
        輸入「XXXX一元換新台幣多少元?」，例如「英鎊一元換新台幣多少元?」
               '''
        message = TextSendMessage(
            text = text1
        )
        line_bot_api.reply_message(event.reply_token,message)
    except:
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text='發生錯誤！'))

def sendLUIS(event, mtext):  #LUIS
    try:
        r = requests.get('https://westus.api.cognitive.microsoft.com/luis/v2.0/apps/21d9108a-0ae0-4980-850b-05b40c4d579b?verbose=true&timezoneOffset=-360&subscription-key=e0e3262d50894837a902bfa7ab53fb11&q=' + mtext)  #終結點
        result = r.json()

        city = ''
        money = ''
        if result['topScoringIntent']['intent'] == '縣市天氣':
            for en in result['entities']:
                if en['type'] == '地點':  #由LUIS天氣類取得地點
                    city = en['entity']
                    break
        elif result['topScoringIntent']['intent'] == '匯率查詢':
            for en in result['entities']:
                if en['type'] == '幣別':  #由LUIS匯率類取得幣別
                    money = en['entity']
                    break
        if not city == '':  #天氣類地點存在
            flagcity = False  #檢查是否為縣市名稱
            city = city.replace('台', '臺')  #氣象局資料使用「臺」
            if city in cities:  #加上「市」
                city += '市'
                flagcity = True
            elif city in counties:  #加上「縣」
                city += '縣'
                flagcity = True
            if flagcity:  #是縣市名稱
                weather = city + '天氣資料：\n'
                #由氣象局API取得氣象資料
                api_link = "https://opendata.cwb.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization=CWB-4F1E78C6-CD21-4332-A767-0BE5254A00FA&format=XML"
                report = requests.get(api_link).text
                root = et.fromstring(report)
                locations_info = dataset.findall('./records/location')
                target_idx = -1
                # 取得 <location> Elements,每個 location 就表示一個縣市資料
                for idx,ele in enumerate(locations_info):
                    locationName = ele[0].text # 取得縣市名
                    if locationName == city:
                        target_idx = idx
                        break  
                # 挑選出目前想要 location 的氣象資料
                tlist = ['天氣狀況', '降雨機率', '最低溫', '舒適度', '最高溫']
                for i in range(5):
                    element = locations_info[target_idx][i+1] # 取出 Wx (氣象描述)
                    timeblock = element[1] # 取出目前時間點的資料
                    data = timeblock[2][0].text
                    weather = weather + tlist[i] + '：' + data + '\n'
                weather = weather[:-1]  #移除最後一個換行
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=weather))
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text='無此地點天氣資料！'))
        elif not money == '':  #匯率類幣別存在
            if money in keys:
                rate = float(twder.now(currencies[money])[3])  #由匯率套件取得匯率
                message = money + '的匯率為 ' + str(rate)
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))
            else:
                head = list(currency)[0]
                like = []
                for i in keys:
                    if head in i:
                        like.append(i)
                if len(like) > 0:
                    print('找不到此貨幣。\n可能的項目有："' + '"或"'.join(like) + '"？')
                else:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text='無此幣別匯率資料！'))
        else:  #其他未知輸入
            text = '無法了解你的意思，請重新輸入！'
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=text))
            
    except:
       line_bot_api.reply_message(event.reply_token, TextSendMessage(text='執行時產生錯誤！'))
