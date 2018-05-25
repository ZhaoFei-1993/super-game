# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import requests
from bs4 import BeautifulSoup

base_url = 'http://www.310win.com/buy/jingcai.aspx?typeID=105&oddstype=2'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}


class Command(BaseCommand):
    help = "爬取足球比赛"

    def handle(self, *args, **options):
        response = requests.get(base_url, headers=headers)
        soup = BeautifulSoup(response.text, 'lxml')
        data = list(soup.select('table[class="socai"]')[0].children)
        for dt in list(data)[13:14]:
            print(list(dt.children)[5]['title'][5:])
            print(list(list(dt.children)[1].strings)[0])
            print(dt['gamename'])

            print(dt.select('td[align="right"]')[0].a.string)
            print('VS')
            print(dt.select('td[align="left"]')[0].a.string)

            score_list = list(dt.children)[23]
            no_let_score_list = list(list(score_list.children)[0].children)[0]
            let_score_list = list(list(score_list.children)[0].children)[1]

            for no_let_score in list(no_let_score_list)[1:4]:
                print(no_let_score['title'] + ':' + no_let_score.string)

            print('-----------------')

            for let_score in list(let_score_list)[1:4]:
                print(let_score['title'] + ':' + let_score.string)
