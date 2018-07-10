# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from quiz.models import Rule, Option
from django.db.models import Q
from django.db import transaction
from users.models import User, UserCoin, Coin
from console.models import Address


class Command(BaseCommand):
    # help = "更新选项"
    help = "更新GSG"

    @transaction.atomic()
    def handle(self, *args, **options):
        print('>>>>>>>>>>>>>>>>>>>>>>>> 开始 >>>>>>>>>>>>>>>>>>>>>>>>')
        coin_gsg = Coin.objects.get(id=6)
        i = 1
        s = 1
        a = 1
        for user in User.objects.all():
            if user.is_robot == 0:
                user_coin_number = UserCoin.objects.filter(~Q(address=''), user_id=user.id, coin__is_eth_erc20=True).count()
                if user_coin_number != 0:
                    address = UserCoin.objects.filter(~Q(address=''), user_id=user.id, coin__is_eth_erc20=True).first()
                else:
                    address = Address.objects.select_for_update().filter(user=0, coin_id=Coin.ETH).first()
                    address.user = user.pk
                    address.save()

                gsg_count = UserCoin.objects.filter(user_id=user.id, coin_id=6).count()
                if gsg_count == 0:
                    user_coin = UserCoin()
                    user_coin.coin = coin_gsg
                    user_coin.user = user
                    user_coin.balance = user.integral
                    user_coin.address = address.address
                    user_coin.save()
                else:
                    user_gsg_count = UserCoin.objects.filter(~Q(address=''), user_id=user.id, coin_id=6).count()
                    if user_gsg_count == 0:
                        user_coin = UserCoin.objects.get(user_id=user.id, coin_id=6)
                        user_coin.address = address.address
                        user_coin.save()
                    else:
                        pass
                s += 1
            else:
                gsg_count = UserCoin.objects.filter(user_id=user.id, coin_id=6).count()
                if gsg_count == 0:
                    user_coin = UserCoin()
                    user_coin.coin = coin_gsg
                    user_coin.user = user
                    user_coin.balance = user.integral
                    user_coin.save()
                a += 1
            print(
                "》》》》》》》第" + str(i) + "个用户， ID：" + str(user.id) + ' 《《《《《《《其中已处理'+str(s)+'个用户《《《《《《'+str(a)+'机器人《《《《《《')
            i += 1
        # 88978978979879
        # i = 0
        #
        # for rule in Rule.objects.filter(type=str(Rule.RESULTS)):
        #     rule.tips_en = ' Winner'
        #     rule.save()
        #     i += 1
        #     print('========================> i = ', i)
        #
        # for rule in Rule.objects.filter(type=str(Rule.POLITENESS_RESULTS), tips_en=''):
        #     rule.tips_en = 'Handicap Results'
        #     rule.save()
        #     i += 1
        #     print('========================> i = ', i)
        #
        # for rule in Rule.objects.filter(type=str(Rule.SCORE)):
        #     rule.tips_en = 'Scored'
        #     rule.save()
        #     i += 1
        #     print('========================> i = ', i)
        #
        # for rule in Rule.objects.filter(type=str(Rule.TOTAL_GOAL), tips_en=''):
        #     rule.tips_en = 'Total goals'
        #     rule.save()
        #     i += 1
        #     print('========================> i = ', i)
        #
        # for rule in Rule.objects.filter(type=str(Rule.RESULT)):
        #     rule.tips_en = ' Winner'
        #     rule.save()
        #     i += 1
        #     print('========================> i = ', i)
        #
        # for rule in Rule.objects.filter(type=str(Rule.POLITENESS_RESULT), tips_en=''):
        #     rule.tips_en = 'Handicap Results'
        #     rule.save()
        #     i += 1
        #     print('========================> i = ', i)
        #
        # for rule in Rule.objects.filter(type=str(Rule.SIZE_POINTS), tips_en=''):
        #     rule.tips = '大小分'
        #     rule.tips_en = 'Compare the total score'
        #     rule.save()
        #     i += 1
        #     print('========================> i = ', i)
        #
        # for rule in Rule.objects.filter(type=str(Rule.VICTORY_GAP), tips_en=''):
        #     rule.tips_en = 'Wins the gap'
        #     rule.save()
        #     i += 1
        #     print('========================> i = ', i)
        # 564165465465465465
        # for option in Option.objects.all():
        #     if '主胜' in option.option:
        #         option.option_en = 'Home'
        #     elif '主负' in option.option:
        #         option.option_en = 'Away'
        #     elif '平局' in option.option:
        #         option.option_en = 'Draw'
        #     elif ':' in option.option:
        #         option.option_en = option.option
        #     elif '球' in option.option:
        #         if option.option[0] == '7':
        #             option.option_en = '7+'
        #         else:
        #             option.option_en = option.option[0]
        #     elif option.option == '胜其他' or option.option == '平其他' or option.option == '负其他':
        #         option.option_en = 'Other'
        #     elif '-' in option.option:
        #         option.option_en = option.option
        #     elif '总分大于' in option.option:
        #         option.option_en = 'More than ' + option.option[4:]
        #     elif '总分小于' in option.option:
        #         option.option_en = 'Less than ' + option.option[4:]
        #
        #     option.save()

        # i += 1
        # print('========================> i = ', i)

        print('>>>>>>>>>>>>>>>>>>>>>>>> 结束 >>>>>>>>>>>>>>>>>>>>>>>>')
