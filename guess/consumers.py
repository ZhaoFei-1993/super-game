# -*- coding: UTF-8 -*-
from channels.consumer import get_channel_layer
from asgiref.sync import async_to_sync
from guess.models import Periods


def confirm_period(period_id, period_status):
    """
    发送确认
    :param period_id 期数ID
    :param period_status 状态
    :return:
    """
    group = 'period_' + str(period_id)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "stock.message",
            "period_id": period_id,
            "period_status": period_status,
        },
    )


def guess_pk_detail(issue_id):
    """
        推送详情标志
        :param issue_id 当前期数
        :return:
    """
    group = 'guess_pk_' + str(issue_id)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "detail.message",
        },
    )


def guess_pk_result_list(issue_id):
    """
        推送结果列表标志
        :param issue_id 当前期数
        :return:
    """
    group = 'guess_pk_' + str(issue_id)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "result_list.message",
        },
    )


def guess_graph(period_id, index_dic):
    """
        推送结果列表标志
        :param period_id 当前期数
        :param index_dic
        :return:
    """
    group = 'period_' + str(period_id)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "guess_graph.message",
            "group": group,
            "index_dic": index_dic,
        },
    )


def guess_pk_index(issue, left_index_value, right_index_value):
    """
        推送指数
        :param issue 期数对象
        :param left_index_value
        :param right_index_value
        :return:
    """
    left_periods_id = issue.left_periods_id
    right_periods_id = issue.right_periods_id
    periods_obj_dic = {}
    for periods in Periods.objects.filter(id__in=[left_periods_id, right_periods_id]):
        periods_obj_dic.update({
            periods.id: {
                'start_value': periods.start_value,
            }
        })
    # color 1: 涨, 2: 跌, 3: 平
    left_start_value = periods_obj_dic[left_periods_id]['start_value']
    if left_index_value > left_start_value:
        left_index_color = 1
    elif left_index_value < left_start_value:
        left_index_color = 2
    else:
        left_index_color = 3

    right_start_value = periods_obj_dic[right_periods_id]['start_value']
    if right_index_value > right_start_value:
        right_index_color = 1
    elif right_index_value < right_start_value:
        right_index_color = 2
    else:
        right_index_color = 3

    group = 'guess_pk_' + str(issue.id)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "index.message",

            "left_index_value": str(left_index_value),
            "left_index_color": left_index_color,

            "right_index_value": str(right_index_value),
            "right_index_color": right_index_color,
        },
    )
