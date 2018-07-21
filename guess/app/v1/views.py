# -*- coding: UTF-8 -*-
from base.app import ListAPIView
from base.function import LoginRequired
from .serializers import StockListSerialize, GuessPushSerializer
from ...models import Stock, Record, Play, BetLimit, Options, Periods
from chat.models import Club
from users.models import UserCoin
from utils.functions import normalize_fraction


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
                "title": list["title"],
                "periods": list["periods"],
                "closing_time": list["closing_time"],
                "previous_result": list["previous_result"],
                "previous_result_colour": list["previous_result_colour"],
                "index": list["index"],
                "index_colour": list["index_colour"],
                "rise": list["rise"],
                "fall": list["fall"]
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
                    "quiz_id": item['id'],
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
        stock_id = int(self.request.GET.get('stock_id'))  # 周期表ID
        plays = Play.objects.filter(stock_id=stock_id).order_by('type')  # 所有玩法

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

            tips = Play.tips  # 提示短语
            if self.request.GET.get('language') == 'en':
                tips = Play.tips_en

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
                "play_id": play,
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
