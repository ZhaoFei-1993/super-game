from django.core.management.base import BaseCommand, CommandError
import websocket
import json
from dragon_tiger.models import Table, Boots, Number_tab, Dragontigerrecord
from utils.functions import ludan_save, normalize_fraction, to_decimal
import hashlib
import time
from urllib import parse
from django.conf import settings
from users.models import UserCoin
from rq import Queue
from redis import Redis
from dragon_tiger.consumers import dragon_tiger_table_info, dragon_tiger_number_info, \
    dragon_tiger_boots_info, dragon_tiger_result, dragon_tiger_lottery, dragon_tiger_road_info
from utils.cache import delete_cache
from decimal import Decimal
from users.models import CoinDetail


class Command(BaseCommand):
    help = '龙虎斗5号台'

    @staticmethod
    def on_message(ws, message):
        messages = json.loads(message)
        print('messages = ', messages)
        # with open(settings.BASE_DIR + '/0000', 'a+') as f:
        #     f.write(str(messages))           # 保存数据成文件
        status = messages["status"]
        sendModes = messages["sendMode"]
        redis_conn = Redis()
        q = Queue(connection=redis_conn)
        if status is False:
            table_info = Table.objects.get(three_table_id=4)
            table_info.in_checkout = 2
            table_info.save()
            # ws.close()
            print("------------------桌子暂未运营------------------")
        else:
            table_info = Table.objects.get(three_table_id=4)
            if sendModes == "onlineLogin" and status is True:
                print("--------------------第一次链接-------------------------")
                if messages["round"]["number_tab_status"]["type"] == 1:
                    table_info.in_checkout = int(messages["round"]["number_tab_status"]["in_checkout"])
                    table_info.save()
                    print("-------------桌子状态推送---------------")
                    q.enqueue(dragon_tiger_table_info, table_info.id,
                              messages["round"]["number_tab_status"]["in_checkout"])
                    print("-----------桌子状态推送完成--------------")
                    print("------------------桌子状态改变成功------------------")
                if messages["round"]["number_tab_status"]["type"] == 2:
                    is_boots = Boots.objects.filter(boot_id=messages["round"]["boot_id"],
                                                    tid_id=table_info.id,
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
                        boots = Boots.objects.get(tid_id=table_info.id,
                                                  boot_id=messages["round"]["boot_id"],
                                                  boot_num=messages["round"]["boot_num"])
                    print("-------------靴号开始推送---------------")
                    q.enqueue(dragon_tiger_boots_info, table_info.id, boots.id, boots.boot_num)
                    print("-----------靴号推送完成--------------")
                    is_Number_tab = Number_tab.objects.filter(tid_id=table_info.id,
                                                              number_tab_id=messages["round"]["number_tab_id"],
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
                        print("-------------局数开始推送---------------")
                        q.enqueue(dragon_tiger_number_info, table_info.id, number_tab.id,
                                  messages["round"]["number_tab_status"]["betStatus"])
                        print("-----------局数推送完成--------------")
                    else:
                        print("---------------当前局数已经存在------------------")
                    ludan_save(messages, boots, table_info.id)

            elif sendModes == "openingDtResult" and status is True:
                print("-----------------开奖--------------------")
                boots = Boots.objects.filter(tid_id=table_info.id).first()
                number_tab = Number_tab.objects.filter(tid_id=table_info.id).first()
                number_tab.tid = table_info
                number_tab.boots = boots
                number_tab.number_tab_id = messages["round"]["number_tab_id"]
                number_tab.number_tab_number = messages["round"]["number_tab_number"]
                number_tab.previous_number_tab_id = messages["round"]["previous_number_tab_id"]
                answer = 0
                if "opening" in messages["round"]:
                    number_tab.opening = messages["round"]["opening"]
                    if int(messages["round"]["opening"]) == 1:
                        answer = 1
                    elif int(messages["round"]["opening"]) == 2:
                        answer = 3
                    elif int(messages["round"]["opening"]) == 3:
                        answer = 2
                if "pair" in messages["round"]:
                    number_tab.pair = messages["round"]["pair"]
                number_tab.bet_statu = 3
                number_tab.save()
                if answer != 0:
                    print("-----------获得答案-----------", answer)
                    record_list = Dragontigerrecord.objects.filter(number_tab=number_tab.id)
                    lottery_info = {1: {}, 2: {}, 3: {}, 4: {}, 5: {}, 6: {}, 7: {}, 8: {}, 9: {}, 10: {}, 11: {},
                                    12: {}}
                    for record in record_list:
                        print("-------------开始循环表------------")
                        if record.option.id == answer:
                            print("------------用户id：" + str(record.user.id) + "-------答案正确--------")
                            earn_coin_one = record.option.odds * record.bets
                            earn_coin = earn_coin_one + record.bets
                            coin_id = record.club.coin.id
                            user_coin = UserCoin.objects.get(coin_id=coin_id, user_id=record.user.id)
                            user_coin.balance += earn_coin
                            user_coin.save()
                            coins = normalize_fraction(earn_coin, int(record.club.coin.coin_accuracy))
                            record.earn_coin = earn_coin
                            record.is_distribution = True
                            record.status = 1
                            record.save()
                            coin_detail = CoinDetail()
                            coin_detail.user = record.user
                            coin_detail.coin_name = record.club.coin.name
                            coin_detail.amount = '+' + str(coins)
                            coin_detail.rest = user_coin.balance
                            coin_detail.sources = 5
                            coin_detail.save()

                            balance = str(normalize_fraction(user_coin.balance, int(record.club.coin.coin_accuracy)))
                            if lottery_info[record.club.id] == {}:
                                lottery_info[record.club.id][record.user.id] = {"user_id": record.user.id,
                                                                                "balance": balance,
                                                                                "coins": coins,
                                                                                "coin_name": record.club.coin.name}
                            else:
                                if record.user.id in lottery_info[record.club.id]:
                                    lottery_info[record.club.id][record.user.id]["coins"] += coins
                                    lottery_info[record.club.id][record.user.id]["balance"] = balance
                                else:
                                    lottery_info[record.club.id][record.user.id] = {"user_id": record.user.id,
                                                                                    "balance": balance,
                                                                                    "coins": coins,
                                                                                    "coin_name": record.club.coin.name}
                        else:
                            print("------------用户id：" + str(record.user.id) + "-------答案错误--------")
                            old_earn_coin = "-" + str(record.bets)
                            old_earn_coin = to_decimal(old_earn_coin)
                            record.earn_coin = old_earn_coin
                            record.is_distribution = True
                            record.status = 1
                            record.save()

                    for club_id in lottery_info:
                        if lottery_info[club_id] == {}:
                            pass
                        else:
                            for user_id in lottery_info[club_id]:
                                print("-------------开奖开始推送---------------")
                                user_id = lottery_info[club_id][user_id]["user_id"]
                                balance = lottery_info[club_id][user_id]["balance"]
                                coins = str(lottery_info[club_id][user_id]["coins"])
                                coin_name = lottery_info[club_id][user_id]["coin_name"]
                                q.enqueue(dragon_tiger_lottery, user_id, coins, number_tab.opening, balance,
                                          coin_name, club_id)
                                print("-----------开奖推送完成--------------")
                # print("-------------开奖开始推送---------------")
                # coins = str(coins)
                # balance = str(normalize_fraction(user_coin.balance, int(record.club.coin.coin_accuracy)))
                # q.enqueue(dragon_tiger_lottery, record.user_id, coins, number_tab.opening,
                #           balance, record.club.coin.name, record.club.id)
                # print("-----------开奖推送完成--------------")

                print("-------------局数开始推送---------------")
                q.enqueue(dragon_tiger_number_info, table_info.id, number_tab.id,
                          3)
                opening = int(number_tab.opening)
                q.enqueue(dragon_tiger_result, table_info.id, number_tab.id, opening)
                print("-----------局数推送完成--------------")
                ludan_save(messages, boots, table_info.id)
                USER_BET_AVATAR = "USER_BET_AVATAR" + str(number_tab.id)  # key
                delete_cache(USER_BET_AVATAR)
                print("-------------第" + str(number_tab.boots.boot_id) + "靴----第" + str(number_tab.number_tab_number)
                      + "局---已经开奖----")

            elif sendModes == "startBet" and status is True:
                print("------------------开始接受下注--------------------")
                table_info.in_checkout = 0
                table_info.save()
                boots = Boots.objects.filter(tid_id=table_info.id).first()
                number_tab = Number_tab()
                number_tab.tid = table_info
                number_tab.boots = boots
                number_tab.bet_statu = messages["round"]["number_tab_status"]["betStatus"]
                number_tab.save()
                print("-------------桌子状态，局数开始推送---------------")
                q.enqueue(dragon_tiger_table_info, table_info.id, table_info.in_checkout)
                q.enqueue(dragon_tiger_number_info, table_info.id, number_tab.id,
                          messages["round"]["number_tab_status"]["betStatus"])
                print("-----------桌子状态，局数推送完成--------------")
                print("---------------接受下注---------新局部数生成成功---------")

            elif sendModes == "endBet" and status is True:
                print("------------------开始结束下注--------------------")
                # boots = Boots.objects.all().first()
                number_tab = Number_tab.objects.filter(tid_id=table_info.id).first()
                # number_tab.tid = table_info
                # number_tab.boots = boots
                number_tab.bet_statu = messages["round"]["number_tab_status"]["betStatus"]
                number_tab.save()
                print("-------------局数推送---------------")
                q.enqueue(dragon_tiger_number_info, table_info.id, number_tab.id,
                          messages["round"]["number_tab_status"]["betStatus"])
                print("-----------局数推送完成--------------")
                print("---------------结束下注---------当局状态改变---------")

            elif sendModes == "inCheckout" and status is True:
                print("------------------桌子开始洗牌------------------")
                if messages["round"]["number_tab_status"]["type"] == 1:
                    table_info.in_checkout = int(messages["round"]["number_tab_status"]["in_checkout"])
                    table_info.save()
                    print("-------------桌子状态推送---------------")
                    q.enqueue(dragon_tiger_table_info, table_info.id,
                              messages["round"]["number_tab_status"]["in_checkout"])
                    print("-----------桌子状态推送完成--------------")
                    print("------------------桌子开始洗牌成功------------------")

            elif sendModes == "changeBoot" and status is True:
                print("------------------桌子开始换靴------------------")
                if messages["round"]["number_tab_status"]["type"] == 2:
                    is_boots = Boots.objects.filter(tid_id=table_info.id,
                                                    boot_id=messages["round"]["boot_id"],
                                                    boot_num=messages["round"]["boot_num"]).count()
                    if is_boots == 0:
                        boots = Boots()
                        boots.tid = table_info
                        boots.boot_id = int(messages["round"]["boot_id"])
                        boots.boot_num = int(messages["round"]["boot_num"])
                        boots.save()
                        print("---------------新靴号入库成功------------------")
                        print("-------------靴号推送---------------")
                        q.enqueue(dragon_tiger_boots_info, table_info.id, boots.id, boots.boot_num)
                        print("-----------靴号推送完成--------------")
                    else:
                        print("---------------该靴号已经存在------------------")
                        boots = Boots.objects.get(tid_id=table_info.id,
                                                  boot_id=messages["round"]["boot_id"],
                                                  boot_num=messages["round"]["boot_num"])
                    is_Number_tab = Number_tab.objects.filter(tid_id=table_info.id,
                                                              number_tab_id=messages["round"]["number_tab_id"],
                                                              number_tab_number=messages["round"][
                                                                  "number_tab_number"]).count()
                    print("-------------局数推送---------------")
                    ludan = {
                        "showroad_list": "",
                        "bigroad_list": "",
                        "bigeyeroad_list": "",
                        "psthway_list": "",
                        "roach_list": ""
                    }
                    q.enqueue(dragon_tiger_road_info, table_info.id, ludan)
                    print("-----------局数推送完成--------------")
                    if is_Number_tab == 0:
                        number_tab = Number_tab()
                        number_tab.tid = table_info
                        number_tab.boots = boots
                        number_tab.number_tab_id = messages["round"]["number_tab_id"]
                        number_tab.number_tab_number = messages["round"]["number_tab_number"]
                        number_tab.bet_statu = messages["round"]["number_tab_status"]["betStatus"]
                        number_tab.save()
                        print("---------------新局数入库成功------------------")
                        print("-------------局数推送---------------")
                        q.enqueue(dragon_tiger_number_info, table_info.id, number_tab.id,
                                  messages["round"]["number_tab_status"]["betStatus"])
                        print("-----------局数推送完成--------------")
                        print("------------------桌子洗牌成功------------------")
                    else:
                        print("---------------新局数已经存在------------------")

            elif sendModes == "resetBoot" and status is True:
                print("------------------日结开始------------------")
                # print("------------------上局部路单入库--------------------")
                # boots = Boots.objects.all().first()
                # ludan_save(messages, boots, table_info.id)
                # print("---------------上局部路单入库成功------------------")
                table_info.in_checkout = 2
                table_info.save()
                print("-------------桌子状态推送---------------")
                q.enqueue(dragon_tiger_table_info, table_info.id, 2)
                print("-----------桌子状态推送完成--------------")
                print("------------桌子状态改变成功-------------")
                if messages["round"]["number_tab_status"]["type"] == 2:
                    is_boots = Boots.objects.filter(tid_id=table_info.id,
                                                    boot_id=messages["round"]["boot_id"],
                                                    boot_num=messages["round"]["boot_num"]).count()
                    if is_boots == 0:
                        boots = Boots()
                        boots.tid = table_info
                        boots.boot_id = int(messages["round"]["boot_id"])
                        boots.boot_num = int(messages["round"]["boot_num"])
                        boots.save()
                        print("---------------当前靴号入库成功------------------")
                        print("-------------靴号推送---------------")
                        q.enqueue(dragon_tiger_boots_info, table_info.id, boots.id, boots.boot_num)
                        print("-----------靴号推送完成--------------")
                    else:
                        print("---------------靴号已经存在------------------")
                        boots = Boots.objects.get(tid_id=table_info.id,
                                                  boot_id=messages["round"]["boot_id"],
                                                  boot_num=messages["round"]["boot_num"])
                    is_Number_tab = Number_tab.objects.filter(tid_id=table_info.id,
                                                              number_tab_id=messages["round"]["number_tab_id"],
                                                              number_tab_number=messages["round"][
                                                                  "number_tab_number"]).count()
                    if is_Number_tab == 0:
                        number_tab = Number_tab()
                        number_tab.tid = table_info
                        number_tab.boots = boots
                        number_tab.number_tab_id = messages["round"]["number_tab_id"]
                        number_tab.number_tab_number = messages["round"]["number_tab_number"]
                        number_tab.bet_statu = messages["round"]["number_tab_status"]["betStatus"]
                        number_tab.save()
                        print("---------------当前局数入库成功------------------")
                        print("-------------局数推送---------------")
                        q.enqueue(dragon_tiger_number_info, table_info.id, number_tab.id,
                                  messages["round"]["number_tab_status"]["betStatus"])
                        print("-----------局数推送完成--------------")
                    else:
                        print("---------------当前局数已经存在------------------")
                    print("---------------日结-成功------------------")

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
