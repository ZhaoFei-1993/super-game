# -*- coding: UTF-8 -*-
from base.app import CreateAPIView, ListCreateAPIView, ListAPIView, DestroyAPIView, RetrieveAPIView, \
    RetrieveUpdateAPIView
from base.function import LoginRequired
from users.models import UserCoin, CoinDetail
from users.models import User, DailyLog, UserInvitation, UserMessage
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



class PromotionInfoView(ListAPIView):
    """
    用户邀请信息
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        return

    def list(self, request, *args, **kwargs):
        type = request.GET.get('type')

        user = self.request.user
        user_avatar = user.avatar          # 用户头像
        nowadays_day = datetime.datetime.now().strftime('%Y-%m-%d')
        nowadays_now = str(nowadays_day) + ' 00:00:00'
        nowadays_old = str(nowadays_day) + ' 23:59:59'
        yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        yesterday_now = str(nowadays_day) + ' 00:00:00'
        yesterday_old = str(nowadays_day) + ' 23:59:59'
        # all_club = Club.objects.filter(~Q(is_recommend=0))
        # club_icon_list = [club.icon for club in all_club]
        # club_id_list = [club.id for club in all_club]
        # coin_name_list = [club.coin.name for club in all_club]
        nowadays_number = UserInvitation.objects.filter(Q(created_at__lte=nowadays_old)|Q(created_at__gte=nowadays_now), inviter_id=user.id).count()            # 今天邀请人数
        yesterday_number = UserInvitation.objects.filter(Q(created_at__lte=yesterday_old)|Q(created_at__gte=yesterday_now), inviter_id=user.id).count()        # 昨天邀请人数
        all_invitation = UserInvitation.objects.filter(inviter_id=user.id, inviter_type=1, status=2).aggregate(Sum('money'))        # 昨天邀请人数
        all_user_number = UserInvitation.objects.filter(inviter_id=user.id, ).aggregate(Sum('money'))        # 昨天邀请人数
        sum_gsg = all_invitation['money__sum'] if all_invitation['money__sum'] is not None else 0


        return self.response(
            {'code': 0})


class PromotionUserView(ListAPIView):
    """
    扫描二维码拿用户消息
    """

    def get_queryset(self):
        return

    def list(self, request, *args, **kwargs):
        user_id = request.GET.get('from_id')
        try:
            user_info = User.objects.get(pk=user_id)
        except DailyLog.DoesNotExist:
            return 0

        invitation_code = user_info.invitation_code
        pk = user_info.pk
        nickname = user_info.nickname
        avatar = user_info.avatar
        username = user_info.username
        return self.response({'code': 0, "pk": pk, "nickname": nickname, "avatar": avatar, "username": username,
                              "invitation_code": invitation_code})



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