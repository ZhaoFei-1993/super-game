# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
import random
import bisect


class Command(BaseCommand):
    """
    带权重的随机数
    """
    help = "带权重的随机数"

    prize = ['A', 'B', 'C', 'D']

    def handle(self, *args, **options):
        choices = {
            'A': 0,
            'B': 0,
            'C': 0,
            'D': 0,
        }
        for i in range(1, 100000):
            choice = self.prize[self.weight_choice([50000, 30000, 19999, 1])]
            choices[choice] += 1

        print('choices = ', choices)

    @staticmethod
    def weight_choice(weight):
        """
        :param weight: prize对应的权重序列
        :return:选取的值在原列表里的索引
        """
        weight_sum = []
        sum = 0
        for a in weight:
            sum += a
            weight_sum.append(sum)
        t = random.randint(0, sum - 1)
        return bisect.bisect_right(weight_sum, t)
