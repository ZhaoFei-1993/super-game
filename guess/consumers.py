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


def guess_graph(period_id, index_list):
    """
        推送结果列表标志
        :param period_id 当前期数
        :param index_list
        :return:
    """
    group = 'period_' + str(period_id)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "guess_graph.message",
            "index_list": index_list,
        },
    )
