# -*- coding: UTF-8 -*-
from base.app import ListAPIView, ListCreateAPIView
from utils.functions import value_judge, float_to_str
from django.db import transaction
from base import code as error_code
from base.exceptions import ParamErrorException
import requests
from utils.functions import value_judge, get_sql
import json
import re
from decimal import Decimal
from dragon_tiger.models import BetLimit
from utils.functions import normalize_fraction
from base.function import LoginRequired
from dragon_tiger.models import BetLimit, Number_tab, Options, Dragontigerrecord, Table
from users.models import Coin, UserCoin, CoinDetail
from chat.models import Club
from utils.cache import get_cache, set_cache
from utils.functions import obtain_token


class Table_boots(ListAPIView):
    """
    桌子信息
    """

    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        if 'table_id' not in self.request.GET:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        table_id = str(self.request.GET.get('table_id'))
        sql_list = "db.id, db.boot_id, db.boot_num"
        sql = "select " + sql_list + " from dragon_tiger_boots db"
        sql += " where db.tid_id= '" + table_id + "'"
        sql += " order by db.id desc limit 1"
        boot_info = get_sql(sql)
        if boot_info == ():
            boot_list = {}
        else:
            boot_list = {
                "boot_id": boot_info[0][0],           # 靴ID
                "three_boot_id": boot_info[0][1],        # 第三方靴ID
                "boot_number": boot_info[0][2]         # 靴号
            }

        if boot_info == ():
            number_tab_list = {
                "number_tab_id": "",  # 局id
                "number_tab_number": "",  # 第三方局号
                "opening": 0,  # 开局结果(0.空/1.龙&庄/2.虎&闲/3.和)
                # "opening": "空“,      # 开局结果(0.空/1.龙&庄/2.虎&闲/3.和)
                "pair": 0,  # 开局结果(对子)[0.空/1.龙对&庄对/2.虎对&闲对/3.和&对]
                # "pair": "空“,        # 开局结果(对子)[0.空/1.龙对&庄对/2.虎对&闲对/3.和&对]
                "bet_statu": 0,  # 本局状态[0.尚未接受下注/1.接受下注/2.停止下注-等待开盘/3.已开奖]
                # "bet_statu": 尚未接受下注,      # 本局状态
                "previous_three_number_tab_id": "",  # 第三方上局_id
                "three_number_tab_id": ""  # 第三方局ID
            }
            ludan = {
                "showroad_list": "",
                "bigroad_list": "",
                "bigeyeroad_list": "",
                "psthway_list": "",
                "roach_list": ""
            }
        else:
            sql_list = "nt.id, nt.number_tab_number, nt.opening, nt.pair, nt.bet_statu, nt.previous_number_tab_id, " \
                       "nt.number_tab_id"
            sql = "select " +sql_list + " from dragon_tiger_number_tab nt"
            sql += " where nt.tid_id = '" + table_id + "'"
            sql += " and nt.boots_id = '" + str(boot_info[0][0]) + "'"
            sql += " order by nt.id desc limit 1"
            number_tab_info = get_sql(sql)
            # opening_list = dict(Number_tab.OPENING_LIST)
            # pair_list = dict(Number_tab.PAIR_LIST)
            # bet_list = dict(Number_tab.BET_LIST)
            if number_tab_info == ():
                number_tab_list = {}
            else:
                number_tab_list = {
                    "number_tab_id": number_tab_info[0][0],  # 局id
                    "number_tab_number": number_tab_info[0][1],  # 第三方局号
                    "opening": number_tab_info[0][2],  # 开局结果(0.空/1.龙&庄/2.虎&闲/3.和)
                    # "opening": opening_list[int(i[0][2])],      # 开局结果(0.空/1.龙&庄/2.虎&闲/3.和)
                    "pair": number_tab_info[0][3],  # 开局结果(对子)[0.空/1.龙对&庄对/2.虎对&闲对/3.和&对]
                    # "pair": pair_list[int(i[0][3])],        # 开局结果(对子)[0.空/1.龙对&庄对/2.虎对&闲对/3.和&对]
                    "bet_statu": number_tab_info[0][4],  # 本局状态[0.尚未接受下注/1.接受下注/2.停止下注-等待开盘/3.已开奖]
                    # "bet_statu": bet_list[int(i[0][4])],      # 本局状态
                    "previous_three_number_tab_id": number_tab_info[0][5],  # 第三方上局_id
                    "three_number_tab_id": number_tab_info[0][6],  # 第三方局ID
                }

            sql_list = "sr.result_show, sr.show_x_show, sr.show_y_show"
            sql = "select " +sql_list+ " from dragon_tiger_showroad sr"
            sql += " where sr.boots_id = '" + str(boot_info[0][0]) + "'"
            sql += " order by sr.order_show"
            showroad_info = get_sql(sql)
            showroad_list = []             # 结果图
            for i in showroad_info:
                showroad_list.append({
                    "show_x": i[1],      # X轴
                    "show_y": i[2],      # Y轴
                    "result": int(i[0])     # 结果[1.龙&庄/2.虎&闲/3.和]
                    })

            sql_list = "br.result_big, br.show_x_big, br.show_y_big, br.tie_num"
            sql = "select " +sql_list+ " from dragon_tiger_bigroad br"
            sql += " where br.boots_id = '" + str(boot_info[0][0]) + "'"
            sql += " order by br.order_big"
            bigroad_info = get_sql(sql)
            bigroad_list = []             # 大路图
            for i in bigroad_info:
                bigroad_list.append({
                    "show_x": i[1],      # X轴
                    "show_y": i[2],      # Y轴
                    "result": int(i[0]),     # 结果[1.龙&庄/2.虎&闲/3.和]
                    "tie_num": i[3]     # 是否有和
                    })

            sql_list = "be.result_big_eye, be.show_x_big_eye, be.show_y_big_eye"
            sql = "select " + sql_list + " from dragon_tiger_bigeyeroad be"
            sql += " where be.boots_id = '" + str(boot_info[0][0]) + "'"
            sql += " order by be.order_big_eye"
            bigeyeroad_info = get_sql(sql)
            bigeyeroad_list = []  # 大路图
            for i in bigeyeroad_info:
                bigeyeroad_list.append({
                    "show_x": i[1],  # X轴
                    "show_y": i[2],  # Y轴
                    "result": int(i[0]),  # 结果[1.龙&庄/2.虎&闲]
                })

            sql_list = "pw.result_psthway, pw.show_x_psthway, pw.show_y_psthway"
            sql = "select " +sql_list+ " from dragon_tiger_psthway pw"
            sql += " where pw.boots_id = '" + str(boot_info[0][0]) + "'"
            sql += " order by pw.order_psthway"
            psthway_info = get_sql(sql)
            psthway_list = []             # 结果图
            for i in psthway_info:
                psthway_list.append({
                    "show_x": i[1],      # X轴
                    "show_y": i[2],      # Y轴
                    "result": int(i[0])     # 结果[1.龙&庄/2.虎&闲]
                    })

            sql_list = "r.result_roach, r.show_x_roach, r.show_y_roach"
            sql = "select " +sql_list+ " from dragon_tiger_roach r"
            sql += " where r.boots_id = '" + str(boot_info[0][0]) + "'"
            sql += " order by r.order_roach"
            roach_info = get_sql(sql)
            roach_list = []             # 结果图
            for i in roach_info:
                roach_list.append({
                    "show_x": i[1],      # X轴
                    "show_y": i[2],      # Y轴
                    "result": int(i[0])     # 结果[1.龙&庄/2.虎&闲]
                    })
            ludan = {
                "showroad_list": showroad_list,
                "bigroad_list": bigroad_list,
                "bigeyeroad_list": bigeyeroad_list,
                "psthway_list": psthway_list,
                "roach_list": roach_list
            }

        data = {
            "boot_list": boot_list,
            "number_tab_list": number_tab_list,
            "ludan": ludan

        }
        return self.response({'code': 0, "data": data})


class Table_list(ListAPIView):
    """
    获取桌子列表
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        if 'type' not in self.request.GET:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        types = str(self.request.GET.get('type'))
        regex = re.compile(r'^(1|2)$')
        if types is None or not regex.match(types):
            raise ParamErrorException(error_code.API_10104_PARAMETER_EXPIRED)
        sql_list = "dt.id, dt.three_table_id, dt.table_name, dt.status, dt.in_checkout, dt.wait_time, dt.game_name"
        sql = "select "+sql_list+" from dragon_tiger_table dt"
        sql += " where dt.game_name = '" + types + "'"
        table_list = get_sql(sql)  # 获取桌子信息
        data = []
        name_list = dict(Table.NAME_LIST)
        # table_status = dict(Table.Table_STATUS)
        # table_in_checkou = dict(Table.TABLE_IN_CHECKOU)
        for i in table_list:
            data.append({
                "table_id": i[0],     # 桌ID
                "three_table_id": i[1],  # 第三方桌ID
                "table_name": i[2],  # 桌子昵称
                "wait_time": i[5],     # 等待时间
                "game_name": name_list[int(i[6])],   # 游戏昵称
                # "status": table_status[int(i[3])],    # 桌子状态(开、停)
                # "in_checkout": table_in_checkou[int(i[4])],    # 桌子状态
                "in_checkout_number": i[4],    # 桌子状态(0.正常/1,洗牌/2.停桌)
            })

        return self.response({'code': 0, "data": data})


class Dragontigeroption(ListAPIView):
    """
    龙虎斗：选项
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        if 'club_id' not in self.request.GET or 'type' not in self.request.GET:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        user_id = str(request.user.id)
        user_avatar = request.user.avatar
        club_id = str(self.request.GET.get('club_id'))
        types = str(self.request.GET.get('type'))
        sql = "select cc.coin_id from chat_club cc"
        sql += " where cc.id = '" + club_id + "'"
        coin_id = get_sql(sql)[0][0]  # 获取coin_id

        sql = "select uc.coin_accuracy, uc.icon from users_coin uc"
        sql += " where uc.id = '" + str(coin_id) + "'"
        coin_info = get_sql(sql)[0]  # 获取货币精度
        coin_accuracy = int(coin_info[0])  # 获取货币精度
        coin_icon = coin_info[1]  # 获取货币精度

        sql = "select uc.balance from users_usercoin uc"
        sql += " where uc.coin_id = '" + str(coin_id) + "'"
        sql += " and uc.user_id= '" + user_id + "'"
        user_balance = get_sql(sql)[0][0]  # 获取用户金额
        user_balance = float(user_balance)
        user_balance = normalize_fraction(user_balance, coin_accuracy)

        sql = "select b.bets_one, b.bets_two, b.bets_three, b.bets_four, b.red_limit from dragon_tiger_betlimit b"
        sql += " where b.club_id = '" + club_id + "'"
        sql += " and b.types= '" + types + "'"
        betlimit_list = get_sql(sql)[0]  # 选项和限红

        # sql = "select dto.title, concat(1,':',dto.odds), dto.order from dragon_tiger_options dto"
        # sql += " where dto.types = '" + types + "'"
        # option_list = get_sql(sql)  # 获取选项               # 留下来的例子(查询并且处理字段)

        sql = "select dto.title, dto.odds, dto.order, dto.id from dragon_tiger_options dto"
        sql += " where dto.types = '" + types + "'"
        option_list = get_sql(sql)  # 获取选项
        dragon_odds = str(1) + ":" + str(int(option_list[0][1]))
        tie_odds = str(1) + ":" + str(int(option_list[1][1]))
        player_odds = str(1) + ":" + str(int(option_list[2][1]))
        option_info = {
            "dragon": {
                "title": option_list[0][0],
                "odds": dragon_odds,
                "order": option_list[0][2],
                "option_id": option_list[0][3],
            },
            "tie": {
                "title": option_list[1][0],
                "odds": tie_odds,
                "order": option_list[1][2],
                "option_id": option_list[1][3],
            },
            "player": {
                "title": option_list[2][0],
                "odds": player_odds,
                "order": option_list[2][2],
                "option_id": option_list[2][3],
            }
        }

        return self.response({'code': 0,
                              "user_balance": user_balance,
                              "coin_icon": coin_icon,
                              "user_avatar": user_avatar,
                              "bets_one": betlimit_list[0],
                              "bets_one_icon": "https://api.gsg.one/uploads/pokermaterial/web/c_1_m.png",
                              "bets_two": betlimit_list[1],
                              "bets_two_icon": "https://api.gsg.one/uploads/pokermaterial/web/c_2_m.png",
                              "bets_three": betlimit_list[2],
                              "bets_three_icon": "https://api.gsg.one/uploads/pokermaterial/web/c_3_m.png",
                              "bets_four": betlimit_list[3],
                              "bets_four_icon": "https://api.gsg.one/uploads/pokermaterial/web/c_4_m.png",
                              "red_limit": int(betlimit_list[4]),
                              "option_info": option_info
                              })


class DragontigerBet(ListCreateAPIView):
    """
    龙虎斗下注
    """

    def get_queryset(self):
        pass

    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        value = value_judge(request, "number_tab_id", "option_id", "bet", "club_id")
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        user = request.user
        number_tab_id = self.request.data['number_tab_id']  # 获取周期ID
        option_id = self.request.data['option_id']  # 获取俱乐部ID
        club_id = self.request.data['club_id']  # 获取俱乐部ID
        coins = self.request.data['bet']  # 获取投注金额
        coins = float(coins)

        try:
            number_tab_info = Number_tab.objects.get(pk=number_tab_id)
        except Exception:
            raise ParamErrorException(error_code.API_40105_SMS_WAGER_PARAMETER)
        clubinfo = Club.objects.get(pk=club_id)
        coin_id = clubinfo.coin.pk  # 货币ID
        coin_accuracy = int(clubinfo.coin.coin_accuracy)  # 货币精度

        try:  # 判断选项ID是否有效
            option_odds = Options.objects.get(pk=option_id)
        except Exception:
            raise ParamErrorException(error_code.API_50101_QUIZ_OPTION_ID_INVALID)

        if int(option_odds.types) != 2:
            raise ParamErrorException(error_code.API_50101_QUIZ_OPTION_ID_INVALID)

        if int(number_tab_info.bet_statu) == 0:
            raise ParamErrorException(error_code.API_90101_DRAGON_TIGER_NO_BET)
        if int(number_tab_info.bet_statu) == 2:
            raise ParamErrorException(error_code.API_90102_DRAGON_TIGER_NO_BET)
        if int(number_tab_info.bet_statu) == 3:
            raise ParamErrorException(error_code.API_90101_DRAGON_TIGER_NO_BET)
        i = float(0)
        # 判断赌注是否有效
        if i >= Decimal(coins):
            raise ParamErrorException(error_code.API_50102_WAGER_INVALID)

        try:
            bet_limit = BetLimit.objects.get(club_id=club_id, types=2)
        except Exception:
            raise ParamErrorException(error_code.API_40105_SMS_WAGER_PARAMETER)

        if int(option_id) == 2:
            option_id_one = 1
            option_id_two = 3
        elif int(option_id) == 1:
            option_id_one = 2
            option_id_two = 3
        else:
            option_id_one = 1
            option_id_two = 2
        option_number = "("+str(option_id_one)+", "+str(option_id_two)+")"
        sql = "select sum(dtr.bets) from dragon_tiger_dragontigerrecord dtr"
        sql += " where dtr.option_id in"+option_number
        sql += " and dtr.number_tab_id = '" + str(number_tab_id) + "'"
        print("sql===========================", sql)
        coin_number = get_sql(sql)[0][0]
        if coin_number == None or coin_number == 0:
            all_earn_coins = bet_limit.red_limit
        else:
            coin_number = normalize_fraction(coin_number, int(coin_accuracy))
            all_earn_coins = coin_number + normalize_fraction(bet_limit.red_limit, int(coin_accuracy))  # 能赔金额
        print("一共可以赔============================", all_earn_coins)

        sql = "select sum(dtr.earn_coin) from dragon_tiger_dragontigerrecord dtr"
        sql += " where dtr.option_id = '" + str(option_id) + "'"
        sql += " and dtr.number_tab_id = '" + str(number_tab_id) + "'"
        coin_number_in = get_sql(sql)[0][0]
        earn_coin = float(option_odds.odds) * coins  # 应赔金额
        if coin_number_in == None or coin_number_in == 0:
            coin_number_in = 0
            all_earn_coin = earn_coin  # 应赔金额
        else:
            coin_number_in = normalize_fraction(coin_number_in, int(coin_accuracy))
            all_earn_coin = float(coin_number_in) + earn_coin
        print("一共要赔======================", all_earn_coin)

        if all_earn_coin > all_earn_coins:
            is_coins = (all_earn_coins - coin_number_in) / option_odds.odds
            is_coins = normalize_fraction(float(is_coins), int(coin_accuracy))
            message = str(is_coins) + str(clubinfo.coin.name) + "!"
            raise ParamErrorException(error_code.API_90104_DRAGON_TIGER_NO_BET, {'params': (message,)})  # 限红

        usercoin = UserCoin.objects.get(user_id=user.id, coin_id=coin_id)
        # 判断用户金币是否足够
        if float(usercoin.balance) < coins:
            raise ParamErrorException(error_code.API_50104_USER_COIN_NOT_METH)

        record = Dragontigerrecord()
        record.user = user
        record.club = clubinfo
        record.number_tab = number_tab_info
        record.option = option_odds
        record.bets = coins

        record.earn_coin = earn_coin+coins
        source = request.META.get('HTTP_X_API_KEY')
        if source == "ios":
            source = 1
        elif source == "android":
            source = 2
        else:
            source = 3
        if user.is_robot == True:
            source = 4
        record.source = source
        record.save()

        # 用户减少金币
        # balance = float_to_str(float(usercoin.balance), coin_accuracy)
        usercoin.balance = usercoin.balance - Decimal(coins)
        usercoin.save()

        coin_detail = CoinDetail()
        coin_detail.user = user
        coin_detail.coin_name = usercoin.coin.name
        coin_detail.amount = '-' + str(coins)
        coin_detail.rest = usercoin.balance
        coin_detail.sources = 15
        coin_detail.save()
        response = {
            'code': 0,
            'data': {
                'message': '下注成功，金额总数为 ' + str(
                    normalize_fraction(coins, int(coin_accuracy))) + '，预计可得猜币 ' + str(
                    normalize_fraction(earn_coin, int(coin_accuracy))),
                'balance': normalize_fraction(usercoin.balance, int(coin_accuracy))
            }
        }
        return self.response(response)
