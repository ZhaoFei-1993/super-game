# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from guess.models import Index_day
import tushare as ts

url = 'http://nufm.dfcfw.com/EM_Finance2014NumericApplication/JS.aspx?cb=jQuery17202690225701728284_1532446114928&type=CT&cmd=DJIA_UI&sty=OCGIFO&st=z&js=((x))&token=4f1862fc3b5e77c150a2b985b12db0fd'


class Command(BaseCommand):
    help = "发送消息"

    def handle(self, *args, **options):
        shang_data = ts.get_k_data('000001', index=True).tail(90)
        sheng_data = ts.get_k_data('399001', index=True).tail(90)
        hsi_data = ts.get_k_data('hkHSI', index=True).tail(90)

        code_dic = {'shang': 1, 'sheng': 3, 'hsi': 5}
        stock_dic = {'shang': shang_data, 'sheng': sheng_data, 'hsi': hsi_data}
        time_dic = {'shang': '15:00:00', 'sheng': '15:00:00', 'hsi': '16:10:00'}

        print('----------')
        for stock_name in stock_dic:
            for index, row in stock_dic[stock_name].iterrows():
                print(row['date'], '   ', row['close'])
                index_day = Index_day()
                index_day.stock_id = code_dic[stock_name]
                index_day.index_value = 0
                index_day.save()
                index_day.index_value = float(row['close'])
                index_day.index_time = row['date'] + ' ' + time_dic[stock_name]
                index_day.created_at = row['date'] + ' ' + '23:59:59'
                index_day.save()
        print('----------')