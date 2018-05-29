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
from base.exceptions import ParamErrorException

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

        telephone = request.data.get('telephone')

        code_type = request.data.get('code_type')
        if int(code_type) not in range(1, 6):
            raise ParamErrorException(error_code.API_40105_SMS_WAGER_PARAMETER)
        # 判断距离上次发送是否超过了60秒
        record = Sms.objects.filter(telephone=telephone).order_by('-id').first()
        if record is not None:
            last_sent_time = record.created_at.astimezone(pytz.timezone(settings.TIME_ZONE))
            current_time = time.mktime(datetime.now().timetuple())
            if current_time - time.mktime(last_sent_time.timetuple()) <= settings.SMS_PERIOD_TIME:
                return self.response({'code': error_code.API_40104_SMS_PERIOD_INVALID})
        sms_message = settings.SMS_CL_SIGN_NAME + settings.SMS_CL_TEMPLATE_REGISTER  # 用户注册
        if int(code_type) == 1:  # 绑定手机
            sms_message = settings.SMS_CL_SIGN_NAME + settings.SMS_CL_BINDING_CELL_PHONE
        elif int(code_type) == 2:  # 解除手机绑定
            sms_message = settings.SMS_CL_SIGN_NAME + settings.SMS_CL_RELIEVE_BINDING_CELL_PHONE
        elif int(code_type) == 3:  # 忘记密保
            sms_message = settings.SMS_CL_SIGN_NAME + settings.SMS_CL_TEMPLATE_SET_PASSCODE
        elif int(code_type) == 5:  # 忘记密码
            sms_message = settings.SMS_CL_SIGN_NAME + settings.SMS_CL_TEMPLATE_RESET_PASSWORD

        code = sms.code()
        model = Sms()
        model.telephone = telephone
        model.code = code
        model.message = sms_message.replace('{code}', code)
        model.type = code_type
        model.status = Sms.READY
        model.save()

        # 消息队列
        redis_conn = Redis()
        q = Queue(connection=redis_conn)
        q.enqueue(send_sms, model.id)
        print("code=================================================", code)
        return self.response({'code': error_code.API_0_SUCCESS})


class SmsVerifyView(ListCreateAPIView):
    """
    校验手机短信验证码
    """
    serializer_class = serializers.SmsSerializer

    def post(self, request, *args, **kwargs):
        if "telephone" not in request.data:
            message = Sms.objects.get(code=request.data.get('code'))
        else:
            message = Sms.objects.get(telephone=request.data.get('telephone'), code=request.data.get('code'))

        code_type = request.data.get('code_type')
        if int(code_type) not in range(1, 5):
            raise ParamErrorException(error_code.API_40105_SMS_WAGER_PARAMETER)

        if int(code_type) != int(message.type):
            return self.response({'code': error_code.API_40106_SMS_PARAMETER})

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
