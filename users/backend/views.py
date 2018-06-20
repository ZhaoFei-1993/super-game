# -*- coding: UTF-8 -*-
from itertools import chain
import os
from base.backend import CreateAPIView, FormatListAPIView, FormatRetrieveAPIView, DestroyAPIView, UpdateAPIView, \
    ListAPIView, ListCreateAPIView, RetrieveUpdateAPIView, RetrieveAPIView, RetrieveUpdateDestroyAPIView
from django.db import transaction
from decimal import Decimal
from django.db import connection
from datetime import datetime, timedelta, date
from django.db.models.functions import ExtractDay
from django.db.models import Q, Count, Sum, Max, F, Func, When, Case, DecimalField
from chat.models import Club
from users.models import Coin, CoinLock, Admin, UserCoinLock, UserCoin, User, CoinDetail, CoinValue, RewardCoin, \
    LoginRecord, UserInvitation, UserPresentation, CoinOutServiceCharge, UserRecharge, CoinGiveRecords, CoinGive, \
    UserMessage, IntInvitation
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
from utils.functions import reversion_Decorator
from url_filter.integrations.drf import DjangoFilterBackend
from quiz.models import Record, Quiz


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
    queryset = User.objects.filter(is_robot=0).order_by('-id')
    serializer_class = serializers.UserAllSerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['id', 'username', 'is_block']

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
                and 'txid' not in request.data\
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
                    language = request.data.get('language','')
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
            txid = request.data.get('txid')
            item.txid = txid
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
        user_register = User.objects.filter(is_robot=0)
        register_num = user_register.count()
        user_invite = user_register.extra(select={
            'sum_invite': 'select count(*) from users_userinvitation as ui where ui.inviter_id=users_user.id'}).values(
            'sum_invite')
        invite_4 = 0
        invite_0 = 0
        for i in user_invite:
            if i['sum_invite'] == 0:
                invite_0 += 1
            if i['sum_invite'] >= 4:
                invite_4 += 1
        gsg_eq_0_user = user_register.filter(integral=0).count()
        gsg_sum_integral = self.ts_null_2_zero(
            user_register.values('integral').aggregate(Sum('integral'))['integral__sum'])
        gsg_sum_amount = self.ts_null_2_zero(
            CoinDetail.objects.filter(user__is_robot=0, coin_name='GSG', sources=4).values('amount').aggregate(
                Sum('amount'))['amount__sum'])
        gsg_sent = Decimal(str(gsg_sum_integral)) - Decimal(str(gsg_sum_amount))  # 发放gsg数量
        recharge_all_sum = UserRecharge.objects.filter(user__is_robot=0).values('user_id').distinct().count()  # 充值总人数
        present_all_sum = UserPresentation.objects.filter(user__is_robot=0).values(
            'user_id').distinct().count()  # 提现总人数
        # hand_recharge = \
        #     UserRecharge.objects.filter(coin__name='HAND', user__is_robot=0).values('amount').aggregate(Sum('amount'))[
        #         'amount__sum']
        # hand_system = CoinDetail.objects.filter(coin_name='HAND', user__is_robot=0, sources__in=[4, 6, 7, 8]).values(
        #     'amount').aggregate(Sum('amount'))['amount__sum']
        # records = Record.objects.filter(source=Record.NORMAL, roomquiz_id=1)
        # hand_bet = records.values('bet').aggregate(Sum('bet'))['bet__sum']
        # hand_out = records.filter(quiz__status=5, option__option__is_right=1).annotate(
        #     hand_o=F('bet') * (F('odds') - 1)).aggregate(Sum('hand_o'))['hand_o__sum']
        # hand_in = records.filter(quiz__status=5, option__option__is_right=0).annotate(
        #     hand_i=F('bet')).aggregate(Sum('hand_i'))['hand_i__sum']
        # hand_bet_not_begin = records.filter(quiz__status=0).aggregate(Sum('bet'))['bet__sum']
        # hand_rest = \
        #     UserCoin.objects.filter(user__is_robot=0, coin__name='HAND').values('balance').aggregate(Sum('balance'))[
        #         'balance__sum']
        # hand_rest_num = UserCoin.objects.filter(user__is_robot=0, balance__gt=0, coin__name='HAND').count()
        # hand_sent = hand_rest + hand_bet_not_begin + hand_in - hand_recharge
        # usdt_record = Record.objects.filter(source__in=[Record.NORMAL, Record.GIVE], roomquiz_id=6)
        # usdt_recharge_count = UserRecharge.objects.filter(user__is_robot=0, coin__name='USDT').values(
        #     'user_id').distinct().count()
        # usdt_recharge = \
        #     UserRecharge.objects.filter(coin__name='USDT', user__is_robot=0).values('amount').aggregate(Sum('amount'))[
        #         'amount__sum']
        # usdt_bet = usdt_record.values('bet').aggregate(Sum('bet'))['bet__sum']
        # usdt_out = usdt_record.filter(quiz__status=5, option__option__is_right=1).annotate(
        #     hand_o=F('bet') * (F('odds') - 1)).aggregate(Sum('hand_o'))['hand_o__sum']
        # usdt_in = usdt_record.filter(quiz__status=5, option__option__is_right=0).annotate(
        #     hand_i=F('bet')).aggregate(Sum('hand_i'))['hand_i__sum']
        # usdt_system = \
        #     CoinGiveRecords.objects.all().values('coin_give__number').aggregate(total_coin=Sum('coin_give__number'))[
        #         'total_coin']
        # usdt_rest = \
        #     UserCoin.objects.filter(user__is_robot=0, coin__name='USDT').values('balance').aggregate(Sum('balance'))[
        #         'balance__sum']
        # usdt_bet_not_begin = usdt_record.filter(quiz__status=0).aggregate(Sum('bet'))['bet__sum']
        # usdt_balance_max = \
        #     UserCoin.objects.filter(user__is_robot=0, coin__name='USDT').values('balance').aggregate(Max('balance'))[
        #         'balance__max']
        # usdt_lock_coin_max = \
        #     CoinGiveRecords.objects.filter(user__is_robot=0).values('lock_coin').aggregate(Max('lock_coin'))[
        #         'lock_coin__max']
        # usdt_present_temp = CoinGiveRecords.objects.filter(user__is_robot=0, is_recharge_lock=1)
        # usdt_lock_present = 0
        # for x in usdt_present_temp:
        #     if UserPresentation.objects.filter(user_id=x.user_id, coin__name='USDT').exists():
        #         usdt_lock_present += 1
        # usdt_present = UserPresentation.objects.filter(user__is_robot=0, coin__name='USDT').count()
        # usdt_success = UserPresentation.objects.filter(user__is_robot=0, coin__name='USDT', status=1).count()
        # usdt_rest_num = UserCoin.objects.filter(user__is_robot=0, balance__gt=0, coin__name='USDT').count()
        #
        # int_record = Record.objects.filter(source__in=[Record.NORMAL, Record.GIVE], roomquiz_id=2)
        # int_recharge_count = UserRecharge.objects.filter(user__is_robot=0, coin__name='INT').values(
        #     'user_id').distinct().count()
        # int_recharge = \
        #     UserRecharge.objects.filter(coin__name='INT', user__is_robot=0).values('amount').aggregate(Sum('amount'))[
        #         'amount__sum']
        # int_bet = int_record.values('bet').aggregate(Sum('bet'))['bet__sum']
        # int_out = int_record.filter(quiz__status=5, option__option__is_right=1).annotate(
        #     hand_o=F('bet') * (F('odds') - 1)).aggregate(Sum('hand_o'))['hand_o__sum']
        # int_in = int_record.filter(quiz__status=5, option__option__is_right=0).annotate(
        #     hand_i=F('bet')).aggregate(Sum('hand_i'))['hand_i__sum']
        # int_rest = \
        #     UserCoin.objects.filter(user__is_robot=0, coin__name='INT').values('balance').aggregate(Sum('balance'))[
        #         'balance__sum']
        # int_present = UserPresentation.objects.filter(user__is_robot=0, coin__name='INT').count()
        # int_success = UserPresentation.objects.filter(user__is_robot=0, coin__name='INT', status=1).count()
        # int_rest_num = UserCoin.objects.filter(user__is_robot=0, balance__gt=0, coin__name='INT').count()

        #     results.append(temp_dict)
        # for x in records:
        #     option = Option.objects.filter(is_right=1, rule_id=x.rule_id)
        #     if len(option) > 0:
        #         if option[0].id == x.option.option_id:
        #             hand_out += x.bet * (x.odds - 1)
        #         else:
        #             hand_in += x.bet
        # data = {'register_num': register_num,  # 总注册用户数
        #         'invite_4': invite_4,  # 邀请4个以上的用户数
        #         'invite_0': invite_0,  # 邀请0个用户数
        #         'gsg_0': gsg_0,  # gsg余额为0用户数
        #         'gsg_sent': gsg_sent,  # gsg发放的金额数
        #         'gsg_rest': sum_integral,  # gsg余额
        #         'recharge_sum': recharge_sum,  # 充值人数
        #         'present_sum': present_sum,  # 提现人数
        #         'hand_recharge': hand_recharge,  # hand币充值金额
        #         'hand_system': hand_system,  # hand币系统发放
        #         'hand_bet': hand_bet,  # hand币投注金额
        #         'hand_out': hand_out,  # hand币投注发出金额
        #         'hand_in': hand_in,  # hand币投注回收金额
        #         'hand_rest': hand_rest,  ##hand币所有用户余额
        #         'hand_rest_num': hand_rest_num,
        #         'hand_bet_not_begin': hand_bet_not_begin,  # hand币投注未开奖金额
        #         'hand_sent': hand_sent,  # hand币发放金额
        #         'usdt_recharge_count': usdt_recharge_count,  # usdt充值人数
        #         'usdt_recharge': 0 if usdt_recharge == None else usdt_recharge,  # usdt充值额度
        #         'usdt_bet': usdt_bet,  # usdt下注值
        #         'usdt_out': usdt_out,  # usdt下注平台发放
        #         'usdt_in': usdt_in,  # usdt下注平台回收
        #         'usdt_system': usdt_system,  # usdt平台系统赠送
        #         'usdt_rest': usdt_rest,  # usdt用户余额
        #         'usdt_bet_not_begin': usdt_bet_not_begin,  # usdt用户投注未结算
        #         'usdt_balance_max': usdt_balance_max,  # usdt用户余额最大值
        #         'usdt_lock_coin_max': usdt_lock_coin_max,  # usdt用户锁定金额最大值
        #         'usdt_lock_present': usdt_lock_present,
        #         'usdt_success': usdt_success,
        #         'usdt_present': usdt_present,
        #         'usdt_rest_num': usdt_rest_num,
        #         'usdt_earn_gte_10': self.count_earn_coin(10),
        #         'usdt_earn_gte_20': self.count_earn_coin(20),
        #         'usdt_earn_gte_30': self.count_earn_coin(30),
        #         'usdt_earn_gte_40': self.count_earn_coin(40),
        #         'usdt_earn_gte_50': self.count_earn_coin(50),
        #         'int_recharge_count': int_recharge_count,
        #         'int_recharge': 0 if int_recharge == None else int_recharge,
        #         'int_bet': int_bet,
        #         'int_out': 0 if int_out == None else int_out,
        #         'int_in': 0 if int_in == None else int_in,
        #         'int_rest': int_rest,
        #         'int_rest_num': int_rest_num,
        #         'int_success': int_success,
        #         'int_present': int_present,
        #         'now_time': datetime.now().strftime('%Y年%m月%d日')
        #         }
        data = {
            'register_num': register_num,  # 总注册用户数
            'invite_0': invite_0,  # 邀请0个用户数
            'gsg_0': gsg_eq_0_user,  # gsg余额为0用户数
            'gsg_sent': gsg_sent,  # gsg发放的金额数
            'gsg_rest': gsg_sum_integral,  # gsg余额
            'invite_4': invite_4,  # 邀请4个以上的用户数
            'recharge_sum': recharge_all_sum,  # 充值人数
            'present_sum': present_all_sum,  # 提现人数
            'now_time': datetime.now().strftime('%Y年%m月%d日'),
            # 'results':results
        }
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
            return float(normalize_fraction(item, 4))

    def list(self, request, *args, **kwargs):
        cursor = connection.cursor()
        club = int(kwargs['room_id'])
        # clubs = Club.objects.all()
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
        sql = "select sum(a.bet) from quiz_record a"
        sql += " inner join quiz_quiz b on a.quiz_id=b.id"
        sql += " where source <> " + str(Record.CONSOLE)
        sql += " and a.roomquiz_id= " + str(r_id)
        sql += " and b.status=5"
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
        sql = "select sum(earn_coin) from quiz_record"
        sql += " where source <> " + str(Record.CONSOLE)
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
        temp_dict['earn'] = normalize_fraction(temp_dict['bet_end'] - temp_dict['out'], 8)
        # temp_dict['bet_not_begin'] = self.ts_null_2_zero(
        #     records.filter(~Q(quiz__status=5)).aggregate(Sum('bet'))['bet__sum'])
        # -----------------------------------------------------------------------------------
        # 未结算下注额
        sql = "select sum(bet) from quiz_record a"
        sql += " inner join quiz_quiz b on a.quiz_id=b.id"
        sql += " where roomquiz_id= " + str(r_id)
        sql += " and source <> " + str(Record.CONSOLE)
        sql += " and  b.status<> 5"
        cursor.execute(sql, None)
        dt_all = cursor.fetchall()
        bet_total = dt_all[0][0] if dt_all[0][0] else 0
        temp_dict['bet_not_begin'] = self.ts_null_2_zero(bet_total)
        # temp_dict['bet_user_sum'] = records.values('user_id').distinct().count()
        # 计算下注用户数
        # -----------------------------------------------------------------------------------
        sql = "select count(distinct(user_id)) from quiz_record "
        sql += "where source <> " + str(Record.CONSOLE)
        sql += " and roomquiz_id= " + str(r_id)
        cursor.execute(sql, None)
        dt_all = cursor.fetchall()
        bet_total = dt_all[0][0] if dt_all[0][0] else 0
        temp_dict['bet_user_sum'] = bet_total
        # -----------------------------------------------------------------------------------
        # 下注次数
        sql = "select count(id) from quiz_record "
        sql += "where source <> " + str(Record.CONSOLE)
        sql += " and roomquiz_id= " + str(r_id)
        cursor.execute(sql, None)
        dt_all = cursor.fetchall()
        bet_total = dt_all[0][0] if dt_all[0][0] else 0
        temp_dict['bet_times'] = bet_total
        # temp_dict['bet_times'] = records.count()
        # -----------------------------------------------------------------------------------
        # 计算总余额
        sql = "select sum(a.balance) from users_usercoin a"
        sql += " inner join users_user b on a.user_id=b.id"
        sql += " where b.is_robot= 0"
        sql += " and  coin_id=" + str(coin_id)
        cursor.execute(sql, None)
        dt_all = cursor.fetchall()
        bet_total = dt_all[0][0] if dt_all[0][0] else 0
        temp_dict['rest'] = self.ts_null_2_zero(bet_total)
        # temp_dict['rest'] = self.ts_null_2_zero(user_coin.aggregate(Sum('balance'))['balance__sum'])
        # -----------------------------------------------------------------------------------
        # 计算余额大于0用户数
        sql = "select count(a.user_id) from users_usercoin a"
        sql += " inner join users_user b on a.user_id=b.id"
        sql += " where b.is_robot= 0"
        sql += " and  a.balance > 0"
        sql += " and  coin_id=" + str(coin_id)
        cursor.execute(sql, None)
        dt_all = cursor.fetchall()
        bet_total = dt_all[0][0] if dt_all[0][0] else 0
        temp_dict['rest_gt_0'] = self.ts_null_2_zero(bet_total)
        # temp_dict['rest_gt_0'] = user_coin.filter(balance__gt=0).values('id').count()
        # -----------------------------------------------------------------------------------
        # user_coin = UserCoin.objects.filter(user__is_robot=0, coin_id=coin_id)
        sql = "select count(a.user_id) from users_usercoin a"
        sql += " inner join users_user b on a.user_id=b.id"
        sql += " where b.is_robot= 0"
        sql += " and  a.balance = 0"
        sql += " and  coin_id=" + str(coin_id)
        cursor.execute(sql, None)
        dt_all = cursor.fetchall()
        bet_total = dt_all[0][0] if dt_all[0][0] else 0
        temp_dict['rest_eq_0'] = self.ts_null_2_zero(bet_total)
        # -----------------------------------------------------------------------------------
        # temp_dict['rest_eq_0'] = user_coin.filter(balance=0).values('id').count()
        recharge = UserRecharge.objects.select_related().filter(user__is_robot=0, coin_id=coin_id)
        temp_dict['recharge_num'] = recharge.count()
        temp_dict['recharge_user_num'] = recharge.values('user_id').distinct().count()
        temp_dict['recharge_amount'] = self.ts_null_2_zero(recharge.aggregate(Sum('amount'))['amount__sum'])
        present = UserPresentation.objects.select_related().filter(user__is_robot=0, coin_id=coin_id)
        temp_dict['present_user_num'] = present.values('user_id').distinct().count()
        temp_dict['present_amount'] = self.ts_null_2_zero(present.aggregate(Sum('amount'))['amount__sum'])
        temp_dict['present_num'] = present.count()
        temp_dict['present_success_num'] = present.select_related().filter(status=1).values('id').count()
        # if room.coin.name == 'USDT':
        #     usdt = CoinGiveRecords.objects.select_related().all()
        #     temp_dict['rest_gte_10'] = self.count_earn_coin(usdt, 10)
        #     temp_dict['rest_gte_20'] = self.count_earn_coin(usdt, 20)
        #     temp_dict['rest_gte_30'] = self.count_earn_coin(usdt, 30)
        #     temp_dict['rest_gte_40'] = self.count_earn_coin(usdt, 40)
        #     temp_dict['rest_gte_50'] = self.count_earn_coin(usdt, 50)
        #     temp_dict['rest_gte_60'] = self.count_earn_coin(usdt, 60)
        return JsonResponse({'data': [temp_dict]})


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
        new_register = User.objects.filter(is_robot=0, is_block=0).extra(select={'date': 'date(created_at)'}).values(
            'date').annotate(
            date_sum=Count('ip_address', distinct=True)).order_by('date')
        activy_user = LoginRecord.objects.annotate(date=Func(F('login_time'), function='date')).filter(
            ~Q(user__created_at__date__contains=F('date')), user__is_robot=0).values('date').annotate(
            date_sum=Count('user_id', distinct=True)).order_by('date')
        presents = UserPresentation.objects.all().filter(status=1).extra(select={'date': 'date(created_at)'}).values(
            'date').annotate(
            date_sum=Count('user_id', distinct=True)).order_by('date')
        recharge = UserRecharge.objects.all().extra(select={'date': 'date(created_at)'}).values('date').annotate(
            date_sum=Count('user_id', distinct=True)).order_by('date')
        recharge_time = UserRecharge.objects.all().extra(select={'date': 'date(created_at)'}).values('date').annotate(
            date_sum=Count('id')).order_by('date')
        items = {
            'new_register': new_register,
            'activy_user': activy_user,
            'presents': presents,
            'recharge': recharge,
            'recharge_times': recharge_time
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
        for a, b, c, d, e in zip(*list(items.values())):
            temp_dict = {
                'date': a['date'].strftime('%m/%d'),
                '新增有效用户数': float(a['date_sum']),
                '活跃用户': float(b['date_sum']),
                '提现人数': float(c['date_sum']),
                '充值人数': float(d['date_sum']),
                '充值人次': float(e['date_sum'])
            }
            data.append(temp_dict)

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

        sql = "select date(b.begin_at) as day, sum(a.bet), count(distinct(a.user_id)), count(a.user_id) from quiz_record a"
        sql += " inner join quiz_quiz b on a.quiz_id=b.id"
        sql += " where b.status=5 and a.source <> " + str(Record.CONSOLE)
        sql += " and roomquiz_id = " + str(club.id)
        sql += " group by day order by day"
        dt_sum = get_sql(sql)
        if len(dt_sum) == 0:
            return JsonResponse({'coin_name': coin_name, 'results': []}, status=status.HTTP_200_OK)
        sql = "select date(b.begin_at) as day, sum(earn_coin) from quiz_record a"
        sql += " inner join quiz_quiz b on a.quiz_id=b.id"
        sql += " where b.status=5 and a.source <> " + str(Record.CONSOLE)
        sql += " and roomquiz_id = " + str(club.id)
        sql += " and earn_coin > 0"
        sql += " group by day order by day"
        dt_earn = get_sql(sql)

        sql = 'select date(a.created_at) as day, sum(a.amount) as day from users_userrecharge a'
        sql += ' inner join users_user b on b.id=a.user_id'
        sql += ' where b.is_robot=0'
        sql += ' and a.coin_id=' + str(club.coin_id)
        sql += ' group by day'
        dt_recharge = get_sql(sql)

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

        data_recharge=[]
        for x in dt_recharge:
            temp_dict2 = {
                'date': x[0].strftime('%m/%d'),
                '充值总额':float(normalize_fraction(x[1], 8))
            }
            data_recharge.append(temp_dict2)
        # import csv
        # date = datetime.now().strftime('%Y%m%d')
        # save_file = '/home/zhijiefong/sts/' + date + 'gsg.csv'
        # is_exist = os.path.exists(save_file)
        # with open(save_file, 'a') as hf:
        #     writer = csv.DictWriter(hf, data[0].keys())
        #     if not is_exist:
        #         writer.writeheader()
        #     for info in data:
        #         writer.writerow(info)
        return JsonResponse({'coin_name': coin_name, 'results': data, 'recharge':data_recharge}, status=status.HTTP_200_OK)


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


# class JJtest(ListCreateAPIView):
    """
    测试
    """

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
