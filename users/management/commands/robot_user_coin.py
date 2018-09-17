from django.core.management.base import BaseCommand
from users.models import User, UserCoin
from console.models import Address


class Command(BaseCommand):
    help = '机器人实例user coin表记录'

    def handle(self, *args, **options):
        print('脚本开始运行...')
        robots = User.objects.filter(is_robot=True).order_by('-id')

        total_robot = len(robots)
        print('获取到 ' + str(total_robot) + ' 条机器人记录')

        for robot in robots:
            user_coins = UserCoin.objects.filter(user_id=robot.id)
            Address.objects.initial(robot.id, user_coins)

            total_robot -= 1
            print('剩余 ' + str(total_robot) + ' 待处理记录')

        print('done.')
