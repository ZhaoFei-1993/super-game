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
            int_quiz_1 = int(random.uniform(6, 8))
            int_guess_1 = int(random.uniform(5, 8))
            usdt_quiz_1 = int(random.uniform(30, 40))
            usdt_guess_1 = int(random.uniform(15, 20))
            btc_quiz_1 = int(random.uniform(10, 15))
            btc_guess_1 = int(random.uniform(5, 8))
            bch_quiz_1 = int(random.uniform(10, 15))
            bch_guess_1 = int(random.uniform(5, 8))
            soc_quiz_1 = int(random.uniform(50, 60))
            soc_guess_1 = int(random.uniform(35, 40))
            db_quiz_1 = int(random.uniform(6, 8))
            db_guess_1 = int(random.uniform(3, 4))
            hand_quiz_1 = int(random.uniform(300, 400))
            hand_guess_1 = int(random.uniform(180, 230))
            eth_quiz_1 = int(random.uniform(50, 60))
            eth_guess_1 = int(random.uniform(35, 40))  # 00.00 - 09.00
            int_quiz_2 = int(random.uniform(20, 30))
            int_guess_2 = int(random.uniform(10, 15))
            usdt_quiz_2 = int(random.uniform(70, 90))
            usdt_guess_2 = int(random.uniform(35, 45))
            btc_quiz_2 = int(random.uniform(20, 25))
            btc_guess_2 = int(random.uniform(13, 16))
            bch_quiz_2 = int(random.uniform(20, 25))
            bch_guess_2 = int(random.uniform(13, 16))
            soc_quiz_2 = int(random.uniform(80, 100))
            soc_guess_2 = int(random.uniform(50, 60))
            db_quiz_2 = int(random.uniform(20, 30))
            db_guess_2 = int(random.uniform(10, 15))
            hand_quiz_2 = int(random.uniform(380, 450))
            hand_guess_2 = int(random.uniform(250, 300))
            eth_quiz_2 = int(random.uniform(80, 100))
            eth_guess_2 = int(random.uniform(50, 60))  # 09.00 - 12.00
            int_quiz_3 = int(random.uniform(6, 8))
            int_guess_3 = int(random.uniform(5, 8))
            usdt_quiz_3 = int(random.uniform(30, 40))
            usdt_guess_3 = int(random.uniform(15, 20))
            btc_quiz_3 = int(random.uniform(15, 19))
            btc_guess_3 = int(random.uniform(8, 13))
            bch_quiz_3 = int(random.uniform(15, 19))
            bch_guess_3 = int(random.uniform(8, 13))
            soc_quiz_3 = int(random.uniform(50, 60))
            soc_guess_3 = int(random.uniform(35, 40))
            db_quiz_3 = int(random.uniform(6, 8))
            db_guess_3 = int(random.uniform(3, 4))
            hand_quiz_3 = int(random.uniform(300, 400))
            hand_guess_3 = int(random.uniform(180, 230))
            eth_quiz_3 = int(random.uniform(50, 60))
            eth_guess_3 = int(random.uniform(35, 40))  # 12.00 - 20.00
            int_quiz_4 = int(random.uniform(40, 50))
            int_guess_4 = int(random.uniform(20, 30))
            usdt_quiz_4 = int(random.uniform(100, 160))
            usdt_guess_4 = int(random.uniform(60, 80))
            btc_quiz_4 = int(random.uniform(38, 45))
            btc_guess_4 = int(random.uniform(20, 25))
            bch_quiz_4 = int(random.uniform(38, 45))
            bch_guess_4 = int(random.uniform(20, 25))
            soc_quiz_4 = int(random.uniform(140, 160))
            soc_guess_4 = int(random.uniform(70, 80))
            db_quiz_4 = int(random.uniform(40, 50))
            db_guess_4 = int(random.uniform(20, 30))
            hand_quiz_4 = int(random.uniform(700, 800))
            hand_guess_4 = int(random.uniform(350, 450))
            eth_quiz_4 = int(random.uniform(140, 160))
            eth_guess_4 = int(random.uniform(70, 80))  # 20.00 - 23.00
            int_quiz_5 = int(random.uniform(20, 30))
            int_guess_5 = int(random.uniform(10, 15))
            usdt_quiz_5 = int(random.uniform(70, 90))
            usdt_guess_5 = int(random.uniform(35, 45))
            btc_quiz_5 = int(random.uniform(25, 30))
            btc_guess_5 = int(random.uniform(16, 21))
            bch_quiz_5 = int(random.uniform(25, 30))
            bch_guess_5 = int(random.uniform(16, 21))
            soc_quiz_5 = int(random.uniform(50, 60))
            soc_guess_5 = int(random.uniform(35, 40))
            db_quiz_5 = int(random.uniform(20, 30))
            db_guess_5 = int(random.uniform(10, 15))
            hand_quiz_5 = int(random.uniform(380, 450))
            hand_guess_5 = int(random.uniform(250, 300))
            eth_quiz_5 = int(random.uniform(50, 60))
            eth_guess_5 = int(random.uniform(35, 40))  # 23.00 - 00.00
            data = [{
                "1": {
                    "int": {
                        "quiz": int_quiz_1,
                        "guess": int_guess_1
                    },
                    "usdt": {
                        "quiz": usdt_quiz_1,
                        "guess": usdt_guess_1
                    },
                    "btc": {
                        "quiz": btc_quiz_1,
                        "guess": btc_guess_1
                    },
                    "hand": {
                        "quiz": hand_quiz_1,
                        "guess": hand_guess_1
                    },
                    "eth": {
                        "quiz": eth_quiz_1,
                        "guess": eth_guess_1
                    },
                    "bch": {
                        "quiz": bch_quiz_1,
                        "guess": bch_guess_1
                    },
                    "soc": {
                        "quiz": soc_quiz_1,
                        "guess": soc_guess_1
                    },
                    "db": {
                        "quiz": db_quiz_1,
                        "guess": db_guess_1
                    }
                },
                "2": {
                    "int": {
                        "quiz": int_quiz_2,
                        "guess": int_guess_2
                    },
                    "usdt": {
                        "quiz": usdt_quiz_2,
                        "guess": usdt_guess_2
                    },
                    "btc": {
                        "quiz": btc_quiz_2,
                        "guess": btc_guess_2
                    },
                    "hand": {
                        "quiz": hand_quiz_2,
                        "guess": hand_guess_2
                    },
                    "eth": {
                        "quiz": eth_quiz_2,
                        "guess": eth_guess_2
                    },
                    "bch": {
                        "quiz": bch_quiz_2,
                        "guess": bch_guess_2
                    },
                    "soc": {
                        "quiz": soc_quiz_2,
                        "guess": soc_guess_2
                    },
                    "db": {
                        "quiz": db_quiz_2,
                        "guess": db_guess_2
                    }
                },
                "3": {
                    "int": {
                        "quiz": int_quiz_3,
                        "guess": int_guess_3
                    },
                    "usdt": {
                        "quiz": usdt_quiz_3,
                        "guess": usdt_guess_3
                    },
                    "btc": {
                        "quiz": btc_quiz_3,
                        "guess": btc_guess_3
                    },
                    "hand": {
                        "quiz": hand_quiz_3,
                        "guess": hand_guess_3
                    },
                    "eth": {
                        "quiz": eth_quiz_3,
                        "guess": eth_guess_3
                    },
                    "bch": {
                        "quiz": bch_quiz_3,
                        "guess": bch_guess_3
                    },
                    "soc": {
                        "quiz": soc_quiz_3,
                        "guess": soc_guess_3
                    },
                    "db": {
                        "quiz": db_quiz_3,
                        "guess": db_guess_3
                    }
                },
                "4": {
                    "int": {
                        "quiz": int_quiz_4,
                        "guess": int_guess_4
                    },
                    "usdt": {
                        "quiz": usdt_quiz_4,
                        "guess": usdt_guess_4
                    },
                    "btc": {
                        "quiz": btc_quiz_4,
                        "guess": btc_guess_4
                    },
                    "hand": {
                        "quiz": hand_quiz_4,
                        "guess": hand_guess_4
                    },
                    "eth": {
                        "quiz": eth_quiz_4,
                        "guess": eth_guess_4
                    },
                    "bch": {
                        "quiz": bch_quiz_4,
                        "guess": bch_guess_4
                    },
                    "soc": {
                        "quiz": soc_quiz_4,
                        "guess": soc_guess_4
                    },
                    "db": {
                        "quiz": db_quiz_4,
                        "guess": db_guess_4
                    }
                },
                "5": {
                    "int": {
                        "quiz": int_quiz_5,
                        "guess": int_guess_5
                    },
                    "usdt": {
                        "quiz": usdt_quiz_5,
                        "guess": usdt_guess_5
                    },
                    "btc": {
                        "quiz": btc_quiz_5,
                        "guess": btc_guess_5
                    },
                    "hand": {
                        "quiz": hand_quiz_5,
                        "guess": hand_guess_5
                    },
                    "eth": {
                        "quiz": eth_quiz_5,
                        "guess": eth_guess_5
                    },
                    "bch": {
                        "quiz": bch_quiz_5,
                        "guess": bch_guess_5
                    },
                    "soc": {
                        "quiz": soc_quiz_5,
                        "guess": soc_guess_5
                    },
                    "db": {
                        "quiz": db_quiz_5,
                        "guess": db_guess_5
                    }
                },

            }]
            set_cache(number_key, data, 24 * 3600)

            print('初始化人数设置成功')
