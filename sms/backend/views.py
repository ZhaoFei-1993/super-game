# -*- coding: UTF-8 -*-
from base.backend import ListCreateAPIView
from sms.backend import serializers
from wsms import sms
from sms.models import Sms
from base import code as error_code
from datetime import datetime
import time
import pytz
from django.conf import settings
from base.exceptions import ParamErrorException
from users.models import User

from rq import Queue
from redis import Redis
from sms.consumers import send_sms


class SmsView(ListCreateAPIView):
    """
    发送手机短信
    """
    serializer_class = serializers.SmsSerializer

    def post(self, request, *args, **kwargs):
        """
        发送注册时手机短信验证码
        """
        super().post(request, *args, **kwargs)

        area_code = request.data.get('area_code')
        telephone = request.data.get('telephone')
        # 判断距离上次发送是否超过了60秒
        record = Sms.objects.filter(telephone=telephone).order_by('-id').first()
        if record is not None:
            last_sent_time = record.created_at.astimezone(pytz.timezone(settings.TIME_ZONE))
            current_time = time.mktime(datetime.now().timetuple())
            if current_time - time.mktime(last_sent_time.timetuple()) <= settings.SMS_PERIOD_TIME:
                raise ParamErrorException(error_code.API_40104_SMS_PERIOD_INVALID)
        if area_code is None or area_code == '':
            area_code = 86

        sms_message = '【财务系统】尊敬的用户您好！您正在修改密码。验证码：{code}，如不是您本人的操作，请忽略。'

        code = sms.code()
        model = Sms()
        model.area_code = area_code
        model.telephone = telephone
        model.code = code
        model.message = sms_message.replace('{code}', code)
        model.type = 7
        model.status = Sms.READY
        model.save()

        # 消息队列
        redis_conn = Redis()
        q = Queue(connection=redis_conn)
        q.enqueue(send_sms, model.id)
        return self.response({'code': error_code.API_0_SUCCESS})


class SmsVerifyView(ListCreateAPIView):
    """
    校验手机短信验证码
    """
    serializer_class = serializers.SmsSerializer

    def post(self, request, *args, **kwargs):
        area_code = request.data.get('area_code')
        if 'area_code' not in request.data.get:
            area_code = 86
        if "telephone" not in request.data:
            message = Sms.objects.get(code=request.data.get('code'),type=7)
        else:
            message = Sms.objects.get(area_code=area_code, telephone=request.data.get('telephone'),
                                      code=request.data.get('code'),type=7)

        if request.data.get('telephone') is not None:
            record = Sms.objects.filter(area_code=area_code, telephone=request.data.get('telephone'),type=7).order_by(
                '-id').first()
            if not record:
                raise ParamErrorException(error_code.API_40106_SMS_PARAMETER)
            if int(record.degree) >= 5:
                raise ParamErrorException(error_code.API_40107_SMS_PLEASE_REGAIN)
            else:
                record.degree += 1
                record.save()

        # 短信发送时间
        code_time = message.created_at.astimezone(pytz.timezone(settings.TIME_ZONE))
        code_time = time.mktime(code_time.timetuple())
        current_time = time.mktime(datetime.now().timetuple())

        # 判断code_id有效性
        if message is None:
            raise ParamErrorException(error_code.API_40101_SMS_CODE_ID_INVALID)

        # 判断code有效性
        if message.code != request.data.get('code'):
            raise ParamErrorException(error_code.API_40103_SMS_CODE_INVALID)

        # 判断code是否过期
        if (settings.SMS_CODE_EXPIRE_TIME > 0) and (current_time - code_time > settings.SMS_CODE_EXPIRE_TIME):
            raise ParamErrorException(error_code.API_40102_SMS_CODE_EXPIRED)

        # 若校验通过，则更新短信发送记录表状态为校验通过
        message.is_passed = True
        message.save()

        return self.response({'code': error_code.API_0_SUCCESS})

