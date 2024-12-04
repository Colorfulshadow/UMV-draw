"""
@Author: Tianyi Zhang
@Date: 2024/12/4
@Description: 用于uvm抽奖
"""
import hashlib
from datetime import datetime
import pytz
import requests
import time

def caltime():
    cst_tz = pytz.timezone("Asia/Shanghai")
    today = datetime.now(cst_tz).date()
    cst_8am = cst_tz.localize(datetime(today.year, today.month, today.day, 8, 0, 0))
    timestamp = int(cst_8am.timestamp() * 1000)
    return timestamp

def hash_phone_number(phone_number):
    hash_value = hashlib.md5(phone_number.encode('utf-8')).hexdigest()
    return hash_value

def get_server_time_offset(server_url):
    try:
        start = time.time()
        response = requests.head(server_url)
        end = time.time()

        # 计算本地到服务器的单程时间 (RTT / 2)
        rtt = (end - start) / 2
        if "Date" in response.headers:
            server_time_str = response.headers["Date"]
            # 转换服务器时间为 UTC 时间
            server_time = datetime.strptime(server_time_str, "%a, %d %b %Y %H:%M:%S GMT")
            server_time = server_time.replace(tzinfo=pytz.utc)
            # 计算时间偏移
            local_time = datetime.now(pytz.utc)
            offset = (server_time - local_time).total_seconds() + rtt
            return offset
        else:
            print("无法获取服务器时间，使用默认本地时间")
            return 0
    except Exception as e:
        print(f"获取服务器时间差异常: {e}")
        return 0

def send_post(server_url, phone_number, timestamp, Authorization):
    hashed_phone_number = hash_phone_number(phone_number)
    payload ={
        "actId": 3,
        "cityCode": "110100",
        "nonce": f"{hashed_phone_number}{timestamp}",
    }

    headers = {
        "Content-Type": "application/json",
        "User-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.109 Safar",
        "terminal": 10,
        "Authorization": Authorization,
    }

    try:
        response = requests.post(server_url, json=payload, headers=headers)
        if response.status_code == 200:
            return True
        else:
            return False
    except Exception as e:
        return False

def send_message(message,status,send_keys):
    send_keys = [send_keys[i] for i in [0]]
    for send_key in send_keys:
        server_url = f'https://notice.zty.ink/{send_key}'
        if status:
            payload = {
                'title': '抢琴房成功啦',
                'body': message,
                'icon': 'https://api.zty.ink/api/v2/objects/icon/se2ezd5tzxgsubc0rx.png',
                'group': '每日一抢琴房'
            }
        else:
            payload = {
                'title': '好可惜，没抢到琴房',
                'body': message,
                'icon': 'https://api.zty.ink/api/v2/objects/icon/fi9tl1ylkeyi8yoirb.png',
                'group': '每日一抢琴房'
            }
        try:
            response = requests.post(server_url, data=payload)
            if response.status_code == 200:
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Message sent successfully.")
            else:
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Failed to send message. Status code: {response.status_code}")
        except Exception as e:
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Error sending message: {e}")

if __name__ == '__main__':
    print(caltime())
    print(hash_phone_number('13971873575'))
    print(get_server_time_offset(' https://youmi.umvcard.com'))
