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
from utils.functions import value_judge, guess_is_seal
from utils.functions import normalize_fraction
from decimal import Decimal
from datetime import datetime, timedelta
import time
from api import settings
import pytz
from django.db.models import Q, Sum


class StockList(ListAPIView):
    """
    股票列表
    """
    permission_classes = (LoginRequired,)
    serializer_class = StockListSerialize

    def get_queryset(self):
        stock_list = Stock.objects.all()
        return stock_list

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        data = []
        for list in items:
            data.append({
                "stock_id": list["pk"],
                "periods_id": list["periods_id"],
                "icon": list["icon"],
                "title": list["title"],
                "closing_time": list["closing_time"],
                "previous_result": list["previous_result"],
                "previous_result_colour": list["previous_result_colour"],
                "index": list["index"],
                "index_colour": list["index_colour"],
                "rise": list["rise"],
                "fall": list["fall"],
                "is_seal": list["is_seal"],
                "result_list": list["result_list"]
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
        is_seal = guess_is_seal(periods)  # 是否达到封盘时间，如达到则修改is_seal字段并且返回

        plays = Play.objects.filter(stock_id=stock_id).order_by('play_name')  # 所有玩法

        clubinfo = Club.objects.get(pk=int(club_id))
        coin_id = clubinfo.coin.pk  # 俱乐部coin_id
        user_coin = UserCoin.objects.get(user_id=user.id, coin_id=coin_id)
        coin_icon = user_coin.coin.icon
        coin_name = user_coin.coin.name
        balance = normalize_fraction(user_coin.balance, int(user_coin.coin.coin_accuracy))  # 用户余额

        data = []
        for play in plays:
            user_number = Record.objects.filter(club_id=club_id, periods_id=periods_id, play_id=play.id).count()
            betlimit = BetLimit.objects.get(club_id=club_id, play_id=play.pk)

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
            options_list = Options.objects.filter(play_id=play.pk).order_by("order")
            for options in options_list:
                is_record = Record.objects.filter(user_id=user.pk, club_id=club_id, periods_id=periods_id,
                                                  options_id=options.pk).count()
                is_choice = 0
                if int(is_record) > 0:
                    is_choice = 1

                up_and_down = periods.up_and_down
                if self.request.GET.get('language') == 'en':
                    up_and_down = periods.up_and_down_en
                size = periods.size
                if self.request.GET.get('language') == 'en':
                    size = periods.size_en
                points = periods.points.split(',')
                pair = periods.pair
                right_list = [up_and_down, size, pair]

                title = options.title  # 选项标题
                if self.request.GET.get('language') == 'en':
                    title = options.title_en

                is_right = 0
                if title in right_list or title in points:
                    is_right = 1
                options_number = Record.objects.filter(club_id=club_id, periods_id=periods_id,
                                                       options_id=options.pk).count()
                if options_number == 0 or user_number == 0:
                    support_number = 0
                else:
                    support_number = round((int(options_number) / int(user_number)) * 100, 2)  # 支持人数

                odds = options.odds  # 赔率

                sub_title = options.sub_title  # 选项子标题
                if self.request.GET.get('language') == 'en':
                    sub_title = options.sub_title_en
                list.append({
                    "option_id": options.pk,
                    "title": title,
                    "sub_title": sub_title,
                    "odds": odds,
                    "is_choice": is_choice,
                    "is_right": is_right,
                    "support_number": support_number
                })
            data.append({
                "play_id": play.pk,
                "play_name": play_name,
                "tips": tips,
                'bets_one': bets_one,
                'bets_two': bets_two,
                'bets_three': bets_three,
                'bets_min': bets_min,
                'bets_max': bets_max,
                "list": list
            })
        coin_list = {'balance': balance,
                     'coin_name': coin_name,
                     'coin_icon': coin_icon
                     }
        return self.response({'code': 0,
                              'data': data,
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
        coins = float(coins)

        periods_info = Periods.objects.get(pk=periods_id)
        clubinfo = Club.objects.get(pk=club_id)
        coin_id = clubinfo.coin.pk  # 破产赠送hand功能
        coin_accuracy = clubinfo.coin.coin_accuracy  # 破产赠送hand功能

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
        if is_seal == True:
            raise ParamErrorException(error_code.API_80101_STOP_BETTING)

        try:
            bet_limit = BetLimit.objects.get(club_id=club_id, play_id=play_id)
        except Exception:
            raise ParamErrorException(error_code.API_40105_SMS_WAGER_PARAMETER)

        coin_betting_control = float(bet_limit.bets_min)
        coin_betting_toplimit = float(bet_limit.bets_max)
        if coin_betting_control > coins or coin_betting_toplimit < coins:
            raise ParamErrorException(error_code.API_50102_WAGER_INVALID)

        # 单场比赛最大下注
        bet_sum = Record.objects.filter(user_id=user.id, club_id=club_id, periods_id=periods_id).aggregate(
            Sum('bets'))
        bet_sum = float(bet_sum) + float(self.request.data['bet'])
        if coin_id == Coin.HAND:
            if bet_sum['bets__sum'] is not None and bet_sum['bets__sum'] >= 5000000:
                raise ParamErrorException(error_code.API_50109_BET_LIMITED)
        elif coin_id == Coin.INT:
            if bet_sum['bets__sum'] is not None and bet_sum['bets__sum'] >= 20000:
                raise ParamErrorException(error_code.API_50109_BET_LIMITED)
        elif coin_id == Coin.ETH:
            if bet_sum['bets__sum'] is not None and bet_sum['bets__sum'] >= 6:
                raise ParamErrorException(error_code.API_50109_BET_LIMITED)
        elif coin_id == Coin.BTC:
            if bet_sum['bets__sum'] is not None and bet_sum['bets__sum'] >= 0.5:
                raise ParamErrorException(error_code.API_50109_BET_LIMITED)
        elif coin_id == Coin.USDT:
            if bet_sum['bets__sum'] is not None and bet_sum['bets__sum'] >= 3100:
                raise ParamErrorException(error_code.API_50109_BET_LIMITED)

        usercoin = UserCoin.objects.get(user_id=user.id, coin_id=coin_id)
        # 判断用户金币是否足够
        if float(usercoin.balance) < coins:
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
        if user.is_robot == True:
            source = 4
        record.source = source
        record.save()
        earn_coins = coins * option_odds.odds
        earn_coins = normalize_fraction(earn_coins, coin_accuracy)
        # 用户减少金币
        balance = normalize_fraction(usercoin.balance, coin_accuracy)
        usercoin.balance = balance - coins
        usercoin.save()

        coin_detail = CoinDetail()
        coin_detail.user = user
        coin_detail.coin_name = usercoin.coin.name
        coin_detail.amount = '-' + str(coins)
        coin_detail.rest = usercoin.balance
        coin_detail.sources = 13
        coin_detail.save()
        response = {
            'code': 0,
            'data': {
                'message': '下注成功，金额总数为 ' + str(
                    normalize_fraction(coins, int(usercoin.coin.coin_accuracy))) + '，预计可得猜币 ' + str(
                    normalize_fraction(earn_coins, int(usercoin.coin.coin_accuracy))),
                'balance': normalize_fraction(usercoin.balance, int(usercoin.coin.coin_accuracy))
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
        results = super().list(request, *args, **kwargs)
        Progress = results.data.get('results')
        data = []
        tmp = ''
        for fav in Progress:
            pecific_dates = fav.get('created_at')[0].get('years')
            pecific_date = fav.get('created_at')[0].get('year')
            if tmp == pecific_date:
                pecific_date = ""
                pecific_dates = ""
            else:
                tmp = pecific_date
            data.append({
                "id": fav.get('id'),
                "stock_id": fav.get('stock_id'),
                "periods_id": fav.get('periods_id'),
                "guess_title": fav.get('guess_title'),  # 股票昵称
                'earn_coin': fav.get('earn_coin'),  # 竞猜结果
                'type': fav.get('type'),  # 竞猜结果
                'pecific_dates': pecific_dates,
                'pecific_date': pecific_date,
                'pecific_time': fav.get('created_at')[0].get('time'),
                'my_option': fav.get('my_option'),  # 投注选项
                'is_right': fav.get('is_right'),  # 是否为正确答案
                'coin_avatar': fav.get('coin_avatar'),  # 货币图标
                'index': fav.get('index'),  # 指数
                'index_colour': fav.get('index_colour'),  # 指数颜色
                'guess_result': fav.get('guess_result'),  # 当期结果
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
        info = Index.objects.filter(periods_id=periods_id).order_by("index_time")
        return info

    def list(self, request, *args, **kwargs):
        periods_id = int(self.request.GET.get('periods_id'))  # 期数ID
        periods_info = Periods.objects.get(pk=periods_id)
        new_start_value = periods_info.start_value
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
                new_amplitude = normalize_fraction(old_amplitude, 2)
                amplitude = "+" + str(new_amplitude * 100) + "%"
            elif new_index < new_start_value:
                index_colour = 2  # 股票颜色
                old_amplitude = (new_start_value - new_index) / new_start_value
                new_amplitude = normalize_fraction(old_amplitude, 2)
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
                              "new_start_value": new_start_value})


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
        new_start_value = periods_info.start_value
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
                new_amplitude = normalize_fraction(old_amplitude, 2)
                amplitude = "+" + str(new_amplitude * 100) + "%"
            elif new_index < new_start_value:
                index_colour = 2  # 股票颜色
                old_amplitude = (new_start_value - new_index) / new_start_value
                new_amplitude = normalize_fraction(old_amplitude, 2)
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
                              'max_index_value': int(max_index_value), 'min_index_value': int(min_index_value)})
