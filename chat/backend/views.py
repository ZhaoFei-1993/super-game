# -*- coding: UTF-8 -*-
from base.backend import RetrieveUpdateDestroyAPIView, ListCreateAPIView, ListAPIView
from django.http import JsonResponse
from ..models import Club, ClubBanner, ClubRule
from .serializers import ClubBackendSerializer, BannerImageSerializer, ClubRuleBackendSerializer, CoinSerialize
from users.models import Coin
from rest_framework import status
from utils.functions import reversion_Decorator, value_judge
from url_filter.integrations.drf import DjangoFilterBackend


class ClubBackendListView(ListCreateAPIView):
    """
    后台俱乐部列表
    """
    queryset = Club.objects.all()
    serializer_class = ClubBackendSerializer

    @reversion_Decorator
    def post(self, request, *args, **kwargs):
        value = value_judge(request, ('room_title', 'autograph', 'icon', 'room_number', 'coin', 'is_recommend'))
        if value:
            return JsonResponse({'Error': '参数不正确'}, status=status.HTTP_400_BAD_REQUEST)
        values = dict(request.data)
        coin = values.pop('coin')
        club = Club(**values, coin_id=int(coin))
        club.save()
        return JsonResponse({}, status=status.HTTP_200_OK)


class ClubBackendListDetailView(RetrieveUpdateDestroyAPIView):
    """
    俱乐部详情
    """

    def retrieve(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        try:
            club = Club.objects.get(id=pk)
        except Exception:
            return JsonResponse({'Error:对象不存在'}, status=status.HTTP_400_BAD_REQUEST)
        club_s = ClubBackendSerializer(club)
        return JsonResponse({'results': club_s.data}, status=status.HTTP_200_OK)

    @reversion_Decorator
    def patch(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        try:
            club = Club.objects.get(id=pk)
        except Exception:
            return JsonResponse({'Error:对象不存在'}, status=status.HTTP_400_BAD_REQUEST)
        values = dict(request.data)
        club.__dict__.update(**values)
        club.save()
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
