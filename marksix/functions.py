from rest_framework.pagination import LimitOffsetPagination

class CountPage(LimitOffsetPagination):
    max_limit = 10  # 最大限制默认是None
    default_limit = 10  # 设置每一页显示多少条
    limit_query_param = 'limit'  # 往后取几条
    offset_query_param = 'offset'  # 当前所在的位置