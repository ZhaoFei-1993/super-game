# -*- coding: UTF-8 -*-
from django.db import transaction
from base.app import ListAPIView, ListCreateAPIView
from base.function import LoginRequired
from .serializers import StockListSerialize, GuessPushSerializer, RecordSerialize, GraphSerialize, GraphDaySerialize, \
    PeriodsListSerialize
from ...models import Stock, Record, Play, BetLimit, Options, Periods, Index, Index_day
from chat.models import Club
from base import code as error_code
from base.exceptions import ParamErrorException
from users.models import UserCoin, CoinDetail, Coin
from utils.functions import value_judge, guess_is_seal, language_switch, get_sql
from utils.functions import normalize_fraction
from decimal import Decimal
from datetime import datetime, timedelta
from utils.functions import value_judge, get_sql, get_club_info, to_decimal
from django.db.models import Q, Sum
import time
from api import settings
import pytz
from api.settings import MEDIA_DOMAIN_HOST
from promotion.models import PromotionRecord
from utils.cache import get_cache, set_cache


class StockList(ListAPIView):
    """
    股票列表
    """
    permission_classes = (LoginRequired,)
    serializer_class = StockListSerialize

    last_periods_list = []
    previous_periods_list = []
    stock_info = {}

    def get_queryset(self):
        for stock in Stock.objects.filter(stock_guess_open=True):

            title = Stock.STOCK[int(stock.name)][1]
            if self.request.GET.get('language') == 'en':
                title = Stock.STOCK_EN[int(stock.name)][1]
            self.stock_info.update({
                stock.pk: {
                    'title': title, 'icon': stock.icon
                }
            })

        pre_period = []
        # 取当前期
        for period in Periods.objects.filter(is_result=False, stock_id__in=self.stock_info.keys()):
            self.last_periods_list.append(period)
            if period.periods - 1 != 0:
                pre_period.append({period.stock_id: period.periods - 1})
        print('pre_period =========== ', pre_period)
        # 取上期
        for pre_period in Periods.objects.filter(
                Q(Q(stock_id=list(pre_period[0].keys())[0]) & Q(periods=list(pre_period[0].values())[0])) | Q(
                    Q(stock_id=list(pre_period[1].keys())[0]) & Q(periods=list(pre_period[1].values())[0])) | Q(
                    Q(stock_id=list(pre_period[2].keys())[0]) & Q(periods=list(pre_period[2].values())[0])) | Q(
                    Q(stock_id=list(pre_period[3].keys())[0]) & Q(periods=list(pre_period[3].values())[0]))):
            self.previous_periods_list.append(pre_period)

        return Periods.objects.filter(is_result=False, stock_id__in=self.stock_info.keys())

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        data = []

        previous_periods_dt = {}
        for previous_period in self.previous_periods_list:
            previous_result = previous_period.lottery_value  # 上期开奖指数

            if previous_period.periods - 1 == 0 or previous_period.periods == '':  # 上期开奖answer
                answer = ''
                previous_result_color = 3
            else:
                up_and_down = previous_period.up_and_down
                size = previous_period.size
                points = previous_period.points
                pair = previous_period.pair
                if pair is None or pair == '':
                    answer = str(size) + "、  " + str(points)
                else:
                    answer = str(size) + "、  " + str(points) + "、  " + str(pair)

                if up_and_down == '涨':  # 上期开奖指数颜色
                    previous_result_color = 1
                elif up_and_down == '跌':
                    previous_result_color = 2
                else:
                    previous_result_color = 3

            previous_periods_dt.update(
                {
                    previous_period.stock_id: {
                        'previous_result': previous_result,
                        'answer': answer,
                        'previous_result_color': previous_result_color,
                    }
                })
        # 缺少上期情况
        if len(previous_periods_dt.keys()) < len(self.stock_info.keys()):
            for stock_id in self.stock_info.keys():
                if stock_id not in previous_periods_dt.keys():
                    previous_periods_dt.update(
                        {
                            stock_id: {
                                'previous_result': '',
                                'answer': '',
                                'previous_result_colour': 3,
                            }
                        })
        # 本期指数颜色
        index_info = {}
        sql = 'SELECT periods_id,stock_id,index_value,start_value,index_time FROM guess_index a '
        sql += 'LEFT JOIN guess_periods ON a.periods_id = guess_periods.id WHERE a.id IN'
        sql += '(SELECT MAX(a.id) FROM guess_index a ' \
               'WHERE periods_id IN({periods_id}) ' \
               'GROUP BY periods_id)'.format(periods_id=','.join([str(obj.id) for obj in self.get_queryset()]))
        for dt in get_sql(sql):
            index_info.update({
                dt[1]: {
                    'start_value': dt[3], 'index_value': dt[2], 'periods_id': dt[0],
                }
            })
        for stock_id in self.stock_info.keys():
            if stock_id not in index_info.keys():
                index_info.update({
                    stock_id: {
                        'start_value': None, 'index_value': None, 'periods_id': None,
                    }
                })
        index_dic = {}
        for period in self.last_periods_list:
            start_value = index_info[period.stock_id]['start_value']
            index_value = index_info[period.stock_id]['index_value']
            if index_value is None or start_value is None:
                index_status = "竞猜中"
                index_color = 4
            else:
                if index_value > start_value:
                    index_color = 1
                elif index_value < start_value:
                    index_color = 2
                else:
                    index_color = 3
                index_status = index_value
            index_dic.update({
                period.stock_id: {
                    'index_color': index_color, 'index_status': index_status,
                }
            })

        # 股票封盘时间
        closing_time_dic = {}
        periods_id_dic = {}
        for item in items:
            closing_time_dic.update(item['closing_time'])
            periods_id_dic.update(item['periods_id'])
        # 返回值
        for stock_id in self.stock_info.keys():
            data.append({
                "stock_id": stock_id,
                "periods_id": periods_id_dic[stock_id]["period_id"],
                "icon": self.stock_info[stock_id]['icon'],
                "title": self.stock_info[stock_id]['title'],
                "closing_time": closing_time_dic[stock_id]['start'],
                "lottery_time": closing_time_dic[stock_id]["start_at"],
                "status": closing_time_dic[stock_id]["status"],
                "previous_result": previous_periods_dt[stock_id]['previous_result'],
                "previous_result_colour": previous_periods_dt[stock_id]['previous_result_color'],
                "index": index_dic[stock_id]['index_status'],
                "index_colour": index_dic[stock_id]['index_color'],
                "rise": periods_id_dic[stock_id]["rise"],
                "fall": periods_id_dic[stock_id]["fall"],
                "is_seal": periods_id_dic[stock_id]["is_seal"],
                "result_list": previous_periods_dt[stock_id]['answer']
            })
        return self.response({'code': 0, 'data': data})


class PeriodsList(ListAPIView):
    """
    期数列表
    """
    permission_classes = (LoginRequired,)
    serializer_class = PeriodsListSerialize

    def get_queryset(self):
        stock_id = self.request.GET.get('stock_id')
        periods_list = Periods.objects.filter(stock_id=stock_id).order_by('-lottery_time')[:15]
        return periods_list

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        data = []
        for list in items:
            data.append({
                "date": list["date"],
                "index_value": list["index_value"],
                "is_result": list["is_result"],
            })

        return self.response({'code': 0, 'data': data})


class GuessPushView(ListAPIView):
    """
    详情页面推送
    """
    permission_classes = (LoginRequired,)
    serializer_class = GuessPushSerializer

    def get_queryset(self):
        club_id = self.request.GET.get('club_id')
        periods_id = self.request.GET.get('periods_id')
        record = Record.objects.filter(club_id=club_id, periods_id=periods_id)
        return record

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        data = []
        for item in items:
            data.append(
                {
                    "record_id": item['pk'],
                    "username": item['username'],
                    "my_play": item['my_play'],
                    "my_option": item['my_option'],
                    "bet": item['bet']
                }
            )
        return self.response({"code": 0, "data": data})


class PlayView(ListAPIView):
    """
    股票选项
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        user = request.user
        club_id = int(self.request.GET.get('club_id'))  # 俱乐部表ID
        periods_id = int(self.request.GET.get('periods_id'))  # 周期表ID
        stock_id = int(self.request.GET.get('stock_id'))  # 股票配置表ID
        try:
            periods = Periods.objects.get(pk=periods_id)  # 判断比赛
        except Exception:
            raise ParamErrorException(error_code.API_40105_SMS_WAGER_PARAMETER)
        begin_at = periods.rotary_header_time.astimezone(pytz.timezone(settings.TIME_ZONE))
        begin_at = time.mktime(begin_at.timetuple())
        rotary_header_time = int(begin_at)
        created_at = periods.lottery_time.astimezone(pytz.timezone(settings.TIME_ZONE))
        created_at = time.mktime(created_at.timetuple())
        lottery_time = int(created_at)
        is_seal = guess_is_seal(periods)  # 是否达到封盘时间，如达到则修改is_seal字段并且返回

        plays = Play.objects.filter(~Q(play_name=0), stock_id=stock_id).order_by('play_name')  # 所有玩法

        plays_id_list = [play.id for play in plays]  # 所有玩法id

        # 获取 betlimit
        betlimit_dic = {}  # {play_id: betlimit obj}
        for betlimit in BetLimit.objects.filter(club_id=club_id, play_id__in=plays_id_list):
            betlimit_dic.update({betlimit.play_id: betlimit})
        # print(betlimit_dic)

        # 获取各个玩法下所有的选项对象
        options_dic = {}  # {play_id: [option obj]}
        options = Options.objects.filter(play_id__in=plays_id_list)
        for option in options:
            options_dic.update({option.play_id: []})
        for option in options:
            options_dic[option.play_id].append(option)
        # print(options_dic)

        # 获取用户在此期投注的选项
        option_id_list = []  # 所有玩法所有选项的id
        for key, value in options_dic.items():
            for option in value:
                option_id_list.append(option.id)
        user_options_list = Record.objects.filter(user_id=user.pk, club_id=club_id, periods_id=periods_id,
                                                  options_id__in=option_id_list).values_list('options_id', flat=True)

        cache_club_value = get_club_info()
        coin_id = cache_club_value[club_id]['coin_id']  # 俱乐部coin_id
        user_coin = UserCoin.objects.get(user_id=user.id, coin_id=coin_id)
        coin_icon = cache_club_value[club_id]['coin_icon']
        coin_name = cache_club_value[club_id]['coin_name']
        coin_accuracy = cache_club_value[club_id]['coin_accuracy']
        balance = normalize_fraction(user_coin.balance, int(user_coin.coin.coin_accuracy))  # 用户余额

        # 看大，看小，人数支持率
        key_record_bet_count = 'record_stock_bet_count' + '_' + str(periods.id)
        record_stock_bet_count = get_cache(key_record_bet_count)
        bet_sum = record_stock_bet_count['rise'] + record_stock_bet_count['fall']
        support_rise = 0
        support_fall = 0
        if bet_sum != 0:
            support_rise = round(record_stock_bet_count['rise'] / bet_sum * 100, 2)
            support_fall = to_decimal(100) - to_decimal(support_rise)

        data = []
        for play in plays:
            # betlimit = BetLimit.objects.get(club_id=club_id, play_id=play.pk)
            betlimit = betlimit_dic[play.pk]

            play_name = Play.PLAY[int(play.play_name)][1]  # 玩法名字
            if self.request.GET.get('language') == 'en':
                play_name = Play.PLAY_EN[int(play.play_name_en)][1]

            tips = play.tips  # 提示短语
            if self.request.GET.get('language') == 'en':
                tips = play.tips_en

            bets_one = betlimit.bets_one  # 下注值1
            bets_two = betlimit.bets_two  # 下注值2
            bets_three = betlimit.bets_three  # 下注值3
            bets_min = betlimit.bets_min  # 最小下注值
            bets_max = betlimit.bets_max  # 最大下注值

            list = []
            # options_list = Options.objects.filter(play_id=play.pk).order_by("order")

            options_list = options_dic[play.pk]
            for options in reversed(options_list):
                # is_record = Record.objects.filter(user_id=user.pk, club_id=club_id, periods_id=periods_id,
                #                                   options_id=options.pk).count()

                is_choice = 0
                if options.pk in user_options_list:
                    is_choice = 1
                # if int(is_record) > 0:
                #     is_choice = 1

                up_and_down = periods.up_and_down
                if self.request.GET.get('language') == 'en':
                    up_and_down = periods.up_and_down_en
                size = periods.size
                if self.request.GET.get('language') == 'en':
                    size = periods.size_en
                points_one = ''
                points_two = ''
                if periods.points != '':
                    points_one = periods.points[0]
                    points_two = periods.points[1]
                pair = periods.pair
                right_list = [up_and_down, size, pair, points_one, points_two]

                title = options.title  # 选项标题
                if self.request.GET.get('language') == 'en':
                    title = options.title_en

                is_right = 0
                if title in right_list:
                    is_right = 1

                if options.title == '大':
                    support_number = support_rise  # 看大支持率
                elif options.title == '小':
                    support_number = support_fall  # 看小支持率
                else:
                    support_number = 0

                odds = options.odds  # 赔率

                sub_title = options.sub_title  # 选项子标题
                if self.request.GET.get('language') == 'en':
                    sub_title = options.sub_title_en

                if int(play.play_name) == 0:
                    club = Club.objects.get(pk=club_id)
                    sql = "select sum(a.bets) from guess_record a"
                    sql += " where a.club_id = '" + str(club_id) + "'"
                    sql += " and a.periods_id = '" + str(periods_id) + "'"
                    sql += " and a.options_id = '" + str(options.pk) + "'"
                    total_coin = get_sql(sql)[0][0]  # 投注金额
                    if total_coin == None or total_coin == '':
                        total_coin = 0
                    else:
                        total_coin = normalize_fraction(str(total_coin), int(club.coin.coin_accuracy))
                    list.append({
                        "option_id": options.pk,
                        "title": title,
                        "sub_title": sub_title,
                        "total_coin": total_coin,
                        "odds": odds,
                        "is_choice": is_choice,
                        "is_right": is_right,
                        "support_number": support_number
                    })
                else:
                    list.append({
                        "option_id": options.pk,
                        "title": title,
                        "sub_title": sub_title,
                        "odds": odds,
                        "is_choice": is_choice,
                        "is_right": is_right,
                        "support_number": support_number
                    })
            if int(play.play_name) == 0:
                coin_number = list[0]['total_coin'] + list[1]['total_coin']
                tips = "猜涨跌当前总奖池 " + str(coin_number) + " " + str(coin_name) + ','
            data.append({
                "play_id": play.pk,
                "play_name": play_name,
                "tips": tips,
                'bets_one': bets_one,
                'bets_two': bets_two,
                'bets_three': bets_three,
                'bets_min': normalize_fraction(str(bets_min), coin_accuracy),
                'bets_max': normalize_fraction(str(bets_max), coin_accuracy),
                "list": list
            })
        coin_list = {'balance': balance,
                     'coin_name': coin_name,
                     'coin_icon': coin_icon
                     }
        return self.response({'code': 0,
                              'data': data,
                              'rotary_header_time': rotary_header_time,
                              'lottery_time': lottery_time,
                              'coin_list': coin_list,
                              'is_seal': is_seal
                              })


class BetView(ListCreateAPIView):
    """
    股票下注
    """

    def get_queryset(self):
        pass

    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        value = value_judge(request, "periods_id", "option_id", "play_id", "bet", "club_id")
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        user = request.user
        periods_id = self.request.data['periods_id']  # 获取周期ID
        club_id = self.request.data['club_id']  # 获取俱乐部ID
        play_id = self.request.data['play_id']  # 获取俱乐部ID
        option = self.request.data['option_id']  # 获取选项ID
        coins = self.request.data['bet']  # 获取投注金额
        coins = Decimal(coins)

        periods_info = Periods.objects.get(pk=periods_id)
        clubinfo = Club.objects.get_one(pk=int(club_id))
        coin_info = Coin.objects.get_one(pk=int(clubinfo.coin.pk))
        coin_id = coin_info.pk
        coin_accuracy = coin_info.coin_accuracy

        try:  # 判断选项ID是否有效
            option_odds = Options.objects.get(pk=option)
        except Exception:
            raise ParamErrorException(error_code.API_50101_QUIZ_OPTION_ID_INVALID)

        if int(option_odds.play_id) != int(play_id):
            raise ParamErrorException(error_code.API_50101_QUIZ_OPTION_ID_INVALID)
        i = 0
        Decimal(i)
        # 判断赌注是否有效
        if i >= Decimal(coins):
            raise ParamErrorException(error_code.API_50102_WAGER_INVALID)
        try:
            periods = Periods.objects.get(pk=periods_id)  # 判断比赛
        except Exception:
            raise ParamErrorException(error_code.API_40105_SMS_WAGER_PARAMETER)
        is_seal = guess_is_seal(periods)  # 是否达到封盘时间，如达到则修改is_seal字段并且返回
        if is_seal is True:
            raise ParamErrorException(error_code.API_80101_STOP_BETTING)

        nowtime = datetime.now()
        if nowtime > periods_info.rotary_header_time:
            raise ParamErrorException(error_code.API_80101_STOP_BETTING)

        try:
            bet_limit = BetLimit.objects.get(club_id=club_id, play_id=play_id)
        except Exception:
            raise ParamErrorException(error_code.API_40105_SMS_WAGER_PARAMETER)

        coin_betting_control = Decimal(bet_limit.bets_min)
        coin_betting_toplimit = Decimal(bet_limit.bets_max)
        if coin_betting_control > coins or coin_betting_toplimit < coins:
            raise ParamErrorException(error_code.API_50102_WAGER_INVALID)

        # 单场比赛最大下注
        bet_sum = Record.objects.filter(user_id=user.id, club_id=club_id, periods_id=periods_id).aggregate(
            Sum('bets'))

        bet_sum = bet_sum['bets__sum'] if bet_sum['bets__sum'] else 0
        bet_sum = Decimal(bet_sum) + Decimal(coins)

        betting_toplimit = coin_info.betting_toplimit
        if Decimal(bet_sum) > betting_toplimit:
            raise ParamErrorException(error_code.API_50109_BET_LIMITED)

        usercoin = UserCoin.objects.get(user_id=user.id, coin_id=coin_id)
        # 判断用户金币是否足够
        if Decimal(usercoin.balance) < coins:
            raise ParamErrorException(error_code.API_50104_USER_COIN_NOT_METH)
        play_info = option_odds.play

        coins = normalize_fraction(coins, coin_accuracy)  # 总下注额
        record = Record()
        record.user = user
        record.periods = periods_info
        record.club = clubinfo
        record.play = play_info
        record.options = option_odds
        record.bets = coins
        record.odds = option_odds.odds
        source = request.META.get('HTTP_X_API_KEY')
        if source == "ios":
            source = 1
        elif source == "android":
            source = 2
        else:
            source = 3
        if user.is_robot is True:
            source = 4
        record.source = source
        record.save()

        # 猜大小人数统计到缓存中
        key_record_bet_count = 'record_stock_bet_count' + '_' + str(periods.id)
        record_stock_bet_count = get_cache(key_record_bet_count)
        if option_odds.id in [1, 2, 3, 4]:
                record_stock_bet_count['rise'] += 1
                set_cache(key_record_bet_count, record_stock_bet_count)
        if option_odds.id in [5, 6, 7, 8]:
                record_stock_bet_count['fall'] += 1
                set_cache(key_record_bet_count, record_stock_bet_count)

        earn_coins = coins * option_odds.odds
        earn_coins = normalize_fraction(earn_coins, coin_accuracy)
        # 用户减少金币
        balance = normalize_fraction(usercoin.balance, coin_accuracy)
        usercoin.balance = balance - coins
        usercoin.save()

        coin_detail = CoinDetail()
        coin_detail.user = user
        coin_detail.coin_name = coin_info.name
        coin_detail.amount = '-' + str(coins)
        coin_detail.rest = usercoin.balance
        coin_detail.sources = CoinDetail.BETS
        coin_detail.save()

        if int(club_id) == 1 or int(user.is_robot) == 1:
            pass
        else:
            PromotionRecord.objects.insert_record(user, clubinfo, record.id, Decimal(coins), 4, record.created_at)
        response = {
            'code': 0,
            'data': {
                'message': '下注成功，金额总数为 ' + str(
                    normalize_fraction(coins, int(coin_accuracy))) + '，预计可得猜币 ' + str(
                    normalize_fraction(earn_coins, int(coin_accuracy))),
                'balance': normalize_fraction(usercoin.balance, int(coin_accuracy))
            }
        }
        return self.response(response)


class RecordsListView(ListCreateAPIView):
    """
    竞猜记录
    """
    permission_classes = (LoginRequired,)
    serializer_class = RecordSerialize

    def get_queryset(self):
        club_id = int(self.request.GET.get('club_id'))  # 俱乐部表ID
        if 'user_id' not in self.request.GET:
            user_id = self.request.user.id
            if 'is_end' not in self.request.GET:
                record = Record.objects.filter(user_id=user_id, club_id=club_id).order_by('-created_at')
                return record
            else:
                is_end = self.request.GET.get('is_end')
                if int(is_end) == 1:
                    return Record.objects.filter(
                        status=0,
                        user_id=user_id,
                        club_id=club_id).order_by('-created_at')
                else:
                    return Record.objects.filter(status=1,
                                                 user_id=user_id,
                                                 club_id=club_id).order_by('-created_at')
        else:
            user_id = self.request.GET.get('user_id')
            return Record.objects.filter(user_id=user_id, club_id=club_id).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        # 完成数据库查询构造
        stock_obj_info = {}
        for stock in Stock.objects.all():
            stock_obj_info.update({
                stock.id: {
                    'name': stock.name, 'name_en': stock.name_en
                }
            })

        plays_dic = {}
        options_dic = {}
        for play in Play.objects.all():
            plays_dic.update({
                play.id:
                    {
                        'play_name': play.play_name,
                    }
            })
        for option in Options.objects.all():
            options_dic.update({
                option.id:
                    {
                        'title': option.title, 'title_en': option.title_en,
                    }
            })

        records_obj_dic = {}
        for record in self.get_queryset():
            records_obj_dic.update({
                record: {
                    'id': record.id, 'play_id': record.play_id, 'options_id': record.options_id,
                }
            })

        records_periods_id_list = self.get_queryset().values_list('periods_id', flat=True)
        period_obj_dic = {}
        for period in Periods.objects.filter(id__in=records_periods_id_list):
            if period.id not in period_obj_dic.keys():
                period_obj_dic.update({
                    period.id:
                        {'stock_id': period.stock_id, 'lottery_value': period.lottery_value,
                         'start_value': period.start_value, 'up_and_down': period.up_and_down,
                         'up_and_down_en': period.up_and_down_en, 'size': period.size,
                         'size_en': period.size_en, 'points': period.points, 'pair': period.pair
                         }
                })

        results = super().list(request, *args, **kwargs)
        Progress = results.data.get('results')
        data = []
        tmp = ''
        for fav in Progress:
            obj = fav.get('obj')
            # 构造接口数据
            record_id = fav.get('id')
            print('record_id=======', record_id)
            periods_id = fav.get('periods_id')
            stock_id = period_obj_dic[periods_id]['stock_id']
            index = period_obj_dic[periods_id]['lottery_value']
            start_value = period_obj_dic[periods_id]['start_value']
            earn_coin = fav.get('earn_coin')
            earn_coin_result = fav.get('earn_coin_result')

            # 股票昵称
            stock_name = stock_obj_info[stock_id]['name']
            stock_name_en = stock_obj_info[stock_id]['name_en']
            guess_title = Stock.STOCK[int(stock_name)][1]
            if self.request.GET.get('language') == 'en':
                guess_title = Stock.STOCK_EN[int(stock_name_en)][1]

            # 本期指数颜色
            index_colour = ''
            if earn_coin > 0 or earn_coin < 0:
                if index > start_value:
                    index_colour = 1
                elif index < start_value:
                    index_colour = 2
                else:
                    index_colour = 3

            # 开奖结果
            up_and_down = period_obj_dic[periods_id]['up_and_down']
            size = period_obj_dic[periods_id]['size']
            if self.request.GET.get('language') == 'en':
                up_and_down = period_obj_dic[periods_id]['up_and_down_en']
                size = period_obj_dic[periods_id]['size_en']
            points = period_obj_dic[periods_id]['points']
            pair = period_obj_dic[periods_id]['pair']
            if up_and_down is None or up_and_down == '':
                guess_result = ''
            elif pair is None or pair == '':
                guess_result = str(size) + "、 " + str(points)
            else:
                guess_result = str(size) + "、 " + str(points) + "、 " + str(pair)

            # 我的玩法选项
            play_id = records_obj_dic[obj]['play_id']
            option_id = records_obj_dic[obj]['options_id']
            play_name = Play.PLAY[int(plays_dic[play_id]['play_name'])][1]
            option_title = options_dic[option_id]['title']
            title = str(play_name) + "：" + str(option_title)
            if self.request.GET.get('language') == 'en':
                play_name = Play.PLAY_EN[int(plays_dic[play_id]['play_name'])][1]
                option_title = options_dic[option_id]['title_en']
                title = str(play_name) + "：" + str(option_title)

            pecific_dates = fav.get('created_at')[0].get('years')
            pecific_date = fav.get('created_at')[0].get('year')
            if tmp == pecific_date:
                pecific_date = ""
                pecific_dates = ""
            else:
                tmp = pecific_date
            data.append({
                "id": fav.get('id'),
                "stock_id": stock_id,
                "periods_id": periods_id,
                "guess_title": guess_title,  # 股票昵称
                'earn_coin': earn_coin_result,  # 竞猜结果
                'type': fav.get('type'),  # 竞猜结果
                'pecific_dates': pecific_dates,
                'pecific_date': pecific_date,
                'pecific_time': fav.get('created_at')[0].get('time'),
                'my_option': title,  # 投注选项
                'is_right': fav.get('is_right'),  # 是否为正确答案
                'coin_avatar': fav.get('coin_avatar'),  # 货币图标
                'index': index,  # 指数
                'index_colour': index_colour,  # 指数颜色
                'guess_result': guess_result,  # 当期结果
                'coin_name': fav.get('coin_name'),  # 货币昵称
                'bet': fav.get('bet')  # 下注金额
            })
        return self.response({'code': 0, 'data': data})


class StockGraphListView(ListCreateAPIView):
    """
    曲线图(时)
    """
    permission_classes = (LoginRequired,)
    serializer_class = GraphSerialize

    def get_queryset(self):
        periods_id = int(self.request.GET.get('periods_id'))  # 期数ID
        index_number = Index.objects.filter(periods_id=periods_id).count()
        if index_number == 0:
            periods_info = Periods.objects.get(id=periods_id)
            periods_periods = periods_info.periods - 1
            old_periods_info = Periods.objects.get(periods=periods_periods, stock_id=periods_info.stock_id)
            info = Index.objects.filter(periods_id=old_periods_info.pk).order_by("index_time")
        else:
            info = Index.objects.filter(periods_id=periods_id).order_by("index_time")
        return info

    def list(self, request, *args, **kwargs):
        periods_id = int(self.request.GET.get('periods_id'))  # 期数ID
        periods_info = Periods.objects.get(pk=periods_id)
        day = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        lottery_time = periods_info.lottery_time.strftime('%Y-%m-%d %H:%M:%S')  # 开奖时间
        start_time = periods_info.start_time.strftime('%Y-%m-%d %H:%M:%S')  # 开始下注时间
        rotary_header_time = periods_info.rotary_header_time.strftime('%Y-%m-%d %H:%M:%S')  # 封盘时间
        status = -1
        if start_time < day < rotary_header_time:
            status = 0  # 开始投注
        elif periods_info.is_seal is True and periods_info.is_result is not True and datetime.now() < periods_info.lottery_time:
            status = 1  # 封盘中
        elif datetime.now() > periods_info.lottery_time and periods_info.is_result is not True:
            status = 2  # 结算中
        elif periods_info.is_result is True:
            status = 3  # 已开奖
        # index_number = Index.objects.filter(periods_id=periods_id).count()
        # periods_info = Periods.objects.get(id=periods_id)
        periods_periods = periods_info.periods - 1
        periods_info_old = Periods.objects.get(periods=periods_periods, stock_id=periods_info.stock_id)

        new_start_value = periods_info_old.lottery_value
        index_info = Index.objects.filter(periods_id=periods_id).first()
        if index_info == None or index_info == '':
            new_index = 0
            index_colour = 3
            amplitude = "0.00%"
        else:
            new_index = index_info.index_value
            if new_index > new_start_value:
                index_colour = 1
                old_amplitude = (new_index - new_start_value) / new_start_value
                new_amplitude = normalize_fraction(old_amplitude, 4)
                amplitude = "+" + str(new_amplitude * 100) + "%"
            elif new_index < new_start_value:
                index_colour = 2  # 股票颜色
                old_amplitude = (new_start_value - new_index) / new_start_value
                new_amplitude = normalize_fraction(old_amplitude, 4)
                amplitude = "-" + str(new_amplitude * 100) + "%"  # 幅度
            else:
                index_colour = 3
                amplitude = "0.00%"

        results = super().list(request, *args, **kwargs)
        Progress = results.data.get('results')
        index_value_list = []
        index_time_list = []
        i = 0
        for fav in Progress:
            index_value = float(fav.get('index_value'))
            index_value = float(index_value)
            if index_value > i:
                i = index_value
            index_value_list.append(fav.get('index_value'))
            index_time_list.append(fav.get('time'))
        len_number = len(str(i))
        if len_number == 8:
            max_index_value = i + 10000
            min_index_value = i - 10000
        elif len_number == 7:
            max_index_value = i + 1000
            min_index_value = i - 1000
        elif len_number == 9:
            max_index_value = i + 100000
            min_index_value = i - 100000
        else:
            max_index_value = i + 100
            min_index_value = i - 100

        return self.response({'code': 0, 'index_value_list': index_value_list, 'index_time_list': index_time_list,
                              'new_index': new_index, 'amplitude': amplitude, 'index_colour': index_colour,
                              'max_index_value': int(max_index_value), 'min_index_value': int(min_index_value),
                              "new_start_value": new_start_value, 'status': status})


class StockGraphDayListView(ListCreateAPIView):
    """
    曲线图(日)
    """
    permission_classes = (LoginRequired,)
    serializer_class = GraphDaySerialize

    def get_queryset(self):
        stock_id = int(self.request.GET.get('stock_id'))  # 期数ID
        old_datetime = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        starting_time = str(old_datetime) + ' 00:00:00'  # 结束时间
        info = Index_day.objects.filter(stock_id=stock_id, created_at__gte=starting_time).order_by("index_time")
        return info

    def list(self, request, *args, **kwargs):
        periods_id = int(self.request.GET.get('periods_id'))  # 期数ID
        periods_info = Periods.objects.get(pk=periods_id)
        day = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        lottery_time = periods_info.lottery_time.strftime('%Y-%m-%d %H:%M:%S')  # 开奖时间
        start_time = periods_info.start_time.strftime('%Y-%m-%d %H:%M:%S')  # 开始下注时间
        rotary_header_time = periods_info.rotary_header_time.strftime('%Y-%m-%d %H:%M:%S')  # 封盘时间
        status = -1
        if start_time < day < rotary_header_time:
            status = 0  # 开始投注
        elif periods_info.is_seal is True and periods_info.is_result is not True and datetime.now() < periods_info.lottery_time:
            status = 1  # 封盘中
        elif datetime.now() > periods_info.lottery_time and periods_info.is_result is not True:
            status = 2  # 结算中
        elif periods_info.is_result is True:
            status = 3  # 已开奖
        # periods_info = Periods.objects.get(id=periods_id)
        periods_periods = periods_info.periods - 1
        periods_info_old = Periods.objects.get(periods=periods_periods, stock_id=periods_info.stock_id)
        new_start_value = periods_info_old.lottery_value
        index_info = Index.objects.filter(periods_id=periods_id).first()
        if index_info == None or index_info == '':
            new_index = 0
            index_colour = 3
            amplitude = "0.00%"
        else:
            new_index = index_info.index_value
            if new_index > new_start_value:
                index_colour = 1
                old_amplitude = (new_index - new_start_value) / new_start_value
                new_amplitude = normalize_fraction(old_amplitude, 4)
                amplitude = "+" + str(new_amplitude * 100) + "%"
            elif new_index < new_start_value:
                index_colour = 2  # 股票颜色
                old_amplitude = (new_start_value - new_index) / new_start_value
                new_amplitude = normalize_fraction(old_amplitude, 4)
                amplitude = "-" + str(new_amplitude * 100) + "%"  # 幅度
            else:
                index_colour = 3
                amplitude = "0.00%"

        results = super().list(request, *args, **kwargs)
        Progress = results.data.get('results')
        index_value_list = []
        index_time_list = []
        i = 0
        for fav in Progress:
            index_value = float(fav.get('index_value'))
            index_value = float(index_value)
            if index_value > i:
                i = index_value
            index_value_list.append(fav.get('index_value'))
            index_time_list.append(fav.get('index_day'))
        len_number = len(str(i))
        if len_number == 8:
            max_index_value = i + 3000
            min_index_value = i - 3000
        elif len_number == 7:
            max_index_value = i + 500
            min_index_value = i - 500
        elif len_number == 9:
            max_index_value = i + 30000
            min_index_value = i - 30000
        else:
            max_index_value = i + 100
            min_index_value = i - 100

        return self.response({'code': 0, 'index_value_list': index_value_list, 'index_time_list': index_time_list,
                              'new_index': new_index, 'amplitude': amplitude, 'index_colour': index_colour,
                              'max_index_value': int(max_index_value), 'min_index_value': int(min_index_value),
                              'status': status})


class PlayRuleImage(ListAPIView):
    """
    玩法规则图
    """
    permission_classes = (LoginRequired,)

    def get(self, request, *args, **kwargs):
        # now_time = datetime.now().strftime('%Y%m%d%H%M')
        # language = self.request.GET.get('language')
        # print("now_time========================", now_time)
        # print("now_time========================", language_switch(language, "GUESS_RULE") + ".jpg?t=%s" % now_time)
        rule_img = '/'.join(
            [MEDIA_DOMAIN_HOST, "smstp_2.png"])
        return self.response(
            {'code': 0, 'data': {'image': rule_img}})
