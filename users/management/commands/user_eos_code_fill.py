# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
import random
from users.models import User, EosCode


class Command(BaseCommand):
    """
    用户EOS充值码填充
    """
    help = "用户EOS充值码填充"

    def handle(self, *args, **options):
        # 获取所有非机器人、非黑名单用户数据
        users = User.objects.filter(is_robot=False, eos_code=0)
        total = len(users)
        print('获取到' + str(total) + '条用户记录')

        print('正在随机获取EOS充值码')
        eos_codes = EosCode.objects.filter(is_used=False, is_good_code=False)[0:1000000]
        print('获取到 ' + str(len(eos_codes)) + ' 条充值码')
        random_codes = []
        while True:
            idx = random.randint(1, len(eos_codes))
            eos_code = eos_codes[idx]

            if eos_code.code in random_codes:
                continue

            if len(random_codes) == total:
                break

            random_codes.append(eos_code.code)
            eos_code.is_used = True
            eos_code.save()

            print('获取到 ' + str(len(random_codes)) + ' 条充值码')

        print('正在填充数据...')
        index = 0
        for user in users:
            user.eos_code = random_codes[index]
            user.save()

            index += 1
            print('剩余处理条数: ', str(total - index))

        print('Success')
