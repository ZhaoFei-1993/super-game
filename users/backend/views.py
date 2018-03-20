# -*- coding: UTF-8 -*-
from base.backend import CreateAPIView, FormatListAPIView, FormatRetrieveAPIView
from django.db import transaction
from users.models import Coin, CoinLock
from rest_framework import status
from base import code as error_code
from base.exceptions import ParamErrorException
from django.http import HttpResponse
from . import serializers
import json
import rest_framework_filters as filters


class CoinLockSeria(filters.FilterSet):
    """
    竞猜列表筛选
    """
    class Meta:
        model = CoinLock
        fields = {
            "period": ['contains'],
            "profit": ['contains'],
            "limit_start": ['contains'],
            "limit_end": ['contains']
        }


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
    filter_class = CoinLockSeria
    queryset = CoinLock.objects.filter(is_delete=0)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        coins = Coin.objects.get(pk=request.data['Coin'])
        admin = self.request.user

        coinlock = CoinLock()
        coinlock.period = request.data['period']
        coinlock.profit = request.data['profit']/100
        coinlock.limit_start = request.data['limit_start']
        coinlock.limit_end = request.data['limit_end']
        coinlock.Coin = coins
        coinlock.admin = admin
        coinlock.save()

        content = {'status': status.HTTP_201_CREATED}
        return HttpResponse(json.dumps(content), content_type='text/json')

    @transaction.atomic
    def delete(self, request):
        key = request.GET.get('id')
        coinlock = CoinLock.objects.get(pk=key)
        coinlock.is_delete = 1
        coinlock.save()

        content = {'status': status.HTTP_200_OK}
        return HttpResponse(json.dumps(content), content_type='text/json')

    @transaction.atomic
    def put(self, request):
        key = request.GET.get('id')
        coinlock = CoinLock.objects.get(pk=key)

