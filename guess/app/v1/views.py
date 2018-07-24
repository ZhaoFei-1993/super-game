# -*- coding: UTF-8 -*-
from django.db import transaction
from base.app import ListAPIView, ListCreateAPIView
from base.function import LoginRequired
from .serializers import StockListSerialize, GuessPushSerializer
from ...models import Stock, Record, Play, BetLimit, Options, Periods
from chat.models import Club
from base import code as error_code
from base.exceptions import ParamErrorException
from users.models import UserCoin, CoinDetail, Coin
from utils.functions import value_judge
from utils.functions import normalize_fraction
from decimal import Decimal
from datetime import datetime
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
                "result_list": list["result_list"]
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
        plays = Play.objects.filter(stock_id=stock_id).order_by('play_name')  # 所有玩法

        clubinfo = Club.objects.get(pk=int(club_id))
        coin_id = clubinfo.coin.pk  # 俱乐部coin_id
        user_coin = UserCoin.objects.get(user_id=user.id, coin_id=coin_id)
        balance = normalize_fraction(user_coin.balance, int(user_coin.coin.coin_accuracy))  # 用户余额

        data = []
        for play in plays:
            user_number = Record.objects.filter(user_id=user.pk, club_id=club_id, periods_id=periods_id).count()
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
            options_list = Options.objects.filter(play_id=play.pk)
            for options in options_list:
                options_number = Record.objects.filter(user_id=user.pk, club_id=club_id, periods_id=periods_id,
                                                       options_id=options.pk).count()
                if options_number == 0:
                    support_number = 0
                else:
                    support_number = int(options_number)/int(user_number)    # 支持人数

                odds = options.odds  # 赔率

                title = options.title  # 选项标题
                if self.request.GET.get('language') == 'en':
                    title = options.title_en

                sub_title = options.sub_title  # 选项子标题
                if self.request.GET.get('language') == 'en':
                    sub_title = options.sub_title_en
                list.append({
                    "option_id": options.pk,
                    "title": title,
                    "sub_title": sub_title,
                    "odds": odds,
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

        return self.response({'code': 0,
                              'data': data,
                              'balance': balance
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

        if int(option_odds.play.pk) != int(play_id):
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
        nowtime = datetime.now()
        begin_at = periods.rotary_header_time.astimezone(pytz.timezone(settings.TIME_ZONE))
        begin_at = time.mktime(begin_at.timetuple())
        start = int(begin_at)-600
        if nowtime >= start:    # 是否已封盘
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
            Sum('bet'))
        if coin_id == Coin.HAND:
            if bet_sum['bet__sum'] is not None and bet_sum['bet__sum'] >= 5000000:
                raise ParamErrorException(error_code.API_50109_BET_LIMITED)
        elif coin_id == Coin.INT:
            if bet_sum['bet__sum'] is not None and bet_sum['bet__sum'] >= 20000:
                raise ParamErrorException(error_code.API_50109_BET_LIMITED)
        elif coin_id == Coin.ETH:
            if bet_sum['bet__sum'] is not None and bet_sum['bet__sum'] >= 6:
                raise ParamErrorException(error_code.API_50109_BET_LIMITED)
        elif coin_id == Coin.BTC:
            if bet_sum['bet__sum'] is not None and bet_sum['bet__sum'] >= 0.5:
                raise ParamErrorException(error_code.API_50109_BET_LIMITED)
        elif coin_id == Coin.USDT:
            if bet_sum['bet__sum'] is not None and bet_sum['bet__sum'] >= 3100:
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
        record.source = request.META.get('HTTP_X_API_KEY')
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