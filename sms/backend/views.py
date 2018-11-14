# -*- coding: UTF-8 -*-
from base.app import ListCreateAPIView
from sms.backend import serializers
from utils.functions import message_code
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
from base.function import LoginRequired
from users.models import RecordMark
from sms.models import Announcement
from django.db.models import Max
from utils.functions import reversion_Decorator, value_judge


class SmsView(ListCreateAPIView):
    """
    发送手机短信
    """
    permission_classes = (LoginRequired,)
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

        code = message_code()
        model = Sms()
        model.area_code = area_code
        model.telephone = telephone
        model.code = code
        model.message = sms_message.replace('{code}', code)
        model.type = 7
        model.status = Sms.READY
        model.save()
        print(model.id)
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


class AnnouncementVerifyView(ListCreateAPIView):
    """
    公告管理
    """
    def get(self, request, *args, **kwargs):
        list = Announcement.objects.filter(is_deleted=False).order_by('order', 'id')
        data = []
        for i in list:
            data.append({
                "id": i.id,
                "carousel_map": i.carousel_map,
                "carousel_map_env": i.carousel_map_en,
                "thumbnail": i.thumbnail,
                "thumbnail_en": i.thumbnail_en,
                "details": i.details,
                "details_en": i.details_en,
                "is_map": i.is_map,
                "order": i.order
            })
        return self.response({'code': 0, 'data': data})

    def post(self, request, *args, **kwargs):
        announcement = Announcement()
        value = value_judge(request, "thumbnail", "details", "thumbnail_en", "details_en")
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        announcement.thumbnail = request.data.get('thumbnail')    # 公告列表
        announcement.thumbnail_en = request.data.get('thumbnail_en')    # 公告列表
        announcement.details = request.data.get('details')    # 详情
        announcement.details_en = request.data.get('detailsn_en')    # 详情
        if 'carousel_map' in request.data:
            announcement.carousel_map = request.data.get('carousel_map')  #轮播图
            if 'carousel_map_en' not in request.data:
                raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
            announcement.carousel_map_en = request.data.get('carousel_map_en')  #轮播图
            announcement.is_map = 1     #是否轮播图
            order = int(Announcement.objects.filter(is_map=True, is_deleted=False).annotate(Max('order')))
            announcement.order = order + 1    #轮播图排序
        announcement.save()
        user_list = []
        RecordMark.objects.insert_all_record_mark(user_list, 7)
        return self.response({'code': 0})

    @reversion_Decorator
    def delete(self, request, *args, **kwargs):
        announcement_id = self.request.parser_context['kwargs']['pk']
        announcement = Announcement.objects.get(pk=announcement_id)
        announcement.is_delete = True
        announcement.save()
        return self.response({'code': 0})


class AnnouncementInfoView(ListCreateAPIView):
    """
    公告管理
    """
    def get(self, request, *args, **kwargs):
        pk = int(self.request.GET.get("pk"))
        list = Announcement.objects.get(id=pk).order_by('order', 'id')
        data = {
            "carousel_map": list.carousel_map,
            "carousel_map_env": list.carousel_map_en,
            "thumbnail": list.thumbnail,
            "thumbnail_en": list.thumbnail_en,
            "details": list.details,
            "details_en": list.details_en,
            "is_map": list.is_map,
            "order": list.order
        }
        return self.response({'code': 0, 'data': data})

    @reversion_Decorator
    def post(self, request, *args, **kwargs):
        value = value_judge(request, "pk")
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        pk = int(request.data['pk'])
        announcement = Announcement.objects.get(pk=pk, is_delete=0)
        if 'thumbnail' in request.data:
            announcement.thumbnail = request.data['thumbnail']
        if 'thumbnail_en' in request.data:
            announcement.thumbnail = request.data['thumbnail_en']
        if 'details' in request.data:
            announcement.details = request.data['details']
        if 'details_en' in request.data:
            announcement.details = request.data['details_en']
        if 'is_map' in request.data:
            announcement.is_map = int(request.data['is_map'])
        if 'carousel_map' in request.data:
            announcement.carousel_map = request.data['carousel_map']
        if 'carousel_map_en' in request.data:
            announcement.carousel_map = request.data['carousel_map_en']
        announcement.save()
        return self.response({'code': 0})


class AnnouncementOrderView(ListCreateAPIView):
    """
    公告排序管理
    """

    @reversion_Decorator
    def post(self, request, *args, **kwargs):
        value = value_judge(request, "list")
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        list = request.data['list']
        for i in list:
            announcement = Announcement.objects.get(pk=int(i['id']), is_delete=0)
            announcement.order = int(i['order'])
            announcement.save()
        return self.response({'code': 0})
