# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from guess.models import RecordStockPk, Issues, OptionStockPk, Periods
from utils.cache import set_cache, get_cache
from .stock_result_new import GuessPKRecording
import datetime
from django.db.models import Q
from promotion.models import PromotionRecord, UserPresentation
from users.models import RecordMark
from chat.models import Club
from banker.models import BankerRecord


class Command(BaseCommand):
    help = "处理投注表"

    def handle(self, *args, **options):
        issues = Issues.objects.filter(~Q(size_pk_result=''), result_confirm__gte=2, is_open=False).order_by('id')[:10]
        if len(issues) > 0:
            option_obj_dic = {}
            for option in OptionStockPk.objects.all():
                option_obj_dic.update({
                    option.id: {
                        'title': option.title
                    }
                })
            i = 0
            for issue in issues:
                record_stock_pk = GuessPKRecording()
                i += 1
                print('正在处理第 ', i, ' 期,issues_id=', issue.id, '   ', '期数是: ', issue.issue, '    ',
                      datetime.datetime.now())
                # 结算
                records = RecordStockPk.objects.filter(issue_id=issue.id, status=str(RecordStockPk.AWAIT))
                if len(records) > 0:
                    for record_pk in records:
                        record_stock_pk.pk_size(record_pk, option_obj_dic, issue)
                    record_stock_pk.insert_info()

                # 删除缓存中的投注人数, 如果是当日最后一日则不删除缓存，直到下一期的第一期再删除
                key_pk_bet_count = 'record_pk_bet_count' + '_' + str(issue.stock_pk_id)
                pk_bet_count = get_cache(key_pk_bet_count)
                if issue.issue == 48 or issue.issue == 78:
                    pass
                else:
                    if issue.issue == 1:
                        del pk_bet_count[sorted(pk_bet_count)[0]]
                    del pk_bet_count[issue.id]
                    set_cache(key_pk_bet_count, pk_bet_count)

                real_records = RecordStockPk.objects.filter(~Q(source=str(RecordStockPk.ROBOT)), ~Q(club_id=1),
                                                            issue_id=issue.id, status=str(RecordStockPk.OPEN))
                # 推广代理事宜
                if len(real_records) > 0:
                    print('start')
                    PromotionRecord.objects.insert_all(real_records, 5, 1)
                    PromotionRecord.objects.club_flow_statistics(real_records, 5)
                    print('end')

                    # 公告记录标记
                    RecordMark.objects.insert_all_record_mark(real_records.values_list('user_id', flat=True), 6)

                    # 联合坐庄事宜
                    banker_result = []
                    target = {}
                    profit_result = {}
                    bet_sum_result = {}
                    for club in Club.objects.get_all():
                        target.update({club.id: {"key_id": issue.id, "bet_sum": 0, "profit": 0, "club_id": club.id, "status": 2}})
                    profit_list = real_records.values('bets', 'earn_coin', 'club_id')
                    for profit_dt in profit_list:
                        target[profit_dt['club_id']]['bet_sum'] += profit_dt['bets']
                        if profit_dt['earn_coin'] < 0:
                            target[profit_dt['club_id']]['profit'] += abs(profit_dt['earn_coin'])
                        else:
                            target[profit_dt['club_id']]['profit'] -= profit_dt['earn_coin'] - profit_dt['bets']
                    for key, value in target.items():
                        banker_result.append(value)
                        bet_sum_result.update({key: value['bet_sum']})
                        profit_result.update({key: value['profit']})
                    # BankerRecord.objects.banker_settlement(banker_result, 5)

                    # 计算盈亏
                    issue.bet_sum = str(bet_sum_result)
                    issue.profit = str(profit_result)
                    issue.save()

                else:
                    # 计算盈亏
                    profit_result = {}
                    bet_sum_result = {}
                    for club in Club.objects.get_all():
                        bet_sum_result.update({club.id: 0})
                        profit_result.update({club.id: 0})
                    issue.bet_sum = str(bet_sum_result)
                    issue.profit = str(profit_result)
                    issue.save()

                issue.is_open = True
                issue.save()
        else:
            print('当前无需要处理的数据')
