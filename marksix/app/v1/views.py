# -*- coding: UTF-8 -*-
from base.app import ListCreateAPIView, ListAPIView
from .serializers import PlaySerializer, OpenPriceSerializer, RecordSerializer, ColorSerializer
from base import code as error_code
from django.conf import settings
from users.models import User, UserCoin
from marksix.models import Play, OpenPrice, Option, Number, Animals, SixRecord, MarkSixBetLimit
from django.http import JsonResponse, HttpResponse
from users.finance.functions import get_now
from marksix.functions import date_exchange, change_num
from django.db import transaction
from datetime import datetime
from utils.functions import value_judge, handle_zero
from base.exceptions import ParamErrorException
from base import code as error_code
from chat.models import Club
from marksix.functions import valied_content, CountPage
from decimal import *
from users.models import User, CoinDetail
from django.db.models import Sum
from base.function import LoginRequired
from rest_framework.views import APIView
import pytz
import time
from utils.cache import set_cache, get_cache, delete_cache
from users.models import Coin
from itertools import combinations


class SortViews(ListAPIView):
    permission_classes = (LoginRequired,)
    serializer_class = PlaySerializer

    def get_queryset(self):
        res = Play.objects.filter(is_deleted=0)
        return res

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        # 获取上期开奖时间和本期开奖时间
        now = get_now()
        openprice = OpenPrice.objects.all().order_by('-id').first()
        if openprice == None or openprice == '':
            prev_issue = ""  # 上期开奖期数
            prev_flat = ""  # 上期平码
            prev_special = ""  # 上期特码
            current_issue = ""
            current_open = ""  # 这期开奖时间
            begin_at = ""  # 这期开奖时间
        else:
            prev_issue = openprice.issue  # 上期开奖期数
            prev_flat = openprice.flat_code  # 上期平码
            prev_special = openprice.special_code  # 上期特码
            current_issue = str(int(prev_issue) + 1)  # 这期开奖期数
            # current_issue = (3 - len(current_issue)) * '0' + current_issue
            current_issue = current_issue
            current_open = date_exchange(openprice.next_open)  # 这期开奖时间
            begin_at = openprice.next_open.astimezone(pytz.timezone(settings.TIME_ZONE))
            begin_at = time.mktime(begin_at.timetuple())
            begin_at = int(begin_at)  # 这期开奖时间

        return self.response({'code': 0,
                              'data': items,
                              'prev_issue': prev_issue,
                              'prev_flat': prev_flat,
                              'prev_special': prev_special,
                              'current_issue': current_issue,
                              'current_open': current_open,
                              'begin_at': begin_at
                              })


class OpenViews(ListAPIView):
    permission_classes = (LoginRequired,)
    # authentication_classes = ()
    serializer_class = OpenPriceSerializer

    def get_queryset(self):
        res = OpenPrice.objects.all().order_by('-id')
        return res

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')

        animals = Animals.objects.all()
        marksix_all_code = "marksix_animal_dict"  # key
        animals_dict = get_cache(marksix_all_code)
        if animals_dict == None or animals_dict == '':
            animals_dict = {}
            for item in animals:
                animals_dict[change_num(item.num)] = Animals.ANIMAL_CHOICE[int(item.animal) - 1][1]
            set_cache(marksix_all_code, animals_dict)
        data = {
            'open_list': items,
            'animals_dict': animals_dict
        }

        return self.response({'code': 0, 'data': data})


class OddsViews(ListAPIView):
    permission_classes = (LoginRequired,)

    def list(self, request, id):
        language = request.GET.get('language')
        club_id = request.GET.get('club_id')
        if not club_id:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)

        try:
            coin_name = Club.objects.get(id=club_id).coin.name
        except:
            coin_name = ''

        marksix_all_code = "marksix_all_code"  # key
        bet_num = get_cache(marksix_all_code)
        if bet_num == None or bet_num == '':
            ress = Option.objects.filter(play_id=1)
            bet_num = []
            for item in ress:
                bet_dict = {}
                bet_dict['id'] = item.id
                bet_dict['num'] = change_num(item.option)
                bet_dict['pitch'] = False
                bet_num.append(bet_dict)
            set_cache(marksix_all_code, bet_num)

        if not language:
            language = 'zh'

        # 如果是六肖中特玩法，拿出生肖options
        bet_odds_top = []
        if id == '8':
            for option in Option.objects.filter(play_id=int(id)):
                bet_odds_top.append({
                    'id': option.id,
                    'option': option.option,
                    'odds': option.odds,
                })
            res = Option.objects.filter(play_id='5')
        else:
            res = Option.objects.filter(play_id=int(id))

        if id == '1':  # 特码，暂时只要获取一个赔率，因为目前赔率都相等
            play = Play.objects.get(id=1)
            if language == 'zh':
                option = play.title
            else:
                option = play.title_en
            bet_odds = {
                'option': option,
                'id': 1,
                'odds': int(res[0].odds) if str(res[0].odds).split('.')[1] == '00' else float(res[0].odds)
            }
            bet_odds['num'] = bet_num
        else:
            bet_odds = []
            if language == 'zh':
                option = '三中二'
            else:
                option = 'Three Hit Two'
            three_to_three = {
                'option': option,
            }

            tag = 0  # 标记

            for item in res:
                if language == 'zh':
                    option = item.option
                else:
                    option = item.option_en

                res_dict = {}
                res_dict['id'] = item.id
                res_dict['option'] = option
                res_dict['odds'] = int(item.odds) if str(item.odds).split('.')[1] == '00' else float(item.odds)
                res_dict['pitch'] = False

                if id == '2':  # 波色
                    color_id = Option.WAVE_CHOICE[item.option]
                    num_list = Number.objects.filter(color=color_id).values_list('num', flat=True)
                    res_dict['num_list'] = list(num_list)
                # elif id == '4': # 两面

                elif id == '3':  # 连码
                    if three_to_three['option'] in res_dict['option']:
                        if tag == 0:
                            three_to_three['id'] = item.id
                            three_to_three['odds'] = int(item.odds) if str(item.odds).split('.')[1] == '00' else float(
                                item.odds)
                            three_to_three['pitch'] = False
                            bet_odds.append(three_to_three)
                            tag = 1
                        else:
                            three_to_three['odds1'] = int(item.odds) if str(item.odds).split('.')[1] == '00' else float(
                                item.odds)
                            if language == 'zh':
                                three_to_three['option1'] = '中三'
                            else:
                                three_to_three['option1'] = 'Three Hit Three'
                        continue
                elif id == '5' or id == '8':  # 平特一肖或六肖中特
                    # 获取当前年份
                    year = datetime.now().year
                    animal_id = Option.ANIMAL_CHOICE[item.option]
                    num_list = Animals.objects.filter(animal=animal_id, year=year).values_list('num', flat=True)
                    res_dict['num_list'] = list(num_list)
                # elif id == '6': # 特头尾
                elif id == '7':  # 五行
                    element_id = Option.ELEMENT_CHOICE[item.option]
                    num_list = Number.objects.filter(element=element_id).values_list('num', flat=True)
                    res_dict['num_list'] = list(num_list)

                if res_dict.get('num_list', ''):
                    num_list = res_dict['num_list']
                    for i in num_list:
                        res_dict['num_list'][num_list.index(i)] = change_num(i)

                bet_odds.append(res_dict)

        # if id == '3':
            #     bet_odds.append(three_to_three)

        # 获取上期开奖时间和本期开奖时间
        now = get_now()
        openprice = OpenPrice.objects.all().order_by('-id').first()
        if openprice == None or openprice == '':
            prev_issue = ""  # 上期开奖期数
            prev_flat = ""  # 上期平码
            prev_special = ""  # 上期特码
            current_issue = ""
            current_open = ""  # 这期开奖时间
        else:
            prev_issue = openprice.issue  # 上期开奖期数
            prev_flat = openprice.flat_code  # 上期平码
            prev_special = openprice.special_code  # 上期特码
            # current_issue = str(int(prev_issue) + 1)  # 这期开奖期数
            current_issue = openprice.next_issue  # 这期开奖期数
            current_issue = (3 - len(current_issue)) * '0' + current_issue
            current_open = date_exchange(openprice.next_open)  # 这期开奖时间

        limit = MarkSixBetLimit.objects.get(club_id=club_id, options_id=id)
        base_data = {
            'prev_issue': prev_issue,
            'prev_flat': prev_flat,
            'prev_special': prev_special,
            'current_issue': current_issue,
            'current_open': current_open,
            'coin_name': coin_name,
            'play_id': id,
            'max_limit': handle_zero(limit.max_limit),
            'min_limit': handle_zero(limit.min_limit)
        }
        if id == '3':
            data = {
                'bet_odds': bet_odds,
                'bet_num': bet_num,
            }
            data.update(base_data)
        elif id == '8':
            data = {
                'bet_odds_top': bet_odds_top,
                'bet_odds': bet_odds,
            }
            data.update(base_data)
        else:
            data = {
                'bet_odds': bet_odds,
            }
            data.update(base_data)

        return JsonResponse({'code': 0, 'data': data})


class BetsViews(ListCreateAPIView):
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    @transaction.atomic()
    def post(self, request, *args, **kwargs):  # 两面的三中二玩法有两个赔率，记录只记录一个赔率，开奖的时候再进行具体的赔率判断
        user = self.request.user
        user_id = user.id
        res = value_judge(request, 'club_id', 'bet', 'bet_coin', 'issue', 'content', 'play')
        if not res:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)

        club_id = request.data.get('club_id')
        play_id = request.data.get('play')
        bet = request.data.get('bet')
        bet_coin = Decimal(request.data.get('bet_coin'))
        issue = request.data.get('issue')
        content = request.data.get('content')  # 数组，当为特码或者连码时，传入号码串；当为其他类型时，传入id

        # 如果是色波玩法，最多允许选两个
        if int(play_id) == 2:
            if len(content.split(',')) > 2:
                raise ParamErrorException(error_code.API_50206_BET_COLOR_OVER)

        # 期数判断
        now = get_now()
        openprice = OpenPrice.objects.all().order_by('-id').first()
        prev_issue = openprice.issue  # 上期开奖期数

        # 封盘
        if datetime.now() > openprice.next_closing:
            raise ParamErrorException(error_code.API_50204_BET_CLOSED)

        if int(openprice.next_issue) != int(issue):
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)

        # 注数判断
        if play_id == '3':  # 连码
            try:
                option_id = request.data.get('option_id')
            except:
                raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
            if not option_id:
                raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
            op = Option.objects.get(id=option_id)
            # 二中二: n(n-1)/2 ,三中二或三中三: n(n-1)(n-2)/6
            n = len(content.split(','))
            if op.option == '二中二':
                if int(bet) != n * (n - 1) / 2:
                    raise ParamErrorException(error_code.API_50203_BET_ERROR)
            elif op.option != '平码':
                if int(bet) != n * (n - 1) * (n - 2) / 6:
                    raise ParamErrorException(error_code.API_50203_BET_ERROR)
            else:
                if int(bet) != len(content.split(',')):
                    raise ParamErrorException(error_code.API_50203_BET_ERROR)

        elif play_id == '8':  # 六肖中特
            try:
                option_id = request.data.get('option_id')
            except Exception:
                raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
            if not option_id:
                raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
            if int(bet) != len(list(combinations(content.split(','), 6))):
                raise ParamErrorException(error_code.API_50203_BET_ERROR)

        else:
            if int(bet) != len(content.split(',')):
                raise ParamErrorException(error_code.API_50203_BET_ERROR)
            else:
                option_id = content.split(',')[0]

        # 判断最大最小金额
        limit = MarkSixBetLimit.objects.get(options_id=option_id, club_id=club_id)
        limit_max = limit.max_limit
        limit_min = limit.min_limit
        if float(bet_coin) > limit_max or float(bet_coin) < limit_min:
            raise ParamErrorException(error_code.API_50204_BET_ERROR)

        if play_id == '1':  # 为特码
            option_id = ''
            odds = Option.objects.filter(play_id=play_id)[0].odds

        elif play_id == '3':  # 为连码时，赔率唯一
            try:
                option_id = request.data.get('option_id')
            except:
                raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
            if not option_id:
                raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
            try:
                op = Option.objects.get(id=option_id, play_id=play_id)
            except:
                raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
            # 判断用户下注是否合法,连码需要判断
            title_list = ['二中二', '三中二', '三中三']
            if op.option == title_list[0]:  # 二中二，最低两个号码，不超过七个
                res = valied_content(content, 2, 7)
                if not res:
                    raise ParamErrorException(error_code.API_50201_BET_LIMITED)
            if title_list[1] in op.option:  # 三中二,最低三个号码，不超过七个
                res = valied_content(content, 3, 7)
                if not res:
                    raise ParamErrorException(error_code.API_50201_BET_LIMITED)
            if op.option == title_list[2]:  # 三中三,最低三个号码，不超过十个
                res = valied_content(content, 3, 10)
                if not res:
                    raise ParamErrorException(error_code.API_50201_BET_LIMITED)
            if not op:
                raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
            odds = op.odds

        elif play_id == '8':  # 六肖中特
            try:
                option_id = request.data.get('option_id')
            except Exception:
                raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
            res = valied_content(content, 6, 8)
            if not res:
                raise ParamErrorException(error_code.API_50201_BET_LIMITED)
            odds = Option.objects.filter(play_id=play_id)[0].odds

        else:  # 当为其他类型时，赔率多个
            option_id = ''
            content_list = content.split(',')
            odd_list = []
            for id in content_list:
                try:
                    op = Option.objects.get(id=int(id), play_id=play_id)
                except:
                    raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
                odd_list.append(str(op.odds))
            odds = ','.join(odd_list)

        # 判断投注是否上限
        # clubinfo = Club.objects.get(pk=club_id)
        # coin_id = clubinfo.coin.pk
        # bet_sum = SixRecord.objects.filter(user_id=user.id, club_id=club_id, play_id=play_id).aggregate(
        #     Sum('bet_coin'))
        # if coin_id == Coin.HAND:
        #     if bet_sum['bet_coin__sum'] is not None and bet_sum['bet_coin__sum'] >= 5000000:
        #         raise ParamErrorException(error_code.API_50202_MARKSIX_BET_LIMITED)
        # elif coin_id == Coin.INT:
        #     if bet_sum['bet_coin__sum'] is not None and bet_sum['bet_coin__sum'] >= 20000:
        #         raise ParamErrorException(error_code.API_50202_MARKSIX_BET_LIMITED)
        # elif coin_id == Coin.ETH:
        #     if bet_sum['bet_coin__sum'] is not None and bet_sum['bet_coin__sum'] >= 6:
        #         raise ParamErrorException(error_code.API_50202_MARKSIX_BET_LIMITED)
        # elif coin_id == Coin.BTC:
        #     if bet_sum['bet_coin__sum'] is not None and bet_sum['bet_coin__sum'] >= 0.5:
        #         raise ParamErrorException(error_code.API_50202_MARKSIX_BET_LIMITED)
        # elif coin_id == Coin.USDT:
        #     if bet_sum['bet_coin__sum'] is not None and bet_sum['bet_coin__sum'] >= 3100:
        #         raise ParamErrorException(error_code.API_50202_MARKSIX_BET_LIMITED)

        # 获取币种
        club = Club.objects.get(id=club_id)
        coin_id = club.coin_id
        # 查看用户余额是否足够
        usercoin = UserCoin.objects.get(user_id=user_id, coin_id=coin_id)
        # 判断用户金币是否足够
        if float(usercoin.balance) < float(bet_coin):
            raise ParamErrorException(error_code.API_50104_USER_COIN_NOT_METH)

        # 判断用户
        source = request.META.get('HTTP_X_API_KEY')  # 获取用户请求类型
        if source == "ios":
            source = 1
        elif source == "android":
            source = 2
        else:
            source = 3
        if user.is_robot is True:
            source = 4

        # 更新下注表
        sixcord = SixRecord()
        sixcord.play_id = play_id
        sixcord.user_id = user_id
        sixcord.club_id = club_id
        sixcord.option_id = option_id
        sixcord.odds = odds
        sixcord.bet = bet
        sixcord.bet_coin = bet_coin
        sixcord.issue = issue
        sixcord.content = content
        sixcord.source = source
        sixcord.save()

        # 更新用户余额UserCoin
        usercoin.balance = usercoin.balance - bet_coin
        usercoin.save()
        # 更新资金流向表 CoinDetail
        coin_detail = CoinDetail()
        coin_detail.user = user
        coin_detail.coin_name = usercoin.coin.name
        coin_detail.amount = '-' + str(bet_coin)
        coin_detail.rest = usercoin.balance
        coin_detail.sources = 3
        coin_detail.save()

        return self.response({'code': 0})


class BetsListViews(ListAPIView):
    permission_classes = (LoginRequired,)
    # authentication_classes = ()
    serializer_class = RecordSerializer

    def get_queryset(self):
        user = self.request.user
        user_id = user.id
        club_id = self.request.GET.get('club_id')
        # user_id = 2476
        type = self.kwargs['type']
        if type == '0':  # 全部记录
            res = SixRecord.objects.filter(user_id=user_id, club_id=club_id)
        elif type == '1':  # 未开奖
            res = SixRecord.objects.filter(user_id=user_id, club_id=club_id, status=0)
        elif type == '2':  # 已开奖
            res = SixRecord.objects.filter(user_id=user_id, club_id=club_id, status=1)
        else:
            res = []
        return res

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        res = results.data.get('results')
        # 获取下注记录，以期数分类，按时间顺序排列
        issue_tag = ''
        for item in res:
            issue = item['issue']
            if issue != issue_tag:
                issue_tag = issue
            else:
                item['issue'] = ''
        return self.response({'code': 0, 'data': res})


class ColorViews(APIView):
    def get(self, request, *args, **kwargs):
        res = Number.objects.all()

        marksix_all_code = "marksix_color_dict"  # key
        res_dict = get_cache(marksix_all_code)
        if res_dict == None or res_dict == '':
            res_dict = {}
            for item in res:
                res_dict[change_num(item.num)] = item.color
            set_cache(marksix_all_code, res_dict)
        color = {
            1: '红波',
            2: '蓝波',
            3: '绿波'
        }
        return JsonResponse({'code': 0, 'data': {'num_dict': res_dict, 'color_dict': color}})
