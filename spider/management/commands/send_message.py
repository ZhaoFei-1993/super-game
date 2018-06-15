# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from users.models import User, UserMessage


class Command(BaseCommand):
    help = "发送消息"

    def handle(self, *args, **options):
        for user in User.objects.filter(is_robot=False, is_block=False):
            # 发送信息
            u_mes = UserMessage()
            u_mes.status = 0
            u_mes.user_id = user.id
            u_mes.message_id = 6  # 私人信息
            u_mes.title = '超级游戏团队致歉声明'
            u_mes.content = '超级游戏团队始料未及有大量用户拥入，赠送USDT、HAND、INT活动也导致钱包服务器拥挤。' \
                            '经过连续多天作战，充值已经恢复正常，钱包是基于区块链技术，充值到账时间5〜30分钟。'\
                            '提现将继续采用人工 + 机制审核增加用户账号安全和防虚假用户刷币行为。\n\n' \
                            '超级游戏团队在此就造成用户的困扰及担忧致以诚挚的道歉。\n\n' \
                            'GSG是超级游戏发行的Token；GSG可以锁定分红、投票、返现等权益，GSG将带给用户更多的惊喜，请期待。\n\n' \
                            '微信客服：gsgone （进群）'
            u_mes.save()
