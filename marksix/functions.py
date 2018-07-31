from rest_framework.pagination import LimitOffsetPagination
from datetime import datetime


class CountPage(LimitOffsetPagination):
    max_limit = 10  # 最大限制默认是None
    default_limit = 10  # 设置每一页显示多少条
    limit_query_param = 'limit'  # 往后取几条
    offset_query_param = 'offset'  # 当前所在的位置

def date_exchange(dt):
    return dt.strftime("%Y年%m月%d日 %H:%M:%S")


def valied_content(content, min=0, max=0):
    """
    :param content: 下注号码串，以,分割号码
    :param min: 最少
    :param max: 
    :return: 判断结果
    """
    content_list = content.strip(',').split(',')
    # # 判断是否是合法号码
    # for num in content_list:
    #     if not '01' <= num <= '49':
    #         print(num)
    #         return 0

    if not min <= len(content_list) <= max:
        print(content_list,'----------')
        return 0

    return 1


if __name__ == '__main__':
    print(valied_content('01,02,03,', 3, 10))
