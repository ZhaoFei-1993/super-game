# -*- coding: UTF-8 -*-
# from django.db.models import Q, Sum
# from rest_framework import serializers
# from ...models import Gsg_Switch
#
#
# class Gsg_SwitchSerializer(serializers.ModelSerializer):
#     """
#     开关序列化
#     """
#     prize_number = serializers.SerializerMethodField()
#     prize_name = serializers.SerializerMethodField()
#
#     class Meta:
#         model = Gsg_Switch
#         fields = ('id', )
#
#     def get_prize_name(self, obj):
#         prize_name = obj.prize_name
#         if self.context['request'].GET.get('language') == 'en' and prize_name == '谢谢参与':
#             prize_name = 'Thanks'
#         if self.context['request'].GET.get('language') == 'en' and prize_name == '再来一次':
#             prize_name = 'Once again'
#         return prize_name
#
#     @staticmethod
#     def get_prize_number(obj):
#         prize_number = obj.prize_number
#         if prize_number == 0:
#             prize_number = ""
#         else:
#             if obj.prize_name == "GSG":
#                 prize_number = normalize_fraction(float(prize_number), 2)
#             else:
#                 coin = Coin.objects.filter(name=obj.prize_name)
#                 prize_number = normalize_fraction(float(prize_number), int(coin[0].coin_accuracy))
#         return prize_number