# -*- coding: UTF-8 -*-
from base.app import ListCreateAPIView, ListAPIView
from .serializers import PlaySerializer, OpenPriceSerializer
from base import code as error_code
from django.conf import settings
from users.models import User
from marksix.models import Play, OpenPrice, Option
from marksix.functions import CountPage
from django.http import JsonResponse


class SortViews(ListAPIView):
    authentication_classes = ()
    serializer_class = PlaySerializer

    def get_queryset(self):
        res = Play.objects.filter(parent_id='', is_deleted=0)
        return res

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')

        return self.response({'code': 0, 'data': items})


class OpenViews(ListAPIView):
    authentication_classes = ()
    serializer_class = OpenPriceSerializer

    def get_queryset(self):
        res = OpenPrice.objects.all()
        return res

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')

        return self.response({'code': 0, 'data': items})


class OddsViews(ListAPIView):
    authentication_classes = ()

    def list(self, request, id):
        res = Option.objects.filter(play_id=id)
        if id == '1':  # 特码，只要获取一个赔率，因为赔率都相等
            res = res[0]
            item = Play.objects.get(id=id)
            res['title'] = item['title']
            res['title_en'] = item['title_en']
            return self.response({'code': 0, 'data': res})
        else:
            for item in res:
                option = item['option']  # 获取结果id
                play = Play.objects.filter(id=option)
                item['title'] = play['title']
                item['title_en'] = play['title_en']

        return JsonResponse({'code': 0})
