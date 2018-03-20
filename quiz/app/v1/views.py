# -*- coding: UTF-8 -*-
from base.app import FormatListAPIView, FormatRetrieveAPIView, CreateAPIView
from django.db import transaction
from django.db.models import Q
from base.function import LoginRequired
from base.app import ListAPIView, ListCreateAPIView
from ...models import Category, Quiz, Record, Rule, Option
from users.models import User
from base.exceptions import ParamErrorException
from base import code as error_code
from decimal import Decimal
from .serializers import QuizSerialize, RecordSerialize, QuizDetailSerializer
from utils.functions import amount, value_judge
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
        return self.response({'code': 0, 'items': items})


class QuizListView(ListCreateAPIView):
    """
    获取竞猜列表
    """
    permission_classes = (LoginRequired,)
    serializer_class = QuizSerialize

    def get_queryset(self):
        if 'category' not in self.request.GET:
            if 'is_end' not in self.request.GET:
                return Quiz.objects.filter(~Q(status=2), is_delete=False)
            else:
                return Quiz.objects.filter(status=self.request.GET.get('is_end'), is_delete=False)
        category_id = str(self.request.GET.get('category'))
        category_arr = category_id.split(',')
        if 'is_end' not in self.request.GET:
            return Quiz.objects.filter(~Q(status=2), is_delete=False, category__in=category_arr)
        else:
            return Quiz.objects.filter(status=self.request.GET.get('is_end'), category__in=category_arr,
                                       is_delete=False)


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


class RuleView(ListAPIView):
    """
    竞猜选项
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        return

    def list(self, request, *args, **kwargs):
        quiz_id = kwargs['quiz_id']
        rule = Rule.objects.filter(quiz_id=quiz_id)
        data = []
        for i in rule:
            option = Option.objects.filter(rule_id=i.pk)
            list = []
            total = Record.objects.filter(rule_id=i.pk).count()
            for s in option:
                number = Record.objects.filter(rule_id=i.pk, option_id=s.pk).count()
                if number == 0 or total == 0:
                    accuracy = "0%"
                else:
                    accuracy = number / total * 100
                    accuracy = Decimal(accuracy).quantize(Decimal('0.00'))
                    accuracy = str(accuracy) + '%'
                list.append({
                    "option_id": s.pk,
                    "option": s.option,
                    "odds": s.odds,
                    "is_right": s.is_right,
                    "accuracy": accuracy
                })
            data.append({
                "quiz_id": i.quiz_id,
                "type": i.TYPE_CHOICE[int(i.type)][1],
                "tips": i.tips,
                "handicap_score": i.handicap_score,
                "estimate_score": i.estimate_score,
                "list": list
            })
        return self.response({'code': 0, 'data': data})


# class OptionView(ListAPIView):
#     """
#     竞猜玩法下选项
#     """
#     permission_classes = (LoginRequired,)
#
#     def get_queryset(self):
#         return
#
#     def list(self, request, *args, **kwargs):
#         rule_id = kwargs['rule_id']
#         option = Option.objects.filter(rule_id=rule_id)
#         data=[]
#         total = Record.objects.filter(rule_id=rule_id).count()
#         for i in option:
#             number=Record.objects.filter(rule_id=rule_id,option_id=i.pk).count()
#             if number == 0 or total == 0:
#                 accuracy = "0%"
#             else:
#                 accuracy = number / total * 100
#                 accuracy = Decimal(accuracy).quantize(Decimal('0.00'))
#                 accuracy = str(accuracy) + '%'
#             data.append({
#                 "option_id": i.pk,
#                 "rule_id": i.rule_id,
#                 "option": i.option,
#                 "odds": i.odds,
#                 "is_right": i.is_right,
#                 "accuracy":accuracy
#             })
#         return self.response({'code': 0, 'data': data})


class CoinView(ListAPIView):
    """
    切换币总
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        return

    def list(self, request, *args, **kwargs):
        user = self.request.user.id
        users = User.objects.get(pk=user)
        meth = users.meth
        total = users.ggtc
        ggtc_locked = amount(user)  # 该用户锁定的金额 = amount(user)
        ggtc = total - ggtc_locked
        return self.response({'code': 0,
                              'meth': meth,
                              'ggtc': ggtc})


class BetView(ListCreateAPIView):
    """
    竞猜下注
    """
    max_wager = 10000

    def get_queryset(self):
        pass

    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        value = value_judge(request, "quiz_id", "coin_type", "option", "wager")
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)

        user = request.user
        quiz_id = self.request.data['quiz_id']  # 获取竞猜ID
        coin_type = self.request.data['coin_type']  # 获取货币类型
        regex = re.compile(r'^(0|1)$')
        if coin_type is None or not regex.match(coin_type):
            raise ParamErrorException(error_code.API_10104_PARAMETER_EXPIRED)
        option = str(self.request.data['option'])  # 获取选项ID(字符串)
        option_arr = option.split(',')
        coins = str(self.request.data['wager'])  # 获取投注金额(字符串)
        coins_arr = coins.split(',')

        coin = 0
        if len(option_arr) != len(coins_arr):
            raise ParamErrorException(error_code.API_50106_PARAMETER_EXPIRED)

        for (option_id, wager) in zip(option_arr, coins_arr):
            try:  # 判断选项ID是否有效
                option_id = int(option_id)
            except Exception:
                raise ParamErrorException(error_code.API_50101_QUIZ_OPTION_ID_INVALID)

            coin += int(wager)
            try:  # 判断赌注是否有效
                wager = int(wager)
            except Exception:
                raise ParamErrorException(error_code.API_50102_WAGER_INVALID)
                # 赌注是否超过上限
            if wager > self.max_wager:
                raise ParamErrorException(error_code.API_50103_WAGER_LIMITED)

        quiz = Quiz.objects.get(pk=quiz_id)  # 判断比赛数学
        if int(quiz.status) != Quiz.PUBLISHING or quiz.is_delete is True:
            raise ParamErrorException(error_code.API_50107_USER_BET_TYPE_ID_INVALID)

        if int(coin_type) == 1:  # 判断用户金币是否足够
            if user.meth < coin:
                raise ParamErrorException(error_code.API_50104_USER_COIN_NOT_METH)
        elif int(coin_type) == 2:
            if user.ggtc < coin:
                raise ParamErrorException(error_code.API_50105_USER_COIN_NOT_GGTC)

        earn_coins = 0
        for (option_id, wager) in zip(option_arr, coins_arr):
            # 获取选项赔率
            options = Option.objects.get(pk=int(option_id))

            record = Record()
            record.user = user
            record.quiz = quiz
            record.rule = options.rule
            record.option = options
            record.bet = int(wager)
            record.earn_coin = int(wager) * options.odds
            record.save()
            earn_coins += int(wager) * options.odds
            # 用户减少金币
            if int(coin_type) == 1:
                user.meth -= wager
                user.save()
            elif int(coin_type) == 2:
                user.ggtc -= wager
                user.save()

        response = {
            'code': 0,
            'message': '下注成功，金额总数为 ' + str(coin) + '，预计可得猜币 ' + str(earn_coins),
        }
        return self.response(response)
