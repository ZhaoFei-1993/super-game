# -*- coding: UTF-8 -*-
from base.app import ListCreateAPIView
from . import serializers
from base.app import ListAPIView
from base.function import LoginRequired
from .serializers import MessageListSerialize
from wsms import sms
from base import code as error_code
from datetime import datetime
import time
import pytz
from django.conf import settings
from base.exceptions import ParamErrorException


class QuizPushView(ListAPIView):
    """
    下注页面推送
    """
    permission_classes = (LoginRequired,)
    serializer_class = MessageListSerialize

    def get_queryset(self):
        # quiz_id = self.request.parser_context['kwargs']['quiz_id']
        # quiz = Quiz.objects.filter(pk=quiz_id)
        # return quiz
        pass

    def list(self, request, *args, **kwargs):
        # results = super().list(request, *args, **kwargs)
        # items = results.data.get('results')
        # data = []
        # for item in items:
        #     data.append(
        #         {
        #             "quiz_id": item['id'],
        #             "quiz_push": item['quiz_push']
        #         }
        #     )
        return self.response({"code": 0})