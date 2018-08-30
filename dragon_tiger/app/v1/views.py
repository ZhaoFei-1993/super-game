# -*- coding: UTF-8 -*-
from base.app import ListAPIView, ListCreateAPIView
from utils.functions import value_judge, float_to_str
import hashlib
from django.db import transaction
from base import code as error_code
from base.exceptions import ParamErrorException
import time
from utils.functions import value_judge, get_sql
import urllib.request
import urllib.parse
import json
from decimal import Decimal
from dragon_tiger.models import BetLimit
from utils.functions import normalize_fraction
from base.function import LoginRequired
from dragon_tiger.models import BetLimit, Number_tab, Options, Dragontigerrecord
from users.models import Coin, UserCoin, CoinDetail
from chat.models import Club
from utils.cache import get_cache, set_cache


class Encryption(ListAPIView):
    """
    加密
     appid = '58000000'                              # 你的Appid
    appsecret = '92e56d8195a9dd45a9b90aacf82886b1'               # 你的Secret
    menu = 'home'
    game = 0、
    url = 'http://api.wt123.co/service'                         # API请求地址 | 测试阶段地址
    """

    def post(self, request):
        value = value_judge(request, "appsecret", "appid", "menu", "game")
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        appid = request.data.get('appid')  # 你的Appid
        appsecret = request.data.get('appsecret')  # 你的Secret
        menu = request.data.get('menu')  # 你的Appid
        game = request.data.get('game')  # 你的Appid
        array = {}
        arr = {}
        array['appid'] = appid
        array['menu'] = menu
        array['game'] = game
        times = int(time.time())
        m = hashlib.md5()  # 创建md5对象
        hash_str = str(times) + appid + appsecret
        hash_str = hash_str.encode('utf-8')
        m.update(hash_str)
        token = m.hexdigest()
        array['token'] = token
        arr['token'] = token
        list = ""
        for key in array:
            value = array[key]
            list += str(key) + str(value)
        list += appsecret
        list = list.encode('utf-8')
        sign = hashlib.sha1(list)
        sign = sign.hexdigest()
        sign = sign.upper()
        arr['sign'] = sign
        return arr


class Request_post(ListAPIView):
    """
    url = 'http://api.wt123.co/service'                         # API请求地址 | 测试阶段地址
    """

    def post(self, request):
        if 'data' not in request.data:
            raise ParamErrorException(error_code.API_20105_GOOGLE_RECAPTCHA_FAIL)
        data = request.data.get('recaptcha')

        result = request.post('http://api.wt123.co/service', data=data)
        res = json.loads(result.content.decode('utf-8'))
        print("res=============================", res)
        if res is False:
            raise ParamErrorException(error_code.API_20105_GOOGLE_RECAPTCHA_FAIL)


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

        sql = "select uc.coin_accuracy from users_coin uc"
        sql += " where uc.id = '" + str(coin_id) + "'"
        coin_accuracy = int(get_sql(sql)[0][0])  # 获取货币精度

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
        # option_list = get_sql(sql)  # 获取选项

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
                              "user_avatar": user_avatar,
                              "bets_one": betlimit_list[0],
                              "bets_two": betlimit_list[1],
                              "bets_three": betlimit_list[2],
                              "bets_four": betlimit_list[3],
                              "red_limit": betlimit_list[4],
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

        sql = "select sum(dtr.bets) from dragon_tiger_dragontigerrecord dtr"
        sql += " where dtr.option_id = '" + str(option_id_one) + "'"
        sql += " or dtr.option_id = '" + str(option_id_two) + "'"
        coin_number = get_sql(sql)[0][0]
        if coin_number == None or coin_number == 0:
            all_earn_coins = bet_limit.red_limit
        else:
            coin_number = normalize_fraction(coin_number, int(coin_accuracy))
            all_earn_coins = coin_number + normalize_fraction(bet_limit.red_limit, int(coin_accuracy))  # 能赔金额
        print("一共可以赔============================", all_earn_coins)

        sql = "select sum(dtr.earn_coin) from dragon_tiger_dragontigerrecord dtr"
        sql += " where dtr.option_id = '" + str(option_id) + "'"
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

        record.earn_coin = earn_coin
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
