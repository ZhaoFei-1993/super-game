# -*- coding: UTF-8 -*-
from base.backend import RetrieveUpdateDestroyAPIView, ListCreateAPIView
from django.http import JsonResponse
from rest_framework import status
from ..models import Play, Option, OpenPrice, Number, Animals
from .serializers import PlayBackendSerializer, OptionBackendSerializer, OpenPriceBackendSerializer
from utils.functions import reversion_Decorator, value_judge
from url_filter.integrations.drf import DjangoFilterBackend
from datetime import datetime, timedelta

MARKSIX_CLOSING = 10
MARKSIX_STARTING = 10


class PlaysBackendList(ListCreateAPIView):
    """
    玩法列表
    """
    queryset = Play.objects.all().order_by('id')
    serializer_class = PlayBackendSerializer

    @reversion_Decorator
    def post(self, request, *args, **kwargs):
        value = value_judge(request, ('title', 'title_en', 'is_deleted'))
        if value:
            return JsonResponse({'Error': '参数不正确'}, status=status.HTTP_400_BAD_REQUEST)
        values = dict(request.data)
        play = Play(**values)
        play.save()
        return JsonResponse({}, status=status.HTTP_200_OK)


class PlaysBackendDetail(RetrieveUpdateDestroyAPIView):
    """
    玩法明细
    """

    def retrieve(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        try:
            play = Play.objects.get(id=pk)
        except Exception:
            return JsonResponse({'Error:对象不存在'}, status=status.HTTP_400_BAD_REQUEST)
        plays = PlayBackendSerializer(play)
        return JsonResponse({'results': plays.data}, status=status.HTTP_200_OK)

    @reversion_Decorator
    def patch(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        try:
            play = Play.objects.get(id=pk)
        except Exception:
            return JsonResponse({'Error:对象不存在'}, status=status.HTTP_400_BAD_REQUEST)
        values = dict(request.data)
        play.__dict__.update(**values)
        play.save()
        return JsonResponse({}, status=status.HTTP_200_OK)

    @reversion_Decorator
    def delete(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        try:
            play = Play.objects.get(id=pk)
        except Exception:
            return JsonResponse({'Error:对象不存在'}, status=status.HTTP_400_BAD_REQUEST)
        play.is_deleted = True
        play.save()
        return JsonResponse({}, status=status.HTTP_200_OK)


class OptionsBackendList(ListCreateAPIView):
    """
    选项列表
    """
    queryset = Option.objects.all().order_by('id')
    serializer_class = OptionBackendSerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['option', 'play_id', 'is_deleted']

    @reversion_Decorator
    def post(self, request, *args, **kwargs):
        value = value_judge(request, ('option', 'option_en', 'play_id', 'odds', 'is_deleted'))
        if value:
            return JsonResponse({'Error': '参数不正确'}, status=status.HTTP_400_BAD_REQUEST)
        values = dict(request.data)
        option = Option(**values)
        option.save()
        return JsonResponse({}, status=status.HTTP_200_OK)


class OptionsBackendDetail(RetrieveUpdateDestroyAPIView):
    """
    选项明细
    """

    def retrieve(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        try:
            option = Option.objects.get(id=pk)
        except Exception:
            return JsonResponse({'Error:对象不存在'}, status=status.HTTP_400_BAD_REQUEST)
        options = OptionBackendSerializer(option)
        return JsonResponse({'results': options.data}, status=status.HTTP_200_OK)

    @reversion_Decorator
    def patch(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        try:
            option = Option.objects.get(id=pk)
        except Exception:
            return JsonResponse({'Error:对象不存在'}, status=status.HTTP_400_BAD_REQUEST)
        values = dict(request.data)
        option.__dict__.update(**values)
        option.save()
        return JsonResponse({}, status=status.HTTP_200_OK)

    @reversion_Decorator
    def delete(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        try:
            option = Option.objects.get(id=pk)
        except Exception:
            return JsonResponse({'Error:对象不存在'}, status=status.HTTP_400_BAD_REQUEST)
        option.is_deleted = True
        option.save()
        return JsonResponse({}, status=status.HTTP_200_OK)


class PlayTinyView(ListCreateAPIView):
    """
    返回六合彩的玩法字典格式
    """

    def list(self, request, *args, **kwargs):
        plays = Play.objects.filter(is_deleted=0).order_by('id')
        play = {}
        if plays.exists():
            for x in plays:
                play[str(x.id)] = x.title
        return JsonResponse({'plays': play}, status=status.HTTP_200_OK)


class OpenPriceBackendList(ListCreateAPIView):
    """
    开奖结果
    """
    queryset = OpenPrice.objects.all()
    serializer_class = OpenPriceBackendSerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['issue', 'is_open']

    @reversion_Decorator
    def post(self, request, *args, **kwargs):
        value = value_judge(request, ('issue', 'flat_code', 'special_code', 'closing', 'open', 'next_open', 'is_open'))
        if value:
            return JsonResponse({'Error': '参数不正确'}, status=status.HTTP_400_BAD_REQUEST)
        year = datetime.now().year
        issue = request.data.get('issue')
        object = OpenPrice.objects.filter(issue=issue, open__year=year).order_by('-open')
        values = dict(request.data)
        values['open'] = datetime.strptime(values['open'], "%Y-%m-%d %H:%M:%S") if values['open'] else ''
        values['next_open'] = datetime.strptime(values['next_open'], "%Y-%m-%d %H:%M:%S") if values['next_open'] else ''
        # values['closing'] = datetime.strptime(values['closing'], "%Y-%m-%d %H:%M:%S") if values['closing'] else ''
        values['starting'] = datetime.strptime(values['starting'], "%Y-%m-%d %H:%M:%S") if values['starting'] else ''
        special = int(request.data.get('special_code')) if request.data.get('special_code') else ''
        is_open = values.pop('is_open')
        if special in range(1, 50):
            if object.exists():
                openprice = object.first()
                openprice.__dict__.update(**values)
                num = Number.objects.get(num=special)
                animal = Animals.objects.get(num=special)
                openprice.color = num.color
                openprice.animal = animal.animal
                openprice.element = num.element
                openprice.save()
            else:
                openprice = OpenPrice(**values)
                num = Number.objects.get(num=special)
                animal = Animals.objects.get(num=special)
                openprice.color = num.color
                openprice.animal = animal.animal
                openprice.element = num.element
                openprice.save()
            next_issue = str(int(issue) + 1)
            new_object = OpenPrice(issue=next_issue, open=values['next_open'],
                                   closing=values['next_open'] - timedelta(minutes=MARKSIX_CLOSING),
                                   starting=values['next_open'] + timedelta(minutes=MARKSIX_STARTING))
            new_object.save()
            if is_open == 1:
                openprice.is_open = is_open
                openprice.save()
            return JsonResponse({}, status=status.HTTP_200_OK)
        else:
            return JsonResponse({'Error': '特码不在1-49范围内'}, status=status.HTTP_400_BAD_REQUEST)


class OpenPriceBackendDetail(RetrieveUpdateDestroyAPIView):
    """
    开奖结果详情
    """

    def retrieve(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        try:
            openprice = OpenPrice.objects.get(id=pk)
        except Exception:
            return JsonResponse({'Error:对象不存在'}, status=status.HTTP_400_BAD_REQUEST)
        openprices = OpenPriceBackendSerializer(openprice)
        return JsonResponse({'results': openprices.data}, status=status.HTTP_200_OK)

    @reversion_Decorator
    def patch(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        try:
            openprice = OpenPrice.objects.get(id=pk)
        except Exception:
            return JsonResponse({'Error:对象不存在'}, status=status.HTTP_400_BAD_REQUEST)
        values = dict(request.data)
        is_open = 0
        if 'open' in values:
            values['open'] = datetime.strptime(values['open'], "%Y-%m-%d %H:%M:%S") if values['open'] else ''
            if values != '' and 'closing' not in values:
                values['closing'] = values['open'] - timedelta(minutes=MARKSIX_CLOSING)
            if values != '' and 'starting' not in values:
                values['starting'] = values['open'] + timedelta(minutes=MARKSIX_STARTING)
        if 'next_open' in values:
            values['next_open'] = datetime.strptime(values['next_open'], "%Y-%m-%d %H:%M:%S") if values[
                'next_open'] else ''
        if 'closing' in values:
            values['closing'] = datetime.strptime(values['closing'], "%Y-%m-%d %H:%M:%S") if values['closing'] else ''
        if 'starting' in values:
            values['starting'] = datetime.strptime(values['starting'], "%Y-%m-%d %H:%M:%S") if values[
                'starting'] else ''
        if 'is_open' in request.data:
            is_open = int(values.pop('is_open'))
        if 'special_code' in request.data:
            special = request.data.get('special_code')
            if special:
                special = int(special)
                num = Number.objects.get(num=special)
                animal = Animals.objects.get(num=special)
                openprice.color = num.color
                openprice.animal = animal.animal
                openprice.element = num.element
        openprice.__dict__.update(**values)
        openprice.save()
        if is_open == 1:
            openprice.is_open = is_open
            openprice.save()
            next_issue = str(int(openprice.issue) + 1)
            new_object = OpenPrice(issue=next_issue, open=openprice.next_open,
                                   closing=openprice.next_open - timedelta(minutes=MARKSIX_CLOSING),
                                   starting=openprice.next_open + timedelta(minutes=MARKSIX_STARTING))
            new_object.save()
        return JsonResponse({}, status=status.HTTP_200_OK)
