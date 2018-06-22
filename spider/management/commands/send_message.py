# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from users.models import User, Message


class Command(BaseCommand):
    help = "发送消息"

    def handle(self, *args, **options):
        message = Message.objects.all().order_by('-id')
        print("message======================", message[0].content)
        # u_mes = Message()
        # u_mes.type = 1
        # u_mes.title = '每日签到赠送活动更换通知'
        # u_mes.content = '亲爱的用户：\n' \
        #                 '超级游戏第一波签到赠送GSG已经圆满结束啦！第二波蓄势待发！从6月24日起，每日签到由之前的送GSG更换为签到送HAND。\n\n' \
        #                 '给您带来不便敬请谅解，如您有任何疑问，欢迎随时联系在线客服微信 gsgone。感谢您对我们的支持与信任，祝您愉快!\n\n' \
        #                 '                                                GSG超级游戏团队\n' \
        #                 '                                                2018年6月22日\n'
        # u_mes.save()
