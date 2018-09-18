# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
import time
from datetime import datetime, timedelta
from utils.cache import get_cache, set_cache
import random
from django.db import transaction, connection
from django.db.models import Q

from quiz.models import Quiz, Option, Record, Rule, OptionOdds, Category
from users.models import User, UserCoin, CoinValue, Coin
from chat.models import Club
from utils.weight_choice import WeightChoice
from utils.functions import make_insert_sql


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

    robot_bet_change_odds = False

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
        quiz_list = Quiz.objects.filter(status=Quiz.PUBLISHING, is_delete=False, begin_at__gt=datetime.now()).order_by('begin_at')
        if len(quiz_list) == 0:
            raise CommandError('当前无进行中的竞猜')

        quizs = self.get_get_quiz(quiz_list)
        quiz_len = len(quizs)

        # 获取所有俱乐部数据
        all_clubs = Club.objects.get_all()
        clubs = []
        for club in all_clubs:
            if int(club.is_recommend) == Club.CLOSE:
                continue
            clubs.append(club)

        # 获取所有竞猜分类数据
        categorys = Category.objects.get_all()

        # 机器人数据
        robot_users = User.objects.filter(is_robot=True)

        # 货币下注金额数据
        coin_values = CoinValue.objects.all().order_by('value')
        map_coin_values = {}
        for coin_value in coin_values:
            if coin_value.coin_id not in map_coin_values:
                map_coin_values[coin_value.coin_id] = []
            map_coin_values[coin_value.coin_id].append(coin_value)

        idx = 0
        values = []
        for quiz in quizs:
            # 按照比赛时间顺序递减下注数
            bet_number = random.randrange(quiz_len + 1, quiz_len * 3 + 1)
            bet_number -= idx * 2

            # 比赛前两个小时下注更密集
            time_now = datetime.now()
            countdown = (quiz.begin_at - time_now).seconds

            # 两个小时内
            if 3600 < countdown <= 7200:
                bet_number *= 2
            elif countdown <= 3600:
                bet_number *= 3

            if bet_number < 2:
                continue

            for n in range(1, bet_number):
                # 随机获取俱乐部
                club = self.get_bet_club(clubs)
                if club is False:
                    continue

                # 随机抽取玩法
                category_type = Category.FOOTBALL
                for category in categorys:
                    if quiz.category_id == category.id:
                        category_type = category.parent_id
                        break
                rule = self.get_bet_rule(quiz.id, category_type)
                if rule is False:
                    continue

                # 随机下注选项
                option = self.get_bet_option(club.id, rule.id)
                if option is False:
                    continue

                # 随机下注用户
                user = self.get_bet_user(robot_users)

                # 随机下注币、赌注
                wager = self.get_bet_wager(club.coin_id, map_coin_values)

                current_odds = option.odds

                current_datetime = str(datetime.now())
                values.append({
                    'type': '0',
                    'quiz_id': str(quiz.id),
                    'user_id': str(user.id),
                    'rule_id': str(rule.id),
                    'option_id': str(option.id),
                    'roomquiz_id': str(club.id),
                    'bet': str(wager),
                    'odds': str(current_odds),
                    'source': str(Record.CONSOLE),
                    'handicap': str(rule.handicap),
                    'earn_coin': '0',
                    'is_distribution': '0',
                    'open_prize_time': current_datetime,
                    'created_at': current_datetime,
                })

                if self.robot_bet_change_odds is True:
                    Option.objects.change_odds(rule.id, club.coin_id, club.id)

                # 用户减少对应币持有数
                # user_coin = UserCoin.objects.get(user=user, coin_id=club.coin_id)
                # user_coin.balance -= wager
                # user_coin.save()

                # 更新俱乐部对应竞猜投注的数据
                Record.objects.update_club_quiz_bet_data(quiz_id=quiz.id, club_id=club.id, user_id=user.id)

                # rule_title = Rule.TYPE_CHOICE[int(rule.type)][1]
                robot_user = '机器人-' + user.nickname + '在'
                coin = Coin.objects.get(pk=club.coin_id)
                vs_info = quiz.host_team + ' VS ' + quiz.guest_team + ' - ' + str(quiz.begin_at)
                self.stdout.write(self.style.SUCCESS(robot_user + club.room_title + '(' + vs_info + ') ' + rule.tips + '下注' + str(wager) + '个' + coin.name))

            idx += 1

        sql = make_insert_sql(table_name='quiz_record', values=values)
        with connection.cursor() as cursor:
            cursor.execute(sql)

        user_generated_datetime.append(current_generate_time)
        set_cache(self.get_key(self.key_today_generated), user_generated_datetime)

        self.stdout.write(self.style.SUCCESS('下注成功'))

    @staticmethod
    def get_get_quiz(quizs):
        """
        进行中的比赛下注权重
        3天数据：今天比赛:明天比赛:后天比赛 = 7:2:1
        4天数据：今天比赛:明天比赛:后天比赛:大后天 = 6:2:1:1
        5天以上数据，则随机用3天或4天数据
        :param quizs:
        :return:
        """
        quiz_choice = {
            0: 7,
            1: 2,
            2: 1,
        }
        if len(quizs) == 4:
            quiz_choice = {
                0: 6,
                1: 2,
                2: 1,
                3: 1,
            }
        elif len(quizs) == 5:
            quiz_choice = {
                0: 60,
                1: 13,
                2: 12,
                3: 8,
                4: 7
            }
        elif len(quizs) >= 6:
            quiz_choice = {
                0: 65,
                1: 8,
                2: 8,
                3: 7,
                4: 7,
                5: 5
            }

        weight_choice = WeightChoice()
        weight_choice.set_choices(quiz_choice)
        date_index = weight_choice.choice()

        # 竞猜以日期分组
        obj = {}
        for quiz in quizs:
            dt = quiz.begin_at.strftime('%Y%m%d')

            dt_len = 0
            try:
                dt_len = len(obj[dt])
            except Exception:
                pass

            if dt_len == 0:
                obj[dt] = []

            obj[dt].append(quiz)

        items = {}
        index = 0
        for idx in sorted(obj):
            items[index] = obj[idx]
            index += 1

        if len(items) <= date_index:
            date_index = len(items) - 1

        return items[date_index]

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
        user_total = random.randint(100, 300)
        start_date, end_date = self.get_date()

        random_datetime = []
        for i in range(0, user_total):
            random_datetime.append(random.randint(start_date, end_date))

        set_cache(self.get_key(self.key_today_random), user_total, 24 * 3600)
        set_cache(self.get_key(self.key_today_random_datetime), random_datetime, 24 * 3600)

    @staticmethod
    def get_bet_club(clubs):
        """
        获取下注的俱乐部
        不同俱乐部选择权重不同
        :return:
        """
        if len(clubs) == 0:
            return False

        club_weight = {
            1: 350,
            2: 100,
            3: 100,
            4: 100,
            6: 350,
            8: 200,
            9: 300,
        }

        weight_choice = WeightChoice()
        weight_choice.set_choices(club_weight)
        club_id = weight_choice.choice()

        club_choice = None
        for club in clubs:
            if int(club.id) == int(club_id):
                club_choice = club
                break

        if club_choice is None:
            raise CommandError('未匹配到俱乐部，club_id = ', club_id)

        return club_choice

    @staticmethod
    def get_bet_rule(quiz_id, category_type):
        """
        获取下注玩法，随机获取
        :param quiz_id:         竞猜ID
        :param category_type:   竞猜分类：2－足球、1－篮球
        :return:
        """
        rules = Rule.objects.filter(quiz_id=quiz_id)
        if len(rules) < 4:
            return False
        if len(rules) == 0:
            return False

        # 4种玩法设置权重，70:20:5:5
        if category_type == Category.BASKETBALL:
            """
            篮球
            """
            rules_weight = {
                4: 70,  # 胜负
                5: 20,  # 让分胜负
                6: 5,  # 大小分
                7: 5,  # 胜分差
            }
        else:
            """
            足球
            """
            rules_weight = {
                0: 60,      # 赛果
                1: 20,      # 让分赛果
                2: 5,       # 比分
                3: 5,       # 总进球
                8: 10       # 亚盘
            }
            if len(rules) == 4:
                rules_weight = {
                    0: 60,  # 赛果
                    1: 20,  # 让分赛果
                    2: 10,  # 比分
                    3: 10,  # 总进球
                }
        weight_choice = WeightChoice()
        weight_choice.set_choices(rules_weight)
        rule_type = weight_choice.choice()

        choice = None
        for rule in rules:
            if int(rule.type) == int(rule_type):
                choice = rule
                break

        if choice is None:
            raise CommandError('未匹配到玩法 quiz_id = ' + str(quiz_id))
        return choice

    @staticmethod
    def get_bet_option(club_id, rule_id):
        """
        获取下注选项，目前随机获取
        :param club_id 俱乐部ID
        :param rule_id 玩法ID
        :return:
        """
        options = OptionOdds.objects.filter(club_id=club_id, option__rule_id=rule_id).order_by('odds')
        if len(options) == 0:
            return False

        # 低赔率下注数权重高于高赔率
        choices = {
            0: 70,
            1: 20,
            2: 10,
        }
        if len(options) == 2:
            choices = {
                0: 50,
                1: 50,
            }

        weight_choice = WeightChoice()
        weight_choice.set_choices(choices)
        idx = weight_choice.choice()

        return options[idx]

    @staticmethod
    def get_bet_user(robot_users):
        """
        随机获取用户
        :param robot_users  机器人数据
        :return:
        """
        secure_random = random.SystemRandom()
        return secure_random.choice(robot_users)

    @staticmethod
    def get_bet_wager(coin_id, coin_values):
        """
        获取用户拥有哪些币种，并返回币种可下注金额
        高价值币种选择较下注金额
        :param coin_id
        :param coin_values
        :return:
        """
        coin_value = coin_values[coin_id]
        values = []
        for coin_val in coin_value:
            values.append(coin_val.value)

        choices = {
            values[0]: 334,
            values[1]: 333,
            values[2]: 333,
        }
        if coin_id == Coin.BTC:
            """
            BTC下币权重
            """
            choices = {
                values[0]: 70,
                values[1]: 29,
                values[2]: 1,
            }
        elif coin_id == Coin.ETH:
            """
            ETH下币权重
            """
            choices = {
                values[0]: 80,
                values[1]: 15,
                values[2]: 5,
            }
        elif coin_id == Coin.USDT:
            """
            USDT下币权重
            """
            choices = {
                values[0]: 80,
                values[1]: 15,
                values[2]: 5,
            }

        weight_choice = WeightChoice()
        weight_choice.set_choices(choices)
        return weight_choice.choice()
