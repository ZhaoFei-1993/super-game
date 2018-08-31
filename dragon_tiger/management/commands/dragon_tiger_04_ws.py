from django.core.management.base import BaseCommand, CommandError
import websocket
import json
from dragon_tiger.models import Table, Boots, Number_tab, Showroad, Bigroad, Bigeyeroad, Psthway, Roach
from utils.functions import ludan_save
import hashlib
import time
from urllib import parse
from django.conf import settings


class Command(BaseCommand):
    help = '小样'

    @staticmethod
    def on_message(ws, message):
        messages = json.loads(message)
        print('messages = ', messages)
        # with open(settings.BASE_DIR + '/0000', 'a+') as f:
        #     f.write(str(messages))           # 保存数据成文件
        status = messages["status"]
        sendModes = messages["sendMode"]
        if status == False:
            table_info = Table.objects.get(three_table_id=4)
            table_info.in_checkout = 2
            table_info.save()
            ws.close()
            print("------------------桌子暂未运营------------------")
        else:
            table_info = Table.objects.get(three_table_id=4)
            if sendModes == "onlineLogin" and status == True:
                if messages["round"]["number_tab_status"]["type"] == 1:
                    table_info.in_checkout = int(messages["round"]["number_tab_status"]["in_checkout"])
                    # table_info.save()
                    print("------------------桌子状态改变成功------------------")
                if messages["round"]["number_tab_status"]["type"] == 2:
                    is_boots = Boots.objects.filter(boot_id=messages["round"]["boot_id"],
                                                    boot_num=messages["round"]["boot_num"]).count()
                    if is_boots == 0:
                        boots = Boots()
                        boots.tid = table_info
                        boots.boot_id = int(messages["round"]["boot_id"])
                        boots.boot_num = int(messages["round"]["boot_num"])
                        boots.save()
                        print("---------------当前靴号入库成功------------------")
                    else:
                        print("---------------靴号已经存在------------------")
                        boots = Boots.objects.get(boot_id=messages["round"]["boot_id"],
                                                  boot_num=messages["round"]["boot_num"])
                    is_Number_tab = Number_tab.objects.filter(number_tab_id=messages["round"]["number_tab_id"],
                                                              number_tab_number=messages["round"][
                                                                  "number_tab_number"]).count()
                    if is_Number_tab == 0:
                        number_tab = Number_tab()
                        number_tab.tid = table_info
                        number_tab.boots = boots
                        number_tab.number_tab_id = messages["round"]["number_tab_id"]
                        number_tab.number_tab_number = messages["round"]["number_tab_number"]
                        if "opening" in messages["round"]:
                            number_tab.opening = messages["round"]["opening"]
                        if "pair" in messages["round"]:
                            number_tab.pair = messages["round"]["pair"]
                        number_tab.bet_statu = messages["round"]["number_tab_status"]["betStatus"]
                        number_tab.save()
                        print("---------------当前局数入库成功------------------")
                    else:
                        print("---------------当前局数已经存在------------------")
                    ludan_save(messages, boots)

            elif sendModes == "openingDtResult" and status == True:
                boots = Boots.objects.all().first()
                number_tab = Number_tab.objects.get(bet_statu=2, number_tab_id=0, number_tab_number=0, boots_id=boots.id, opening=0, pair=0, previous_number_tab_id=0)
                number_tab.tid = table_info
                number_tab.boots = boots
                number_tab.number_tab_id = messages["round"]["number_tab_id"]
                number_tab.number_tab_number = messages["round"]["number_tab_number"]
                number_tab.previous_number_tab_id = messages["round"]["previous_number_tab_id"]
                if "opening" in messages["round"]:
                    number_tab.opening = messages["round"]["opening"]
                if "pair" in messages["round"]:
                    number_tab.pair = messages["round"]["pair"]
                number_tab.bet_statu = messages["round"]["number_tab_status"]["betStatus"]
                number_tab.save()
                ludan_save(messages, boots)
                print("-------------第"+str(number_tab.boots.boot_id)+"靴----第"+str(number_tab.number_tab_number)+"局---已经开奖----")
            elif sendModes == "startBet" and status == True:
                table_info.in_checkout = 0
                table_info.save()
                boots = Boots.objects.all().first()
                number_tab = Number_tab()
                number_tab.tid = table_info
                number_tab.boots = boots
                number_tab.bet_statu = messages["round"]["number_tab_status"]["betStatus"]
                number_tab.save()
                print("---------------接受下注---------新局部数生成成功---------")
            elif sendModes == "endBet" and status == True:
                boots = Boots.objects.all().first()
                number_tab = Number_tab()
                number_tab.tid = table_info
                number_tab.boots = boots
                number_tab.bet_statu = messages["round"]["number_tab_status"]["betStatus"]
                number_tab.save()
                print("---------------结束下注---------当局状态改变---------")
            elif sendModes == "inCheckout" and status == True:
                print("------------------桌子开始洗牌------------------")
                if messages["round"]["number_tab_status"]["type"] == 1:
                    table_info.in_checkout = int(messages["round"]["number_tab_status"]["in_checkout"])
                    table_info.save()
                    print("------------------桌子开始洗牌成功------------------")
            elif sendModes == "changeBoot" and status == True:
                print("------------------桌子开始换靴------------------")
                if messages["round"]["number_tab_status"]["type"] == 2:
                    is_boots = Boots.objects.filter(boot_id=messages["round"]["boot_id"],
                                                    boot_num=messages["round"]["boot_num"]).count()
                    if is_boots == 0:
                        boots = Boots()
                        boots.tid = table_info
                        boots.boot_id = int(messages["round"]["boot_id"])
                        boots.boot_num = int(messages["round"]["boot_num"])
                        boots.save()
                        print("---------------新靴号入库成功------------------")
                    else:
                        print("---------------该靴号已经存在------------------")
                        boots = Boots.objects.get(boot_id=messages["round"]["boot_id"],
                                                  boot_num=messages["round"]["boot_num"])
                    is_Number_tab = Number_tab.objects.filter(number_tab_id=messages["round"]["number_tab_id"],
                                                              number_tab_number=messages["round"][
                                                                  "number_tab_number"]).count()
                    if is_Number_tab == 0:
                        number_tab = Number_tab()
                        number_tab.tid = table_info
                        number_tab.boots = boots
                        number_tab.number_tab_id = messages["round"]["number_tab_id"]
                        number_tab.number_tab_number = messages["round"]["number_tab_number"]
                        if "opening" in messages["round"]:
                            number_tab.opening = messages["round"]["opening"]
                        if "pair" in messages["round"]:
                            number_tab.pair = messages["round"]["pair"]
                        number_tab.bet_statu = messages["round"]["number_tab_status"]["betStatus"]
                        number_tab.save()
                        print("---------------新局数入库成功------------------")
                    else:
                        print("---------------新局数已经存在------------------")
            elif sendModes == "resetBoot" and status == True:
                print("------------------日结------------------")
                # if messages["round"]["number_tab_status"]["type"] == 1:
                #     table_info.in_checkout = int(messages["round"]["number_tab_status"]["in_checkout"])
                #     table_info.save()
                #     print("------------------桌子开始洗牌成功------------------")


    @staticmethod
    def on_error(ws, error):
        print("ws链接报错！=====================", error)

    @staticmethod
    def on_close(ws):
        print("### ws链接关闭 ###")

    @staticmethod
    def get_websocket_url():
        table_info = Table.objects.get(three_table_id=4)
        return table_info.websocket_url

    @staticmethod
    def on_open(ws):
        get_token = Table.objects.get_token(three_table_id=4)
        params = json.dumps(get_token)
        ws.send(params)

    def handle(self, *args, **options):
        websocket_url = self.get_websocket_url()
        websocket.enableTrace(True)
        wsapp = websocket.WebSocketApp(
            websocket_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close)
        wsapp.on_open = self.on_open
        wsapp.run_forever(ping_timeout=30)

# -----------------------大路图需要修改--------------------
