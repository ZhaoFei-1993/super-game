# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "测试亚盘"

    def handle(self, *args, **options):
        rule_dic = {
            '平手': '0', '平手/半球': '0/0.5', '半球': '0.5', '半球/一球': '0.5/1', '一球': '1', '一球/一球半': '1/1.5',
            '一球半': '1.5', '球半/两球': '1.5/2', '两球': '2', '两球/两球半': '2/2.5', '三球': '3', '三球/三球半': '3/3.5',
            '四球': '4',
        }

        result = '一球/一球半'
        clean_score = -1

        if clean_score < 0:
            print('上盘全负， 下盘全胜')
        else:
            if len(rule_dic[result].split('/')) == 1:
                if clean_score == int(rule_dic[result]):
                    print('上，下 退还本金')
                elif clean_score < int(rule_dic[result]):
                    print('上盘全负， 下盘全胜')
                elif clean_score > int(rule_dic[result]):
                    print('上盘全胜， 下盘全负')
            else:
                if str(clean_score) in rule_dic[result].split('/'):
                    if rule_dic[result].split('/').index(str(clean_score)) == 0:
                        print('上盘负一半， 下盘胜一半')
                    elif rule_dic[result].split('/').index(str(clean_score)) == 1:
                        print('上盘胜一半， 下盘输一半')
                else:
                    if float(clean_score) < float(rule_dic[result].split('/')[0]):
                        print('上盘全负， 下盘全胜')
                    elif float(clean_score) > float(rule_dic[result].split('/')[1]):
                        print('上盘全胜， 下盘全负')

