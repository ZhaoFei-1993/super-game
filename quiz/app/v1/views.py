# -*- coding: UTF-8 -*-
from base.app import FormatListAPIView, FormatRetrieveAPIView, CreateAPIView
from django.db import transaction
from django.db.models import Q
from base.function import LoginRequired
from base.app import ListAPIView, ListCreateAPIView
from ...models import Category, Quiz, Record, Rule, Option
from users.models import UserCoin, CoinValue
from base.exceptions import ParamErrorException
from base import code as error_code
from decimal import Decimal
from .serializers import QuizSerialize, RecordSerialize, QuizDetailSerializer, QuizPushSerializer
from utils.functions import value_judge
from datetime import datetime
import re


class CategoryView(ListAPIView):
    """
    竞猜分类
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        return

    def list(self, request, *args, **kwargs):
        categorys = Category.objects.filter(parent_id=None)
        data = []
        for category in categorys:
            children = []
            categoryslist = Category.objects.filter(parent_id=category.id, is_delete=0).order_by("order")
            for categorylist in categoryslist:
                children.append({
                    "category_id": categorylist.id,
                    "category_name": categorylist.name,
                })
            data.append({
                "category_id": category.id,
                "category_name": category.name,
                "children": children
            })
        return self.response({'code': 0, 'data': data})


class HotestView(ListAPIView):
    """
    热门比赛
    """
    permission_classes = (LoginRequired,)
    serializer_class = QuizSerialize

    def get_queryset(self):
        return Quiz.objects.filter(status=0, is_delete=False).order_by('-total_people')[:10]

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        return self.response({'code': 0, 'data': {'items': items}})


class QuizListView(ListCreateAPIView):
    """
    获取竞猜列表
    """
    permission_classes = (LoginRequired,)
    serializer_class = QuizSerialize

    def get_queryset(self):
        if 'is_user' not in self.request.GET:
            if 'category' not in self.request.GET:
                if 'is_end' not in self.request.GET:
                    return Quiz.objects.filter(Q(status=0) | Q(status=1), is_delete=False)
                else:
                    return Quiz.objects.filter(Q(status=2) | Q(status=3) | Q(status=4), is_delete=False)
            category_id = str(self.request.GET.get('category'))
            category_arr = category_id.split(',')
            if 'is_end' not in self.request.GET:
                return Quiz.objects.filter(Q(status=0) | Q(status=1), is_delete=False, category__in=category_arr)
            else:
                return Quiz.objects.filter(Q(status=2) | Q(status=3) | Q(status=4), category__in=category_arr,
                                           is_delete=False)
        else:
            userid = self.request.user.id
            quiz_id = list(set(Record.objects.filter(user_id=userid).values_list('quiz_id', flat=True)))
            my_quiz = Quiz.objects.filter(id__in=quiz_id)
            return my_quiz

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        value = results.data.get('results')
        return self.response({"code": 0, "data": value})


class RecordsListView(ListCreateAPIView):
    """
    竞猜记录
    """
    permission_classes = (LoginRequired,)
    serializer_class = RecordSerialize

    def get_queryset(self):
        if 'user_id' not in self.request.GET:
            user_id = self.request.user.id
        else:
            self.request.GET.get('user_id')
        return Record.objects.filter(user_id=user_id).order_by('created_at')

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        Progress = results.data.get('results')
        data = []
        # quiz_id = ''
        tmp = ''
        time = ''
        host = ''
        guest = ''
        for fav in Progress:
            # record = fav.get('pk')
            # quiz = fav.get('quiz_id')
            pecific_date = fav.get('created_at')[0].get('year')
            pecific_time = fav.get('created_at')[0].get('time')
            host_team = fav.get('host_team')
            guest_team = fav.get('guest_team')
            if tmp == pecific_date and time == pecific_time and host == host_team and guest == guest_team:
                host_team = ""
                guest_team = ""
            else:
                host = host_team
                guest = guest_team

            if tmp == pecific_date and time == pecific_time:
                pecific_time = ""
            else:
                time = pecific_time

            if tmp == pecific_date:
                pecific_date = ""
            else:
                tmp = pecific_date

            # records = Record.objects.get(pk=record)
            # earn_coin = records.earn_coin
            # print("earn_coin=================", earn_coin)
            # if quiz_id==quiz:
            #     pass
            # else:
            #     quiz_id=quiz
            data.append({
                "quiz_id": fav.get('quiz_id'),
                'host_team': host_team,
                'guest_team': guest_team,
                'pecific_date': pecific_date,
                'pecific_time': pecific_time,
                'my_option': fav.get('my_option')[0].get('my_option'),
                'is_right': fav.get('my_option')[0].get('is_right'),
            })

        return self.response({'code': 0, 'data': data})


class QuizDetailView(ListAPIView):
    """
    竞猜详情
    """
    permission_classes = (LoginRequired,)
    serializer_class = QuizDetailSerializer

    def get_queryset(self):
        quiz_id = self.request.parser_context['kwargs']['quiz_id']
        quiz = Quiz.objects.filter(pk=quiz_id)
        return quiz

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        item = items[0]
        return self.response({"code": 0, "data": {
            "id": item['id'],
            "host_team": item['host_team'],
            "host_team_score": item['host_team_score'],
            "guest_team": item['guest_team'],
            "guest_team_score": item['guest_team_score'],
            "begin_at": item['start'],
            "year": item['year'],
            "time": item['time'],
            "status": item['status']
        }})


class QuizPushView(ListAPIView):
    """
    下注页面推送
    """
    permission_classes = (LoginRequired,)
    serializer_class = QuizPushSerializer

    def get_queryset(self):
        quiz_id = self.request.parser_context['kwargs']['quiz_id']
        record = Record.objects.filter(quiz_id=quiz_id)
        print("record=================", record)
        return record

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        data = []
        for item in items:
            print("555555555555555")
            data.append(
                {
                    "quiz_id": item['id'],
                    "username": item['username'],
                    "my_rule": item['my_rule'],
                    "my_option": item['my_option'],
                    "bet": item['bet']
                }
            )
        return self.response({"code": 0, "data": data})


class RuleView(ListAPIView):
    """
    竞猜选项
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        return

    def list(self, request, *args, **kwargs):
        user = request.user.id
        quiz_id = kwargs['quiz_id']
        rule = Rule.objects.filter(quiz_id=quiz_id).order_by('type')
        type = UserCoin.objects.filter(user_id=user, is_bet=1).count()
        if type == 0:
            usercoin = UserCoin.objects.get(user_id=user, coin__type=1, is_opt=0)
            is_bet = usercoin.id
            balance = usercoin.balance
            balance = [str(balance), int(balance)][int(balance) == balance]
            coin_name = usercoin.coin.name
            coin_icon = usercoin.coin.icon
            coin_id = usercoin.coin.pk
            coinvalue = CoinValue.objects.filter(coin_id=coin_id).order_by('value')
        else:
            usercoin = UserCoin.objects.get(user_id=user, is_bet=1)
            is_bet = usercoin.id
            balance = usercoin.balance
            balance = [str(balance), int(balance)][int(balance) == balance]
            coin_name = usercoin.coin.name
            coin_icon = usercoin.coin.icon
            coin_id = usercoin.coin.pk
            coinvalue = CoinValue.objects.filter(coin_id=coin_id).order_by('value')
        value1 = coinvalue[0].value
        value1 = [str(value1), int(value1)][int(value1) == value1]
        value2 = coinvalue[1].value
        value2 = [str(value2), int(value2)][int(value2) == value2]
        value3 = coinvalue[2].value
        value3 = [str(value3), int(value3)][int(value3) == value3]
        data = []
        for i in rule:
            option = Option.objects.filter(rule_id=i.pk).order_by('order')
            list = []
            total = Record.objects.filter(rule_id=i.pk).count()
            for s in option:
                number = Record.objects.filter(rule_id=i.pk, option_id=s.pk).count()
                if number == 0 or total == 0:
                    accuracy = "0"
                else:
                    accuracy = number / total
                    accuracy = Decimal(accuracy).quantize(Decimal('0.00'))
                list.append({
                    "option_id": s.pk,
                    "option": s.option,
                    "odds": s.odds,
                    "option_type": s.option_type,
                    "is_right": s.is_right,
                    "accuracy": accuracy,
                    "order": s.order
                })
            # 比分
            win = []
            flat = []
            loss = []
            if int(i.type) == 2:
                for l in list:
                    if str(l['option_type']) == "胜":
                        win.append(l)
                    elif str(l['option_type']) == "平":
                        flat.append(l)
                    else:
                        loss.append(l)
                data.append({
                    "quiz_id": i.quiz_id,
                    "type": i.TYPE_CHOICE[int(i.type)][1],
                    "tips": i.tips,
                    "home_let_score": i.home_let_score,
                    "guest_let_score": i.guest_let_score,
                    "estimate_score": i.estimate_score,
                    "list_win": win,
                    "list_flat": flat,
                    "list_loss": loss
                })
            elif int(i.type) == 7:
                for l in list:
                    if str(l['option_type']) == "主胜":
                        win.append(l)
                    else:
                        loss.append(l)
                    win.sort(key=lambda x: x["order"])
                    flat.sort(key=lambda x: x["order"])
                    loss.sort(key=lambda x: x["order"])
                data.append({
                    "quiz_id": i.quiz_id,
                    "type": i.TYPE_CHOICE[int(i.type)][1],
                    "tips": i.tips,
                    "home_let_score": i.home_let_score,
                    "guest_let_score": i.guest_let_score,
                    "estimate_score": i.estimate_score,
                    "list_win": win,
                    "list_loss": loss,
                })
            else:
                data.append({
                    "quiz_id": i.quiz_id,
                    "type": i.TYPE_CHOICE[int(i.type)][1],
                    "tips": i.tips,
                    "home_let_score": i.home_let_score,
                    "guest_let_score": i.guest_let_score,
                    "estimate_score": i.estimate_score,
                    "list": list
                })
        return self.response({'code': 0, 'data': data,
                              'list': {'is_bet': is_bet, 'balance': balance, 'coin_name': coin_name,
                                       'coin_icon': coin_icon, 'value1': value1, 'value2': value2, 'value3': value3}})


class BetView(ListCreateAPIView):
    """
    竞猜下注
    """
    # max_wager = 10000

    def get_queryset(self):
        pass

    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        value = value_judge(request, "usercoin_id", "quiz_id", "option", "wager")
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)

        user = request.user
        quiz_id = self.request.data['quiz_id']  # 获取竞猜ID
        usercoin_id = self.request.data['usercoin_id']  # 获取货币类型

        # 单个下注
        option = self.request.data['option']  # 获取选项ID
        coins = self.request.data['wager']  # 获取投注金额
        coin = 0
        try:  # 判断选项ID是否有效
            option_id = int(option)
        except Exception:
            raise ParamErrorException(error_code.API_50101_QUIZ_OPTION_ID_INVALID)

        try:  # 判断赌注是否有效
            coins = int(coins)
        except Exception:
            raise ParamErrorException(error_code.API_50102_WAGER_INVALID)

        quiz = Quiz.objects.get(pk=quiz_id)  # 判断比赛
        if int(quiz.status) != Quiz.PUBLISHING or quiz.is_delete is True:
            raise ParamErrorException(error_code.API_50107_USER_BET_TYPE_ID_INVALID)

        usercoin = UserCoin.objects.get(pk=usercoin_id)
        # 判断用户金币是否足够
        if usercoin.balance < coin:
            raise ParamErrorException(error_code.API_50104_USER_COIN_NOT_METH)

        options = Option.objects.get(pk=int(option_id))

        record = Record()
        record.user = user
        record.quiz = quiz
        record.rule = options.rule
        record.option = options
        record.bet = int(coins)
        record.earn_coin = int(coins) * int(options.odds)
        record.save()
        earn_coins = int(coins) * options.odds
        # 用户减少金币

        usercoin.balance -= int(coins)
        usercoin.save()
        quiz.total_people += 1
        quiz.save()

        #   多个一起下注(预留)
        # option = str(self.request.data['option'])  # 获取选项ID(字符串)
        # coins = str(self.request.data['wager'])  # 获取投注金额(字符串)
        # option_arr = option.split(',')
        # coins_arr = coins.split(',')
        #
        # coin = 0
        # if len(option_arr) != len(coins_arr):
        #     raise ParamErrorException(error_code.API_50106_PARAMETER_EXPIRED)
        #
        # for (option_id, wager) in zip(option_arr, coins_arr):
        #     try:  # 判断选项ID是否有效
        #         option_id = int(option_id)
        #     except Exception:
        #         raise ParamErrorException(error_code.API_50101_QUIZ_OPTION_ID_INVALID)
        #
        #     coin += int(wager)
        #     try:  # 判断赌注是否有效
        #         wager = int(wager)
        #     except Exception:
        #         raise ParamErrorException(error_code.API_50102_WAGER_INVALID)
        #     #     # 赌注是否超过上限
        #     # if wager > self.max_wager:
        #     #     raise ParamErrorException(error_code.API_50103_WAGER_LIMITED)
        #
        # quiz = Quiz.objects.get(pk=quiz_id)  # 判断比赛数学
        # if int(quiz.status) != Quiz.PUBLISHING or quiz.is_delete is True:
        #     raise ParamErrorException(error_code.API_50107_USER_BET_TYPE_ID_INVALID)
        #
        # usercoin = UserCoin.objects.get(pk=usercoin_id)
        # # 判断用户金币是否足够
        # if usercoin.balance < coin:
        #     raise ParamErrorException(error_code.API_50104_USER_COIN_NOT_METH)
        #
        # earn_coins = 0
        # for (option_id, wager) in zip(option_arr, coins_arr):
        #     # 获取选项赔率
        #     options = Option.objects.get(pk=int(option_id))
        #
        #     record = Record()
        #     record.user = user
        #     record.quiz = quiz
        #     record.rule = options.rule
        #     record.option = options
        #     record.bet = int(wager)
        #     record.earn_coin = int(wager) * int(options.odds)
        #     record.save()
        #     earn_coins += int(wager) * options.odds
        #     # 用户减少金币
        #
        #     usercoin.balance -= int(wager)
        #     usercoin.save()
        #     quiz.total_people += 1
        #     quiz.save()

        response = {
            'code': 0,
            'data': {
                'message': '下注成功，金额总数为 ' + str(coin) + '，预计可得猜币 ' + str(earn_coins),
                'balance': usercoin.balance
            }
        }
        return self.response(response)


class RecommendView(ListAPIView):
    """
    竞猜推荐
    """
    permission_classes = (LoginRequired,)
    serializer_class = QuizSerialize

    def get_queryset(self):
        return Quiz.objects.filter(status__lt=2, is_delete=False).order_by('-total_people')[:20]

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        data = []
        for item in items:
            data.append(
                {
                    "quiz_id": item['id'],
                    "match": item['host_team'] + " VS " + item['guest_team'],
                    "match_time": datetime.strftime(datetime.fromtimestamp(item['begin_at']), '%H:%M')
                }
            )
        return self.response({"code": 0, "data": data})
