# -*- coding: utf-8 -*-

import time


def get_time():
    time_now = time.time()
    time_local = time.localtime(time_now)
    dt = time.strftime('%Y-%m-%d %H:%M:%S', time_local)
    return dt
