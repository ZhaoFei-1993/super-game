# -*- coding: UTF-8 -*-
from base.app import ListAPIView, ListCreateAPIView
from django.db import transaction
from base import code as error_code
from base.exceptions import ParamErrorException
from utils.functions import value_judge, get_sql
from decimal import Decimal
from utils.functions import normalize_fraction
from base.function import LoginRequired
from dragon_tiger.models import BetLimit, Options, Table
from users.models import UserCoin, CoinDetail, RecordMark
from chat.models import Club
import re
# from utils.cache import get_cache, set_cache
from rq import Queue
from redis import Redis
# from baccarat.consumers import baccarat_avatar
from baccarat.models import Baccaratrecord, Number_tab

redis_conn = Redis()
q = Queue(connection=redis_conn)
from promotion.models import PromotionRecord


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
        sql_list = "dt.id, dt.three_table_id, dt.table_name, dt.status, dt.in_checkout, dt.wait_time, dt.game_name"
        sql = "select " + sql_list + " from dragon_tiger_table dt"
        sql += " where dt.id = '" + table_id + "'"
        table_list = get_sql(sql)  # 获取桌子信息
        data = []
        name_list = dict(Table.NAME_LIST)
        if table_list == ():
            table_info = {}
        else:
            table_info = {
                "table_id": table_list[0][0],  # 桌ID
                "three_table_id": table_list[0][1],  # 第三方桌ID
                "table_name": table_list[0][2],  # 桌子昵称
                "wait_time": table_list[0][5],  # 等待时间
                "game_name": name_list[int(table_list[0][6])],  # 游戏昵称
                # "status": table_status[int(i[3])],    # 桌子状态(开、停)
                # "in_checkout": table_in_checkou[int(i[4])],    # 桌子状态
                "in_checkout_number": table_list[0][4],  # 桌子状态(0.正常/1,洗牌/2.停桌)
            }

        sql_list = "bb.id, bb.boot_id, bb.boot_num"
        sql = "select " + sql_list + " from baccarat_boots bb"
        sql += " where bb.tid_id= '" + table_id + "'"
        sql += " order by bb.id desc limit 1"
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
            sql_list = "bn.id, bn.number_tab_number, bn.opening, bn.pair, bn.bet_statu, bn.previous_number_tab_id, " \
                       "bn.number_tab_id"
            sql = "select " +sql_list + " from baccarat_number_tab bn"
            sql += " where bn.tid_id = '" + table_id + "'"
            sql += " and bn.boots_id = '" + str(boot_info[0][0]) + "'"
            sql += " order by bn.id desc limit 1"
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
                    "opening": int(number_tab_info[0][2]),  # 开局结果(0.空/1.龙&庄/2.虎&闲/3.和)
                    # "opening": opening_list[int(i[0][2])],      # 开局结果(0.空/1.龙&庄/2.虎&闲/3.和)
                    "pair": int(number_tab_info[0][3]),  # 开局结果(对子)[0.空/1.龙对&庄对/2.虎对&闲对/3.和&对]
                    # "pair": pair_list[int(i[0][3])],        # 开局结果(对子)[0.空/1.龙对&庄对/2.虎对&闲对/3.和&对]
                    "bet_statu": int(number_tab_info[0][4]),  # 本局状态[0.尚未接受下注/1.接受下注/2.停止下注-等待开盘/3.已开奖]
                    # "bet_statu": bet_list[int(i[0][4])],      # 本局状态
                    "previous_three_number_tab_id": number_tab_info[0][5],  # 第三方上局_id
                    "three_number_tab_id": number_tab_info[0][6],  # 第三方局ID
                }

            sql_list = "sb.result_show, sb.show_x_show, sb.show_y_show, sb.pair"
            sql = "select " +sql_list+ " from baccarat_showroad_baccarat sb"
            sql += " where sb.boots_id = '" + str(boot_info[0][0]) + "'"
            sql += " order by sb.order_show"
            showroad_info = get_sql(sql)
            showroad_list = []             # 结果图
            for i in showroad_info:
                showroad_list.append({
                    "show_x": i[1],      # X轴
                    "show_y": i[2],      # Y轴
                    "result": int(i[0]),     # 结果[1.龙&庄/2.虎&闲/3.和]
                    "pair": int(i[3])     # 结果[1.龙&庄/2.虎&闲/3.和]
                    })

            sql_list = "br.result_big, br.show_x_big, br.show_y_big, br.tie_num"
            sql = "select " +sql_list+ " from baccarat_bigroad_baccarat br"
            sql += " where br.boots_id = '" + str(boot_info[0][0]) + "'"
            sql += " order by br.order_big"
            bigroad_info = get_sql(sql)
            bigroad_list = []             # 大路图
            for i in bigroad_info:
                bigroad_list.append({
                    "show_x": i[1],      # X轴
                    "show_y": i[2],      # Y轴
                    "result": int(i[0]),     # 结果[1.龙&庄/2.虎&闲/3.和]
                    "tie_num": int(i[3])     # 是否有和
                    })

            sql_list = "be.result_big_eye, be.show_x_big_eye, be.show_y_big_eye"
            sql = "select " + sql_list + " from baccarat_bigeyeroad_baccarat be"
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
            sql = "select " +sql_list+ " from baccarat_psthway_baccarat pw"
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
            sql = "select " +sql_list+ " from  baccarat_roach_baccarat r"
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
            "table_info": table_info,
            "boot_list": boot_list,
            "number_tab_list": number_tab_list,
            "ludan": ludan

        }
        return self.response({'code': 0, "data": data})


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
        coins = Decimal(coins)

        try:
            number_tab_info = Number_tab.objects.get(pk=number_tab_id)
        except Exception:
            raise ParamErrorException(error_code.API_40105_SMS_WAGER_PARAMETER)
        clubinfo = Club.objects.get_one(pk=int(club_id))
        coin_id = clubinfo.coin.pk  # 货币ID
        coin_accuracy = int(clubinfo.coin.coin_accuracy)  # 货币精度

        try:  # 判断选项ID是否有效
            option_odds = Options.objects.get(pk=option_id)
        except Exception:
            raise ParamErrorException(error_code.API_50101_QUIZ_OPTION_ID_INVALID)

        if int(option_odds.types) != 1:
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
            bet_limit = BetLimit.objects.get(club_id=club_id, types=1)
        except Exception:
            raise ParamErrorException(error_code.API_40105_SMS_WAGER_PARAMETER)

        if int(option_id) == 4:
            option_id_one = 5
            option_id_two = 6
            option_id_three = 7
            option_id_four = 8
        elif int(option_id) == 5:
            option_id_one = 4
            option_id_two = 6
            option_id_three = 7
            option_id_four = 8
        elif int(option_id) == 6:
            option_id_one = 4
            option_id_two = 5
            option_id_three = 7
            option_id_four = 8
        elif int(option_id) == 7:
            option_id_one = 4
            option_id_two = 5
            option_id_three = 6
            option_id_four = 8
        else:
            option_id_one = 4
            option_id_two = 5
            option_id_three = 6
            option_id_four = 7
        option_number = "("+str(option_id_one)+", "+str(option_id_two)+", "+str(option_id_three)+", "+str(option_id_four)+")"
        sql = "select sum(dtr.bets) from baccarat_baccaratrecord dtr"
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

        sql = "select sum(dtr.bets) from baccarat_baccaratrecord dtr"
        sql += " where dtr.option_id = '" + str(option_id) + "'"
        sql += " and dtr.number_tab_id = '" + str(number_tab_id) + "'"
        coin_number_in = get_sql(sql)[0][0]
        earn_coin = Decimal(option_odds.odds) * coins  # 应赔金额
        if coin_number_in == None or coin_number_in == 0:
            coin_number_in = 0
            all_earn_coin = earn_coin  # 应赔金额
        else:
            coin_number_in = normalize_fraction(coin_number_in, int(coin_accuracy))
            coin_number_in = coin_number_in*Decimal(option_odds.odds)
            all_earn_coin = Decimal(coin_number_in) + earn_coin
        print("一共要赔======================", all_earn_coin)

        if all_earn_coin > all_earn_coins:
            is_coins = (all_earn_coins - coin_number_in) / option_odds.odds
            is_coins = normalize_fraction(float(is_coins), int(coin_accuracy))
            message = str(is_coins) + str(clubinfo.coin.name) + "!"
            raise ParamErrorException(error_code.API_90104_DRAGON_TIGER_NO_BET, {'params': (message,)})  # 限红

        usercoin = UserCoin.objects.get(user_id=user.id, coin_id=coin_id)
        # 判断用户金币是否足够
        if Decimal(usercoin.balance) < coins:
            raise ParamErrorException(error_code.API_50104_USER_COIN_NOT_METH)

        record = Baccaratrecord()
        record.user = user
        record.club = clubinfo
        record.number_tab = number_tab_info
        record.option = option_odds
        record.bets = coins

        # record.earn_coin = "-"+coins
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

        # USER_BET_AVATAR = "USER_BET_AVATAR" + number_tab_id  # key
        # avatar_info = get_cache(USER_BET_AVATAR)
        # if avatar_info[user.id] is not None:
        #     avatar_info[user.id]["bet_amount"] += coins
        # else:
        #     avatar_info[user.id] = {
        #         "user_avatar": user.avatar,
        #         "user_nickname": user.nickname,
        #         "bet_amount": coins
        #     }
        # set_cache(USER_BET_AVATAR, avatar_info)
        # avatar_lists = []
        #
        # for i in avatar_info:
        #     avatar_lists.append(avatar_info[i])
        # now_avatar_list = sorted(avatar_lists, key=lambda s: s["bet_amout"], reverse=True)
        # all_avatar_lists = []
        # if len(now_avatar_list) > 5:
        #     all_avatar_lists.append(now_avatar_list[0])
        #     all_avatar_lists.append(now_avatar_list[1])
        #     all_avatar_lists.append(now_avatar_list[2])
        #     all_avatar_lists.append(now_avatar_list[3])
        #     all_avatar_lists.append(now_avatar_list[4])
        # print("-----------开始推送---------------")
        # q.enqueue(baccarat_avatar, number_tab_id, all_avatar_lists)
        # print("-----------推送完成--------------")

        # 用户减少金币
        # balance = float_to_str(float(usercoin.balance), coin_accuracy)
        usercoin.balance = usercoin.balance - Decimal(coins)
        usercoin.save()

        coin_detail = CoinDetail()
        coin_detail.user = user
        coin_detail.coin_name = usercoin.coin.name
        coin_detail.amount = '-' + str(coins)
        coin_detail.rest = usercoin.balance
        coin_detail.sources = 16
        coin_detail.save()

        RecordMark.objects.update_record_mark(user.id, 5, 1)

        if int(club_id) == 1 or int(user.is_robot) == 1:
            pass
        else:
            PromotionRecord.objects.insert_record(user, clubinfo, record.id, Decimal(coins), 6, record.created_at)
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


# class Avatar(ListAPIView):
#     """
#     头像
#     """
#     permission_classes = (LoginRequired,)
#
#     def get_queryset(self):
#         pass
#
#     def list(self, request, *args, **kwargs):
#         if 'number_tab_id' not in self.request.GET:
#             raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
#         if 'club_id' not in self.request.GET:
#             raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
#         number_tab_id = str(self.request.GET.get('number_tab_id'))
#         club_id = str(self.request.GET.get('club_id'))
#         user_bet_avatar = "USER_BET_AVATAR" + number_tab_id  # key
#         avatar_list = get_cache(user_bet_avatar)
#         if avatar_list == None or avatar_list == '':
#             sql_list = "u.avatar, u.nickname, sum(dtr.bets) as sum_bets"
#             sql = "select " +sql_list + " from dragon_tiger_dragontigerrecord dtr"
#             sql += " inner join users_user u on dtr.user_id=u.id"
#             sql += " where dtr.number_tab_id = '" + number_tab_id + "'"
#             sql += " and dtr.club_id = '" + club_id + "'"
#             sql += " group by dtr.user_id"
#             sql += " order by sum_bets desc limit 5"
#             avatar_list = get_sql(sql)
#             data = []
#             s = 0
#             for i in avatar_list:
#                 data.append({
#                     "user_avatar": i[0],
#                     "user_nickname": i[1],
#                     "bet_amount": i[2]
#                     })
#         return self.response({'code': 0, "data": data})


class Changetable(ListAPIView):
    """
    头像
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        if 'table_id' not in self.request.GET:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        id = int(self.request.GET.get('table_id'))
        regex = re.compile(r'^(1|2|3)$')
        if id is None or not regex.match(id):
            raise ParamErrorException(error_code.API_10104_PARAMETER_EXPIRED)
        if id == 3:
            table_id = 1
        else:
            table_id = id + 1

        return self.response({'code': 0, "table_id": table_id})


class Record(ListAPIView):
    """
    记录
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
       pass

    def list(self, request, *args, **kwargs):
        sql_list = " dtr.number_tab_id"
        sql = "select " +sql_list + " from baccarat_baccaratrecord dtr"
        if 'user_id' not in self.request.GET:
            user_id = str(self.request.user.id)
            if 'is_end' not in self.request.GET:
                sql += " where dtr.user_id = '" + user_id + "'"
            else:
                is_end = self.request.GET.get('is_end')
                if int(is_end) == 1:
                    sql += " where dtr.user_id = '" + user_id + "'"
                    sql += " and dtr.status =0"
                else:
                    sql += " where dtr.user_id = '" + user_id + "'"
                    sql += " and dtr.status =1"
        else:
            user_id = str(self.request.GET.get('user_id'))
            sql += " where dtr.user_id = '" + user_id + "'"
        if "club_id" in self.request.GET:
            club_id = str(self.request.GET.get('club_id'))  # 俱乐部表ID
            sql += " and dtr.club_id = '" + club_id + "'"
        sql += " order by dtr.created_at desc"

        number_tab_id_list = get_sql(sql)  # 获取记录的number_tab_id
        data = []
        if number_tab_id_list == ():
            return self.response({'code': 0, "data": data})
        number_tab_id_list = list(set(number_tab_id_list))
        number_tab_id = []
        if len(number_tab_id_list) == 1:
            for i in number_tab_id_list:
                number_tab_id = "(" + str(i[0]) + ")"
        else:
            for i in number_tab_id_list:
                number_tab_id.append(i[0])
            number_tab_id = str(tuple(number_tab_id))

        sql_list = "sum(dtr.bets), sum(dtr.earn_coin), date_format( dtr.created_at, '%Y' ) as yearss,"
        sql_list += " date_format( dtr.created_at, '%c/%e' ) as years, date_format( dtr.created_at, '%k:%i' ) as time,"
        sql_list += " dtr.number_tab_id, nt.opening, o.title, nt.number_tab_number, dtr.option_id, o.odds, nt.pair,"
        sql_list += " date_format(dtr.created_at, '%Y%c%e%k%i' ) AS created_ats, c.coin_accuracy, c.icon, c.name"
        sql = "select " +sql_list + " from baccarat_baccaratrecord dtr"
        sql += " left join dragon_tiger_options o on dtr.option_id=o.id"
        sql += " left join baccarat_number_tab nt on dtr.number_tab_id = nt.id"
        sql += " left join chat_club c on dtr.club_id = c.id"
        sql += " where dtr.number_tab_id in" + number_tab_id
        if "club_id" in self.request.GET:
            club_id = str(self.request.GET.get('club_id'))  # 俱乐部表ID
            sql += " and dtr.club_id = '" + club_id + "'"
        if 'user_id' not in self.request.GET:
            user_id = str(self.request.user.id)
            if 'is_end' not in self.request.GET:
                sql += " and dtr.user_id = '" + user_id + "'"
            else:
                is_end = self.request.GET.get('is_end')
                if int(is_end) == 1:
                    sql += " and dtr.user_id = '" + user_id + "'"
                    sql += " and dtr.status =0"
                else:
                    sql += " and dtr.user_id = '" + user_id + "'"
                    sql += " and dtr.status =1"
        else:
            user_id = self.request.GET.get('user_id')
            sql += " and dtr.user_id = '" + user_id + "'"
        sql += " group by dtr.number_tab_id, yearss, years, time, o.title, option_id, " \
               "c.coin_accuracy, c.icon, c.name"
        sql += " order by created_ats desc"
        record_list = self.get_list_by_sql(sql)    #

        data = []
        tmp = ''
        for fav in record_list:
            my_option = str(fav[7]) + " - 1 ：" + str(int(fav[10]))

            if fav[1] == 0 or fav[1] == '':
                earn_coin = "待开奖"
                if self.request.GET.get('language') == 'en':
                    earn_coin = "Wait results"
            elif fav[1] < 0:
                earn_coin = "猜错"
                if self.request.GET.get('language') == 'en':
                    earn_coin = "Guess wrong"
            else:
                earn_coin = "+" + str(normalize_fraction(fav[1], int(fav[12])))

            if fav[1] == 0 or fav[1] == '':
                type = 0
            elif fav[1] > 0:
                type = 1
            else:
                type = 2

            bets = normalize_fraction(fav[0], int(fav[12]))

            pecific_dates = fav[2]
            pecific_date = fav[3]
            if tmp == pecific_date:
                pecific_date = ""
                pecific_dates = ""
            else:
                tmp = pecific_date

            if "user_id" not in request.GET:
                user_id = self.request.user.id
            else:
                user_id = self.request.GET.get("user_id")
            RecordMark.objects.update_record_mark(user_id, 5, 0)

            data.append({
                'earn_coin': earn_coin,  # 获得金额
                'type': type,  # 下注金额
                'pecific_dates': pecific_dates,
                'pecific_date': pecific_date,
                'pecific_time': fav[4],
                'my_option': my_option,  # 投注选项
                'coin_avatar': fav[13],  # 货币图标
                'number_tab_number': fav[8],  # 编号
                'right_pair': fav[11],  # 编号
                'coin_name': fav[14],  # 货币昵称
                'bet': bets,  # 下注金额
                'right_option': fav[6]  #
            })

        return self.response({'code': 0, 'data': data})