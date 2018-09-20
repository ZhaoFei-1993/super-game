# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.db import connection
from utils.functions import make_insert_sql


class Command(BaseCommand):
    """
    EOS充值代码生成表
    """
    help = "EOS充值代码生成表"

    def handle(self, *args, **options):
        values = []
        # for code in range(1, 10):     100000000
        for code in range(1000000, 100000001):
            tmp_str = str(code)
            good_cnt = len(tmp_str) - 4

            is_good_code = 0
            if tmp_str.count('0') >= good_cnt or tmp_str.count('1') >= good_cnt or tmp_str.count('2') >= good_cnt\
                    or tmp_str.count('3') >= good_cnt or tmp_str.count('4') >= good_cnt or\
                    tmp_str.count('5') >= good_cnt or tmp_str.count('6') >= good_cnt or tmp_str.count('7') >= good_cnt\
                    or tmp_str.count('8') >= good_cnt or tmp_str.count('9') >= good_cnt:
                is_good_code = 1

            values.append({
                'code': str(code),
                'is_good_code': str(is_good_code),
                'user_id': '0',
            })

        total_values = len(values)
        loop_size = 10000
        total_size = round(total_values / loop_size)

        for i in range(total_size + 1):
            tmp = []
            j = i * loop_size
            j_end = j + loop_size
            j_end = j_end if loop_size <= total_values else total_values
            for j in range(j, j_end):
                tmp.append(values[j])
            sql = make_insert_sql('users_eoscode', tmp)
            with connection.cursor() as cursor:
                cursor.execute(sql)
                print('已插入' + str(len(tmp)) + '条记录')

        print('ok')
