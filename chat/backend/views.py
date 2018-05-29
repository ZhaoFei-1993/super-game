# -*- coding: UTF-8 -*-
from base.backend import RetrieveUpdateDestroyAPIView, ListCreateAPIView
from django.http import JsonResponse
from ..models import Club
from .serializers import ClubBackendSerializer
from rest_framework import status
from utils.functions import reversion_Decorator, value_judge

class ClubBackendListView(ListCreateAPIView):
    """
    后台俱乐部列表
    """
    queryset = Club.objects.all()
    serializer_class = ClubBackendSerializer

    @reversion_Decorator
    def post(self, request, *args, **kwargs):
        value = value_judge(request, ('room_title', 'autograph', 'icon', 'room_number', 'coin','is_recommend'))
        if value:
            return JsonResponse({'Error':'参数不正确'}, status=status.HTTP_400_BAD_REQUEST)
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
            return JsonResponse({'Error:对象不存在'}, status = status.HTTP_400_BAD_REQUEST)
        club_s = ClubBackendSerializer(club)
        return JsonResponse({'results':club_s.data}, status=status.HTTP_200_OK)

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
            return JsonResponse({'Error:对象不存在'}, status = status.HTTP_400_BAD_REQUEST)
        club.is_dissolve = True
        club.save()
        return JsonResponse({},status=status.HTTP_200_OK)