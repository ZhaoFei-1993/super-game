# -*- coding: UTF-8 -*-
from rest_framework import serializers
from marksix.models import Play, OpenPrice, Option, SixRecord, Number, Animals
from base.validators import PhoneValidator
from chat.models import Club
from datetime import datetime
from marksix.functions import change_num
from utils.cache import set_cache, get_cache
from utils.functions import handle_zero


class PlaySerializer(serializers.HyperlinkedModelSerializer):
    """
    玩法
    """
    title = serializers.SerializerMethodField()  # 玩法名称

    class Meta:
        model = Play
        fields = (
            "id", 'title')

    def get_title(self, obj):
        title = obj.title
        if self.context['request'].GET.get('language') == 'en':
            title = obj.title_en
        return title


class OpenPriceSerializer(serializers.HyperlinkedModelSerializer):
    """
    开奖历史
    """

    animal = serializers.SerializerMethodField()  # 动物名称
    element = serializers.SerializerMethodField()  # 五行
    home_field = serializers.SerializerMethodField()  # 家野
    total = serializers.SerializerMethodField()  # 总数
    flat_code = serializers.SerializerMethodField()  # 平码
    special_code = serializers.SerializerMethodField()  # 特码
    single_double = serializers.SerializerMethodField()  # 单双
    special_head = serializers.SerializerMethodField()  # 特头
    special_tail = serializers.SerializerMethodField()  # 特尾
    color = serializers.SerializerMethodField()  # 波色
    pitch = serializers.SerializerMethodField()  # 前端标记

    class Meta:
        model = OpenPrice
        fields = (
            "issue", "flat_code", "special_code", "animal", "color", 'element', 'closing', 'open', 'next_open',
            'starting',
            'home_field', 'total', 'special_head', 'special_tail', 'single_double', 'pitch'
        )

    def get_pitch(self, obj):
        return True

    def get_color(self, obj):
        color = obj.color
        language = self.context['request'].GET.get('language', 'zh')
        if language == 'zh':
            color = Number.WAVE_CHOICE[int(color) - 1][1]
        else:
            color_list = ['RED', 'BLUE', 'GREEN']
            color = color_list[int(color) - 1]
        return color

    def get_single_double(self, obj):
        language = self.context['request'].GET.get('language', 'zh')
        special_code = int(obj.special_code)
        if special_code % 2 != 0:
            if language == 'zh':
                res = '单'
            else:
                res = 'single'
        else:
            if language == 'zh':
                res = '双'
            else:
                res = 'double'
        return res

    def get_special_head(self, obj):
        special_code = obj.special_code
        special_code = change_num(special_code)
        language = self.context['request'].GET.get('language', 'zh')
        if language == 'zh':
            next = '头'
        else:
            next = 'head'
        return str(special_code[0]) + next

    def get_special_tail(self, obj):
        special_code = obj.special_code
        special_code = change_num(special_code)
        language = self.context['request'].GET.get('language', 'zh')
        if language == 'zh':
            next = '尾'
        else:
            next = 'tail'
        return str(special_code[1]) + next

    def get_flat_code(self, obj):
        flat_code = obj.flat_code
        flat_list = flat_code.split(',')
        for num in flat_list:
            flat_list[flat_list.index(num)] = change_num(num)
        return flat_list

    def get_special_code(self, obj):
        special_code = obj.special_code
        return change_num(special_code)

    def get_animal(self, obj):
        animal_index = obj.animal
        if animal_index:
            language = self.context['request'].GET.get('language', 'zh')
            if language == 'zh':
                animal = Animals.ANIMAL_CHOICE[int(animal_index) - 1][1]
            else:
                ANIMAL_EN_CHOICE = [
                    'MOUSE', 'CATTLE', 'TIGER', 'RABBIT', 'DRAGON', 'SNAKE', 'HORSE', 'SHEEP', 'MONKEY', 'CHICKEN',
                    'DOG',
                    'PIG'
                ]
                animal = ANIMAL_EN_CHOICE[int(animal_index) - 1]
        else:
            animal = ''
        return animal

    def get_element(self, obj):
        element_index = obj.element
        if element_index:
            ELEMENT_EN_CHOICE = [
                'GOLD', 'WOOD', 'WATER', 'FIRE', 'SOIL'
            ]
            language = self.context['request'].GET.get('language', 'zh')
            if language == 'zh':
                element = Number.ELEMENT_CHOICE[int(element_index) - 1][1]
            else:
                element = ELEMENT_EN_CHOICE[int(element_index) - 1]
        else:
            element = ''
        return element

    def get_home_field(self, obj):
        special_code = obj.special_code
        language = self.context['request'].GET.get('language', 'zh')
        animal = Animals.objects.filter(num=special_code).first()
        if int(animal.animal) not in [1, 3, 4, 5, 6, 9]:
            if language == 'zh':
                home_file = '家'
            else:
                home_file = 'HOME'
        else:
            if language == 'zh':
                home_file = '野'
            else:
                home_file = 'FIELD'
        return home_file

    def get_total(self, obj):
        flat_code = obj.flat_code.split(',')
        special_code = obj.special_code
        language = self.context['request'].GET.get('language', 'zh')
        sum = int(special_code)
        for num in flat_code:
            sum += int(num)
        if sum >= 175:
            if language == 'zh':
                prev = '大'
            else:
                prev = 'G'
        else:
            if language == 'zh':
                prev = '小'
            else:
                prev = 'L'
        if sum % 2 == 0:
            if language == 'zh':
                next = '双'
            else:
                next = 'D'
        else:
            if language == 'zh':
                next = '单'
            else:
                next = 'S'
        return prev + next


class OddsPriceSerializer(serializers.HyperlinkedModelSerializer):
    """
    玩法赔率
    """

    class Meta:
        model = Option
        fields = (
            "option", "play_id", "odds"
        )


class RecordSerializer(serializers.HyperlinkedModelSerializer):
    """
    下注
    """
    bet_coin = serializers.SerializerMethodField()  # 下注金额
    coin_name = serializers.SerializerMethodField()  # 货币名称
    option_name = serializers.SerializerMethodField()  # 玩法名称
    created_time = serializers.SerializerMethodField()  # 下注时间处理，保留到分钟
    earn = serializers.SerializerMethodField()  # 投注状态，下注结果，下注正确，错误，或者挣钱
    content = serializers.SerializerMethodField()  # 下注内容
    coin_avartar = serializers.SerializerMethodField()  # 币种图标
    one_piece_value = serializers.SerializerMethodField()  # 一注的价值
    status = serializers.SerializerMethodField()  # 状态

    class Meta:
        model = SixRecord
        fields = (
            "bet", "bet_coin", "user_id", "status", "created_time", "issue",
            "content", 'coin_name', 'option_name', 'earn', 'coin_avartar',
            "one_piece_value"
        )

    def get_bet_coin(self, obj):
        return handle_zero(obj.bet_coin)

    def get_content(self, obj):
        play = obj.play
        option_id = obj.option_id
        res = obj.content
        language = self.context['request'].GET.get('language', 'zh')
        res_list = res.split(',')
        if (play.id != 1 and not option_id) or play.id == 8:  # 排除连码和特码
            content_list = []
            for pk in res_list:
                if language == 'zh':
                    title = Option.objects.get(id=pk).option
                else:
                    title = Option.objects.get(id=pk).option_en
                content_list.append(title)
            res = ','.join(content_list)

        # 判断注数
        if language == 'zh':
            last = '注'
        else:
            last = 'notes'
        title = ''
        if option_id:
            title = Option.objects.get(id=option_id).option

        if play.id == 8:
            next = '共' + str(obj.bet) + last
            res = res + '/' + next
            print(res)
        elif play.id != 3 or title == '平码':
            next = '共' + str(len(res.split(','))) + last
            res = res + '/' + next
        else:
            n = len(res.split(','))
            if title == '二中二':
                sum = int(n * (n - 1) / 2)
            else:
                sum = int(n * (n - 1) * (n - 2) / 6)
            next = '共' + str(sum) + last
            res = res + '/' + next
        return res

    def get_coin_name(self, obj):
        club_id = obj.club_id
        coin_name = Club.objects.get(id=club_id).coin.name
        return coin_name

    def get_option_name(self, obj):
        option_id = obj.option_id
        if option_id:
            res = Option.objects.get(id=option_id)
            three_to_two = '三中二'
            option_name = res.option
            if three_to_two in option_name:
                option_name = three_to_two
            if self.context['request'].GET.get('language') == 'en':
                three_to_two = 'Three Hit Two'
                option_name = res.option_en
                if three_to_two in option_name:
                    option_name = three_to_two
        else:
            option_name = obj.play.title
            if self.context['request'].GET.get('language') == 'en':
                option_name = obj.play.title_en

        return option_name

    def get_created_time(self, obj):
        created_time = obj.created_at.strftime('%Y-%m-%d %H:%M')
        return created_time

    def get_earn(self, obj):
        language = 'zh'
        if self.context['request'].GET.get('language') == 'en':
            language = 'en'
        result = obj.status
        earn_coin = obj.earn_coin
        if result == '0':
            if language == 'zh':
                earn = '待开奖'
            else:
                earn = 'AWAIT OPEN'
        else:
            if earn_coin < 0:
                earn = '猜错'
            else:
                earn = '+' + str(float(earn_coin))
                earn = handle_zero(earn)

        return earn

    def get_coin_avartar(self, obj):
        club_id = obj.club_id
        coin_avartar = Club.objects.get(id=club_id).coin.icon
        return coin_avartar

    def get_one_piece_value(self, obj):
        return handle_zero(obj.bet_coin / obj.bet)

    @staticmethod
    def get_status(obj):
        result = obj.status
        earn_coin = obj.earn_coin
        if result == '0':
            status = 0
        else:
            if earn_coin < 0:
                status = 2
            else:
                status = 1
        return status


class ColorSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Number
        fields = (
            'num', 'color'
        )
