# -*- coding: UTF-8 -*-
from channels.consumer import get_channel_layer
from asgiref.sync import async_to_sync


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


def guess_pk_index(issue_id, left_stock_index, right_stock_index):
    """
        推送指数
        :param issue_id 当前期数
        :param left_stock_index
        :param right_stock_index
        :return:
    """
    group = 'guess_pk_' + str(issue_id)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "index.message",
            "left_stock_index": left_stock_index,
            "right_stock_index": right_stock_index,
        },
    )
