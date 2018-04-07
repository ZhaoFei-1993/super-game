# -*- coding: UTF-8 -*-
from base.backend import CreateAPIView, FormatListAPIView, FormatRetrieveAPIView, DestroyAPIView
from django.db import transaction
from users.models import Coin, CoinLock
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

        coinlock = CoinLock()
        coinlock.period = request.data['period']
        coinlock.profit = int(request.data['profit'])/100
        coinlock.limit_start = request.data['start_date']
        coinlock.limit_end = request.data['end_date']
        coinlock.Coin = coins
        coinlock.admin = admin
        coinlock.save()

        content = {'status': status.HTTP_201_CREATED}
        return HttpResponse(json.dumps(content), content_type='text/json')


class CoinLockDetailView(DestroyAPIView, FormatRetrieveAPIView):
    serializer_class = serializers.CoinLockSerializer

    def get_queryset(self, request, *args, **kwargs):
        print("request.data============", request.data)
        print("kwargs['index']============", kwargs['index'])
        id = self.request.data['pk']
        return CoinLock.objects.get(pk=id, is_delete=0)

    def delete(self, request, *args, **kwargs):
        coinlovk_id = self.request.parser_context['kwargs']['pk']
        coinlock = CoinLock.objects.get(pk=coinlovk_id)
        coinlock.is_delete = True
        coinlock.save()
        content = {'status': status.HTTP_200_OK}
        return HttpResponse(json.dumps(content), content_type='text/json')


class LoginView(CreateAPIView):
    """
    后台管理员登录
    """
