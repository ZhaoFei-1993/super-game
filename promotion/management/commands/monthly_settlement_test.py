# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from base.app import BaseView
from promotion.models import PromotionRecord
from quiz.models import Record
from guess.models import RecordStockPk, Record as GuessRecord
from marksix.models import SixRecord
from banker.models import BankerRecord
from users.models import CoinDetail


class Command(BaseCommand, BaseView):
    help = "联合做庄结算方法测试"

    def handle(self, *args, **options):
        user_list = (41239, 52120, 78691, 78833, 78899)
        for i in user_list:
            list = CoinDetail.objects.filter(user_id=int(i), sources=20)
            for s in list:
                print(str(s.user_id) +"----"+str(s.created_at.strftime('%Y-%m-%d'))+"----"+ str(s.amount) +"--------"+ str(s.coin_name))
