# -*- coding: utf-8 -*-
from aliyunsdkdysmsapi.request.v20170525 import SendSmsRequest
from aliyunsdkdysmsapi.request.v20170525 import QuerySendDetailsRequest
from aliyunsdkcore.client import AcsClient
import uuid
from django.conf import settings
from django.core.management.base import BaseCommand
from ...models import Sms
import json

"""
短信业务调用接口示例，版本号：v20170525

"""

REGION = "cn-hangzhou"
ACCESS_KEY_ID = settings.SMS_APP_KEY
ACCESS_KEY_SECRET = settings.SMS_APP_SECRET

acs_client = AcsClient(ACCESS_KEY_ID, ACCESS_KEY_SECRET, REGION)


def send_sms(business_id, phone_numbers, sign_name, template_code, template_param=None):
    smsRequest = SendSmsRequest.SendSmsRequest()
    # 申请的短信模板编码,必填
    smsRequest.set_TemplateCode(template_code)

    # 短信模板变量参数
    if template_param is not None:
        smsRequest.set_TemplateParam(template_param)

    # 设置业务请求流水号，必填。
    smsRequest.set_OutId(business_id)

    # 短信签名
    smsRequest.set_SignName(sign_name)

    # 短信发送的号码列表，必填。
    smsRequest.set_PhoneNumbers(phone_numbers)

    # 调用短信发送接口，返回json
    smsResponse = acs_client.do_action_with_exception(smsRequest)

    # TODO 业务处理

    return smsResponse


def query_send_detail(biz_id, phone_number, page_size, current_page, send_date):
    queryRequest = QuerySendDetailsRequest.QuerySendDetailsRequest()
    # 查询的手机号码
    queryRequest.set_PhoneNumber(phone_number)
    # 可选 - 流水号
    queryRequest.set_BizId(biz_id)
    # 必填 - 发送日期 支持30天内记录查询，格式yyyyMMdd
    queryRequest.set_SendDate(send_date)
    # 必填-当前页码从1开始计数
    queryRequest.set_CurrentPage(current_page)
    # 必填-页大小
    queryRequest.set_PageSize(page_size)

    # 调用短信记录查询接口，返回json
    queryResponse = acs_client.do_action_with_exception(queryRequest)

    # TODO 业务处理

    return queryResponse


class Command(BaseCommand):
    help = "发送手机短信"

    def handle(self, *args, **options):
        queue_sms = Sms.objects.filter(status=Sms.READY)
        if len(queue_sms) == 0:
            self.stdout.write(self.style.SUCCESS('当前待发送短信队列为空'))

        for queue in queue_sms:
            params = '{"code":"' + queue.code + '"}'
            resp = send_sms(uuid.uuid1(), queue.telephone, settings.SMS_SIGN_NAME, settings.SMS_TEMPLATE_ID, params)
            result = json.loads(resp.decode('utf-8'))
            queue.status = Sms.SUCCESS if result['Code'] == 'OK' else Sms.FAIL
            queue.feedback = resp.decode('utf-8')
            queue.save()
            self.stdout.write(self.style.SUCCESS('执行完成'))
