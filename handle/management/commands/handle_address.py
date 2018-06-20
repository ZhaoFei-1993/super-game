# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from api.settings import BASE_DIR
import os


class Command(BaseCommand):
    help = "处理地址"

    def handle(self, *args, **options):
        os.chdir(BASE_DIR + '/cache')
        with open('wrong_address.txt', 'r+') as f:
            for line in f:
                line_dt = line.strip().split('	')
                if int(line_dt[0][0]) == 0 and int(line_dt[1]) > 4:
                    with open('corrent_address.txt', 'a+') as fh:
                        fh.write(line_dt[0] + ',' + line_dt[1])
                        fh.write('\n')
                elif int(line_dt[0][0]) == 1 and int(line_dt[1]) > 2:
                    with open('corrent_address.txt', 'a+') as fh:
                        fh.write(line_dt[0] + ',' + line_dt[1])
                        fh.write('\n')
