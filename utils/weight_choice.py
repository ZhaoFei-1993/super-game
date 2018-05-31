# -*- coding: UTF-8 -*-
"""
随机权重封装
"""
import random
import bisect


class WeightChoice:
    choices = {}

    def set_choices(self, choices):
        """
        设置选项及对应权重
        :param choices:
        :return:
        """
        self.choices = choices

    def _get_weight(self):
        """
        获取权重
        :return:
        """
        weight = []
        for choice in self.choices:
            weight.append(self.choices[choice])

        return weight

    def _get_choice(self, idx):
        """
        获取选项
        :param  idx 选项对应的索引值
        :return:
        """
        choices = []
        for choice in self.choices:
            choices.append(choice)

        return choices[idx]

    def choice(self):
        """
        获取选项
        :return:
        """
        weight = self._get_weight()

        weight_sum = []
        choice_sum = 0
        for a in weight:
            choice_sum += a
            weight_sum.append(choice_sum)
        t = random.randint(0, choice_sum - 1)
        return self._get_choice(bisect.bisect_right(weight_sum, t))

    def test(self, number=10000):
        choices = {
            'A': 0,
            'B': 0,
            'C': 0,
            'D': 0,
        }
        for i in range(1, number):
            choice = self.choice()
            choices[choice] += 1

        print('choices = ', choices)

