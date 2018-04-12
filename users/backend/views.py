# -*- coding: UTF-8 -*-
from base.backend import CreateAPIView, FormatListAPIView, FormatRetrieveAPIView, DestroyAPIView, UpdateAPIView
from django.db import transaction
from users.models import Coin, CoinLock, Admin
from rest_framework import status
from base import code as error_code
from base.exceptions import ParamErrorException
from django.http import HttpResponse
from . import serializers
import json
import rest_framework_filters as filters


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

    @transaction.atomic
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
            "profit": str(coinlock.profit*100),
            "start_date": coinlock.limit_start,
            "end_date": coinlock.limit_end,
            "url": ''
        }
        return HttpResponse(json.dumps(data), content_type='text/json')

    def delete(self, request, *args, **kwargs):
        coinlovk_id = self.request.parser_context['kwargs']['pk']
        coinlock = CoinLock.objects.get(pk=coinlovk_id)
        coinlock.is_delete = True
        coinlock.save()
        content = {'status': status.HTTP_200_OK}
        return HttpResponse(json.dumps(content), content_type='text/json')

    @transaction.atomic
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

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        admin = self.request.user
        exchange_rate = request.data['exchange_rate']

        coin = Coin()
        coin.icon = request.data['icon']
        if int(exchange_rate) != 0:
            coin.exchange_rate = exchange_rate
        coin.name = request.data['name']
        coin.type = request.data['type']
        coin.is_lock = request.data['is_lock']
        coin.admin = admin
        coin.save()

        content = {'status': status.HTTP_201_CREATED}
        return HttpResponse(json.dumps(content), content_type='text/json')


class CurrencyDetailView(DestroyAPIView, FormatRetrieveAPIView, UpdateAPIView):
    serializer_class = serializers.CurrencySerializer

    def get(self, request, *args, **kwargs):
        id = int(kwargs['pk'])
        coin = Coin.objects.get(pk=id)
        is_lock = coin.is_lock
        if is_lock == False:
            is_lock = 0
        if is_lock == True:
            is_lock = 1
        data = {
            "icon": coin.icon,
            "name": coin.name,
            "type": coin.type,
            "exchange_rate": coin.exchange_rate,
            "is_lock": str(is_lock),
            "url": ''
        }
        return HttpResponse(json.dumps(data), content_type='text/json')

    def delete(self, request, *args, **kwargs):
        coin_id = self.request.parser_context['kwargs']['pk']
        coin = Coin.objects.get(pk=coin_id)
        coin.is_delete = True
        coin.save()
        content = {'status': status.HTTP_200_OK}
        return HttpResponse(json.dumps(content), content_type='text/json')

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        id = int(kwargs['pk'])
        coin = Coin.objects.get(pk=id)
        coin.icon = request.data['icon']
        coin.name = request.data['name']
        coin.type = request.data['type']
        coin.exchange_rate = request.data['exchange_rate']
        coin.is_lock = request.data['is_lock']
        coin.save()
        content = {'status': status.HTTP_200_OK}
        return HttpResponse(json.dumps(content), content_type='text/json')


class LoginView(CreateAPIView):
    """
    后台管理员登录
    """
