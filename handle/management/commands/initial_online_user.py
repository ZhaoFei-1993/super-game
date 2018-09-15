# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
import random
from base.app import BaseView
from datetime import datetime
from utils.cache import get_cache, set_cache


class Command(BaseCommand, BaseView):
    help = "明天初始在线用户设置"

    def handle(self, *args, **options):
        day = datetime.now().strftime('%Y-%m-%d')
        number_key = "NOW_INITIAL_ONLINE_USER_" + str(day)
        time_key = "INITIAL_ONLINE_TIME_NOW_" + str(day)
        initial_online_user_time = get_cache(time_key)
        if initial_online_user_time is not None:
            raise CommandError(str(day) + '初始化人数已经设置')

        list = [{
            "time_one": " 00:00:00",
            "time_two": " 08:59:59",
            "time_three": " 09:00:00",
            "time_four": " 11:59:59",
            "time_five": " 12:00:00",
            "time_six": " 19:59:59",
            "time_seven": " 20:00:00",
            "time_eight": " 22:59:59",
            "time_nine": " 23:00:00",
            "time_ten": " 23:59:59"
        }]
        set_cache(time_key, list, 24 * 3600)

        initial_online_user_number = get_cache(number_key)
        if initial_online_user_number is None or initial_online_user_number == '':
            data = [{
                "1": {
                    "int": {
                        "quiz": int(random.uniform(6,8)),
                        "guess": int(random.uniform(3,4)),
                        "six": int(random.uniform(6,8)),
                        "bjl": int(random.uniform(30,40)),
                        "lhd": int(random.uniform(15,20))
                    },
                    "usdt": {
                        "quiz": int(random.uniform(30,40)),
                        "guess": int(random.uniform(15,20)),
                        "six": int(random.uniform(30,40)),
                        "bjl": int(random.uniform(50,60)),
                        "lhd": int(random.uniform(35,40))
                    },
                    "btc": {
                        "quiz": int(random.uniform(10,15)),
                        "guess": int(random.uniform(5,8)),
                        "six": int(random.uniform(10,15)),
                        "bjl": int(random.uniform(50,60)),
                        "lhd": int(random.uniform(35,40)),
                    },
                    "hand": {
                        "quiz": int(random.uniform(180,220)),
                        "guess": int(random.uniform(100,150)),
                        "six": int(random.uniform(180,220)),
                        "bjl": int(random.uniform(310,350)),
                        "lhd": int(random.uniform(250,300)),
                    },
                    "eth": {
                        "quiz": int(random.uniform(50,60)),
                        "guess": int(random.uniform(35,40)),
                        "six": int(random.uniform(50,60)),
                        "bjl": int(random.uniform(120,150)),
                        "lhd": int(random.uniform(80,100)),
                    },
                    "bch": {
                        "quiz": int(random.uniform(10,15)),
                        "guess": int(random.uniform(5,8)),
                        "six": int(random.uniform(10,15)),
                        "bjl": int(random.uniform(50,60)),
                        "lhd": int(random.uniform(35,40)),
                    },
                    "soc": {
                        "quiz": int(random.uniform(6,8)),
                        "guess": int(random.uniform(3,4)),
                        "six": int(random.uniform(6,8)),
                        "bjl": int(random.uniform(30,40)),
                        "lhd": int(random.uniform(15,20)),
                    },
                    "db": {
                        "quiz": int(random.uniform(6,8)),
                        "guess": int(random.uniform(3,4)),
                        "six": int(random.uniform(6,8)),
                        "bjl": int(random.uniform(30,40)),
                        "lhd": int(random.uniform(15,20)),
                    }
                },
                "2": {
                    "int": {
                        "quiz": int(random.uniform(20,30)),
                        "guess": int(random.uniform(10,15)),
                        "six": int(random.uniform(20,30)),
                        "bjl": int(random.uniform(70,90)),
                        "lhd": int(random.uniform(34,45)),
                    },
                    "usdt": {
                        "quiz": int(random.uniform(70,90)),
                         "guess": int(random.uniform(35,45)),
                        "six": int(random.uniform(70,90)),
                        "bjl": int(random.uniform(80,100)),
                        "lhd": int(random.uniform(50,60)),
                    },
                    "btc": {
                        "quiz": int(random.uniform(20,25)),
                         "guess": int(random.uniform(13,16)),
                        "six": int(random.uniform(20,25)),
                        "bjl": int(random.uniform(80,150)),
                        "lhd": int(random.uniform(50,60)),
                    },
                    "hand": {
                        "quiz": int(random.uniform(280,300)),
                         "guess": int(random.uniform(200,250)),
                        "six": int(random.uniform(280,300)),
                        "bjl": int(random.uniform(410,450)),
                        "lhd": int(random.uniform(350,400)),
                    },
                    "eth": {
                        "quiz": int(random.uniform(80,100)),
                         "guess": int(random.uniform(50,60)),
                        "six": int(random.uniform(80,100)),
                        "bjl": int(random.uniform(220,250)),
                        "lhd": int(random.uniform(150,200)),
                    },
                    "bch": {
                        "quiz": int(random.uniform(20,25)),
                         "guess": int(random.uniform(13,16)),
                        "six": int(random.uniform(20,25)),
                        "bjl": int(random.uniform(80,100)),
                        "lhd": int(random.uniform(50,60)),
                    },
                    "soc": {
                        "quiz": int(random.uniform(20,30)),
                        "guess": int(random.uniform(10,15)),
                        "six": int(random.uniform(20,30)),
                        "bjl": int(random.uniform(70,90)),
                        "lhd": int(random.uniform(35,45)),
                    },
                    "db": {
                        "quiz": int(random.uniform(20,30)),
                         "guess": int(random.uniform(10,15)),
                        "six": int(random.uniform(20,30)),
                        "bjl": int(random.uniform(70,90)),
                        "lhd": int(random.uniform(35,45)),
                    }
                },
                "3": {
                    "int": {
                        "quiz": int(random.uniform(6,8)),
                         "guess": int(random.uniform(3,4)),
                        "six": int(random.uniform(6,8)),
                        "bjl": int(random.uniform(30,40)),
                        "lhd": int(random.uniform(15,20)),
                    },
                    "usdt": {
                        "quiz": int(random.uniform(30,40)),
                         "guess": int(random.uniform(15,20)),
                        "six": int(random.uniform(30,40)),
                        "bjl": int(random.uniform(50,60)),
                        "lhd": int(random.uniform(35,40)),
                    },
                    "btc": {
                        "quiz": int(random.uniform(15,19)),
                         "guess": int(random.uniform(8,13)),
                        "six": int(random.uniform(15,19)),
                        "bjl": int(random.uniform(50,60)),
                        "lhd": int(random.uniform(35,40)),
                    },
                    "hand": {
                        "quiz": int(random.uniform(180,220)),
                         "guess": int(random.uniform(100,150)),
                        "six": int(random.uniform(180,220)),
                        "bjl": int(random.uniform(310,350)),
                        "lhd": int(random.uniform(250,300)),
                    },
                    "eth": {
                        "quiz": int(random.uniform(50,60)),
                         "guess": int(random.uniform(35,40)),
                        "six": int(random.uniform(50,60)),
                        "bjl": int(random.uniform(120,150)),
                        "lhd": int(random.uniform(80,100)),
                    },
                    "bch": {
                        "quiz": int(random.uniform(15,19)),
                         "guess": int(random.uniform(8,13)),
                        "six": int(random.uniform(15,19)),
                        "bjl": int(random.uniform(50,60)),
                        "lhd": int(random.uniform(35,40)),
                    },
                    "soc": {
                        "quiz": int(random.uniform(6,8)),
                         "guess": int(random.uniform(3,4)),
                        "six": int(random.uniform(6,8)),
                        "bjl": int(random.uniform(30,40)),
                        "lhd": int(random.uniform(15,20)),
                    },
                    "db": {
                        "quiz": int(random.uniform(6,8)),
                         "guess": int(random.uniform(3,4)),
                        "six": int(random.uniform(6,8)),
                        "bjl": int(random.uniform(30,40)),
                        "lhd": int(random.uniform(15,20)),
                    }
                },
                "4": {
                    "int": {
                        "quiz": int(random.uniform(40,50)),
                         "guess": int(random.uniform(20,30)),
                        "six": int(random.uniform(40,50)),
                        "bjl": int(random.uniform(100,150)),
                        "lhd": int(random.uniform(60,80)),
                    },
                    "usdt": {
                        "quiz": int(random.uniform(100,160)),
                         "guess": int(random.uniform(60,80)),
                        "six": int(random.uniform(100,160)),
                        "bjl": int(random.uniform(140,160)),
                        "lhd": int(random.uniform(70,80)),
                    },
                    "btc": {
                        "quiz": int(random.uniform(38,45)),
                         "guess": int(random.uniform(20,25)),
                        "six": int(random.uniform(38,45)),
                        "bjl": int(random.uniform(140,160)),
                        "lhd": int(random.uniform(70,80)),
                    },
                    "hand": {
                        "quiz": int(random.uniform(350,400)),
                         "guess": int(random.uniform(300,330)),
                        "six": int(random.uniform(350,400)),
                        "bjl": int(random.uniform(510,550)),
                        "lhd": int(random.uniform(450,500)),
                    },
                    "eth": {
                        "quiz": int(random.uniform(140,150)),
                         "guess": int(random.uniform(70,80)),
                        "six": int(random.uniform(140,150)),
                        "bjl": int(random.uniform(300,350)),
                        "lhd": int(random.uniform(250,300)),

                    },
                    "bch": {
                        "quiz": int(random.uniform(38,45)),
                         "guess": int(random.uniform(20,25)),
                        "six": int(random.uniform(38,45)),
                        "bjl": int(random.uniform(140,160)),
                        "lhd": int(random.uniform(70,80)),
                    },
                    "soc": {
                        "quiz": int(random.uniform(40,50)),
                         "guess": int(random.uniform(20,30)),
                        "six": int(random.uniform(40,50)),
                        "bjl": int(random.uniform(100,160)),
                        "lhd": int(random.uniform(60,80)),
                    },
                    "db": {
                        "quiz": int(random.uniform(40,50)),
                         "guess": int(random.uniform(20,30)),
                        "six": int(random.uniform(40,50)),
                        "bjl": int(random.uniform(100,150)),
                        "lhd": int(random.uniform(60,80)),
                    }
                },
                "5": {
                    "int": {
                        "quiz": int(random.uniform(20,30)),
                         "guess": int(random.uniform(10,15)),
                        "six": int(random.uniform(20,30)),
                        "bjl": int(random.uniform(70,90)),
                        "lhd": int(random.uniform(35,45)),
                    },
                    "usdt": {
                        "quiz": int(random.uniform(70,90)),
                         "guess": int(random.uniform(35,45)),
                        "six": int(random.uniform(70,90)),
                        "bjl": int(random.uniform(50,60)),
                        "lhd": int(random.uniform(35,40)),
                    },
                    "btc": {
                        "quiz": int(random.uniform(25,30)),
                         "guess": int(random.uniform(16,21)),
                        "six": int(random.uniform(25,30)),
                        "bjl": int(random.uniform(50,60)),
                        "lhd": int(random.uniform(35,40)),
                    },
                    "hand": {
                        "quiz": int(random.uniform(280,300)),
                         "guess": int(random.uniform(200,250)),
                        "six": int(random.uniform(280,300)),
                        "bjl": int(random.uniform(410,450)),
                        "lhd": int(random.uniform(350,400)),
                    },
                    "eth": {
                        "quiz": int(random.uniform(50,60)),
                         "guess": int(random.uniform(35,40)),
                        "six": int(random.uniform(50,60)),
                        "bjl": int(random.uniform(220,250)),
                        "lhd": int(random.uniform(150,200)),
                    },
                    "bch": {
                        "quiz": int(random.uniform(25,30)),
                         "guess": int(random.uniform(16,21)),
                        "six": int(random.uniform(25,30)),
                        "bjl": int(random.uniform(50,60)),
                        "lhd": int(random.uniform(35,40)),
                    },
                    "soc": {
                        "quiz": int(random.uniform(20,30)),
                         "guess": int(random.uniform(10,15)),
                        "six": int(random.uniform(20,30)),
                        "bjl": int(random.uniform(70,90)),
                        "lhd": int(random.uniform(35,45)),
                    },
                    "db": {
                        "quiz": int(random.uniform(20,30)),
                         "guess": int(random.uniform(10,15)),
                        "six": int(random.uniform(20,30)),
                        "bjl": int(random.uniform(70,90)),
                        "lhd": int(random.uniform(35,45)),
                    }
               }
            }]
            set_cache(number_key, data, 24 * 3600)

            print('初始化人数设置成功')
