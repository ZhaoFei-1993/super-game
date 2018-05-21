# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import time
from utils.cache import get_cache, set_cache
import random
from django.db.models import Sum, F, FloatField
from django.db import transaction

from quiz.models import Quiz, Option, Record, Rule
from users.models import User, UserCoin, CoinValue
from chat.models import Club
from quiz.odds import Game


class Command(BaseCommand):
    """
    机器人下注频率影响因素：
    1.　题目下注数范围
    2.　题目创建时间长短
    3.　题目周期
    4.　赔率调整需要
    目前暂先实现随机时间对进行中的竞猜下注，下注金额随机
    """
    help = "系统用户自动下注"

    # 本日生成的系统用户总量
    key_today_random = 'robot_bet_total'

    # 本日生成的系统用户随机时间
    key_today_random_datetime = 'robot_bet_datetime'

    # 本日已生成的系统用户时间
    key_today_generated = 'robot_bet_quiz_datetime'

    bet_times = 20

    @transaction.atomic()
    def handle(self, *args, **options):
        # 获取当天随机注册用户量
        random_total = get_cache(self.get_key(self.key_today_random))
        random_datetime = get_cache(self.get_key(self.key_today_random_datetime))
        if random_total is None or random_datetime is None:
            self.set_today_random()
            raise CommandError('已生成随机下注时间')

        random_datetime.sort()
        user_generated_datetime = get_cache(self.get_key(self.key_today_generated))
        if user_generated_datetime is None:
            user_generated_datetime = []

        # 算出随机注册时间与已注册时间差集
        diff_random_datetime = list(set(random_datetime) - set(user_generated_datetime))

        current_generate_time = ''
        for dt in diff_random_datetime:
            if self.get_current_timestamp() >= dt:
                current_generate_time = dt
                break

        if current_generate_time == '':
            raise CommandError('非自动下注时间')

        # 获取所有进行中的竞猜
        quizs = Quiz.objects.filter(status=Quiz.PUBLISHING, is_delete=False)
        if len(quizs) == 0:
            raise CommandError('当前无进行中的竞猜')

        for quiz in quizs:
            # 随机获取俱乐部
            club = self.get_bet_club()
            if club is False:
                continue

            # 随机抽取玩法
            rule = self.get_bet_rule(quiz.id)
            if rule is False:
                continue

            # 随机下注选项
            option = self.get_bet_option(rule.id)
            if option is False:
                continue

            # 随机下注用户
            user = self.get_bet_user()

            # 随机下注币、赌注
            wager = self.get_bet_wager(club.coin_id)

            options = Option.objects.select_for_update().filter(rule=rule).order_by('order')
            rates = []
            idx_option = 0
            for o in options:
                rates.append(float(o.odds))
                idx_option += 1

            current_odds = option.odds

            record = Record()
            record.quiz = quiz
            record.user = user
            record.rule = rule
            record.option = option
            record.roomquiz_id = club.id
            record.bet = wager
            record.odds = current_odds
            record.source = Record.CONSOLE
            record.save()

            # 获取奖池总数
            pool_sum = Record.objects.filter(rule=rule).aggregate(Sum('bet'))
            pool = float(pool_sum['bet__sum'])

            # 获取各选项产出猜币数
            option_pays = Record.objects.filter(rule=rule).values('option_id').annotate(
                pool_sum=Sum(F('bet') * F('odds'), output_field=FloatField())).order_by('-pool_sum')
            pays = []
            tmp_idx = 0
            for opt in options:
                pays.append(0)
                for op in option_pays:
                    if opt.id == op['option_id']:
                        pays[tmp_idx] = op['pool_sum']
                tmp_idx += 1

            coin_value = CoinValue.objects.filter(coin_id=club.coin_id).order_by('-value')
            max_wager = int(coin_value[0].value)
            require_coin = max_wager * self.bet_times
            g = Game(settings.BET_FACTOR, require_coin, max_wager, rates)
            g.bet(pool, pays)
            odds = g.get_oddses()

            # 更新选项赔率
            idx = 0
            for option in options:
                option.odds = odds[idx]
                option.save()

                idx += 1

            # 用户减少对应币持有数
            user_coin = UserCoin.objects.get(user=user, coin_id=club.coin_id)
            user_coin.balance -= wager
            user_coin.save()

        self.stdout.write(self.style.SUCCESS('下注成功'))

    @staticmethod
    def get_key(prefix):
        """
        组装缓存key值
        :param prefix:
        :return:
        """
        return prefix + time.strftime("%Y-%m-%d")

    @staticmethod
    def get_current_timestamp():
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        ts = time.strptime(current_time, "%Y-%m-%d %H:%M:%S")
        return int(time.mktime(ts))

    @staticmethod
    def get_date():
        """
        获取当天0点至24点的时间戳
        :return:
        """
        today = time.strftime("%Y-%m-%d")
        start_date = today + " 00:00:00"
        end_date = today + " 23:59:59"

        ts_start = time.strptime(start_date, "%Y-%m-%d %H:%M:%S")
        ts_end = time.strptime(end_date, "%Y-%m-%d %H:%M:%S")
        return int(time.mktime(ts_start)), int(time.mktime(ts_end))

    def set_today_random(self):
        """
        设置今日随机值，写入到缓存中，缓存24小时后自己销毁
        :return:
        """
        user_total = random.randint(1, 10)
        start_date, end_date = self.get_date()

        random_datetime = []
        for i in range(0, user_total):
            random_datetime.append(random.randint(start_date, end_date))

        set_cache(self.get_key(self.key_today_random), user_total, 24 * 3600)
        set_cache(self.get_key(self.key_today_random_datetime), random_datetime, 24 * 3600)

    @staticmethod
    def get_bet_club():
        """
        获取下注的俱乐部
        :return:
        """
        club = Club.objects.filter(status=Club.PUBLISHING)
        if len(club) == 0:
            return False

        secure_random = random.SystemRandom()
        return secure_random.choice(club)

    @staticmethod
    def get_bet_rule(quiz_id):
        """
        获取下注玩法，随机获取
        :param quiz_id:
        :return:
        """
        rule = Rule.objects.filter(quiz_id=quiz_id)
        if len(rule) == 0:
            return False

        secure_random = random.SystemRandom()
        return secure_random.choice(rule)

    @staticmethod
    def get_bet_option(rule_id):
        """
        获取下注选项，目前随机获取
        :param rule_id 玩法ID
        :return:
        """
        options = Option.objects.filter(rule_id=rule_id)
        if len(options) == 0:
            return False

        secure_random = random.SystemRandom()
        return secure_random.choice(options)

    @staticmethod
    def get_bet_user():
        """
        随机获取用户
        :return:
        """
        users = User.objects.filter(is_robot=True)
        secure_random = random.SystemRandom()
        return secure_random.choice(users)

    @staticmethod
    def get_bet_wager(coin_id):
        """
        获取用户拥有哪些币种，并返回币种可下注金额
        :param coin_id
        :return:
        """
        secure_random = random.SystemRandom()
        coin_value = CoinValue.objects.filter(coin_id=coin_id)
        use_value = secure_random.choice(coin_value)

        return use_value.value
