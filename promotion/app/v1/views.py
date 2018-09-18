# -*- coding: UTF-8 -*-
from base.app import CreateAPIView, ListCreateAPIView, ListAPIView, DestroyAPIView, RetrieveAPIView, \
    RetrieveUpdateAPIView
from base.function import LoginRequired
from base import code as error_code
from base.exceptions import ParamErrorException
import os
from django.conf import settings
from utils.functions import random_invitation_code
import pygame
from PIL import Image
import qrcode
from chat.models import Club
from django.db.models import Q, Sum
from users.models import UserInvitation
import datetime
from users.models import Coin
from promotion.models import UserPresentation
import calendar
import re
from datetime import timedelta
from utils.functions import normalize_fraction, value_judge, get_sql



class PromotionInfoView(ListAPIView):
    """
    用户邀请信息
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        return

    def list(self, request, *args, **kwargs):
        user = self.request.user
        nowadays_day = datetime.datetime.now().strftime('%Y-%m-%d')
        nowadays_now = str(nowadays_day) + ' 00:00:00'
        nowadays_old = str(nowadays_day) + ' 23:59:59'
        yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        yesterday_now = str(yesterday) + ' 00:00:00'
        yesterday_old = str(yesterday) + ' 23:59:59'

        user_avatar = user.avatar          # 用户头像
        nowadays_number = UserInvitation.objects.filter(Q(created_at__lte=nowadays_old)|Q(created_at__gte=nowadays_now), inviter_id=user.id).count()            # 今天邀请人数
        yesterday_number = UserInvitation.objects.filter(Q(created_at__lte=yesterday_old)|Q(created_at__gte=yesterday_now), inviter_id=user.id).count()        # 昨天邀请人数
        all_user_number = UserInvitation.objects.filter(inviter_id=user.id, inviter_type=1).count()        # 总邀请人数
        all_user_gsg = UserInvitation.objects.filter(inviter_id=user.id, inviter_type=1, status=2).aggregate(Sum('money'))
        sum_gsg = all_user_gsg['money__sum'] if all_user_gsg['money__sum'] is not None else 0                     # 总邀请获得GSG数
        return self.response({'code': 0, "data": {
            "user_avatar": user_avatar,
            "nowadays_number": nowadays_number,
            "yesterday_number": yesterday_number,
            "all_user_number": all_user_number,
            "sum_gsg": sum_gsg
        }})


class PromotionListView(ListAPIView):
    """
    邀请俱乐部流水
    """

    def get_queryset(self):
        return

    def list(self, request, *args, **kwargs):
        user = self.request.user
        print("user==========================", user.id)
        type = self.request.GET.get('type')
        regex = re.compile(r'^(1|2|3|4)$')              # 1.今天 2.昨天 3.本月 4.上月
        if type is None or not regex.match(type):
            raise ParamErrorException(error_code.API_10104_PARAMETER_EXPIRED)
        if type == 1:
            created_at_day = datetime.datetime.now().strftime('%Y-%m-%d')  # 当天日期
            start = str(created_at_day) + ' 00:00:00'  # 一天开始时间
            end = str(created_at_day) + ' 23:59:59'  # 一天结束时间
        elif type == 2:
            yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            start = str(yesterday) + ' 00:00:00'
            end = str(yesterday) + ' 23:59:59'
        elif type == 3:
            year = datetime.date.today().year  # 获取当前年份
            month = datetime.date.today().month  # 获取当前月份
            weekDay, monthCountDay = calendar.monthrange(year, month)  # 获取当月第一天的星期和当月的总天数
            start = datetime.date(year, month, day=1).strftime('%Y-%m-%d')                #  获取当月第一天
            end = datetime.date(year, month, day=monthCountDay).strftime('%Y-%m-%d')           # 获取当前月份最后一天
            start = str(start) + ' 00:00:00'
            end = str(end) + ' 23:59:59'
        else:
            this_month_start = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, 1)
            end = this_month_start - timedelta(days=1)              # 上个月的最后一天
            start = str(datetime.datetime(end.year, end.month, 1).strftime('%Y-%m-%d')) + ' 00:00:00'       # 上个月i第一天
            end = str(end.strftime('%Y-%m-%d')) + ' 23:59:59'

        coin_id_list = []
        all_club = Club.objects.get_all()
        club_list = {}
        coins = Coin.objects.get_all()
        map_coin = {}
        for coin in coins:
            map_coin[coin.id] = coin
        for i in all_club:
            coin_id_list.append(str(i.id))
            coin = map_coin[i.coin.id]
            club_list[i.coin.id] = {
                "club_id": i.id,
                "coin_name": coin.name,
                "coin_id": coin.id
            }
        sql = "select club_id, sum(pu.bet_water) as sum_bet_water, sum(pu.dividend_water), sum(pu.income) from promotion_userpresentation pu"
        sql += " where pu.club_id in (" + ','.join(coin_id_list) + ")"
        sql += " and pu.user_id = '" + str(user.id) + "'"
        sql += " and pu.created_at >= '" + str(start) + "'"
        sql += " and pu.created_at <= '" + str(end) + "'"
        sql += " group by pu.club_id"
        sql += " order by sum_bet_water desc"
        print("sql==========================",sql)
        coin_number = get_sql(sql)
        print("coin_number===================================", coin_number)




        return self.response({'code': 0})



class PromotionMergeView(ListAPIView):
    """
    生成用户推广页面
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        return

    def list(self, request, *args, **kwargs):
        user = self.request.user

        sub_path = str(user.id % 10000)

        spread_path = settings.MEDIA_ROOT + 'spread/'
        if not os.path.exists(spread_path):
            os.mkdir(spread_path)

        save_path = spread_path + sub_path
        if not os.path.exists(save_path):
            os.mkdir(save_path)

        if user.invitation_code == '':
            invitation_code = random_invitation_code()
            user.invitation_code = invitation_code
            user.save()
        else:
            invitation_code = user.invitation_code

        if self.request.GET.get('language') == 'en':
            if os.access(save_path + '/qrcode_' + str(user.id) + '_new_en.jpg', os.F_OK):
                base_img = settings.MEDIA_DOMAIN_HOST + '/spread/' + sub_path + '/spread_' + str(user.id) + '_en.jpg'
                qr_data = settings.SUPER_GAME_SUBDOMAIN + '/#/register?from_id=' + str(user.id)
                return self.response({'code': 0, "base_img": base_img, "qr_data": qr_data})
        else:
            if os.access(save_path + '/qrcode_' + str(user.id) + '_new.png', os.F_OK):
                base_img = settings.MEDIA_DOMAIN_HOST + '/spread/' + sub_path + '/spread_' + str(user.id) + '_new.jpg'
                qr_data = settings.SUPER_GAME_SUBDOMAIN + '/#/register?from_id=' + str(user.id)
                return self.response({'code': 0, "base_img": base_img, "qr_data": qr_data})

        pygame.init()
        # 设置字体和字号
        font = pygame.font.SysFont('Microsoft YaHei', 60)
        # 渲染图片，设置背景颜色和字体样式,前面的颜色是字体颜色
        ftext = font.render(invitation_code, True, (0, 0, 0), (255, 255, 255))
        # 保存图片
        invitation_code_address = save_path + '/invitation_code_' + str(user.id) + '.jpg'
        pygame.image.save(ftext, invitation_code_address)  # 图片保存地址
        # qr_data = settings.SUPER_GAME_SUBDOMAIN + '/#/register?from_id=' + str(user.id)

        if self.request.GET.get('language') == 'en':
            base_img = Image.open(settings.BASE_DIR + '/uploads/fx_bk_en.jpg')
        else:
            base_img = Image.open(settings.BASE_DIR + '/uploads/fx_bk.jpg')
        qr_data = settings.SUPER_GAME_SUBDOMAIN + '/#/register?from_id=' + str(user.id)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=8,
            border=1,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image()
        base_img.paste(qr_img, (238, 960))
        ftext = Image.open(
            settings.BASE_DIR + '/uploads/spread/' + sub_path + '/invitation_code_' + str(user.id) + '.jpg')
        base_img.paste(ftext, (300, 915))  # 插入邀请码

        # 保存二维码图片
        qr_img.save(save_path + '/qrcode_' + str(user.id) + '.jpg')
        # qr_img = settings.MEDIA_DOMAIN_HOST + '/spread/' + sub_path + '/qrcode_' + str(user_id) + '.png'
        # 保存推广图片
        if self.request.GET.get('language') == 'en':
            base_img.save(save_path + '/spread_' + str(user.id) + '_new_en.jpg', quality=90)
            base_img = settings.MEDIA_DOMAIN_HOST + '/spread/' + sub_path + '/spread_' + str(user.id) + '_new_en.jpg'
        else:
            base_img.save(save_path + '/spread_' + str(user.id) + '_new.jpg', quality=90)
            base_img = settings.MEDIA_DOMAIN_HOST + '/spread/' + sub_path + '/spread_' + str(user.id) + '_new.jpg'

        qr_data = settings.SUPER_GAME_SUBDOMAIN + '/#/register?from_id=' + str(user.id)

        return self.response({'code': 0, "base_img": base_img, "qr_data": qr_data, "invitation_code": invitation_code})