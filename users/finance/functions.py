import time
from datetime import timedelta, datetime
from math import ceil
from rest_framework.pagination import LimitOffsetPagination


def get_now():
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())


def verify_date(str1):
    try:
        datetime.strptime(str1, '%Y-%m-%d')
    except Exception as e:
        return 0
    return 1


def days(start, end):
    # 获取时间相差天数
    start = time.strptime(start, '%Y-%m-%d')
    start = datetime(start[0], start[1], start[2])

    end = time.strptime(end, '%Y-%m-%d')
    end = datetime(end[0], end[1], end[2])
    num = (end - start).days
    return abs(num)


def months(str1, str2):  # 获取两个日期相差的月数
    year1 = datetime.strptime(str1[0:10], "%Y-%m-%d").year
    year2 = datetime.strptime(str2[0:10], "%Y-%m-%d").year
    month1 = datetime.strptime(str1[0:10], "%Y-%m-%d").month
    month2 = datetime.strptime(str2[0:10], "%Y-%m-%d").month
    num = (year1 - year2) * 12 + (month1 - month2)
    return abs(num)


def years(str1, str2):  # 获取两个日期相差多少年
    year1 = int(str1.split('-')[0])
    year2 = int(str2.split('-')[0])
    return abs(year1 - year2)


def weeks(start, end):  # 获取两个日期相差几周
    start = datetime.strptime(start, '%Y-%m-%d')
    end = datetime.strptime(end, '%Y-%m-%d')

    week_start = start - timedelta(days=start.weekday())
    week_end = end - timedelta(days=end.weekday())
    num = int((week_end - week_start).days / 7)
    return abs(num)


def get_range_time(time_type, start, end):  # 获取年月日时间范围
    time_list = []
    s = datetime.strptime(start, "%Y-%m-%d")
    e = datetime.strptime(end, "%Y-%m-%d")
    if time_type == 'd':
        num = days(start, end)
        today_start = datetime.combine(s, datetime.min.time())
        today_end = datetime.combine(s, datetime.max.time())
        time_list.append([today_start, today_end])
        for i in range(1, num + 1):
            prev_start = today_start - timedelta(days=i)
            prev_end = today_end - timedelta(days=i)
            time_list.append([prev_start, prev_end])

    # now_quarter = now.month / 3 if now.month % 3 == 0 else now.month / 3 + 1 季度

    elif time_type == 'w':
        num = weeks(start, end)
        # 本周第一天和最后一天
        this_week_start = e - timedelta(days=e.weekday())
        this_week_start = datetime.combine(this_week_start, datetime.min.time())
        this_week_end = e + timedelta(days=6 - e.weekday())
        this_week_end = datetime.combine(this_week_end, datetime.min.time())
        time_list.append([this_week_start, this_week_end])
        for i in range(1, num + 1):
            this_week_end = this_week_start - timedelta(days=1)
            this_week_start = this_week_end - timedelta(days=6)
            time_list.append([this_week_start, this_week_end])

    elif time_type == 'm':
        num = months(start, end)
        # 本月第一天和最后一天
        this_month_start = datetime(e.year, e.month, 1)
        this_month_end = datetime(e.year, e.month + 1, 1) - timedelta(days=1)
        this_month_end = datetime.combine(this_month_end, datetime.max.time())
        time_list.append([this_month_start, this_month_end])
        for i in range(1, num + 1):
            this_month_end = this_month_start - timedelta(days=1)
            this_month_end = datetime.combine(this_month_end, datetime.max.time())
            this_month_start = datetime(this_month_end.year, this_month_end.month, 1)
            time_list.append([this_month_start, this_month_end])

    # # 本季第一天和最后一天
    # month = (now.month - 1) - (now.month - 1) % 3 + 1
    # this_quarter_start = datetime(now.year, month, 1)
    # this_quarter_end = datetime(now.year, month + 3, 1) - timedelta(days=1)
    #
    # # 上季第一天和最后一天
    # last_quarter_end = this_quarter_start - timedelta(days=1)
    # last_quarter_start = datetime(last_quarter_end.year, last_quarter_end.month - 2, 1)
    elif time_type == 'y':
        num = years(start, end)
        # 本年第一天和最后一天
        this_year_start = datetime(e.year, 1, 1)
        this_year_end = datetime(e.year + 1, 1, 1) - timedelta(days=1)
        this_year_end = datetime.combine(this_year_end, datetime.max.time())
        time_list.append([this_year_start, this_year_end])
        for i in range(1, num + 1):
            this_year_end = this_year_start - timedelta(days=1)
            this_year_start = datetime(this_year_end.year, 1, 1)
            this_year_end = datetime.combine(this_year_end, datetime.max.time())
            time_list.append([this_year_start, this_year_end])

    return time_list


class CountPage(LimitOffsetPagination):
    max_limit = 1  # 最大限制默认是None
    default_limit = 1  # 设置每一页显示多少条
    limit_query_param = 'limit'  # 往后取几条
    offset_query_param = 'offset'  # 当前所在的位置


if __name__ == '__main__':
    # print(get_now())
    print(get_range_time('w', '2018-06-10', '2018-09-09'))
    print(weeks('2018-06-10', '2018-09-09'))
