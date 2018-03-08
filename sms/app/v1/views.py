# -*- coding: UTF-8 -*-
from base.app import ListCreateAPIView

from . import serializers
from wsms import sms
from ...models import Sms
from base import code as error_code
from datetime import datetime
import time
import pytz
from django.conf import settings


class SmsView(ListCreateAPIView):
    """
    发送手机短信
    """
    serializer_class = serializers.SmsSerializer
    queryset = Sms.objects.all()

    def post(self, request, *args, **kwargs):
        """
        发送注册时手机短信验证码
        """
        super().post(request, *args, **kwargs)

        telephone = request.data.get('telephone')

        # 判断距离上次发送是否超过了60秒
        record = Sms.objects.filter(telephone=telephone).order_by('-id').first()
        if record is not None:
            last_sent_time = record.created_at.astimezone(pytz.timezone(settings.TIME_ZONE))
            current_time = time.mktime(datetime.now().timetuple())
            if current_time - time.mktime(last_sent_time.timetuple()) <= settings.SMS_PERIOD_TIME:
                return self.response({'code': error_code.API_40104_SMS_PERIOD_INVALID})

        code = sms.code()
        model = Sms()
        model.telephone = telephone
        model.code = code
        model.message = '你好，你的验证码为：' + code + '，10分钟内有效。'
        model.type = Sms.NORMAL
        model.status = Sms.READY
        model.save()

        return self.response({'code': error_code.API_0_SUCCESS})


class SmsVerifyView(ListCreateAPIView):
    """
    校验手机短信验证码
    """
    serializer_class = serializers.SmsSerializer
    queryset = Sms.objects.all()

    def post(self, request, *args, **kwargs):
        message = Sms.objects.get(id=request.data.get('sms_code_id'))

        # 短信发送时间
        code_time = message.created_at.astimezone(pytz.timezone(settings.TIME_ZONE))
        code_time = time.mktime(code_time.timetuple())
        current_time = time.mktime(datetime.now().timetuple())

        # 判断code_id有效性
        if message is None:
            return self.response({'code': error_code.API_40101_SMS_CODE_ID_INVALID})

        # 判断code有效性
        if message.code != request.data.get('code'):
            return self.response({'code': error_code.API_40103_SMS_CODE_INVALID})

        # 判断code是否过期
        if (settings.SMS_CODE_EXPIRE_TIME > 0) and (current_time - code_time > settings.SMS_CODE_EXPIRE_TIME):
            return self.response({'code': error_code.API_40102_SMS_CODE_EXPIRED})

        # 若校验通过，则更新短信发送记录表状态为校验通过
        message.is_passed = True
        message.save()

        return self.response({'code': error_code.API_0_SUCCESS})
