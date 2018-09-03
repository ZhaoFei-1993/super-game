# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
import hashlib
import time
import requests
import json
from django.conf import settings
from dragon_tiger.models import Table


class Command(BaseCommand):
    help = "发送手机短信"

    def handle(self, *args, **options):
        appid = '58000000'  # 获取token需要参数Appid
        appsecret = '92e56d8195a9dd45a9b90aacf82886b1'  # 获取token需要参数Secret
        times = int(time.time())  # 获取token需要参数time
        # array = {'appid': '58000000', 'menu': 'home', 'game': 2}  # 龙虎斗
        # array = {'appid': '58000000', 'menu': 'bet', 'tid': 4}  # 龙虎斗
        # array = {'appid': '58000000', 'menu': 'home', 'game': 1}  # 百家乐
        # array = {'appid': '58000000', 'menu': 'bet', 'tid': 1}  # 百家乐
        array = {'appid': '58000000', 'menu': 'home', 'game': 0}  # 全部
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

        data = array
        result = requests.post('http://api.wt123.co/service', data=data)
        res = json.loads(result.content.decode('utf-8'))
        i = 1
        if array["menu"] == "bet":
            with open(settings.BASE_DIR + '/0000' + str(i), 'a+') as f:
                f.write(str(res))
                i += 1
        else:
            for info in res["data"]:
                three_table_id = int(info["tableInfo"]["id"])
                websocket_url = str(info["tableInfo"]["websocket_url"])
                game_name = info["tableInfo"]["game_name"]
                print("获取到一张:" + info["tableInfo"]["game_name"] + "游戏桌=======ws链接:", websocket_url)
                number = Table.objects.filter(three_table_id=three_table_id).count()
                if int(number) == 0:
                    table_info = Table()
                    table_info.three_table_id = three_table_id
                    table_info.table_name = info["tableInfo"]["table_name"]
                    table_info.game_id = int(info["tableInfo"]["game_id"])
                    table_info.game_name = 1
                    if game_name == "龙虎斗":
                        table_info.game_name = 2
                    table_info.mode = int(info["tableInfo"]["mode"])
                    table_info.special_num = int(info["tableInfo"]["special_num"])
                    table_info.percent_num = int(info["tableInfo"]["percent_num"])
                    table_info.status = 0
                    if int(info["tableInfo"]["status"]) == 1:
                        table_info.status = int(info["tableInfo"]["status"])
                    table_info.in_checkout = int(info["tableInfo"]["in_checkout"])
                    table_info.websocket_url = websocket_url
                    table_info.wait_time = int(info["tableInfo"]["in_checkout"])
                    print("remake======================", info["tableInfo"]["remake"])
                    if info["tableInfo"]["remake"] != None:
                        table_info.remake = info["tableInfo"]["remake"]
                    table_info.save()
                    print("新桌号----------------入库成功")
                else:
                    print("-------------------桌号已经存在！-------------------")
