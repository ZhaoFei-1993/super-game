# -*- coding: UTF-8 -*-
from base.app import ListCreateAPIView, ListAPIView
from .serializers import PlaySerializer, OpenPriceSerializer, RecordSerializer
from base import code as error_code
from django.conf import settings
from users.models import User, UserCoin
from marksix.models import Play, OpenPrice, Option, Number, Animals, SixRecord
from django.http import JsonResponse, HttpResponse
from users.finance.functions import get_now
from marksix.functions import date_exchange
from django.db import transaction
from datetime import datetime
from utils.functions import value_judge
from base.exceptions import ParamErrorException
from base import code as error_code
from chat.models import Club
from marksix.functions import valied_content, CountPage
from decimal import *
from users.models import User, CoinDetail
from django.db.models import Sum


class SortViews(ListAPIView):
    # authentication_classes = ()
    serializer_class = PlaySerializer

    def get_queryset(self):
        res = Play.objects.filter(is_deleted=0)
        return res

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')

        return self.response({'code': 0, 'data': items})


class OpenViews(ListAPIView):
    # authentication_classes = ()
    serializer_class = OpenPriceSerializer

    def get_queryset(self):
        res = OpenPrice.objects.all()
        return res

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')

        return self.response({'code': 0, 'data': items})


class OddsViews(ListAPIView):
    # authentication_classes = ()

    def list(self, request, id):
        language = request.GET.get('language')
        if not language:
            language = 'zh'
        res = Option.objects.filter(play_id=id)
        if id == '1':  # 特码，暂时只要获取一个赔率，因为目前赔率都相等
            res = res[0]
            play = Play.objects.get(id=1)
            if language == 'zh':
                option = play.title
            else:
                option = play.title_en
            bet_odds = {
                'id': res.id,
                'option': option,
                'odds': res.odds
            }
        else:
            bet_odds = []
            if language == 'zh':
                option = '三中二'
            else:
                option = 'Three Hit Two'
            three_to_three = {
                'option': option,
                'result': []
            }
            for item in res:
                if language == 'zh':
                    option = item.option
                else:
                    option = item.option_en
                res_dict = {}
                res_dict['id'] = item.id
                res_dict['option'] = option
                res_dict['odds'] = item.odds

                if id == '2':  # 波色
                    color_id = Option.WAVE_CHOICE[item.option]
                    num_list = Number.objects.filter(color=color_id).values_list('num', flat=True)
                    res_dict['num_list'] = list(num_list)

                # elif id == '4': # 两面
                elif id == '3':  # 连码
                    if three_to_three['option'] in res_dict['option']:
                        three_to_three['result'].append(res_dict)
                        continue
                elif id == '5':  # 平特一肖
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

                bet_odds.append(res_dict)
            if id == '3':
                bet_odds.append(three_to_three)

        # 获取上期开奖时间和本期开奖时间
        now = get_now()
        openprice = OpenPrice.objects.filter(open__lt=now).first()
        prev_issue = openprice.issue  # 上期开奖期数
        prev_flat = openprice.flat_code  # 上期平码
        prev_special = openprice.special_code  # 上期特码
        current_issue = str(int(prev_issue) + 1)  # 这期开奖期数
        current_issue = (3 - len(current_issue)) * '0' + current_issue
        current_open = date_exchange(openprice.next_open)  # 这期开奖时间
        data = {
            'bet_odds': bet_odds,
            'prev_issue': prev_issue,
            'prev_flat': prev_flat,
            'prev_special': prev_special,
            'current_issue': current_issue,
            'current_open': current_open
        }

        return JsonResponse({'code': 0, 'data': data})


class BetsViews(ListCreateAPIView):
    # authentication_classes = ()

    def get_queryset(self):
        pass

    @transaction.atomic()
    def post(self, request, *args, **kwargs):  # 两面的三中二玩法有两个赔率，记录只记录一个赔率，开奖的时候再进行具体的赔率判断
        user = self.request.user
        user_id = user.id
        # user_id = 1806
        # user = User.objects.get(id=user_id)
        res = value_judge(request, 'club_id', 'option_id', 'bet', 'bet_coin', 'issue', 'content')
        if not res:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)

        club_id = request.data.get('club_id')
        option_id = request.data.get('option_id')
        bet = request.data.get('bet')
        bet_coin = Decimal.from_float(float(request.data.get('bet_coin')))
        issue = request.data.get('issue')
        content = request.data.get('content')  # 号码以逗号分割

        op = Option.objects.get(id=option_id)
        if not op:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        odds = op.odds

        # 判断用户下注是否合法,连码需要判断
        op = Option.objects.get(id=option_id)
        title_list = ['二中二', '三中二', '三中三']
        if op.option == title_list[0] or title_list[1] in op.option:  # 二中二，三中二，最低两个号码，不超过七个
            res = valied_content(content, 2, 7)
            if not res:
                raise ParamErrorException(error_code.API_50201_BET_LIMITED)
        if op.option == title_list[2]:  # 三中三,最低三个号码，不超过十个
            res = valied_content(content, 3, 10)
            if not res:
                raise ParamErrorException(error_code.API_50201_BET_LIMITED)

        # 获取币种
        club = Club.objects.get(id=club_id)
        coin_id = club.coin_id
        # 查看用户余额是否足够
        usercoin = UserCoin.objects.get(user_id=user_id, coin_id=coin_id)
        # 判断用户金币是否足够
        if float(usercoin.balance) < float(bet_coin):
            raise ParamErrorException(error_code.API_50104_USER_COIN_NOT_METH)

        source = request.META.get('HTTP_X_API_KEY')  # 获取用户请求类型
        # 更新下注表
        sixcord = SixRecord()
        sixcord.user_id = user_id
        sixcord.club_id = club_id
        sixcord.option_id = option_id
        sixcord.odds = odds
        sixcord.bet = bet
        sixcord.betcoin = bet_coin
        sixcord.issue = issue
        sixcord.content = content
        if source:  # 如果请求中存在source添加，否则默认为机器人
            sixcord.source = sixcord.__getattribute__(source.upper())
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
    # authentication_classes = ()
    serializer_class = RecordSerializer

    def get_queryset(self):
        user = self.request.user
        user_id = user.id
        # user_id = 1806
        # user = User.objects.get(id=user_id)
        type = self.kwargs['type']
        if type == '0':  # 全部记录
            res = SixRecord.objects.filter(user_id=user_id)
        elif type == '1':  # 未开奖
            res = SixRecord.objects.filter(user_id=user_id, status=0)
        elif type == '2':  # 已开奖
            res = SixRecord.objects.filter(user_id=user_id, status=1)
        else:
            return HttpResponse(status=404)
        return res

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        res = results.data.get('results')
        # 获取下注记录，以期数分类，按时间顺序排列
        issue_list = []
        result_list = []
        for item in res:
            issue = item['issue']
            if issue not in issue_list:
                issue_list.append(issue)
                del item['issue']
                result_list.append({
                    'issue': issue,
                    'list': [item]
                })
            else:
                index = issue_list.index(issue)
                del item['issue']
                result_list[index]['list'].append(item)
        return self.response({'code': 0, 'data': result_list})
