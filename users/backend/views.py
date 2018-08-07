# -*- coding: UTF-8 -*-
from itertools import chain
import os
from base.backend import CreateAPIView, FormatListAPIView, FormatRetrieveAPIView, DestroyAPIView, UpdateAPIView, \
    ListAPIView, ListCreateAPIView, RetrieveUpdateAPIView, RetrieveAPIView, RetrieveUpdateDestroyAPIView
from django.db import transaction
from decimal import Decimal
from django.db import connection
from django.conf import settings
import dateparser
from datetime import datetime, timedelta, date
from django.db.models.functions import ExtractDay
from django.db.models import Q, Count, Sum, Max, F, Func, Min
from chat.models import Club
from users.models import Coin, CoinLock, Admin, UserCoinLock, UserCoin, User, CoinDetail, CoinValue, RewardCoin, \
    LoginRecord, UserInvitation, UserPresentation, CoinOutServiceCharge, UserRecharge, CoinGiveRecords, CoinGive, \
    UserMessage, IntInvitation, Message, CoinPrice, DividendConfig, DividendConfigCoin
from users.app.v1.serializers import PresentationSerialize
from rest_framework import status
import jsonfield
from utils.functions import normalize_fraction, get_sql
from base import code as error_code
from base.exceptions import ParamErrorException
from django.http import HttpResponse
from . import serializers
import json
import rest_framework_filters as filters
from utils.filter import JsonFilter
from base import backend
from django.http import JsonResponse
from utils.functions import reversion_Decorator, value_judge
from url_filter.integrations.drf import DjangoFilterBackend
from quiz.models import Record, Quiz, ClubProfitAbroad
import numpy as np
from chat.models import Club
from urllib.parse import quote_plus


class CoinLockListView(CreateAPIView, FormatListAPIView):
    """
    添加一条货币锁定周期方案
    """
    """
    get:
    锁定周期列表

    post:
    锁定周期表：添加一条方案
    """
    serializer_class = serializers.CoinLockSerializer

    def get_queryset(self):
        return CoinLock.objects.filter(is_delete=0)

    @reversion_Decorator
    def post(self, request, *args, **kwargs):
        coins = Coin.objects.get(pk=1)
        admin = self.request.user
        period = request.data['period']
        if int(period) not in [7, 31, 365]:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        coinlock = CoinLock()
        coinlock.period = period
        coinlock.profit = int(request.data['profit']) / 100
        coinlock.limit_start = request.data['start_date']
        coinlock.limit_end = request.data['end_date']
        coinlock.Coin = coins
        coinlock.admin = admin
        coinlock.save()

        content = {'status': status.HTTP_201_CREATED}
        return HttpResponse(json.dumps(content), content_type='text/json')


class CoinLockDetailView():
    serializer_class = serializers.CoinLockSerializer

    def get(self, request, *args, **kwargs):
        id = int(kwargs['pk'])
        coinlock = CoinLock.objects.get(pk=id, is_delete=0)
        data = {
            "period": str(coinlock.period),
            "profit": str(coinlock.profit * 100),
            "start_date": coinlock.limit_start,
            "end_date": coinlock.limit_end,
            "url": ''
        }
        return JsonResponse({'data': data}, status=status.HTTP_200_OK)

    @reversion_Decorator
    def delete(self, request, *args, **kwargs):
        coinlovk_id = self.request.parser_context['kwargs']['pk']
        coinlock = CoinLock.objects.get(pk=coinlovk_id)
        coinlock.is_delete = True
        coinlock.save()
        content = {'status': status.HTTP_200_OK}
        return HttpResponse(json.dumps(content), content_type='text/json')

    @reversion_Decorator
    def update(self, request, *args, **kwargs):
        id = int(kwargs['pk'])
        coinlock = CoinLock.objects.get(pk=id, is_delete=0)
        coinlock.period = int(request.data['period'])
        coinlock.profit = int(request.data['profit']) / 100
        coinlock.limit_start = int(request.data['start_date'])
        coinlock.limit_end = int(request.data['end_date'])
        coinlock.save()
        content = {'status': status.HTTP_200_OK}
        return HttpResponse(json.dumps(content), content_type='text/json')


class CurrencyListView(ListCreateAPIView):
    """
    get:
    币总列表

    post:
    锁定周期表：添加一条方案
    """
    serializer_class = serializers.CurrencySerializer

    def get_queryset(self):
        return Coin.objects.all()

    @reversion_Decorator
    def post(self, request, *args, **kwargs):
        max_order = Coin.objects.all().aggregate(Max('coin_order'))['coin_order__max']
        admin = self.request.user
        exchange_rate = request.data['exchange_rate']
        cash_control = request.data['cash_control']
        betting_toplimit = request.data['betting_toplimit']
        betting_control = request.data['betting_control']
        betting_value_one = request.data['betting_value_one']
        betting_value_two = request.data['betting_value_two']
        betting_value_three = request.data['betting_value_three']
        coin_accuracy = request.data['coin_accuracy']
        is_eth_erc20 = request.data['is_eth_erc20']
        value = request.data['value']
        Integral_proportion = request.data['Integral_proportion']

        coin = Coin()
        coin.icon = request.data['icon']
        coin.coin_order = int(max_order) + 1
        if int(exchange_rate) != 1:
            coin.exchange_rate = 1
        else:
            coin.exchange_rate = exchange_rate
        coin.cash_control = cash_control
        coin.betting_toplimit = betting_toplimit
        coin.betting_control = betting_control
        coin.is_eth_erc20 = is_eth_erc20
        coin.coin_accuracy = coin_accuracy
        coin.name = request.data['name']
        # coin.type = request.data['type']
        # coin.is_lock = request.data['is_lock']
        coin.admin = admin
        coin.save()
        coin_value = CoinValue()
        coin_value.coin = coin
        coin_value.value_index = 1
        coin_value.value = Decimal(betting_value_one)
        coin_value.save()
        coin_value = CoinValue()
        coin_value.coin = coin
        coin_value.value_index = 2
        coin_value.value = Decimal(betting_value_two)
        coin_value.save()
        coin_value = CoinValue()
        coin_value.coin = coin
        coin_value.value_index = 3
        coin_value.value = Decimal(betting_value_three)
        coin_value.save()

        coin_service = CoinOutServiceCharge()
        # try:
        #     coin_t = Coin.objects.get(coin__name=coin.name)
        # except:
        #     return JsonResponse({'Error':'币不存在,请先添加币%s' % coin.name}, status=status.HTTP_400_BAD_REQUEST)
        coin_service.coin_out = coin
        coin_service.coin_payment = coin
        coin_service.value = value
        coin_service.save()
        reward_coin = RewardCoin()
        reward_coin.coin = coin
        reward_coin.value_ratio = Integral_proportion
        reward_coin.admin = admin
        reward_coin.save()

        return JsonResponse({}, status=status.HTTP_201_CREATED)


class CurrencyDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.CurrencySerializer

    def get(self, request, *args, **kwargs):
        id = int(kwargs['pk'])
        coin = Coin.objects.get(pk=id)
        coinvalue_list = CoinValue.objects.filter(coin_id=coin.id).order_by("value_index")
        value_ratio = RewardCoin.objects.filter(coin_id=coin.id)
        if len(value_ratio) == 0:
            Integral_proportion = ""
        else:
            Integral_proportion = value_ratio[0].value_ratio
        if len(coinvalue_list) != 3:
            betting_value_one = ""
            betting_value_two = ""
            betting_value_three = ""
        else:
            betting_value_one = coinvalue_list[0].value
            betting_value_two = coinvalue_list[1].value
            betting_value_three = coinvalue_list[2].value

        values = CoinOutServiceCharge.objects.filter(coin_out_id=coin.id)
        if len(values) == 0:
            value = ''
        else:
            value = values[0].value
        # is_lock = coin.is_lock
        # if is_lock == False:
        #     is_lock = 0
        # if is_lock == True:
        #     is_lock = 1
        data = {
            "icon": coin.icon,
            "name": coin.name,
            # "type": coin.type,
            "exchange_rate": coin.exchange_rate,
            "cash_control": str(coin.cash_control),
            "betting_toplimit": str(coin.betting_toplimit),
            "betting_control": str(coin.betting_control),
            "betting_value_one": str(betting_value_one),
            "betting_value_two": str(betting_value_two),
            "betting_value_three": str(betting_value_three),
            "Integral_proportion": Integral_proportion,
            "coin_order": coin.coin_order,
            "coin_accuracy": coin.coin_accuracy,
            "value": value,
            "is_eth_erc20": coin.is_eth_erc20,
            # "is_lock": str(is_lock),
            "url": ''
        }
        return JsonResponse({'data': data}, status=status.HTTP_200_OK)

    @reversion_Decorator
    def delete(self, request, *args, **kwargs):
        coin_id = self.request.parser_context['kwargs']['pk']
        coin = Coin.objects.get(pk=coin_id)
        coin.is_delete = True
        coin.save()
        content = {'status': status.HTTP_200_OK}
        return JsonResponse({}, status=status.HTTP_200_OK)

    @reversion_Decorator
    def update(self, request, *args, **kwargs):
        id = int(kwargs['pk'])
        cash_control = request.data['cash_control']
        betting_toplimit = request.data['betting_toplimit']
        betting_control = request.data['betting_control']
        coin_accuracy = request.data['coin_accuracy']
        is_eth_erc20 = request.data['is_eth_erc20']
        coin = Coin.objects.get(pk=id)
        coin.icon = request.data['icon']
        coin.name = request.data['name']
        # coin.type = request.data['type']
        coin.exchange_rate = request.data['exchange_rate']
        coin.cash_control = cash_control
        coin.betting_toplimit = betting_toplimit
        coin.betting_control = betting_control
        coin.coin_accuracy = coin_accuracy
        coin.is_eth_erc20 = is_eth_erc20
        # coin.is_lock = request.data['is_lock']
        coin.coin_order = int(request.data['coin_order'])
        coin.save()
        coin_value_one = CoinValue.objects.get(coin_id=coin.pk, value_index=1)
        coin_value_one.value = request.data['betting_value_one']
        coin_value_one.save()
        coin_value_two = CoinValue.objects.get(coin_id=coin.pk, value_index=2)
        coin_value_two.value = request.data['betting_value_two']
        coin_value_two.save()
        coin_value_three = CoinValue.objects.get(coin_id=coin.pk, value_index=3)
        coin_value_three.value = request.data['betting_value_three']
        coin_value_three.save()
        reward_coin = RewardCoin.objects.get(coin_id=coin.pk)
        reward_coin.value_ratio = request.data['Integral_proportion']
        reward_coin.save()

        coin_service = CoinOutServiceCharge.objects.get(coin_out_id=coin.pk)
        coin_service.value = request.data['value']
        coin_service.save()
        return JsonResponse({}, status=status.HTTP_200_OK)


class UserLockListView(CreateAPIView, FormatListAPIView):
    """
    锁定列表
    """
    serializer_class = serializers.UserCoinLockSerializer

    def get_queryset(self):
        return UserCoinLock.objects.all()


class UserCoinListView(CreateAPIView, FormatListAPIView):
    """
    用户资产管理
    """
    serializer_class = serializers.UserCoinSerializer

    def get_queryset(self):
        return UserCoin.objects.all()


class UserFilter(filters.FilterSet):
    class Meta:
        model = User
        fields = {
            'username': ['contains'],
        }
        filter_overrides = {
            jsonfield.JSONField: {
                'filter_class': JsonFilter,
            }
        }


class UserListView(backend.ListCreateAPIView):
    serializer_class = serializers.UserSerializer
    queryset = User.objects.all()
    filter_class = UserFilter


class UserListDetailView(DestroyAPIView, FormatRetrieveAPIView, UpdateAPIView):
    serializer_class = serializers.UserSerializer
    queryset = User.objects.all()

    @reversion_Decorator
    def post(self, request, *args, **kwargs):
        id = int(kwargs['pk'])
        user = User.objects.get(pk=id)
        admin = self.request.user
        data = request.data
        user.status = data
        user.save()
        content = {'status': status.HTTP_201_CREATED}
        return HttpResponse(json.dumps(content), content_type='text/json')

    @reversion_Decorator
    def delete(self, request, *args, **kwargs):
        coinlovk_id = self.request.parser_context['kwargs']['pk']
        coinlock = CoinLock.objects.get(pk=coinlovk_id)
        coinlock.is_delete = True
        coinlock.save()
        content = {'status': status.HTTP_200_OK}
        return HttpResponse(json.dumps(content), content_type='text/json')

    @reversion_Decorator
    def update(self, request, *args, **kwargs):
        id = int(kwargs['pk'])
        coins = UserCoin.objects.filter(user_id=id)
        for i in coins:
            coin_name = i.coin.name
            coinname = 'balance-' + coin_name
            coinname = request.data[coinname]
            i.balance = coinname
            i.save()
        users = User.objects.get(pk=id)
        users.nickname = request.data['nickname']
        users.status = request.data['status']
        users.save()
        content = {'status': status.HTTP_200_OK}
        return HttpResponse(json.dumps(content), content_type='text/json')


class LoginView(CreateAPIView):
    """
    后台管理员登录
    """


class CoinDetailView(ListAPIView, DestroyAPIView):
    """
    用户资金明细
    """
    serializer_class = serializers.CoinDetailSerializer

    def get_queryset(self):
        if "uuid" not in self.request.query_params:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        uuid = self.request.query_params.get("uuid")
        query_s = CoinDetail.objects.filter(user_id=uuid, is_delete=0)
        return query_s

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        count_item = results.data.get('count')
        items = results.data.get('results')
        list_t = Coin.objects.filter(admin=1).values('id', 'name').distinct()
        coin_list = {}
        for x in list_t:
            coin_list[x['name']] = x['id']
        return JsonResponse({"results": items, "choice": coin_list, "count": count_item}, status=status.HTTP_200_OK)

    @reversion_Decorator
    def post(self, request, *args, **kwargs):
        coin = int(request.data['coin'])
        options = dict(request.data['options'])
        ratio = request.data['value_ratio']
        for x in options.keys():
            if CoinValue.objects.filter(coin_id=coin, value_index=x).exists():
                return JsonResponse({"ERROR": "CoinValue Index %d Object Exist,You Can Modify It" % x},
                                    status=status.HTTP_400_BAD_REQUEST)
            coin_value = CoinValue()
            coin_value.coin_id = coin
            coin_value.value_index = int(x)
            coin_value.value = options[x]
            coin_value.save()
        if RewardCoin.objects.filter(coin_id=coin).exists():
            return JsonResponse({"ERROR": "RewardCoin Object Exist,You Can Modify It!"},
                                status=status.HTTP_400_BAD_REQUEST)
        reward_coin = RewardCoin()
        reward_coin.coin_id = coin
        reward_coin.admin_id = 1
        reward_coin.value_ratio = int(ratio)
        reward_coin.save()
        return JsonResponse({}, status=status.HTTP_200_OK)

    @reversion_Decorator
    def patch(self, request, *args, **kwargs):
        coin = int(request.data['coin'])
        if not RewardCoin.objects.filter(coin_id=coin).exists() and not CoinValue.objects.filter(coin_id=coin).exists():
            return JsonResponse({"ERROR": "Coin Items Don't Exist,You Need Create It First"},
                                status=status.HTTP_400_BAD_REQUEST)
        for x in request.data.items():
            if x[0] == 'options':
                values = dict(x[1])
                for vv in values.keys():
                    try:
                        coin_value = CoinValue.objects.get(coin_id=coin, value_index=int(vv))
                    except Exception:
                        return JsonResponse({"Error": 'CoinValue对象不存在'}, status=status.HTTP_400_BAD_REQUEST)
                    coin_value.value = values[vv]
                    coin_value.save()
            if x[0] == 'value_ratio':
                try:
                    reward = RewardCoin.objects.get(coin_id=coin)
                except Exception:
                    return JsonResponse({"Error": 'RewardCoin对象不存在'}, status=status.HTTP_400_BAD_REQUEST)
                reward.value_ratio = int(x[1])
                reward.save()
        return JsonResponse({}, status=status.HTTP_200_OK)


# class InviterInfo(RetrieveAPIView):
#     """
#     推荐人信息
#     """
#
#     def retrieve(self, request, *args, **kwargs):
#         username = request.query_params.get('username')
#         try:
#             record = LoginRecord.objects.filter(user__username=username).order_by('-login_time')[0]
#         except Exception:
#             return JsonResponse({'Error': '用户不存在或参数username未提供'}, status=status.HTTP_400_BAD_REQUEST)
#         rc = serializers.InviterInfoSerializer(record)
#         return JsonResponse({'results': rc.data}, status=status.HTTP_200_OK)


class UserAllView(FormatListAPIView):
    """
    所有用户资产表
    """

    # queryset = User.objects.filter(is_robot=0).order_by('-id')
    # serializer_class = serializers.UserAllSerializer
    # filter_backends = [DjangoFilterBackend]
    # filter_fields = ['id', 'username', 'is_block']

    def list(self, request, *args, **kwargs):
        id = request.GET.get('id', '')
        username = request.GET.get('username__contains', '')
        is_block = request.GET.get('is_block', '')
        page_size = 10
        page = request.GET.get('page', '')

        sql = "select count(id) from users_user where is_robot=0"
        if id != '':
            sql += ' and id = ' + str(id)
        if username != '':
            sql += ' and instr(username,' + str(username) + ') > 0'
        if is_block != '':
            sql += ' and is_block = ' + str(is_block)
        dt_all = get_sql(sql)
        total = dt_all[0][0] if dt_all[0][0] else 0
        if total == 0:
            return JsonResponse({'total': 0, 'results': []}, status=status.HTTP_200_OK)

        pages = int(total / page_size)
        if total % page_size != 0:
            pages = pages + 1
        if page == '':
            page = 1
        else:
            page = int(page)
        if page <= 0:
            page = 1
        if page > pages:
            page = pages
        start = page - 1

        sql = "select id from users_user where is_robot=0"
        if id != '':
            sql += ' and id = ' + str(id)
        if username != '':
            sql += ' and instr(username,' + str(username) + ') > 0'
        if is_block != '':
            sql += ' and is_block = ' + str(is_block)
        sql += ' order by id desc'
        sql += ' limit ' + str(start * page_size) + ', ' + str(page_size)
        user_all = get_sql(sql)
        userall = []
        for x in user_all:
            userall.append(str(x[0]))
        users = '(' + ','.join(userall) + ')'

        sql = "select a.id, a.telephone, a.nickname, a.created_at , c.login_time, a.ip_address, d.ip as login_address, i.integral, h.nickname as inviter, e.inviter_id, f.inviter_new,a.status, a.is_block, ip_count"
        sql += " from users_user a  "
        sql += " left join (select  user_id,max(login_time) as login_time from users_loginrecord where user_id in " + users + " group by user_id) c on a.id=c.user_id"
        sql += " left join users_loginrecord d on d.user_id = a.id and d.login_time = c.login_time"
        sql += " left join ((select  invitee_one as idd ,inviter_id from users_userinvitation a where invitee_one in " + users + ")"
        sql += " union (select  invitee as idd,inviter_id from users_intinvitation a where invitee in " + users + " )) e on e.idd =a.id "
        sql += " left join ((select  inviter_id ,count(id)  as inviter_new from users_userinvitation where inviter_id in " + users + " group by inviter_id)"
        sql += " union (select  inviter_id,count(id)  as inviter_new from users_intinvitation where inviter_id in " + users + " group by inviter_id)) f on f.inviter_id=a.id"
        sql += " left join(select b.id, count(a.ip_address) as ip_count from users_user a join (select  ip_address, id from users_user where id in " + users + ") b on a.ip_address=b.ip_address group by b.id) g on g.id=a.id"
        sql += " left join users_user h on h.id=e.inviter_id"
        sql += " left join (select user_id, balance as integral from users_usercoin where coin_id = 6) i on i.user_id = a.id"
        sql += " where a.id in " + users
        sql += " order by id desc"
        dt_all = get_sql(sql)
        # fields = (
        #     'id', 'telephone', 'nickname', 'created_at', 'login_time', 'ip_address', 'login_address', 'integral',
        #     'inviter', 'inviter_id', 'invite_new', 'status', 'is_block', 'ip_count')
        data = []
        for x in dt_all:
            temp_dict = {
                'id': x[0],
                'telephone': x[1],
                'nickname': x[2],
                'created_at': x[3].strftime('%Y-%m-%d %H:%M:%S'),
                'login_time': x[4].strftime('%Y-%m-%d %H:%M:%S') if x[4] else '',
                'ip_address': x[5] if x[5] else '',
                'login_address': x[6] if x[6] else '',
                'integral': float(normalize_fraction(x[7], 6)) if x[7] else 0,
                'inviter': x[8] if x[8] else '',
                'inviter_id': x[9] if x[9] else '',
                'inviter_new': x[10] if x[10] else 0,
                'status': x[11],
                'is_block': x[12],
                'ip_count': x[13]
            }

            data.append(temp_dict)
        return JsonResponse({'total': total, 'results': data}, status=status.HTTP_200_OK)

    #     sql = 'select a.id, a.telephone, a.nickname, a.created_at, a.ip_address, b.ip, max(b.login_time), integral,'
    #     sql += ' c.inviter, c.inviter_id, count(c.inviter_id) as invite_new,status,is_block,ip_count'

    # def list(self, request, *args, **kwargs):
    #     results = super().list(request, *args, **kwargs)
    #     total = results.comment.get('pagination')
    #     print(total)
    #     return JsonResponse({'count': total['total'], 'results': results.data.get('list')},
    #                         status=status.HTTP_200_OK)


class UserAllDetailView(RetrieveUpdateDestroyAPIView):
    """
    推荐人信息
    """

    def retrieve(self, request, *args, **kwargs):
        uuid = self.kwargs['pk']
        try:
            user = User.objects.get(pk=uuid)
        except Exception:
            return JsonResponse({'Error': '用户不存在'}, status=status.HTTP_400_BAD_REQUEST)
        rc = serializers.UserAllSerializer(user)
        return JsonResponse({'results': [rc.data]}, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        uuid = self.kwargs['pk']
        is_block = request.data.get('title')
        try:
            user = User.objects.get(pk=uuid)
        except Exception:
            return JsonResponse({'Error': '用户不存在'}, status=status.HTTP_400_BAD_REQUEST)
        user.is_block = int(is_block)
        user.save()
        return JsonResponse({}, status=status.HTTP_200_OK)


class InviteNewView(ListAPIView):
    """
    邀请好友数
    """
    serializer_class = serializers.UserAllSerializer

    def get_queryset(self):
        uuid = int(self.kwargs['pk'])
        inviter = UserInvitation.objects.filter(inviter_id=uuid)
        user_id1 = inviter.values_list('invitee_one')
        user_id2 = inviter.values_list('invitee_two')
        invitee = IntInvitation.objects.filter(inviter_id=uuid).values_list('invitee')
        users = []
        if inviter.exists():
            for x in list(user_id1):
                if x[0] != 0:
                    users.append(int(x[0]))
            for x in list(user_id2):
                if x[0] != 0:
                    users.append(int(x[0]))
        if len(user_id1) == 0 and len(user_id2 == 0):
            if len(invitee) != 0:
                for x in invitee:
                    users.append(int(x[0]))
        user_group = User.objects.filter(pk__in=users)
        return user_group


class CoinPresentView(ListAPIView):
    """
    提现记录表
    """
    queryset = UserPresentation.objects.all().order_by('-created_at')
    serializer_class = PresentationSerialize
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['user', 'status', 'coin']


class CoinPresentCheckView(RetrieveUpdateAPIView):
    """
    提现审核
    """

    @reversion_Decorator
    def patch(self, request, *args, **kwargs):
        id = kwargs['pk']  # 提现记录id

        if 'status' not in request.data \
                and 'text' not in request.data \
                and 'is_bill' not in request.data \
                and 'txid' not in request.data \
                and 'language' not in request.data:
            return JsonResponse({'Error': '请传递参数'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            item = UserPresentation.objects.get(pk=id)
        except Exception:
            return JsonResponse({'Error': 'Instance Not Exist'}, status=status.HTTP_400_BAD_REQUEST)
        if 'status' in request.data:
            sts = int(request.data.get('status'))
            item.status = sts
            if sts == 2:
                try:
                    user_coin = UserCoin.objects.get(user=item.user, coin=item.coin)
                    coin_out = CoinOutServiceCharge.objects.get(coin_out=user_coin.coin)
                except Exception:
                    raise
                if user_coin.coin.name == 'HAND':
                    try:
                        eth_coin = UserCoin.objects.get(user=item.user, coin__name='ETH')
                    except Exception:
                        raise
                    eth_coin.balance += coin_out.value
                    eth_coin.save()
                    user_coin.balance += item.amount
                else:
                    user_coin.balance = user_coin.balance + item.amount + coin_out.value
                user_coin.save()
                coin_detail = CoinDetail()
                coin_detail.user = user_coin.user
                coin_detail.name = user_coin.coin.name
                coin_detail.amount = item.amount
                coin_detail.rest = user_coin.balance
                coin_detail.sources = CoinDetail.RETURN
                coin_detail.save()
                if 'text' in request.data:
                    text = request.data.get('text')
                    language = request.data.get('language', '')
                    item.feedback = text
                    user_message = UserMessage()
                    user_message.status = 0
                    if language == 'en':
                        user_message.content = 'Reason for:' + item.feedback
                        user_message.title = 'Present Reject'
                    else:
                        user_message.content = '拒绝提现理由:' + item.feedback
                        user_message.title = '提现失败公告'
                    user_message.user = item.user
                    user_message.message_id = 6  # 修改密码
                    user_message.save()
        if 'is_bill' in request.data:
            bill = request.data.get('is_bill')
            item.is_bill = bill
        if 'txid' in request.data:
            language = request.data.get('language', '')
            txid = request.data.get('txid')
            item.txid = txid
            user_message = UserMessage()
            user_message.status = 0
            if language == 'en':
                user_message.content = 'TXID:' + item.txid
                user_message.title = 'Present Success'
            else:
                user_message.content = 'TXID:' + item.txid
                user_message.title = '提现成功公告'
            user_message.user = item.user
            user_message.message_id = 6  # 修改密码
            user_message.save()
        print(item.txid)
        item.save()

        return JsonResponse({}, status=status.HTTP_200_OK)


class RechargeView(ListAPIView):
    """
    用户充值记录
    """
    #
    serializer_class = serializers.CoinDetailSerializer

    def get_queryset(self):
        pk = int(self.kwargs['pk'])
        coin_name = self.kwargs['coin_name']
        details = CoinDetail.objects.filter(user_id=pk, sources=CoinDetail.RECHARGE, coin_name=coin_name)
        return details


class RechargeAllView(ListAPIView):
    """
    所有用户充值记录
    """
    queryset = UserRecharge.objects.filter(user__is_robot=0).order_by('-created_at')
    serializer_class = serializers.UserRechargeSerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['user', 'coin']


# class RechargeAllDetailView(ListAPIView):
#     """
#     用户充值记录
#     """
#     serializer_class = serializers.UserRechargeSerializer
#
#     def get_queryset(self):
#         pk = self.kwargs['pk']
#         recharges=UserRecharge.objects.filter(user_id=pk)
#         return recharges


class GSGBackendView(ListAPIView):
    """
    用户GSG明细
    """
    serializer_class = serializers.CoinDetailSerializer

    def get_queryset(self):
        pk = int(self.kwargs['pk'])
        details = CoinDetail.objects.filter(user_id=pk, coin_name='GSG')
        return details


class CoinBackendDetail(ListAPIView):
    """
    用户资产情况
    """
    serializer_class = serializers.CoinBackendDetailSerializer

    def get_queryset(self):
        uuid = int(self.kwargs['pk'])
        user_coin = UserCoin.objects.filter(user_id=uuid)
        return user_coin


class RewardBackendDetail(ListAPIView):
    """
    系统奖励及其他
    """
    serializer_class = serializers.CoinDetailSerializer

    def get_queryset(self):
        pk = int(self.kwargs['pk'])
        coin_name = self.kwargs['coin_name']
        details = CoinDetail.objects.filter(~Q(coin_name='GSG'), ~Q(
            sources__in=[CoinDetail.RECHARGE, CoinDetail.REALISATION, CoinDetail.BETS]), user_id=pk,
                                            coin_name=coin_name)
        return details


class CoinPresentDetailView(ListAPIView):
    """
    提现列表--用户管理内
    """
    serializer_class = PresentationSerialize

    def get_queryset(self):
        pk = self.kwargs['pk']
        coin = int(self.kwargs['coin'])
        presents = UserPresentation.objects.filter(user_id=pk, coin_id=coin)
        return presents


class RunningView(ListAPIView):
    """
    运营数据统计
    """

    def ts_null_2_zero(self, item):
        if item == None:
            return 0
        else:
            return float(normalize_fraction(item, 4))

    def list(self, request, *args, **kwargs):
        # 筛选出有效用户数
        sql = "select a.id from users_user a"
        sql += " inner join (select ip_address, count(username) as count from users_user group by ip_address) b on a.ip_address=b.ip_address"
        sql += " where b.count <=3 "
        sql += " and is_robot=0 and is_block=0"
        dt_all = list(get_sql(sql))

        sql = "select distinct(user_id) from users_userrecharge"
        dt_recharge = list(get_sql(sql))

        dt_all = list(set(dt_all + dt_recharge))
        dd = []
        for x in dt_all:
            dd.append(x[0])
        users = tuple(dd)
        data = {'user_effect': len(users)}  # 有效注册用户
        # --------------------------------
        # 总注册用户
        sql = "select count(id) from users_user "
        sql += " where is_robot=0"
        dt_all = get_sql(sql)
        data['user_all'] = dt_all[0][0] if dt_all[0][0] else 0

        # ---------------------------------
        # 计算充值人数
        sql = "select count(distinct(a.user_id)) from users_userrecharge a"
        sql += " inner join users_user b on b.id = a.user_id"
        sql += " where b.is_robot=0"
        sql += " and a.confirmations > 0"
        dt_all = get_sql(sql)
        data['recharge_all'] = dt_all[0][0] if dt_all[0][0] else 0

        # ---------------------------------
        # 计算提现人数
        # sql = "select count(distinct(a.user_id)) from users_userpresentation a"
        # sql += " inner join users_user b on b.id = a.user_id"
        # sql += " where b.is_robot=0"
        # sql += " and a.status = 1"
        # dt_all = get_sql(sql)
        # data['recharge_all'] = dt_all[0][0] if dt_all[0][0] else 0

        # ---------------------------------
        # 计算GSG总数
        sql = "select sources, sum(amount) from users_coindetail a"
        sql += " where user_id in " + str(users)
        sql += " and coin_name = 'GSG'"
        sql += " and sources in " + str((CoinDetail.OTHER, CoinDetail.CASHBACK))
        sql += " group by sources order by sources"
        dt_all = get_sql(sql)
        data['sig_gsg'] = float(normalize_fraction(dt_all[0][1] if dt_all[0][1] else 0, 8))
        data['back_gsg'] = float(normalize_fraction(dt_all[1][1] if dt_all[1][1] else 0, 8))

        sql = "select sum(amount) from users_coindetail a"
        sql += " where user_id in " + str(users)
        sql += " and coin_name = 'GSG'"
        sql += " and sources = " + str(CoinDetail.ACTIVITY)
        sql_gt_0 = " and amount > 0"
        sql_lt_0 = " and amount < 0"
        dt_gt_0 = get_sql(sql + sql_gt_0)
        dt_lt_0 = get_sql(sql + sql_lt_0)
        data['activity_out'] = dt_gt_0[0][0] if dt_gt_0[0][0] else 0
        data['activity_in'] = dt_lt_0[0][0] if dt_lt_0[0][0] else 0

        sql = "select sum(balance) from users_usercoin"
        sql += " where user_id in " + str(users)
        sql += " and coin_id=6"
        dt_all = get_sql(sql)
        data['integral_all'] = float(normalize_fraction(dt_all[0][0] if dt_all[0][0] else 0, 8))
        data['now_time'] = datetime.now().strftime('%Y年%m月%d日')

        return JsonResponse({'results': data}, status=status.HTTP_200_OK)


class ClubSts(ListAPIView):
    """
    各俱乐部
    """

    def count_earn_coin(self, usdt, number):
        """
        计算赠送币的人数
        :return:
        """
        count_user = usdt.filter(lock_coin__gte=number).count()
        return count_user

    def ts_null_2_zero(self, item):
        if item == None:
            return 0
        else:
            return float(normalize_fraction(item, 8))

    # from silk.profiling.profiler import silk_profile
    # @silk_profile()
    def list(self, request, *args, **kwargs):

        cursor = connection.cursor()
        sql = "select a.id from users_user a"
        sql += " inner join (select ip_address, count(username) as count from users_user group by ip_address) b on a.ip_address=b.ip_address"
        sql += " where b.count <=3 "
        sql += " and is_robot=0 and is_block=0"
        sql += " union "
        sql += " select a.user_id as id from users_userrecharge a "
        sql += " join users_user b on a.user_id=b.id"
        sql += " where b.is_robot=0"
        vsql = sql

        club = kwargs['r_id']
        data = []
        # clubs = Club.objects.all().select_related('coin').values('id', 'coin_id', 'coin__name')
        temp_dict = {}
        try:
            room = Club.objects.get(id=club)
        except Exception:
            return JsonResponse({'Error': '币种俱乐部%s不存在' % room.name}, status=status.HTTP_400_BAD_REQUEST)
        r_id = room.id
        coin_id = room.coin_id
        # records = Record.objects.filter(~Q(source=Record.CONSOLE), roomquiz_id=r_id)
        temp_dict['coin_name'] = room.coin.name
        # -----------------------------------------------------------------------------------
        #         #已结算下注额
        sql_q = "select id from quiz_quiz where status=5"
        all_quiz = get_sql(sql_q)
        if len(all_quiz) == 0:
            quizs = '(0)'
        else:
            quiz_all = []
            for x in all_quiz:
                quiz_all.append(str(x[0]))
            quizs = '(' + ','.join(quiz_all) + ')'

        sql = "select sum(a.bet) from quiz_record a"
        # sql += " inner join quiz_quiz b on a.quiz_id=b.id"
        sql += " inner join (" + vsql + ") c on c.id=a.user_id"
        # sql += " inner join ("+sql_q+ ") d on d.id=a.quiz_id"
        sql += " where a.source in (" + str(Record.NORMAL) + ',' + str(Record.GIVE) + ')'
        # sql += " and a.user_id in " + str(users)
        sql += " and a.quiz_id in " + quizs
        sql += " and a.roomquiz_id= " + str(r_id)

        cursor.execute(sql, None)
        dt_all = cursor.fetchall()
        bet_total = dt_all[0][0] if dt_all[0][0] else 0
        temp_dict['bet_end'] = self.ts_null_2_zero(bet_total)
        # temp_dict['bet'] = self.ts_null_2_zero(records.values('bet').aggregate(Sum('bet'))['bet__sum'])
        # temp_dict['out'] = self.ts_null_2_zero(
        #     records.filter(quiz__status=5, earn_coin__gte=0).annotate(
        #         hand_o=F('bet') * (F('odds') - 1)).aggregate(Sum('hand_o'))['hand_o__sum'])

        # -----------------------------------------------------------------------------------
        # 计算用户净放发

        sql = "select sum(earn_coin) from quiz_record a"
        sql += " inner join (" + vsql + ") c on c.id=a.user_id"
        sql += " where a.source in (" + str(Record.NORMAL) + ',' + str(Record.GIVE) + ')'
        # sql += " and user_id in " + str(users)
        sql += " and roomquiz_id= " + str(r_id)
        sql += " and earn_coin > 0"
        cursor.execute(sql, None)
        dt_all = cursor.fetchall()
        bet_total = dt_all[0][0] if dt_all[0][0] else 0
        temp_dict['out'] = self.ts_null_2_zero(bet_total)
        # -----------------------------------------------------------------------------------
        # # 计算用户收入
        # sql = "select sum(bet) from quiz_record "
        # sql += "where source <> " + str(Record.CONSOLE)
        # sql += " and roomquiz_id= " + str(r_id) + " and earn_coin < 0"
        # cursor.execute(sql, None)
        # dt_all = cursor.fetchall()
        # bet_total = dt_all[0][0] if dt_all[0][0] else 0
        # temp_dict['in'] = self.ts_null_2_zero(bet_total)
        # temp_dict['in'] = \
        #     self.ts_null_2_zero(
        #         records.filter(quiz__status=5, earn_coin__lt=0).aggregate(Sum('bet'))['bet__sum'])
        temp_dict['earn'] = self.ts_null_2_zero(normalize_fraction(temp_dict['bet_end'] - temp_dict['out'], 8))
        # temp_dict['bet_not_begin'] = self.ts_null_2_zero(
        #     records.filter(~Q(quiz__status=5)).aggregate(Sum('bet'))['bet__sum'])
        # -----------------------------------------------------------------------------------
        # 未结算下注额
        # sql = "select sum(bet) from quiz_record a"
        # sql += " inner join quiz_quiz b on a.quiz_id=b.id"
        # sql += " where roomquiz_id= " + str(r_id)
        # sql += " and a.source <> " + str(Record.CONSOLE)
        # sql += " and  b.status<> 5"
        # cursor.execute(sql, None)
        # dt_all = cursor.fetchall()
        # bet_total = dt_all[0][0] if dt_all[0][0] else 0
        # temp_dict['bet_not_begin'] = self.ts_null_2_zero(bet_total)
        # temp_dict['bet_user_sum'] = records.values('user_id').distinct().count()
        # 计算下注用户数
        # -----------------------------------------------------------------------------------
        sql = "select count(distinct(user_id)), count(a.id) from quiz_record a "
        sql += " inner join (" + vsql + ") c on c.id=a.user_id"
        sql += " where a.source in (" + str(Record.NORMAL) + ',' + str(Record.GIVE) + ')'
        # sql += " and a.user_id in " + str(users)
        sql += " and roomquiz_id= " + str(r_id)
        cursor.execute(sql, None)
        dt_all = cursor.fetchall()
        bet_total = dt_all[0][0] if dt_all[0][0] else 0
        bet_times = dt_all[0][1] if dt_all[0][1] else 0
        temp_dict['bet_user_sum'] = bet_total
        temp_dict['bet_times'] = bet_times
        # -----------------------------------------------------------------------------------
        # 下注次数
        # sql = "select count(a.id) from quiz_record a"
        # sql += " where a.source <> " + str(Record.CONSOLE)
        # sql += " and user_id in " + str(users)
        # sql += " and roomquiz_id= " + str(r_id)
        # cursor.execute(sql, None)
        # dt_all = cursor.fetchall()
        # bet_total = dt_all[0][0] if dt_all[0][0] else 0
        # temp_dict['bet_times'] = bet_total
        # temp_dict['bet_times'] = records.count()
        # -----------------------------------------------------------------------------------
        # 计算总余额
        sql = "select sum(a.balance) from users_usercoin a"
        sql += " inner join (" + vsql + ") c on c.id=a.user_id"
        # sql += " where user_id in " + str(users)
        sql += " where  coin_id=" + str(coin_id)
        cursor.execute(sql, None)
        dt_all = cursor.fetchall()
        bet_total = dt_all[0][0] if dt_all[0][0] else 0
        temp_dict['rest'] = self.ts_null_2_zero(bet_total)

        # temp_dict['rest'] = self.ts_null_2_zero(user_coin.aggregate(Sum('balance'))['balance__sum'])
        # -----------------------------------------------------------------------------------
        # 计算余额大于0用户数
        # sql = "select count(a.user_id) from users_usercoin a"
        # sql += " inner join users_user b on a.user_id=b.id"
        # sql += " where b.is_robot= 0"
        # sql += " and  a.balance > 0"
        # sql += " and  coin_id=" + str(coin_id)
        # cursor.execute(sql, None)
        # dt_all = cursor.fetchall()
        # bet_total = dt_all[0][0] if dt_all[0][0] else 0
        # temp_dict['rest_gt_0'] = self.ts_null_2_zero(bet_total)
        # temp_dict['rest_gt_0'] = user_coin.filter(balance__gt=0).values('id').count()
        # -----------------------------------------------------------------------------------
        # user_coin = UserCoin.objects.filter(user__is_robot=0, coin_id=coin_id)
        # sql = "select count(a.user_id) from users_usercoin a"
        # sql += " inner join users_user b on a.user_id=b.id"
        # sql += " where b.is_robot= 0"
        # sql += " and  a.balance = 0"
        # sql += " and  coin_id=" + str(coin_id)
        # cursor.execute(sql, None)
        # dt_all = cursor.fetchall()
        # bet_total = dt_all[0][0] if dt_all[0][0] else 0
        # temp_dict['rest_eq_0'] = self.ts_null_2_zero(bet_total)
        # -----------------------------------------------------------------------------------
        # temp_dict['rest_eq_0'] = user_coin.filter(balance=0).values('id').count()
        # recharge = UserRecharge.objects.select_related().filter(user__is_robot=0, coin_id=coin_id)
        # temp_dict['recharge_num'] = recharge.count()
        # temp_dict['recharge_user_num'] = recharge.values('user_id').distinct().count()
        # temp_dict['recharge_amount'] = self.ts_null_2_zero(recharge.aggregate(Sum('amount'))['amount__sum'])

        sql = "select sum(a.amount), count(distinct(a.user_id)), count(a.user_id) from users_userrecharge a"
        sql += " inner join users_user b on b.id = a.user_id"
        sql += " where b.is_robot=0 and b.is_block=0"
        sql += " and coin_id = " + str(coin_id)
        dt_all = get_sql(sql)
        recharge_amount = dt_all[0][0] if dt_all[0][0] else 0
        recharge_user_num = dt_all[0][1] if dt_all[0][1] else 0
        recharge_num = dt_all[0][2] if dt_all[0][2] else 0
        temp_dict['recharge_num'] = recharge_num
        temp_dict['recharge_user_num'] = recharge_user_num
        temp_dict['recharge_amount'] = self.ts_null_2_zero(recharge_amount)
        if coin_id != 9:
            temp_dict['wallet'] = temp_dict['recharge_amount']
        else:
            temp_dict['wallet'] = self.ts_null_2_zero(temp_dict['recharge_amount'] - 14537.66)  # 钱包里直接扣的，需减去

        #
        # present = UserPresentation.objects.select_related().filter(user__is_robot=0, coin_id=coin_id)
        # temp_dict['present_user_num'] = present.values('user_id').distinct().count()
        # temp_dict['present_amount'] = self.ts_null_2_zero(present.aggregate(Sum('amount'))['amount__sum'])
        # temp_dict['present_num'] = present.count()
        # temp_dict['present_success_num'] = present.select_related().filter(status=1).values('id').count()

        sql = "select sum(a.amount), count(distinct(a.user_id)), count(a.user_id) from users_userpresentation a"
        sql += " inner join users_user b on b.id = a.user_id"
        sql += " where b.is_robot=0"
        sql += " and a.coin_id = " + str(coin_id)
        sql += " and a.status = 1"
        dt_all = get_sql(sql)
        present_amount = dt_all[0][0] if dt_all[0][0] else 0
        present_user_num = dt_all[0][1] if dt_all[0][1] else 0
        present_num = dt_all[0][2] if dt_all[0][2] else 0
        temp_dict['present_user_num'] = present_user_num
        temp_dict['present_amount'] = self.ts_null_2_zero(present_amount)
        temp_dict['present_num'] = present_num
        # if room.coin.name == 'USDT':
        #     usdt = CoinGiveRecords.objects.select_related().all()
        #     temp_dict['rest_gte_10'] = self.count_earn_coin(usdt, 10)
        #     temp_dict['rest_gte_20'] = self.count_earn_coin(usdt, 20)
        #     temp_dict['rest_gte_30'] = self.count_earn_coin(usdt, 30)
        #     temp_dict['rest_gte_40'] = self.count_earn_coin(usdt, 40)
        #     temp_dict['rest_gte_50'] = self.count_earn_coin(usdt, 50)
        #     temp_dict['rest_gte_60'] = self.count_earn_coin(usdt, 60)
        # import csv
        # date_x = datetime.now().strftime('%Y%m%d')
        # save_file = '/home/zhijiefong/sts/' + date_x + 'clubsts.csv'
        # is_exist = os.path.exists(save_file)
        # with open(save_file, 'a') as hf:
        #     writer = csv.DictWriter(hf, temp_dict.keys())
        #     if not is_exist:
        #         writer.writeheader()
        #     writer.writerow(temp_dict)
        data.append(temp_dict)
        return JsonResponse({'data': data})


class LoginRateView(ListAPIView):
    """
    用户留存率
    """

    def list(self, request, *args, **kwargs):
        user_register = User.objects.filter(is_robot=0)
        register_num = user_register.count()
        logins = LoginRecord.objects.filter(user__is_robot=0).extra(select={'date': 'date(login_time)'}).values(
            'user_id', 'date', 'user__source').distinct().values('date', 'user__source').annotate(
            Count('user__source')).order_by('date')
        temp_dict = {}
        for x in logins:
            date = x['date'].strftime('%m/%d')
            source_index = x['user__source']
            for i in User.SOURCE_CHOICE:
                if int(source_index) == i[0]:
                    source = i[1]
            if source != '':
                if date not in temp_dict:
                    temp_dict[date] = {
                        source: 0 if register_num == 0 else round(100 * x['user__source__count'] / register_num, 2)
                    }
                else:
                    temp_dict[date][source] = 0 if register_num == 0 else round(
                        100 * x['user__source__count'] / register_num, 2)
        data = []
        for k in temp_dict:
            vv = {'Date': k}
            for j in temp_dict[k]:
                vv[j] = temp_dict[k][j]
            data.append(vv)
        return JsonResponse({'results': data}, status=status.HTTP_200_OK)


class UserSts(ListAPIView):
    """
    用户数据统计
    """

    # def list(self, request, *args, **kwargs):
    #     new_register = User.objects.filter(is_robot=0).extra(select={'date': 'date(created_at)'}).values(
    #         'date').annotate(
    #         register_count=Count('id')).order_by('date')
    #     activy_user = LoginRecord.objects.annotate(date=Func(F('login_time'), function='date')).filter(
    #         ~Q(user__created_at__date__contains=F('date')), user__is_robot=0).values('date').annotate(
    #         activy_count=Count('user_id', distinct=True)).order_by('date')
    #     records = Record.objects.filter(source__in=[Record.NORMAL, Record.GIVE]).extra(
    #         select={'date': 'date(created_at)'}).values('date')
    #     bet_user = records.annotate(user_count=Count('user_id', distinct=True)).order_by('date')
    #     total = 0
    #     data = []
    #     activy_list = [it for it in activy_user]
    #     activy_list = [{'date': datetime.strptime('2018-5-28', '%Y-%m-%d').date(), 'activy_count': 0}] + activy_list
    #     # activy.insert({'date': datetime.strptime('2018-5-28', '%Y-%m-%d').date(), 'activy_count':0})
    #     # print('aaaaaaaaaaaaa',activy)
    #     if len(new_register) == len(activy_list) == len(bet_user):
    #         for x, y, z in zip(new_register, activy_list, bet_user):
    #             if x['date'] == y['date'] == z['date']:
    #                 date = x['date'].strftime('%m/%d')
    #                 total += x['register_count']
    #                 unbet = total - z['user_count']
    #                 temp_dict = {
    #                     'date': date,
    #                     '新增账号': x['register_count'],
    #                     '每日活跃': y['activy_count'],
    #                     '有投注用户': z['user_count'],
    #                     '未投注用户': unbet
    #                 }
    #                 data.append(temp_dict)
    #             else:
    #                 return JsonResponse({'Error': '日期需按同一顺序列表'}, status=status.HTTP_400_BAD_REQUEST)
    #     else:
    #         return JsonResponse({'Error': '缺少天数'}, status=status.HTTP_400_BAD_REQUEST)
    def list(self, request, *args, **kwargs):

        sql = "select a.id from users_user a"
        sql += " inner join (select ip_address, count(username) as count from users_user group by ip_address) b on a.ip_address=b.ip_address"
        sql += " where b.count <=3 "
        sql += " and is_robot=0 and is_block=0"
        dt_all = list(get_sql(sql))

        sql = "select distinct(user_id) from users_userrecharge"
        dt_recharge = list(get_sql(sql))

        dt_all = list(set(dt_all + dt_recharge))
        dd = []
        for x in dt_all:
            dd.append(x[0])
        users = tuple(dd)

        new_register = User.objects.filter(is_robot=0, is_block=0).extra(select={'date': 'date(created_at)'}).values(
            'date').annotate(
            date_sum=Count('ip_address', distinct=True)).order_by('date')
        activy_user = LoginRecord.objects.annotate(date=Func(F('login_time'), function='date')).filter(
            ~Q(user__created_at__date__contains=F('date')), user__is_robot=0, user__is_block=0,
            user_id__in=users).values('date').annotate(
            date_sum=Count('ip', distinct=True)).order_by('date')
        presents = UserPresentation.objects.all().filter(status=1).extra(select={'date': 'date(created_at)'}).values(
            'date').annotate(
            date_sum=Count('user_id', distinct=True)).order_by('date')
        recharge = UserRecharge.objects.all().extra(select={'date': 'date(created_at)'}).values('date').annotate(
            date_sum=Count('user_id', distinct=True)).order_by('date')
        recharge_times = UserRecharge.objects.all().extra(select={'date': 'date(created_at)'}).values('date').annotate(
            date_sum=Count('id')).order_by('date')
        recharge_register = UserRecharge.objects.all().annotate(
            date=Func(F('user__created_at'), function='date')).filter(
            created_at__date=F('date')).values('date').annotate(date_sum=Count('user_id', distinct=True)).order_by(
            'date')
        items = {
            'new_register': new_register,
            'activy_user': activy_user,
            'presents': presents,
            'recharge': recharge,
            'recharge_times': recharge_times,
            'recharge_register': recharge_register
        }
        data = []
        # if club_room ==2:
        #     print(coin_out ,'|', coin_in ,'|', bet_user,'|', bet_times,'|', bet_sum)
        min_date = date(2099, 1, 1)
        max_date = date(1970, 1, 1)
        for x in items:
            if len(items[x]) > 0:
                items[x] = [n for n in items[x]]
                if items[x][0]['date'] < min_date:
                    min_date = items[x][0]['date']
                if items[x][-1]['date'] > max_date:
                    max_date = items[x][-1]['date']
        if min_date == date(2099, 1, 1) or max_date == date(1970, 1, 1):
            return JsonResponse({'results': []}, status=status.HTTP_200_OK)
        delta = (max_date - min_date).days
        for x in range(delta + 1):
            for v in items:
                date_now = min_date + timedelta(x)
                if len(items[v]) == 0:
                    items[v] = [{'date': date_now, 'date_sum': 0}]
                if items[v][-1]['date'] > date_now:
                    if items[v][x]['date'] != date_now:
                        items[v].insert(x, {'date': date_now, 'date_sum': 0})
                if items[v][-1]['date'] < date_now:
                    items[v].append({'date': date_now, 'date_sum': 0})
        for a, b, c, d, e, f in zip(*list(items.values())):
            temp_dict = {
                'date': a['date'].strftime('%m/%d'),
                '新增有效用户数': float(a['date_sum']),
                '活跃用户': float(b['date_sum']),
                '提现人数': float(c['date_sum']),
                '充值人数': float(d['date_sum']),
                '充值人次': float(e['date_sum']),
                '新用户充值': float(f['date_sum'])
            }
            data.append(temp_dict)
        # import csv
        # date_x = datetime.now().strftime('%Y%m%d')
        # save_file = '/home/zhijiefong/sts/' + date_x + 'user.csv'
        # is_exist = os.path.exists(save_file)
        # with open(save_file, 'a') as hf:
        #     writer = csv.DictWriter(hf, data[0].keys())
        #     if not is_exist:
        #         writer.writeheader()
        #     for info in data:
        #         writer.writerow(info)

        return JsonResponse({'results': data}, status=status.HTTP_200_OK)

        # data = []
        # for x in obj_s:
        #     date = x['date'].strftime('%m/%d')
        #     temp_dict = {
        #         'date': date,
        #         'total_count': x['total_count']
        #     }
        #     data.append(temp_dict)


class CoinSts(ListAPIView):
    """
    币统计
    """

    # def compute(self, a, b):
    #     return a * (b - 1)

    def list(self, request, *args, **kwargs):
        club_room = kwargs['club_room']
        try:
            club = Club.objects.get(id=club_room)
        except Exception:
            return JsonResponse({'Error': '俱乐部不存在'}, status=status.HTTP_400_BAD_REQUEST)
        coin_name = club.coin.name
        sql = "select a.id from users_user a"
        sql += " inner join (select ip_address, count(username) as count from users_user group by ip_address) b on a.ip_address=b.ip_address"
        sql += " where b.count <=3 "
        sql += " and is_robot=0 and is_block=0"
        dt_all = list(get_sql(sql))

        sql = "select distinct(user_id) from users_userrecharge"
        dt_recharge = list(get_sql(sql))

        dt_all = list(set(dt_all + dt_recharge))
        dd = []
        for x in dt_all:
            dd.append(str(x[0]))
        users = '(' + ','.join(dd) + ')'

        sql = "select date(b.begin_at) as day, sum(a.bet), count(distinct(a.user_id)), count(a.user_id) from quiz_record a"
        sql += " inner join quiz_quiz b on a.quiz_id=b.id"
        sql += " inner join users_user c on c.id = a.user_id"
        sql += " where b.status=5 and a.source in (" + str(Record.NORMAL) + ',' + str(Record.GIVE) + ')'
        sql += " and c.is_block=0 and user_id in " + str(users)
        sql += " and roomquiz_id = " + str(club.id)
        sql += " group by day order by day"
        dt_sum = get_sql(sql)
        if len(dt_sum) == 0:
            return JsonResponse({'coin_name': coin_name, 'results': []}, status=status.HTTP_200_OK)

        sql = "select date(b.begin_at) as day, sum(earn_coin) from quiz_record a"
        sql += " inner join quiz_quiz b on a.quiz_id=b.id"
        sql += " inner join users_user c on c.id = a.user_id"
        sql += " where b.status=5 and a.source in (" + str(Record.NORMAL) + ',' + str(Record.GIVE) + ')'
        sql += " and c.is_block=0 and user_id in " + str(users)
        sql += " and roomquiz_id = " + str(club.id)
        sql += " and earn_coin > 0"
        sql += " group by day order by day"
        dt_earn = get_sql(sql)

        sql = 'select date(a.created_at) as day, sum(a.amount) as amount from users_userrecharge a'
        sql += ' inner join users_user b on b.id=a.user_id'
        sql += ' where b.is_robot=0'
        sql += ' and a.coin_id=' + str(club.coin_id)
        sql += ' group by day'
        dt_recharge = get_sql(sql)

        sql = "select date(a.created_at) as day, sum(a.amount) as amount from users_userpresentation a"
        sql += " inner join users_user b on b.id=a.user_id"
        sql += " where b.is_block=0 and b.is_robot=0"
        sql += " and a.status=1"
        sql += " and a.coin_id=" + str(club.coin_id)
        sql += " group by day"
        dt_present = get_sql(sql)

        data = []
        for x, y in zip(*[dt_sum, dt_earn]):
            temp_dict = {
                '币种': coin_name,
                # '日期': x[0].strftime('%m月%d日'),
                'date': x[0].strftime('%m/%d'),
                '参与人数': float(normalize_fraction(x[2], 8)),
                '参与次数': float(normalize_fraction(x[3], 8)),
                '总投注额': float(normalize_fraction(x[1], 8)),
                '净发放': float(normalize_fraction(y[1], 8))
            }
            temp_dict['净盈利'] = float(normalize_fraction(temp_dict['总投注额'] - temp_dict['净发放'], 8))
            data.append(temp_dict)

        data_recharge = []
        for x in dt_recharge:
            temp_dict2 = {
                'date': x[0].strftime('%m/%d'),
                'coin_name': coin_name,
                '充值总额': float(normalize_fraction(x[1], 8))
            }
            data_recharge.append(temp_dict2)
        data_present = []
        for x in dt_present:
            temp_dict3 = {
                'date': x[0].strftime('%m/%d'),
                'coin_name': coin_name,
                '提现总额': float(normalize_fraction(x[1], 8))
            }
            data_present.append(temp_dict3)
        # import csv
        # date = datetime.now().strftime('%Y%m%d')
        # save_file = '/home/zhijiefong/sts/' + date + 'data.csv'
        # is_exist = os.path.exists(save_file)
        # with open(save_file, 'a') as hf:
        #     writer = csv.DictWriter(hf, data[0].keys())
        #     if not is_exist:
        #         writer.writeheader()
        #     for info in data :
        #         writer.writerow(info)
        return JsonResponse(
            {'coin_name': coin_name, 'results': data, 'recharge': data_recharge, 'present': data_present},
            status=status.HTTP_200_OK)


class CoinAllSts(ListAPIView):
    """
    币余额统计
    """

    def list(self, request, *args, **kwargs):
        coins = Coin.objects.all()
        data = []
        for coin in coins:
            total = UserCoin.objects.filter(user__is_robot=0, coin_id=coin).values('coin__name').annotate(
                total_balance=Sum('balance')).order_by('total_balance')
            temp_dict = {
                'coin_name': total[0]['coin__name'],
                'total_balance': normalize_fraction(total[0]['total_balance'], coin.coin_accuracy)
            }
            data.append(temp_dict)
        return JsonResponse({'results': data}, status=status.HTTP_200_OK)


# class AABBCC(ListAPIView):
#
#     def list(self, request, *args, **kwargs):
#         user = User.objects.filter(is_robot=0, integral=0)
#         return JsonResponse({'data':gsg}, status=status.HTTP_200_OK)


class RemainRate(ListAPIView):
    """
    用户留存率
    """

    def list(self, request, *args, **kwargs):
        end_day = datetime.now().date()
        register_user = User.objects.filter(is_robot=0, created_at__date__lt=end_day).extra(
            select={'date': 'date(created_at)'}).values('date', 'id').order_by('date')
        temp_user = {}
        for i in register_user:
            date = i['date'].strftime('%Y-%m-%d')
            if date not in temp_user:
                temp_user[date] = [i['id']]
            else:
                temp_user[date].append(i['id'])
        count_dict = {}
        for x in temp_user:
            count_dict[x] = len(temp_user[x])
        data = []
        for x in temp_user:
            start_day = datetime.strptime(x, '%Y-%m-%d').date() + timedelta(1)
            login_users = LoginRecord.objects \
                .filter(user__in=temp_user[x], login_time__date__range=(start_day, end_day)) \
                .extra(select={'date': 'date(login_time)'}) \
                .values('date') \
                .annotate(Count('user_id', distinct=True)) \
                .order_by('date')
            # user = LoginRecord.objects.filter(user__)
            login_temp = {}
            login_temp['date'] = x
            for i in login_users:
                day = i['date'] - datetime.strptime(x, '%Y-%m-%d').date()
                delta = str(day.days)
                login_temp[delta] = round(100 * i['user_id__count'] / count_dict[x], 2)
            data.append(login_temp)
        return JsonResponse({'data': data}, status=status.HTTP_200_OK)


class SameIPAddressView(ListAPIView):
    """
    同ip地址
    """
    serializer_class = serializers.IPAddressSerializer

    def get_queryset(self):
        uuid = self.kwargs['id']
        users = User.objects.filter(id=uuid, is_robot=0)
        if users.exists():
            ip = users[0].ip_address.rsplit('.', 1)[0]
            users = User.objects.filter(ip_address__contains=ip).order_by('-created_at')
        return users


class GSGStsView(ListAPIView):
    """
    GSG统计
    """

    def list(self, request, *args, **kwargs):
        sql = "select a.id from users_user a"
        sql += " inner join (select ip_address, count(username) as count from users_user group by ip_address) b on a.ip_address=b.ip_address"
        sql += " where b.count <=3 "
        sql += " and is_robot=0 and is_block=0"
        dt_all = list(get_sql(sql))

        sql = "select distinct(user_id) from users_userrecharge"
        dt_recharge = list(get_sql(sql))

        dt_all = list(set(dt_all + dt_recharge))
        dd = []
        for x in dt_all:
            dd.append(x[0])
        users = tuple(dd)
        user_all = len(users)

        sql = "select sum(balance) from users_usercoin a"
        sql += " where user_id in " + str(users)
        sql += " and coin_id=6"
        dt_all_sum = get_sql(sql)
        integral_login = dt_all_sum[0][0] if dt_all_sum[0][0] else 0

        # sql = "select sum(integral) from users_user a"
        # sql += " where a.id not in (select distinct(user_id) from users_usercoin where coin_id=6)"
        # sql += " and a.id in " + str(users)
        # dt_all_sum = get_sql(sql)
        # integral_unlogin = dt_all_sum[0][0] if dt_all_sum[0][0] else 0

        sql = "select count(distinct(user_id)) from users_coindetail a"
        sql += " inner join users_user b on a.user_id = b.id"
        sql += " where a.user_id in " + str(users)
        sql += " and coin_name = 'HAND'"
        sql += " and sources = " + str(CoinDetail.OTHER)
        sql += " and amount > 400"
        dt_sig_count = get_sql(sql)
        sig_all = dt_sig_count[0][0] if dt_sig_count[0][0] else 0

        sql = "select count(distinct(user_id)) from users_userrecharge a"
        sql += " inner join users_user b on a.user_id = b.id"
        sql += " where b.is_robot=0 and b.is_block=0"
        sql += " and a.confirmations > 0"
        dt_recharge_count = get_sql(sql)
        recharge_all = dt_recharge_count[0][0] if dt_recharge_count[0][0] else 0

        sql = "select date(a.created_at) as day, count(a.user_id) from users_coindetail a"
        sql += " inner join users_user b on a.user_id = b.id"
        sql += " where b.is_robot=0 and coin_name='HAND'"
        sql += " and a.sources = " + str(CoinDetail.OTHER)
        sql += " and user_id in " + str(users)
        sql_gt_0 = " and amount > 0 group by day"
        sql_gt_3 = " and amount > 400 group by day"
        dt_gt_0 = list(get_sql(sql + sql_gt_0))
        dt_gt_3 = list(get_sql(sql + sql_gt_3))

        sql = "select date(a.created_at) as day, sum(amount) from users_coindetail a"
        sql += " inner join users_user b on a.user_id = b.id"
        sql += " where b.is_robot=0 and coin_name='GSG'"
        sql += " and user_id in " + str(users)
        sql_sig = " and sources= " + str(CoinDetail.OTHER) + " group by day"
        sql_back = " and sources= " + str(CoinDetail.CASHBACK) + " group by day"
        sql_act_gt_0 = "and sources= " + str(CoinDetail.ACTIVITY) + " and amount > 0 group by day"
        sql_act_lt_0 = "and sources= " + str(CoinDetail.ACTIVITY) + " and amount < 0 group by day"
        dt_sig = list(get_sql(sql + sql_sig))
        dt_back = list(get_sql(sql + sql_back))
        dt_act_gt_0 = list(get_sql(sql + sql_act_gt_0))
        dt_act_lt_0 = list(get_sql(sql + sql_act_lt_0))
        items = [dt_gt_0, dt_gt_3, dt_sig, dt_back, dt_act_gt_0, dt_act_lt_0]
        data = []
        min_date = date(2099, 1, 1)
        max_date = date(1970, 1, 1)
        for i, x in enumerate(items):
            if len(x) > 0:
                if x[0][0] < min_date:
                    min_date = x[0][0]
                if x[-1][0] > max_date:
                    max_date = x[-1][0]
        if min_date == date(2099, 1, 1) or max_date == date(1970, 1, 1):
            return JsonResponse({'results': []}, status=status.HTTP_200_OK)
        delta = (max_date - min_date).days
        for x in range(delta + 1):
            for v in items:
                date_now = min_date + timedelta(x)
                if len(v) == 0:
                    v = [(date_now, 0)]
                if v[-1][0] > date_now:
                    if v[x][0] != date_now:
                        v.insert(x, (date_now, 0))
                if v[-1][0] < date_now:
                    v.append((date_now, 0))
        for a, b, c, d, e, f in zip(*items):
            temp_dict = {
                'date': a[0].strftime('%m/%d'),
                '签到人数': int(a[1]),
                '连续签到大于3天人数': int(b[1]),
                '签到赠送数量': float(normalize_fraction(c[1], 8)),
                '返现赠送数量': float(normalize_fraction(d[1], 8)),
                '抽奖赠送数量': float(normalize_fraction(e[1], 8)),
                '抽奖回收数量': float(normalize_fraction(f[1], 8))
            }
            data.append(temp_dict)
        # import csv
        # date_x = datetime.now().strftime('%Y%m%d')
        # save_file = '/home/zhijiefong/sts/'+ date_x +'xxgsg.csv'
        # with open(save_file, 'w') as hf:
        #     writer = csv.DictWriter(hf, data[0].keys())
        #     writer.writeheader()
        #     for info in data:
        #         writer.writerow(info)
        return JsonResponse(
            {'user_all': user_all, 'integral_login': integral_login,
             'sig_all': sig_all, 'recharge_all': recharge_all,
             'results': data}, status=status.HTTP_200_OK)


# class JJtest(ListCreateAPIView):
#     """
#     测试
#     """

# def list(self, request, *args, **kwargs):
#     new_register = User.objects.filter(is_robot=0, is_block=0).extra(select={'date': 'date(created_at)'}).values(
#         'date').annotate(
#         date_sum=Count('ip_address',distinct=True)).order_by('date')
#     activy_user = LoginRecord.objects.annotate(date=Func(F('login_time'), function='date')).filter(
#         ~Q(user__created_at__date__contains=F('date')), user__is_robot=0).values('date').annotate(
#         date_sum=Count('user_id', distinct=True)).order_by('date')
#     presents = UserPresentation.objects.all().filter(status=1).extra(select={'date': 'date(created_at)'}).values('date').annotate(
#         date_sum=Count('user_id', distinct=True)).order_by('date')
#     recharge = UserRecharge.objects.all().extra(select={'date': 'date(created_at)'}).values('date').annotate(
#         date_sum=Count('user_id', distinct=True)).order_by('date')
#     recharge_time = UserRecharge.objects.all().extra(select={'date': 'date(created_at)'}).values('date').annotate(
#         date_sum=Count('id')).order_by('date')
#     items = {
#         'new_register': new_register,
#         'activy_user': activy_user,
#         'presents': presents,
#         'recharge': recharge,
#         'recharge_times':recharge_time
#     }
#     data = []
#     # if club_room ==2:
#     #     print(coin_out ,'|', coin_in ,'|', bet_user,'|', bet_times,'|', bet_sum)
#     min_date = date(2099, 1, 1)
#     max_date = date(1970, 1, 1)
#     for x in items:
#         if len(items[x]) > 0:
#             items[x] = [n for n in items[x]]
#             if items[x][0]['date'] < min_date:
#                 min_date = items[x][0]['date']
#             if items[x][-1]['date'] > max_date:
#                 max_date = items[x][-1]['date']
#     if min_date == date(2099, 1, 1) or max_date == date(1970, 1, 1):
#         return JsonResponse({'results': []}, status=status.HTTP_200_OK)
#     delta = (max_date - min_date).days
#     for x in range(delta + 1):
#         for v in items:
#             date_now = min_date + timedelta(x)
#             if len(items[v]) == 0:
#                 items[v] = [{'date': date_now, 'date_sum': 0}]
#             if items[v][-1]['date'] > date_now:
#                 if items[v][x]['date'] != date_now:
#                     items[v].insert(x, {'date': date_now, 'date_sum': 0})
#             if items[v][-1]['date'] < date_now:
#                 items[v].append({'date': date_now, 'date_sum': 0})
#     for a, b, c, d, e in zip(*list(items.values())):
#         temp_dict = {
#             'date': a['date'].strftime('%m/%d'),
#             '新增有效用户数': float(a['date_sum']),
#             '活跃用户': float(b['date_sum']),
#             '提现人数': float(c['date_sum']),
#             '充值人数': float(d['date_sum']),
#             '充值人次': float(e['date_sum'])
#         }
#         data.append(temp_dict)
#     import csv
#     date_x = datetime.now().strftime('%Y%m%d')
#     save_file = '/home/zhijiefong/sts/'+ date_x +'user.csv'
#     with open(save_file, 'w') as hf:
#         writer = csv.DictWriter(hf, data[0].keys())
#         writer.writeheader()
#         for info in data:
#             writer.writerow(info)
#     return JsonResponse({'results': data}, status=status.HTTP_200_OK)
# #
#     def list(self, request, *args, **kwargs):
#         clubs = Club.objects.all()
#         temp_dict={}
#         for x in clubs:
#             recharge = UserRecharge.objects.filter(coin_id=x.coin).extra(select={'date': 'date(trade_at)'}).values(
#                     'date').annotate(date_sum=Sum('amount')).order_by('date')
#             temp_dict[x.coin.name]=recharge
#         items = temp_dict
#
#         data = []
#         # if club_room ==2:
#         #     print(coin_out ,'|', coin_in ,'|', bet_user,'|', bet_times,'|', bet_sum)
#         min_date = date(2099, 1, 1)
#         max_date = date(1970, 1, 1)
#         for x in items:
#             if len(items[x]) > 0:
#                 items[x] = [n for n in items[x]]
#                 if items[x][0]['date'] < min_date:
#                     min_date = items[x][0]['date']
#                 if items[x][-1]['date'] > max_date:
#                     max_date = items[x][-1]['date']
#         if min_date == date(2099, 1, 1) or max_date == date(1970, 1, 1):
#             return JsonResponse({'results': []}, status=status.HTTP_200_OK)
#         delta = (max_date - min_date).days
#         for x in range(delta + 1):
#             for v in items:
#                 date_now = min_date + timedelta(x)
#                 if len(items[v]) == 0:
#                     items[v] = [{'date': date_now, 'date_sum': 0}]
#                 if items[v][-1]['date'] > date_now:
#                     if items[v][x]['date'] != date_now:
#                         items[v].insert(x, {'date': date_now, 'date_sum': 0})
#                 if items[v][-1]['date'] < date_now:
#                     items[v].append({'date': date_now, 'date_sum': 0})
#         for a,b,c,d,e,f in zip(*[temp_dict['USDT'], temp_dict['EOS'], temp_dict['BTC'], temp_dict['ETH'], temp_dict['INT'],temp_dict['HAND']]):
#             temp_d = {
#                 'date':a['date'].strftime('%m/%d'),
#                 'USDT':float(a['date_sum']),
#                 'EOS':float(b['date_sum']),
#                 'BTC':float(c['date_sum']),
#                 'ETH':float(d['date_sum']),
#                 'INT':float(e['date_sum']),
#                 'HAND':float(f['date_sum']),
#             }
#             data.append(temp_d)
#         import csv
#         date_x = datetime.now().strftime('%Y%m%d')
#         save_file = '/home/zhijiefong/sts/'+ date_x +'recharge.csv'
#         with open(save_file, 'w') as hf:
#             writer = csv.DictWriter(hf, data[0].keys())
#             writer.writeheader()
#             for info in data:
#                 writer.writerow(info)
#         return JsonResponse({'results': data}, status=status.HTTP_200_OK)


# @transaction.atomic()
# def post(self, request, *args, **kwargs):
#     user_id = int(request.data.get('user'))
#     count = request.data.get('count')
#     try:
#         user = User.objects.select_for_update().get(id=user_id)
#     except Exception:
#         raise
#     login_record = LoginRecord()
#     login_record.user_id= user.id
#     user.integral +=1
#     login_record.ip = user.integral
#     login_record.save()
#     user.save()
#
#     return JsonResponse({'data':count},status=status.HTTP_200_OK)

class IpLoginView(ListAPIView):
    """
    显示每天登录第一个Ip地址
    """

    def list(self, request, *args, **kwargs):
        user_id = kwargs['user_id']
        # ips = LoginRecord.objects.filter(user_id=user_id).extra(select={'date': 'date(login_time)'}).values(
        #     'user__username', 'date').annotate(ip=F('ip'),first_time=Min('login_time')).order_by('-date')[:15]
        sql = "select c.username, ip, first_time from users_loginrecord a"
        sql += " join  (select user_id , date(login_time)  as day, min(login_time)  as first_time " \
               " from users_loginrecord  " \
               " where user_id =" + str(user_id) + " group by user_id,day) b "
        sql += " on  a.login_time=b.first_time"
        sql += " join users_user c on a.user_id=c.id"
        sql += " order by first_time desc"
        sql += " limit 15"
        dt_all = get_sql(sql)
        # dt_all = LoginRecord.objects
        if len(dt_all) == 0:
            return JsonResponse({'results': []}, status=status.HTTP_200_OK)
        else:
            data = []
            for x in dt_all:
                temp_dict = {
                    'username': x[0],
                    'ip': x[1],
                    'first_time': x[2].strftime('%Y-%m-%d %H:%M:%S'),
                }
                data.append(temp_dict)
            return JsonResponse({'results': data}, status=status.HTTP_200_OK)


class MessageBackendList(ListCreateAPIView):
    """
    玩法列表
    """
    queryset = Message.objects.all()
    serializer_class = serializers.MessageBackendSerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['title', 'content', 'is_deleted']

    @reversion_Decorator
    def post(self, request, *args, **kwargs):
        value = value_judge(request, ('type', 'title', 'title_en', 'content', 'content_en', 'is_deleted'))
        if value:
            return JsonResponse({'Error': '参数不正确'}, status=status.HTTP_400_BAD_REQUEST)
        values = dict(request.data)
        message = Message(**values)
        message.save()
        return JsonResponse({}, status=status.HTTP_200_OK)


class MessageBackendDetail(RetrieveUpdateDestroyAPIView):
    """
    玩法详情
    """

    def retrieve(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        try:
            message = Message.objects.get(id=pk)
        except Exception:
            return JsonResponse({'Error:对象不存在'}, status=status.HTTP_400_BAD_REQUEST)
        messages = serializers.MessageBackendSerializer(message)
        return JsonResponse({'results': messages.data}, status=status.HTTP_200_OK)

    @reversion_Decorator
    def patch(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        try:
            message = Message.objects.get(id=pk)
        except Exception:
            return JsonResponse({'Error:对象不存在'}, status=status.HTTP_400_BAD_REQUEST)
        values = dict(request.data)
        message.__dict__.update(**values)
        message.save()
        return JsonResponse({}, status=status.HTTP_200_OK)

    @reversion_Decorator
    def delete(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        try:
            message = Message.objects.get(id=pk)
        except Exception:
            return JsonResponse({'Error:对象不存在'}, status=status.HTTP_400_BAD_REQUEST)
        message.is_deleted = True
        message.save()
        return JsonResponse({}, status=status.HTTP_200_OK)


class CoinProfitView(ListAPIView):
    """
    锁定分红-真实收益数据、实际锁定用户数、实际锁定总量、每GSG实际分红货币、每GSG名义分红货币
    """

    def list(self, request, *args, **kwargs):
        date_time_now = dateparser.parse(datetime.strftime(datetime.now(), '%Y-%m-%d'))

        if 'start_date' not in request.GET:
            start_date = date_time_now - timedelta(1)
        else:
            start_date = dateparser.parse(request.GET.get('start_date'))

        if 'end_date' not in request.GET:
            end_date = date_time_now
        else:
            end_date = dateparser.parse(request.GET.get('end_date'))

        profits = ClubProfitAbroad.objects.filter(created_at__gte=start_date, created_at__lt=end_date)
        if len(profits) == 0:
            return JsonResponse({'results': []}, status=status.HTTP_200_OK)

        coins = Coin.objects.filter(is_disabled=False)
        map_coin_id_name = {}
        for coin in coins:
            map_coin_id_name[coin.id] = coin.name

        clubs = Club.objects.filter(is_dissolve=False)
        map_club_coin = {}
        for club in clubs:
            map_club_coin[club.id] = club.coin_id

        data = []
        for item in profits:
            data.append({
                'coin_name': map_coin_id_name[map_club_coin[item.roomquiz_id]],
                'profit': item.profit,
            })

        return JsonResponse({'results': data}, status=status.HTTP_200_OK)


class CoinDividendProposalView(ListCreateAPIView):
    """
    锁定分红-分红方案
    """
    @staticmethod
    def get_coin_id_by_name(coin_name):
        """
        获取货币ID
        :param  coin_name
        :return:
        """
        coin_id = 0
        if coin_name == 'BTC':
            coin_id = Coin.BTC
        elif coin_name == 'ETH':
            coin_id = Coin.ETH
        elif coin_name == 'INT':
            coin_id = Coin.INT
        elif coin_name == 'USDT':
            coin_id = Coin.USDT

        return coin_id

    @staticmethod
    def get_coin_name_by_id(coin_id):
        """
        获取货币名称
        :param  coin_id
        :return:
        """
        coin_name = ''
        if coin_id == Coin.BTC:
            coin_name = 'BTC'
        elif coin_id == Coin.ETH:
            coin_name = 'ETH'
        elif coin_id == Coin.USDT:
            coin_name = 'USDT'
        elif coin_id == Coin.INT:
            coin_name = 'INT'

        return coin_name

    def list(self, request, *args, **kwargs):
        if 'total_dividend' not in request.GET:
            return JsonResponse({'results': {'code': -1, 'message': 'total_dividend参数错误'}}, status=status.HTTP_200_OK)

        total_dividend = float(request.GET.get('total_dividend'))     # 总分红金额

        scale = None
        scale_format = {}
        if 'scale' in request.GET:
            scale = request.GET.get('scale')    # 自定义比例

            if scale != '':
                scale = json.loads(scale)

                # 判断传过来的值总和是否=100
                scale_sum = 0.00
                for scl in scale:
                    scale_sum += float(scale[scl])
                    scale_format[int(scl)] = float(scale[scl])

                if scale_sum != 1:
                    return JsonResponse({'results': {'code': -2, 'message': '比例总和不为1'}}, status=status.HTTP_200_OK)

        if total_dividend == 0:
            return JsonResponse({'results': {'code': -3, 'message': 'total_dividend参数错误'}}, status=status.HTTP_200_OK)

        dividend_decimal = settings.DIVIDEND_DECIMAL  # 分红精度
        coin_ids = [Coin.BTC, Coin.ETH, Coin.INT, Coin.USDT]

        # 获取当前货币价格
        coin_price = CoinPrice.objects.all()
        map_coin_id_price = {}
        if len(coin_price) == 0:
            return JsonResponse({'results': []}, status=status.HTTP_200_OK)
        for cprice in coin_price:
            map_coin_id_price[self.get_coin_id_by_name(cprice.coin_name)] = float(cprice.price)

        clubs = Club.objects.filter(is_dissolve=False, coin_id__in=coin_ids)

        # 随机生成货币分配比例
        scale_sum = 100
        scale_number = len(clubs)
        scale_coin = np.random.multinomial(scale_sum, np.ones(scale_number) / scale_number, size=1)[0]

        # 计算出各个俱乐部币种分红数量
        coin_dividend = {}
        coin_scale = {}
        idx = 0
        for club in clubs:
            coin_id = club.coin_id
            # 排除HAND俱乐部
            if coin_id == Coin.HAND:
                continue

            if scale is not None and scale != '':
                coin_scale_percent = scale_format[coin_id]
            else:
                coin_scale_percent = scale_coin[idx] / 100      # 占有百分比

            scale_dividend = total_dividend * coin_scale_percent
            coin_dividend[coin_id] = int((scale_dividend / map_coin_id_price[coin_id]) * dividend_decimal) / dividend_decimal
            coin_scale[coin_id] = coin_scale_percent
            idx += 1

        # GSG实际锁定总量
        user_coin_lock_sum = UserCoinLock.objects.filter(is_free=False).aggregate(Sum('amount'))
        if user_coin_lock_sum['amount__sum'] is None:
            user_coin_lock_sum['amount__sum'] = 0
        user_coin_lock_sum = int(user_coin_lock_sum['amount__sum'] * settings.DIVIDEND_DECIMAL) / settings.DIVIDEND_DECIMAL

        # GSG实际锁定用户数
        user_coin_lock_total = UserCoinLock.objects.filter(is_free=False).distinct().count()

        items = []
        for coinid in coin_scale:
            amount = str(coin_dividend[coinid])

            # 每GSG实际分红货币数量：分红货币数量 / GSG锁定总量
            if user_coin_lock_sum == 0:
                tmp_gsg_coin_dividend = 0
            else:
                tmp_gsg_coin_dividend = int((float(amount) / user_coin_lock_sum) * settings.DIVIDEND_DECIMAL) / float(
                    settings.DIVIDEND_DECIMAL)

            # 每GSG名义分红货币数量：每GSG实际分红 x 10亿 / GSG锁定总量
            if user_coin_lock_sum == 0:
                tmp_real_sum = 0
            else:
                tmp_real_sum = int((tmp_gsg_coin_dividend * settings.GSG_TOTAL_SUPPLY / float(user_coin_lock_sum)) * float(
                    settings.DIVIDEND_DECIMAL)) / float(settings.DIVIDEND_DECIMAL)

            items.append({
                'coin_id': str(coinid),     # 货币ID
                'coin_name': self.get_coin_name_by_id(coinid),  # 货币名称
                'scale': str(coin_scale[coinid]),   # 货币占有比例
                'dividend_price': str(round(total_dividend * coin_scale[coinid], 2)),     # 分红总价
                'price': str(map_coin_id_price[coinid]),    # 货币对应价格
                'amount': amount,   # 分红数量
                'gsg_coin_dividend': '%.6f' % tmp_gsg_coin_dividend,
                'gsg_coin_titular_dividend': '%.6f' % tmp_real_sum,
            })

        results = {
            'user_coin_lock_sum': user_coin_lock_sum,
            'user_coin_lock_total': user_coin_lock_total,
            'dividend': items,
        }

        return JsonResponse({'results': results}, status=status.HTTP_200_OK)

    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        """
        确定当前锁定分红方案
        :param request:
            - dividend: 分红金额
            - coins: [
                {
                    coin_id: 1,
                    scale: 20,
                    price: 55555
                },
                ...
            ]
        :param args:
        :param kwargs:
        :return:
        """
        dividend = request.data.get('dividend')
        coins = json.loads(request.data.get('coins'))
        dividend_date = dateparser.parse(datetime.strftime(datetime.now(), '%Y-%m-%d'))

        decimal = 1000000

        # 判断该日期是否已经设置，若是，则无法再修改
        dividend_config = DividendConfig.objects.filter(dividend_date=dividend_date).count()
        if dividend_config > 0:
            return JsonResponse({'results': {'code': -1, 'message': '设置后无法修改'}}, status=status.HTTP_200_OK)
        # try:
        #     dividend_config = DividendConfig.objects.get(dividend_date=dividend_date)
        #
        #     DividendConfigCoin.objects.filter(dividend_config=dividend_config).delete()
        # except DividendConfig.DoesNotExist:
        #     dividend_config = DividendConfig()
        dividend_config = DividendConfig()
        dividend_config.dividend = Decimal(dividend)
        dividend_config.dividend_date = dividend_date
        dividend_config.save()

        map_coin_id_club_id = {
            1: 2,
            2: 3,
            3: 4,
            9: 6,
        }
        map_club_id_amount = {}
        for coin in coins:
            scale = float(coin['scale'])
            price = float(coin['price'])
            coin_id = int(coin['coin_id'])

            amount = float(dividend) * scale / price
            amount = int(decimal * amount) / decimal

            dividend_config_coin = DividendConfigCoin()
            dividend_config_coin.dividend_config = dividend_config
            dividend_config_coin.coin_id = coin_id
            dividend_config_coin.scale = scale * 100
            dividend_config_coin.price = price
            dividend_config_coin.amount = amount
            dividend_config_coin.save()

            # 俱乐部ID对应虚拟盈收
            map_club_id_amount[map_coin_id_club_id[coin_id]] = amount

        # 写入虚拟盈利数据表中
        club_profit_date = dateparser.parse(datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d 23:59:59.000000'))
        club_profits = ClubProfitAbroad.objects.filter(created_at=club_profit_date)
        for profit in club_profits:
            for club_id in map_club_id_amount:
                if profit.roomquiz_id != club_id:
                    continue
                profit.virtual_profit = map_club_id_amount[club_id]
                profit.save()

        return JsonResponse({'results': []}, status=status.HTTP_200_OK)
