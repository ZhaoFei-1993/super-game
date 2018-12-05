# -*- coding: UTF-8 -*-
from django.db import models, transaction
from wc_auth.models import Admin
from mptt.models import MPTTModel, TreeForeignKey
import os
from users.models import Coin, User, CoinValue, UserCoin, BankruptcyRecords, UserMessage, CoinDetail
from chat.models import Club
import reversion
from django.conf import settings
from django.db.models import Sum, F, FloatField

from .odds import Game
from decimal import Decimal
from base.models import BaseManager
from utils.cache import set_cache, get_cache, incr_cache, delete_cache
from datetime import date


class CategoryManager(BaseManager):
    """
    竞猜分类数据操作
    """
    key = 'category_data'


@reversion.register()
class Category(MPTTModel):
    FOOTBALL = 2
    BASKETBALL = 1

    name = models.CharField(verbose_name="分类名称", max_length=50)
    name_en = models.CharField(verbose_name="分类名称(英文)", max_length=50, default='')
    icon = models.CharField(verbose_name="分类图标", max_length=255, default='')
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='自身ID', db_index=True, on_delete=models.CASCADE)
    order = models.IntegerField(verbose_name="排序", default=0)
    is_delete = models.BooleanField(verbose_name="是否删除", default=False)

    objects = CategoryManager()

    def save(self, *args, **kwargs):
        """
        重写保存方法
        :param args:
        :param kwargs:
        :return:
        """
        super().save(*args, **kwargs)

        # 删除缓存,等待重新生成
        delete_cache('category_data')

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "竞猜分类表"


class QuizManager(BaseManager):
    """
    体育赛事竞猜数据操作
    """
    key = 'quiz_data'
    order_by = 'begin_at'
    cache_type = 'default'


@reversion.register()
class Quiz(models.Model):
    PUBLISHING = 0  # 已发布
    REPEALED = 1  # 比赛中
    HALF_TIME = 2  # 中场休息
    ENDED = 3  # 已结束
    PUBLISHING_ANSWER = 4  # 已发布答案
    BONUS_DISTRIBUTION = 5  # 已分配奖金
    DELAY = 6  # 推迟比赛
    REPEAT_GAME = 7  # 重复比赛

    TITLE_FIRST_AUDIT = 11  # 题目初审
    TITLE_FINAL_AUDIT = 12  # 题目终审
    OPTION_FIRST_AUDIT = 13  # 答案初审
    OPTION_FINAL_AUDIT = 14  # 答案终审
    TITLE_FIRST_AUDIT_REJECT = 21  # 题目初审不通过
    TITLE_FINAL_AUDIT_REJECT = 22  # 题目终审不通过
    OPTION_FIRST_AUDIT_REJECT = 23  # 答案初审不通过
    OPTION_FINAL_AUDIT_REJECT = 24  # 答案终审不通过

    STATUS_CHOICE = (
        (PUBLISHING, "已发布"),
        (REPEALED, "比赛中"),
        (HALF_TIME, "中场休息"),
        (ENDED, "已结束"),
        (DELAY, "比赛推迟"),
        (REPEAT_GAME, "重复比赛"),
        (PUBLISHING_ANSWER, "已发布答案"),
        (BONUS_DISTRIBUTION, "已分配奖金"),
        (TITLE_FIRST_AUDIT, "题目初审"),
        (TITLE_FINAL_AUDIT, "题目终审"),
        (OPTION_FIRST_AUDIT, "答案初审"),
        (OPTION_FINAL_AUDIT, "答案终审"),
        (TITLE_FIRST_AUDIT_REJECT, "题目初审不通过"),
        (TITLE_FINAL_AUDIT_REJECT, "题目终审不通过"),
        (OPTION_FIRST_AUDIT_REJECT, "答案初审不通过"),
        (OPTION_FINAL_AUDIT_REJECT, "答案终审不通过"),
    )
    category = models.ForeignKey(Category, verbose_name="竞猜分类", on_delete=models.DO_NOTHING)
    host_team = models.CharField(verbose_name="主队", max_length=255)
    host_team_fullname = models.CharField(verbose_name="主队全称", max_length=255, default='')
    host_team_en = models.CharField(verbose_name="主队英文全称", max_length=255, default='')
    host_team_avatar = models.CharField(verbose_name="主队图标", max_length=255, default='')
    host_team_score = models.IntegerField(verbose_name="主队分数", default=0)
    guest_team = models.CharField(verbose_name="客队", max_length=255)
    guest_team_en = models.CharField(verbose_name="客队英文全称", max_length=255, default='')
    guest_team_fullname = models.CharField(verbose_name="客队全称", max_length=255, default='')
    guest_team_avatar = models.CharField(verbose_name="客队图标", max_length=255, default='')
    guest_team_score = models.IntegerField(verbose_name="客队分数", default=0)
    match_name = models.CharField(verbose_name="联赛名称", max_length=50, default="")
    status = models.CharField(verbose_name="状态", choices=STATUS_CHOICE, max_length=2, default=0)
    is_delete = models.BooleanField(verbose_name="是否删除", default=False)
    total_people = models.IntegerField(verbose_name="总参与人数", default=0)
    begin_at = models.DateTimeField(verbose_name="比赛开始时间/截止日期")
    updated_at = models.DateTimeField(verbose_name="最后更新日期", auto_now=True)
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    gaming_time = models.IntegerField(verbose_name="比赛进行时间", default=0)
    match_flag = models.CharField(verbose_name='比赛标识', null=True, max_length=16, default='')
    is_reappearance = models.BooleanField(verbose_name="是否已返现", default=False)
    bet_sum = models.TextField(verbose_name="投注流水", default='')
    profit = models.TextField(verbose_name="盈亏状况", default='')

    objects = QuizManager()

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "竞猜表"


@reversion.register()
class QuizCoin(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "竞猜所支持的货币种类"


@reversion.register()
class Rule(models.Model):
    RESULTS = 0
    POLITENESS_RESULTS = 1
    SCORE = 2
    TOTAL_GOAL = 3
    RESULT = 4
    POLITENESS_RESULT = 5
    SIZE_POINTS = 6
    VICTORY_GAP = 7
    AISA_RESULTS = 8
    TYPE_CHOICE = (
        (RESULTS, "赛果"),
        (POLITENESS_RESULTS, "让分赛果"),
        (SCORE, "比分"),
        (TOTAL_GOAL, "总进球"),
        (RESULT, "胜负"),
        (POLITENESS_RESULT, "让分胜负"),
        (SIZE_POINTS, "大小分"),
        (VICTORY_GAP, "胜分差"),
        (AISA_RESULTS, "亚盘"),
    )
    TYPE_CHOICE_EN = (
        (RESULTS, "Winner"),
        (POLITENESS_RESULTS, "Handicap Results"),
        (SCORE, "Scored"),
        (TOTAL_GOAL, "Total goals"),
        (RESULT, "Winner"),
        (POLITENESS_RESULT, "Handicap Results"),
        (SIZE_POINTS, "Compare the total score"),
        (VICTORY_GAP, "Wins the gap"),
        (AISA_RESULTS, "Asian Handicap"),
    )
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    type = models.CharField(verbose_name="玩法", choices=TYPE_CHOICE, max_length=1, default=RESULTS)
    type_en = models.CharField(verbose_name="英文玩法", choices=TYPE_CHOICE_EN, max_length=1, default=RESULTS)
    tips = models.CharField(max_length=100, verbose_name="选项说明", default="")
    tips_en = models.CharField(max_length=100, verbose_name="英文选项说明", default="")
    home_let_score = models.DecimalField(verbose_name="主队让分，让分赛果，让分胜负玩法适用", max_digits=10, decimal_places=2,
                                         default=0.00)
    guest_let_score = models.DecimalField(verbose_name="客队让分，让分赛果，让分胜负玩法适用", max_digits=10, decimal_places=2,
                                          default=0.00)
    handicap = models.CharField(verbose_name="盘口", max_length=50, default='')
    estimate_score = models.DecimalField(verbose_name="预估分数，大小分玩法适用", max_digits=10, decimal_places=2, default=0.00)
    max_odd = models.DecimalField(verbose_name="最大赔率", max_digits=10, decimal_places=2, default=0.00)
    min_odd = models.DecimalField(verbose_name="最小赔率", max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "竞猜规则表"


class OptionManager(models.Manager):
    """
    选项操作
    """
    require_coin_times = 20  # 最大可赔倍数

    def get_odds_config(self, coin_id, max_rate):
        """
        不同币种不同配置：最大可赔、最大下注数
        :param  coin_id 货币ID
        :param  max_rate 当前最大赔率
        :return: require_coin: Decimal, max_wager: float
        """
        # bet_max = CoinValue.objects.filter(coin_id=coin_id).order_by('-value').first()
        bet_max = Coin.objects.get(pk=coin_id)
        max_bet_value = Decimal(bet_max.betting_toplimit)
        require_coin_times = Decimal(self.require_coin_times)

        if coin_id == Coin.HAND:
            require_coin_times = Decimal(100)

        print('require_coin_times = ', require_coin_times)
        print('max_bet_value = ', max_bet_value)
        print('max_rate = ', max_rate)

        return max_bet_value * require_coin_times * max_rate, max_bet_value

    def change_odds(self, rule_id, coin_id, roomquiz_id):
        """
        变更赔率
        :param rule_id          玩法ID
        :param coin_id          货币ID
        :param roomquiz_id      俱乐部ID
        :return:
        """
        return True  # 暂时关闭下注变更赔率功能
        rule = Rule.objects.get(pk=rule_id)

        options = OptionOdds.objects.select_for_update().filter(option__rule_id=rule_id, club_id=roomquiz_id).order_by(
            'option__order')
        rates = []
        for o in options:
            rates.append(float(o.odds))

        # 获取奖池总数
        pool_sum = Record.objects.filter(rule_id=rule_id, roomquiz_id=roomquiz_id, source=Record.NORMAL).aggregate(
            Sum('bet'))
        pool = pool_sum['bet__sum']
        if pool is None:
            pool = 0
        else:
            pool = float(pool)

        # 获取各选项产出猜币数
        option_pays = Record.objects.filter(rule_id=rule_id, roomquiz_id=roomquiz_id, source=Record.NORMAL).values(
            'option_id').annotate(
            pool_sum=Sum(F('bet') * F('odds'), output_field=FloatField())).order_by('-pool_sum')
        pays = []
        tmp_idx = 0
        for opt in options:
            pays.append(0)
            for op in option_pays:
                if opt.id == op['option_id']:
                    pays[tmp_idx] = op['pool_sum']
            tmp_idx += 1

        require_coin, max_wager = self.get_odds_config(coin_id, rule.max_odd)

        g = Game(settings.BET_FACTOR, require_coin, max_wager, rates)
        g.bet(pool, pays)
        odds = g.get_oddses()

        # 更新选项赔率
        idx = 0
        for option in options:
            option.odds = odds[idx]
            option.save()

            idx += 1


@reversion.register()
class Option(models.Model):
    rule = models.ForeignKey(Rule, on_delete=models.CASCADE)
    option = models.CharField(verbose_name="选项值", max_length=20, default="")
    option_en = models.CharField(verbose_name="英文选项值", max_length=20, default="")
    option_type = models.CharField(verbose_name="选项分类", max_length=20, default="")
    order = models.IntegerField(verbose_name="排序", default=0)
    odds = models.DecimalField(verbose_name="赔率", max_digits=10, decimal_places=2, default=0.00)
    is_right = models.BooleanField(verbose_name="是否正确选项", default=False)
    flag = models.CharField(verbose_name='开奖标记', max_length=8, default="")

    objects = OptionManager()

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "竞猜选项表"


class OptionOddsManager(models.Manager):
    """
    竞猜选项赔率
    """

    @staticmethod
    @transaction.atomic()
    def fill_odds(quiz_list):
        """
        填充赔率
        :param quiz_list    竞猜列表
        :return:
        """
        if len(quiz_list) == 0:
            return True

        clubs = Club.objects.all()

        for club in clubs:
            for quiz in quiz_list:
                has_odds = OptionOdds.objects.filter(quiz=quiz, club_id=club.id).count()
                if has_odds > 0:
                    continue
                # 获取所有rule
                rules = Rule.objects.filter(quiz=quiz)
                if len(rules) == 0:
                    continue
                for rule in rules:
                    options = Option.objects.filter(rule=rule)
                    for option in options:
                        option_odds = OptionOdds()
                        option_odds.club_id = club.id
                        option_odds.quiz = quiz
                        option_odds.option_id = option.id
                        option_odds.odds = option.odds
                        option_odds.save()

    def get_option_odds_title(self, option_odds_ids, language='zh'):
        """
        获取option odds对应的选项标题
        :param  option_odds_ids  选项ID 数组：[1, 2, 3]
        :param  language  语言
        :return: [option_odds_id => option_title]
        """
        option_odds = self.filter(id__in=option_odds_ids)
        option_ids = []
        for oo in option_odds:
            option_ids.append(oo.option_id)

        option_ids = list(set(option_ids))
        options = Option.objects.filter(id__in=option_ids)
        map_option_id_title = {}
        for option in options:
            option_title = option.option
            if language == 'en':
                option_title = option.option_en
                if option_title == '' or option_title is None:
                    option_title = option.option
            map_option_id_title[option.id] = option_title

        map_option_odds_title = {}
        for option_odd in option_odds:
            map_option_odds_title[option_odd.id] = map_option_id_title[option_odd.option_id]

        return map_option_odds_title


class OptionOdds(models.Model):
    club = models.ForeignKey(Club, on_delete=models.DO_NOTHING)
    quiz = models.ForeignKey(Quiz, on_delete=models.DO_NOTHING)
    option = models.ForeignKey(Option, on_delete=models.DO_NOTHING)
    odds = models.DecimalField(verbose_name="赔率", max_digits=10, decimal_places=2, default=1.95)

    objects = OptionOddsManager()

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "竞猜选项赔率表"


class RecordManager(models.Manager):
    """
    竞猜记录数据操作
    """
    KEY_CLUB_QUIZ_BET_COUNT = 'record_club_quiz_bet_count_'
    KEY_CLUB_QUIZ_BET_USERS = 'users'

    def get_club_quiz_bet_count(self, quiz_id, club_id):
        """
        获取俱乐部对应竞猜投注总数
        :param quiz_id:    竞猜ID
        :param club_id:    俱乐部ID
        :return:
        """
        key = self.KEY_CLUB_QUIZ_BET_COUNT + str(quiz_id) + '_' + str(club_id)
        count = get_cache(key)
        if count is None:
            count = Record.objects.filter(quiz_id=quiz_id, roomquiz_id=club_id).count()
            set_cache(key, count)

        return count

    def incre_club_quiz_bet_count(self, quiz_id, club_id):
        """
        俱乐部对应竞猜投注总人数+1
        :param quiz_id:    竞猜ID
        :param club_id:    俱乐部ID
        :return:
        """
        key = self.KEY_CLUB_QUIZ_BET_COUNT + str(quiz_id) + '_' + str(club_id)
        cache_value = get_cache(key)

        if cache_value is None:
            self.get_club_quiz_bet_count(quiz_id=quiz_id, club_id=club_id)

        incr_cache(key=key)

    def get_club_quiz_bet_users(self, quiz_id, club_id, user_id):
        """
        获取俱乐部对应竞猜投注的所有用户ID
        :param quiz_id:     竞猜ID
        :param club_id:     俱乐部ID
        :param user_id:     用户ID
        :return:
        """
        cache_club_dir = settings.CACHE_DIR + '/' + str(club_id) + '/'
        if not os.path.exists(cache_club_dir):
            os.mkdir(cache_club_dir)
        cache_club_quiz_dir = cache_club_dir + str(quiz_id) + '/'
        if not os.path.exists(cache_club_quiz_dir):
            os.mkdir(cache_club_quiz_dir)

        # 从获取中读取，若没有，则从DB中读取，并写入缓存中
        cache_file = cache_club_quiz_dir + self.KEY_CLUB_QUIZ_BET_USERS
        if not os.path.exists(cache_file):
            items = Record.objects.filter(quiz_id=quiz_id, roomquiz_id=club_id).values_list('user_id', flat=True)
            user_ids = list(set(items))

            with open(cache_file, 'a+') as f:
                f.write(','.join(str(x) for x in user_ids))
        else:
            cache_value = None
            obj_cache_file = open(cache_file, 'rU')
            try:
                for line in obj_cache_file:
                    cache_value = line
            finally:
                obj_cache_file.close()

            if cache_value is None:
                return False

            user_ids = cache_value.split(',')

        return str(user_id) in user_ids

    def update_club_quiz_bet_users(self, quiz_id, club_id, user_id):
        """
        增加俱乐部对应竞猜投注的用户ID
        :param quiz_id:
        :param club_id:
        :param user_id:
        :return:
        """
        cache_file = settings.CACHE_DIR + '/' + str(club_id) + '/' + str(quiz_id) + '/' + self.KEY_CLUB_QUIZ_BET_USERS
        if not os.path.exists(cache_file):
            self.get_club_quiz_bet_users(quiz_id, club_id, user_id)
        else:
            with open(cache_file, 'a+') as f:
                f.write(',' + str(user_id))

    def update_club_quiz_bet_data(self, quiz_id, club_id, user_id=0):
        """
        更新俱乐部对应竞猜投注的数据
        :param quiz_id:
        :param club_id:
        :param user_id:
        :return:
        """
        self.incre_club_quiz_bet_count(quiz_id=quiz_id, club_id=club_id)
        self.update_club_quiz_bet_users(quiz_id=quiz_id, club_id=club_id, user_id=user_id)

    def bankruptcy_hand(self, user, roomquiz_id):
        """
        破产赠送hand币活动
        :param user:
        :param roomquiz_id: 俱乐部ID
        :return:
        """
        return True
        user_id = user.id

        user_coin = UserCoin.objects.get(user_id=user_id, coin_id=Coin.HAND)
        record_number = self.filter(user_id=user_id, roomquiz_id=1, type=0).count()
        if int(user_coin.balance) < 1000 and int(roomquiz_id) == 1 and record_number < 1 and user.is_robot is False:
            today = date.today()
            is_give = BankruptcyRecords.objects.filter(user_id=user_id, coin_name="HAND", money=10000,
                                                       created_at__gte=today).count()
            if is_give <= 0:
                user_coin.balance += Decimal(10000)
                user_coin.save()

                coin_bankruptcy = CoinDetail()
                coin_bankruptcy.user = user
                coin_bankruptcy.coin_name = 'HAND'
                coin_bankruptcy.amount = '+' + str(10000)
                coin_bankruptcy.rest = Decimal(user_coin.balance)
                coin_bankruptcy.sources = 4
                coin_bankruptcy.save()

                bankruptcy_info = BankruptcyRecords()
                bankruptcy_info.user = user
                bankruptcy_info.coin_name = 'HAND'
                bankruptcy_info.money = Decimal(10000)
                bankruptcy_info.save()

                user_message = UserMessage()
                user_message.status = 0
                user_message.user = user
                user_message.message_id = 10  # 修改密码
                if user.is_robot is False:
                    user_message.save()


@reversion.register()
class Record(models.Model):
    NORMAL = 0
    CONSOLE = 1
    GIVE = 2

    SOURCE_CHOICE = (
        (NORMAL, "经典竞猜"),
        (CONSOLE, "系统下注"),
        (GIVE, "赠送下注"),
    )
    AWAIT = 0
    CORRECT = 1
    MISTAKE = 2
    ABNORMAL = 3
    TYPE_CHOICE = (
        (AWAIT, "未开奖"),
        (CORRECT, "答对"),
        (MISTAKE, "答错"),
        (ABNORMAL, "异常"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    rule = models.ForeignKey(Rule, on_delete=models.CASCADE)
    option = models.ForeignKey(OptionOdds, on_delete=models.CASCADE)
    roomquiz_id = models.IntegerField(verbose_name="俱乐部题目ID", default=0, db_index=True)
    handicap = models.CharField(verbose_name="盘口", max_length=50, default='')
    odds = models.DecimalField(verbose_name="下注赔率", max_digits=15, decimal_places=3, default=0.000)
    bet = models.DecimalField(verbose_name="下注金额", max_digits=15, decimal_places=3, default=0.000)
    earn_coin = models.DecimalField(verbose_name="获取金额", max_digits=18, decimal_places=8, default=0.00000000)
    source = models.CharField(verbose_name="竞猜来源", choices=SOURCE_CHOICE, max_length=1, default=NORMAL)
    type = models.CharField(verbose_name="状态", choices=TYPE_CHOICE, max_length=1, default=AWAIT)
    created_at = models.DateTimeField(verbose_name="下注时间", auto_now_add=True)
    open_prize_time = models.DateTimeField(verbose_name="开奖时间", auto_now=True)
    is_distribution = models.BooleanField(verbose_name="是否分配过奖金", default=False)

    objects = RecordManager()

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "用户下注表"


class QuizOddsLog(models.Model):
    rule = models.ForeignKey(Rule, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    option = models.ForeignKey(Option, on_delete=models.DO_NOTHING)
    option_title = models.CharField(verbose_name="选项值", max_length=20, default="")
    odds = models.DecimalField(verbose_name="赔率", max_digits=10, decimal_places=2, default=0.00)
    change_at = models.DateTimeField(verbose_name="赔率变化时间")

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "竞猜选项赔率记录表"


class CashBackLog(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    roomquiz_id = models.IntegerField(verbose_name="俱乐部题目ID", default=0)
    platform_sum = models.DecimalField(verbose_name="平台投注额", max_digits=15, decimal_places=3, default=0.000)
    profit = models.DecimalField(verbose_name="盈利", max_digits=15, decimal_places=3, default=0.000)
    cash_back_sum = models.DecimalField(verbose_name="返现总额", max_digits=15, decimal_places=3, default=0.000)
    coin_proportion = models.DecimalField(verbose_name="返现时比例", max_digits=15, decimal_places=2, default=0.00)
    updated_at = models.DateTimeField(verbose_name="发配日期", auto_now=True)

    class Meta:
        verbose_name = verbose_name_plural = "返现记录表"


class ClubProfitAbroad(models.Model):
    roomquiz_id = models.IntegerField(verbose_name="俱乐部ID", default=0)
    robot_platform_sum = models.DecimalField(verbose_name="机器人总投注额", max_digits=18, decimal_places=3, default=0.000)
    robot_platform_rmb = models.DecimalField(verbose_name="机器人总投注额(rmb)", max_digits=18, decimal_places=8,
                                             default=0.00000000)
    platform_sum = models.DecimalField(verbose_name="用户投注额", max_digits=18, decimal_places=3, default=0.000)
    platform_rmb = models.DecimalField(verbose_name="用户投注额(rmb)", max_digits=18, decimal_places=8, default=0.00000000)
    profit = models.DecimalField(verbose_name="真实盈利", max_digits=15, decimal_places=3, default=0.000)
    profit_rmb = models.DecimalField(verbose_name="真实盈利(rmb)", max_digits=15, decimal_places=8, default=0.00000000)
    profit_total = models.DecimalField(verbose_name="总盈利", max_digits=15, decimal_places=3, default=0.000)
    profit_total_rmb = models.DecimalField(verbose_name="总盈利(rmb)", max_digits=15, decimal_places=8, default=0.00000000)
    cash_back_sum = models.DecimalField(verbose_name="返现总额", max_digits=15, decimal_places=3, default=0.000)
    virtual_profit = models.FloatField(verbose_name="虚拟盈利", default=0.000000)
    created_at = models.DateTimeField(verbose_name="创建时间(年月日)", auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "盈利表"


class GsgValue(models.Model):
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    house = models.CharField(verbose_name="交易所名称", max_length=8, default="")
    value = models.DecimalField(verbose_name="价格(ETH)", max_digits=18, decimal_places=8, default=0.00000000)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "GSG价格表"


class EveryDayInjectionValue(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    injection_value = models.DecimalField(verbose_name="总投注值(rmb)", max_digits=18, decimal_places=8, default=0.00000000)
    cash_back_gsg = models.DecimalField(verbose_name="返现的gsg", max_digits=18, decimal_places=8, default=0.00000000)
    is_robot = models.BooleanField(verbose_name="是否机器人", default=False)
    order = models.IntegerField(verbose_name="当日总投注日排名", default=0)
    injection_time = models.DateTimeField(verbose_name="投注时间(年月日)")

    class Meta:
        verbose_name = verbose_name_plural = "投注价值表"


class ChangeRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    change_eth_value = models.DecimalField(verbose_name="兑换值(ETH)", max_digits=18, decimal_places=8, default=0.00000000)
    change_gsg_value = models.DecimalField(verbose_name="兑换值(GSG)", max_digits=18, decimal_places=8, default=0.00000000)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    is_robot = models.BooleanField(verbose_name="是否机器人", default=False)

    class Meta:
        verbose_name = verbose_name_plural = "兑换记录表"
