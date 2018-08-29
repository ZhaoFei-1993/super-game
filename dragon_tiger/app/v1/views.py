# -*- coding: UTF-8 -*-
from base.app import ListAPIView
from utils.functions import value_judge, float_to_str
import hashlib
from base import code as error_code
from base.exceptions import ParamErrorException
import time
from utils.functions import value_judge, get_sql
import urllib.request
import urllib.parse
import json
from dragon_tiger.models import BetLimit
from base.function import LoginRequired
from dragon_tiger.models import BetLimit
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
        user_balance = float_to_str(user_balance, coin_accuracy)

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
                "id": option_list[0][3],
            },
            "tie": {
                "title": option_list[1][0],
                "odds": tie_odds,
                "order": option_list[1][2],
                "id": option_list[1][3],
            },
            "player": {
                "title": option_list[2][0],
                "odds": player_odds,
                "order": option_list[2][2],
                "id": option_list[2][3],
            }
        }

        return self.response({'code': 0,
                              "user_balance": user_balance,
                              "bets_one": betlimit_list[0],
                              "bets_two": betlimit_list[1],
                              "bets_three": betlimit_list[2],
                              "bets_four": betlimit_list[3],
                              "red_limit": betlimit_list[4],
                              "option_info": option_info
                              })
