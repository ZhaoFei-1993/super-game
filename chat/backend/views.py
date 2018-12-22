# -*- coding: UTF-8 -*-
from base.backend import RetrieveUpdateDestroyAPIView, ListCreateAPIView, ListAPIView, CreateAPIView, DestroyAPIView
from django.http import JsonResponse
from ..models import Club, ClubBanner, ClubRule, ClubIdentity, ClubIncomeDetail
from .serializers import ClubBackendSerializer, BannerImageSerializer, ClubRuleBackendSerializer, CoinSerialize
from users.models import Coin, UserCoin, User, CoinDetail
from rest_framework import status
from utils.functions import reversion_Decorator, value_judge, normalize_fraction, to_decimal
from url_filter.integrations.drf import DjangoFilterBackend
from utils.cache import delete_cache
import json
import datetime
from decimal import Decimal
from django.db.models import Q
from base import code as error_code
from base.exceptions import ParamErrorException
from banker.models import BankerRecord
from utils.cache import get_cache, set_cache, delete_cache


class ClubBackendListView(ListCreateAPIView):
    """
    后台俱乐部列表
    """
    queryset = Club.objects.all()
    serializer_class = ClubBackendSerializer

    @reversion_Decorator
    def post(self, request, *args, **kwargs):
        value = value_judge(request, 'room_title', 'autograph', 'icon', 'room_number', 'coin', 'is_recommend')
        if value == 0:
            return JsonResponse({'Error': '参数不正确'}, status=status.HTTP_400_BAD_REQUEST)
        values = dict(request.data)
        coin = values.pop('coin')
        online = values.pop('online')

        club = Club(**values, coin_id=int(coin))
        club.save()

        # 修改数据，清除缓存
        delete_cache(Club.objects.key)

        # 写入俱乐部在线人数缓存
        Club.objects.save_online(online=online, club_id=club.id)

        return JsonResponse({}, status=status.HTTP_200_OK)


class ClubBackendListDetailView(RetrieveUpdateDestroyAPIView):
    """
    俱乐部详情
    """

    def retrieve(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        try:
            club = Club.objects.get(id=pk)

            # 获取在线人数配置
            play_online = Club.objects.get_online_setting(pk)
        except Exception:
            return JsonResponse({'Error:对象不存在'}, status=status.HTTP_400_BAD_REQUEST)

        club_s = ClubBackendSerializer(club)

        return JsonResponse({'results': club_s.data, 'online': play_online}, status=status.HTTP_200_OK)

    @reversion_Decorator
    def patch(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        try:
            club = Club.objects.get(id=pk)
        except Exception:
            return JsonResponse({'Error:对象不存在'}, status=status.HTTP_400_BAD_REQUEST)
        values = dict(request.data)

        online = values.pop('online')

        club.__dict__.update(**values)
        club.save()

        # 修改数据，清除缓存
        delete_cache(Club.objects.key)

        # 写入俱乐部在线人数缓存
        Club.objects.save_online(online=online, club_id=club.id)

        return JsonResponse({}, status=status.HTTP_200_OK)

    @reversion_Decorator
    def delete(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        try:
            club = Club.objects.get(id=pk)
        except Exception:
            return JsonResponse({'Error:对象不存在'}, status=status.HTTP_400_BAD_REQUEST)
        club.is_dissolve = True
        club.save()
        return JsonResponse({}, status=status.HTTP_200_OK)


class ClubBackendSortView(CreateAPIView):
    """
    俱乐部排序
    """
    def post(self, request, *args, **kwargs):
        sorts = request.data.get('sorts')
        sorts = json.loads(sorts)
        for club_id in sorts:
            club = Club.objects.get(pk=club_id)
            club.user = sorts[club_id]
            club.save()

        delete_cache(Club.objects.key)

        return JsonResponse({}, status=status.HTTP_200_OK)


class ClubBankerSwitchView(CreateAPIView):
    """
    俱乐部散户局头开关
    """
    def post(self, request, *args, **kwargs):
        is_banker = request.data.get('is_banker')
        club_id = int(request.data.get('club_id'))
        club_info = Club.objects.get(id=club_id)
        if is_banker is True or int(is_banker) == 1:
            number = ClubIdentity.objects.filter(club_id=club_id, is_deleted=False).count()
            if number > 0:
                raise ParamErrorException(error_code.API_110111_BACKEND_BANKER)
        club_info.is_banker = is_banker
        club_info.save()

        delete_cache(Club.objects.key)

        return self.response({'code': 0, "is_banker": club_info.is_banker})


class BannerImage(ListCreateAPIView):
    """
    轮播图操作
    """
    queryset = ClubBanner.objects.all()
    serializer_class = BannerImageSerializer

    @reversion_Decorator
    def post(self, request, *args, **kwargs):
        value = value_judge(request, ('image', 'active', 'order', 'language'))
        if value:
            return JsonResponse({'Error': '参数不正确'}, status=status.HTTP_400_BAD_REQUEST)
        values = dict(request.data)
        banner = ClubBanner(**values)
        banner.save()
        return JsonResponse({}, status=status.HTTP_200_OK)


class BannerImageDetail(RetrieveUpdateDestroyAPIView):
    """
    轮播图明细
    """

    def retrieve(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        try:
            banner = ClubBanner.objects.get(id=pk)
        except Exception:
            return JsonResponse({'Error:对象不存在'}, status=status.HTTP_400_BAD_REQUEST)
        club_s = BannerImageSerializer(banner)
        return JsonResponse({'results': club_s.data}, status=status.HTTP_200_OK)

    @reversion_Decorator
    def patch(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        try:
            banner = ClubBanner.objects.get(id=pk)
        except Exception:
            return JsonResponse({'Error:对象不存在'}, status=status.HTTP_400_BAD_REQUEST)
        values = dict(request.data)
        banner.__dict__.update(**values)
        banner.save()
        return JsonResponse({}, status=status.HTTP_200_OK)

    @reversion_Decorator
    def delete(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        try:
            banner = ClubBanner.objects.get(id=pk)
        except Exception:
            return JsonResponse({'Error:对象不存在'}, status=status.HTTP_400_BAD_REQUEST)
        banner.is_delete = True
        banner.save()
        return JsonResponse({}, status=status.HTTP_200_OK)


class ClubRuleList(ListCreateAPIView):
    """
    玩法列表
    """
    queryset = ClubRule.objects.all()
    serializer_class = ClubRuleBackendSerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['title', 'is_dissolve', 'is_deleted']

    @reversion_Decorator
    def post(self, request, *args, **kwargs):
        value = value_judge(request, ('title', 'title_en', 'sort', 'icon'))
        if value:
            return JsonResponse({'Error': '参数不正确'}, status=status.HTTP_400_BAD_REQUEST)
        values = dict(request.data)
        club_rule = ClubRule(**values)
        club_rule.save()
        return JsonResponse({}, status=status.HTTP_200_OK)


class ClubRuleDetail(RetrieveUpdateDestroyAPIView):
    """
    玩法详情
    """

    def retrieve(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        try:
            banner = ClubRule.objects.get(id=pk)
        except Exception:
            return JsonResponse({'Error:对象不存在'}, status=status.HTTP_400_BAD_REQUEST)
        club_s = ClubRuleBackendSerializer(banner)
        return JsonResponse({'results': club_s.data}, status=status.HTTP_200_OK)

    @reversion_Decorator
    def patch(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        try:
            club_rule = ClubRule.objects.get(id=pk)
        except Exception:
            return JsonResponse({'Error:对象不存在'}, status=status.HTTP_400_BAD_REQUEST)
        values = dict(request.data)
        club_rule.__dict__.update(**values)
        club_rule.save()
        return JsonResponse({}, status=status.HTTP_200_OK)

    @reversion_Decorator
    def delete(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        try:
            club_rule = ClubRule.objects.get(id=pk)
        except Exception:
            return JsonResponse({'Error:对象不存在'}, status=status.HTTP_400_BAD_REQUEST)
        club_rule.is_deleted = True
        club_rule.save()
        return JsonResponse({}, status=status.HTTP_200_OK)


class CoinsList(ListAPIView):
    """
    获取货币数据
    """
    queryset = Coin.objects.all()
    serializer_class = CoinSerialize


class ClubBankerList(ListAPIView):
    """
    做庄俱乐部选择列表
    """
    def get(self, request, *args, **kwargs):
        club_list = Club.objects.filter(~Q(is_recommend=0), is_dissolve=False, is_banker=False)
        data = []
        for i in club_list:
            data.append({
                "club_id": i.id,
                "club_name": i.room_title,
                "club_icon": i.icon,
                "is_banker": i.is_banker
            })
        return self.response({'code': 0, 'data': data})


class ClubBankerRecord(ListAPIView):
    """
    俱乐部局头记录
    """
    def get(self, request, *args, **kwargs):
        club_id = int(self.request.GET.get("club_id"))
        identity_list = ClubIdentity.objects.filter(club_id=club_id).order_by("-created_at")
        data = []
        for i in identity_list:
            end_time = ""
            if i.is_deleted is True:
                end_time = i.end_time.strftime('%Y-%m-%d %H:%M')
            user_telephone =  str(i.user.area_code) + " " + str(i.user.telephone)
            data.append({
                "club_identity_id": i.id,
                "club_id": i.club_id,
                "club_name": i.club.room_title,
                "club_icon": i.club.icon,
                "user_name": i.user.nickname,
                "user_telephone": user_telephone,
                "starting_time": i.starting_time.strftime('%Y-%m-%d %H:%M'),
                "is_deleted": i.is_deleted,
                "amount": i.amount,
                "end_time": end_time
            })
        return self.response({'code': 0, 'data': data})


class ClubIncome(ListAPIView):
    """
    做庄局头操作
    """

    def get(self, request, *args, **kwargs):
        key = "CLUB_INCOME_ALL"
        user_id = set_cache(key)
        print("user_id==============", user_id)
        if user_id is None:
            area_code = ""
            telephone = ""
        else:
            user = User.objects.get(id=int(user_id))
            area_code = user.area_code
            telephone = user.telephone
        return self.response({'code': 0, 'area_code': area_code, 'telephone': telephone})

    @reversion_Decorator
    def post(self, request, *args, **kwargs):
        """
         用户做庄
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        key = "CLUB_INCOME_ALL"
        delete_cache(key)
        value = value_judge(request, "area_code", "telephone")
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)

        area_code = int(request.data['area_code'])
        telephone = int(request.data['telephone'])

        try:
            user_info = User.objects.get(area_code=area_code, telephone=telephone)  # 获取用户ID
        except Exception:
            raise ParamErrorException(error_code.API_110110_BACKEND_BANKER)
        set_cache(key, user_info.id)
        return self.response({'code': 0})


class ClubIncomeRecord(ListAPIView):
    """
    局头转账
    """

    def get(self, request, *args, **kwargs):
        """
        转账号记录列表
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        list = ClubIncomeDetail.objects.all().order_by("-created_at")
        data = []
        for i in list:
            data.append({
                "user_id": i.user_id,
                "nickname": i.user.nickname,
                "telephone": i.user.telephone,
                "area_code": i.user.area_code,
                "club_id": i.club_id,
                "coin_name": i.club.coin.name,
                "club_icon": i.club.icon,
                "club_name": i.club.room_title,
                "earn_coin": i.earn_coin,
                "created_at": i.created_at.strftime('%Y-%m-%d %H:%M'),
            })
        return self.response({'code': 0, 'data': data})

    @reversion_Decorator
    def post(self, request, *args, **kwargs):
        """
        转账
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        value = value_judge(request, "club_id", "user_id", "amount")
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        club_id = int(request.data['club_id'])
        user_id = int(request.data['user_id'])
        amount = Decimal(str(request.data['amount']))
        club_info = Club.objects.get_one(pk=club_id)
        coin_info = Coin.objects.get_one(pk=int(club_info.coin_id))
        number = ClubIdentity.objects.filter(club_id=club_id, user_id=user_id, is_deleted=0).count()
        if number <= 0:
            raise ParamErrorException(error_code.API_110116_BACKEND_BANKER)
        user_coin = UserCoin.objects.get(user_id=user_id, coin_id=coin_info.id)
        balance = user_coin.balance
        balance = balance + amount
        if balance < 0:
            raise ParamErrorException(error_code.API_110115_BACKEND_BANKER)
        user_coin.balance = balance
        user_coin.save()
        club_income_detail = ClubIncomeDetail()
        club_income_detail.club = club_info
        club_income_detail.user_id = user_id
        club_income_detail.earn_coin = amount
        club_income_detail.save()
        coin_detail = CoinDetail()
        coin_detail.user = user_coin.user
        coin_detail.coin_name = club_info.coin.name
        coin_detail.amount = amount
        coin_detail.rest = user_coin.balance
        coin_detail.sources = 27
        coin_detail.save()
        return self.response({'code': 0})


class UserBanker(ListAPIView, DestroyAPIView):
    """
    做庄局头操作
    """
    def get(self, request, *args, **kwargs):
        """
        每个俱乐部做庄详情
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        list = ClubIdentity.objects.filter(is_deleted=False).order_by("created_at")
        data = []
        for i in list:
            club_info = Club.objects.get_one(pk=int(i.club_id))
            user_coin = UserCoin.objects.get(coin_id=int(club_info.coin_id), user_id=i.user_id)
            user_balance = user_coin.balance
            telephone = i.user.telephone
            area_code = i.user.area_code
            user_telephone = str(area_code) + " " + str(telephone)
            data.append({
                "club_identity_id": i.id,  # 局头做庄表ID
                "club_id": int(club_info.id),   # 俱乐部表ID
                "club_name": club_info.room_title,    # 俱乐部名称
                "club_icon": club_info.icon,      # 俱乐部图标
                "is_banker": club_info.is_banker,    # 该俱乐部联合做庄散户开关 True  False
                "user_id": i.user_id,         # 做庄用户ID
                "amount": normalize_fraction(i.amount, 8),  # 做庄用户对应货币锁定金额
                "balance": normalize_fraction(user_balance, 8),  # 做庄用户对应货币余额
                "user_telephone": user_telephone,    # 做庄用户手机区号+手机号
                "starting_time": i.starting_time.strftime('%Y-%m-%d %H:%M')     # 做庄开始时间
            })
        return self.response({'code': 0, 'data': data})

    @reversion_Decorator
    def post(self, request, *args, **kwargs):
        """
         用户做庄
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        value = value_judge(request, "club_id", "area_code", "telephone", "amount")
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        club_id = int(request.data['club_id'])
        if club_id == 1:
            raise ParamErrorException(error_code.API_110108_BACKEND_BANKER)
        club_info = Club.objects.get_one(pk=club_id)   # 获取俱乐部信息
        if club_info.is_banker is True:
            raise ParamErrorException(error_code.API_110113_BACKEND_BANKER)

        area_code = int(request.data['area_code'])
        telephone = int(request.data['telephone'])
        amount = int(request.data['amount'])       # 做庄金额只能输入整数
        print("amount==================", type(amount))
        if isinstance(amount, int) is False:        # 为了计算不出错局头押金必须为整数
            raise ParamErrorException(error_code.API_110106_BACKEND_BANKER)

        if 'starting_time' not in request.data:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        starting_time = request.data['starting_time']
        number = ClubIdentity.objects.filter(club_id=int(club_info.id), is_deleted=False).count()
        if number > 0:                 # 判断该俱乐部是否已有有效局头
            raise ParamErrorException(error_code.API_110107_BACKEND_BANKER)

        number = BankerRecord.objects.filter(club_id=club_id, status=1).count()
        if number > 0:
            raise ParamErrorException(error_code.API_110112_BACKEND_BANKER)

        try:
            user_info = User.objects.get(area_code=area_code, telephone=telephone)  # 获取用户ID
        except Exception:
            raise ParamErrorException(error_code.API_110110_BACKEND_BANKER)

        user_id = int(user_info.id)
        if user_info.is_robot is True:
            raise ParamErrorException(error_code.API_110109_BACKEND_BANKER)

        try:
            user_coin = UserCoin.objects.get(user_id=user_id, coin_id=int(club_info.coin_id))
            user_balance = int(user_coin.balance)
        except:
            user_balance = 0
            user_coin = ''
        if user_balance < amount:          # 判断该账号是否给钱开局头
            raise ParamErrorException(error_code.API_110105_BACKEND_BANKER)
        user_coin.balance -= to_decimal(amount)
        user_coin.save()

        coin_detail = CoinDetail()
        coin_detail.user = user_coin.user
        coin_detail.coin_name = club_info.coin.name
        coin_detail.amount = to_decimal('-' + str(amount))
        coin_detail.rest = user_coin.balance
        coin_detail.sources = 24
        coin_detail.save()

        club_identity = ClubIdentity()
        club_identity.club = club_info
        club_identity.user = user_info
        if len(starting_time) == 0:
            starting_time = datetime.datetime.now()
        else:
            starting_time = datetime.datetime.strptime(str(starting_time), '%Y-%m-%d')
        club_identity.starting_time = starting_time
        club_identity.amount = to_decimal(amount)
        club_identity.save()
        club_info.is_banker = False
        club_info.save()
        list = {
            "user_name": user_info.nickname,
            "area_code": user_info.area_code,
            "telephone": user_info.telephone,
            "user_balance": normalize_fraction(user_coin.balance, 8),
            "amount": amount,
            "club_name": club_info.room_title
        }
        return self.response({'code': 0, "list": list})

    @reversion_Decorator
    def delete(self, request, *args, **kwargs):
        club_identity_id = int(self.request.GET.get("club_identity_id"))
        club_id = int(self.request.GET.get("club_id"))
        club_info = Club.objects.get_one(pk=club_id)
        user_id = int(self.request.GET.get("user_id"))
        try:
            announcement = ClubIdentity.objects.get(pk=club_identity_id, user_id=user_id, club_id=club_id)
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        announcement.is_deleted = True
        announcement.end_time = datetime.datetime.now()
        announcement.save()
        user_coin = UserCoin.objects.get(user_id=user_id, coin_id=int(club_info.coin_id))
        user_coin.balance += to_decimal(announcement.amount)
        user_coin.save()
        return self.response({'code': 0, "amount": normalize_fraction(announcement.amount, 8)})
