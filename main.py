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
import json
import os

def wait_until_target_time(target_hour, target_minute):
    """等待直到目标时间，动态调整检查频率"""
    while True:
        now = datetime.now()
        target_time = datetime(now.year, now.month, now.day, target_hour, target_minute)
        time_diff = (target_time - now).total_seconds()

        if time_diff <= 0:
            break  # 到达目标时间，退出循环

        if time_diff > 60:
            time.sleep(10)  # 离目标时间超过 1 分钟时，每 10 秒检查一次
        elif 2 < time_diff <= 60:
            time.sleep(1)  # 离目标时间 1-60 秒时，每秒检查一次
        else:
            time.sleep(0.05)  # 离目标时间不到 1 秒时，每 0.1 秒检查一次

def load_config(config_path):
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return {}

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
        "terminal": "10",
        "Authorization": Authorization,
    }
    try:
        response = requests.post(server_url, json=payload, headers=headers)
        print(response.text)
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("code") == 0 and response_data.get("data", {}).get("timeDrawStatus") is False:
                send_message("好可惜，没有抢到金属卡，但是明天一定可以的！","1", config['send_keys'])
            else:
                send_message("好像情况有变，请查看","2", config['send_keys'])
        else:
            send_message(f"HTTP 错误，状态码: {response.status_code}","3",config['send_keys'])
    except requests.exceptions.RequestException as e:
        send_message(f"请求异常: {e}","3",config['send_keys'])

def send_message(message,status,send_keys):
    send_keys = [send_keys[i] for i in [0]]
    for send_key in send_keys:
        server_url = f'https://notice.zty.ink/{send_key}'
        if status == "1":
            payload = {
                'title': '可惜没有抢到金属卡',
                'body': message,
                'icon': 'https://api.zty.ink/api/v2/objects/icon/fi9tl1ylkeyi8yoirb.png',
                'group': 'UVM金属卡'
            }
        elif status == "2":
            payload = {
                'title': '金属卡情报有变，速速查看',
                'body': message,
                'icon': 'https://api.zty.ink/api/v2/objects/icon/se2ezd5tzxgsubc0rx.png',
                'group': 'UVM金属卡'
            }
        elif status == "3":
            payload = {
                'title': '脚本出错啦',
                'body': message,
                'icon': 'https://api.zty.ink/api/v2/objects/icon/vf1n10zm4cyoc2v5st.png',
                'group': 'UVM金属卡'
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

    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    config = load_config(config_path)

    # 使用配置参数
    server_url = 'https://youmi.umvcard.com/app-api/promotion/share-activity-draw/execute'
    phone_number = config.get('phone_number', '')
    Authorization = config.get('Authorization', '')
    send_keys = config.get('send_keys', '')

    wait_until_target_time(8, 0)
    send_post(server_url, phone_number, caltime(), Authorization)