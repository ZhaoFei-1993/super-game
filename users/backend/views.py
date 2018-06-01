# -*- coding: UTF-8 -*-
from itertools import chain
from base.backend import CreateAPIView, FormatListAPIView, FormatRetrieveAPIView, DestroyAPIView, UpdateAPIView, \
    ListAPIView, ListCreateAPIView, RetrieveUpdateAPIView, RetrieveAPIView
from django.db import transaction
from django.db.models import Q
from users.models import Coin, CoinLock, Admin, UserCoinLock, UserCoin, User, CoinDetail, CoinValue, RewardCoin, \
    LoginRecord, UserInvitation, UserPresentation, CoinOutServiceCharge, UserRecharge
from users.app.v1.serializers import PresentationSerialize
from rest_framework import status
import jsonfield
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


class CoinLockDetailView(DestroyAPIView, FormatRetrieveAPIView, UpdateAPIView):
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
        return HttpResponse(json.dumps(data), content_type='text/json')

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


class CurrencyListView(CreateAPIView, FormatListAPIView):
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
        admin = self.request.user
        exchange_rate = request.data['exchange_rate']
        cash_control = request.data['cash_control']
        betting_toplimit = request.data['betting_toplimit']
        betting_control = request.data['betting_control']
        betting_value_one = request.data['betting_value_one']
        betting_value_two = request.data['betting_value_two']
        betting_value_three = request.data['betting_value_three']
        coin_order = int(request.data['coin_order'])
        # Integral_proportion = request.data['Integral_proportion']

        coin = Coin()
        coin.icon = request.data['icon']
        coin.coin_order = coin_order
        if int(exchange_rate) != 1:
            coin.exchange_rate = 1
        else:
            coin.exchange_rate = exchange_rate
        coin.cash_control = cash_control
        coin.betting_toplimit = betting_toplimit
        coin.betting_control = betting_control
        coin.name = request.data['name']
        # coin.type = request.data['type']
        # coin.is_lock = request.data['is_lock']
        coin.admin = admin
        coin.save()
        coin_value = CoinValue()
        coin_value.coin = coin
        coin_value.value_index = 1
        coin_value.value = float(betting_value_one)
        coin_value.save()
        coin_value = CoinValue()
        coin_value.coin = coin
        coin_value.value_index = 2
        coin_value.value = float(betting_value_two)
        coin_value.save()
        coin_value = CoinValue()
        coin_value.coin = coin
        coin_value.value_index = 3
        coin_value.value = float(betting_value_three)
        coin_value.save()
        # reward_coin = RewardCoin()
        # reward_coin.coin = coin
        # reward_coin.value_ratio = Integral_proportion
        # reward_coin.admin = admin
        # reward_coin.save()

        content = {'status': status.HTTP_201_CREATED}
        return HttpResponse(json.dumps(content), content_type='text/json')


class CurrencyDetailView(DestroyAPIView, FormatRetrieveAPIView, UpdateAPIView):
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
            # "is_lock": str(is_lock),
            "url": ''
        }
        return HttpResponse(json.dumps(data), content_type='text/json')

    @reversion_Decorator
    def delete(self, request, *args, **kwargs):
        coin_id = self.request.parser_context['kwargs']['pk']
        coin = Coin.objects.get(pk=coin_id)
        coin.is_delete = True
        coin.save()
        content = {'status': status.HTTP_200_OK}
        return HttpResponse(json.dumps(content), content_type='text/json')

    @reversion_Decorator
    def update(self, request, *args, **kwargs):
        id = int(kwargs['pk'])
        cash_control = request.data['cash_control']
        betting_toplimit = request.data['betting_toplimit']
        betting_control = request.data['betting_control']
        coin = Coin.objects.get(pk=id)
        coin.icon = request.data['icon']
        coin.name = request.data['name']
        # coin.type = request.data['type']
        coin.exchange_rate = request.data['exchange_rate']
        coin.cash_control = cash_control
        coin.betting_toplimit = betting_toplimit
        coin.betting_control = betting_control
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
        content = {'status': status.HTTP_200_OK}
        return HttpResponse(json.dumps(content), content_type='text/json')


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


class UserAllView(ListAPIView):
    """
    所有用户资产表
    """
    queryset = User.objects.filter(is_robot=0).order_by('-created_at')
    serializer_class = serializers.UserAllSerializer


class InviterDetailView(RetrieveAPIView):
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
        users = []
        if inviter.exists():
            for x in list(user_id1):
                if x[0] != 0:
                    users.append(int(x[0]))
            for x in list(user_id2):
                if x[0] != 0:
                    users.append(int(x[0]))
        user_group = User.objects.filter(pk__in=users)
        return user_group


class CoinPresentView(ListAPIView):
    """
    提现记录表
    """
    queryset = UserPresentation.objects.all().order_by('-created_at', 'status')
    serializer_class = PresentationSerialize


class CoinPresentCheckView(RetrieveUpdateAPIView):
    """
    提现审核
    """

    @reversion_Decorator
    def patch(self, request, *args, **kwargs):
        id = kwargs['pk'] #提现记录id
        if 'status' not in request.data and 'text' not in request.data and 'is_bill' not in request.data:
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
        if 'text' in request.data:
            text = request.data.get('text')
            item.feedback = text

        if 'is_bill' in request.data:
            bill = request.data.get('is_bill')
            item.is_bill = bill
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
            sources__in=[CoinDetail.RECHARGE, CoinDetail.REALISATION, CoinDetail.BETS]), user_id=pk, coin_name=coin_name)
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