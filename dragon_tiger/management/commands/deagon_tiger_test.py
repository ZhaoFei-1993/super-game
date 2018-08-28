#!/usr/bin/python
import websocket
# import thread
import threading
import time
from dragon_tiger.models import Table
from django.core.management.base import BaseCommand
import hashlib
import time
import requests
import json
from django.conf import settings


class Command(BaseCommand):
    help = "发送手机短信"

    def handle(self, *args, **options):
        table_list = Table.objects.all()
        for table in table_list:
            # print("table_id=====================", table.three_table_id)
            appid = '58000000'  # 获取token需要参数Appid
            appsecret = '92e56d8195a9dd45a9b90aacf82886b1'  # 获取token需要参数Secret
            times = int(time.time())  # 获取token需要参数time

            array = {'appid': '58000000', 'menu': 'bet', 'tid': table.three_table_id}  # 龙虎斗

            m = hashlib.md5()  # 创建md5对象
            hash_str = str(times) + appid + appsecret
            hash_str = hash_str.encode('utf-8')
            m.update(hash_str)
            token = m.hexdigest()
            array['token'] = token
            list = ""
            for key in array:
                value = array[key]
                list += str(key) + str(value)
            list += appsecret
            list = list.encode('utf-8')
            sign = hashlib.sha1(list)
            sign = sign.hexdigest()
            sign = sign.upper()
            array['sign'] = sign
            in_token = {
                "connect": "api",
                "mode": "onlineLogin",
                "json": array
            }  # ws参数组装
            return in_token

    def on_message(ws, message):
        print("获取信息=================", message)

    def on_error(ws, error):
        print("ws链接报错！=====================", error)

    def on_close(ws):
        print("### ws链接关闭 ###")

    # def on_open(ws):
    #     def run(*args):
    #         ws.send("Hello %d" % i)
    #         ws.close()
    #         print("thread terminating...")
    #
    #     thread.start_new_thread(run, ())

    def on_open(ws):
        def run(*args):
            ws.send("Hello %d")
            ws.close()
            print("thread terminating...")

        threading.Thread(run()).start()

    if __name__ == "__main__":
        websocket.enableTrace(True)
        ws = websocket.WebSocketApp("ws://118.184.66.99:9501:9501",
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close)
        ws.on_open = on_open

        ws.run_forever()
