# -*- coding: UTF-8 -*-
from channels.consumer import get_channel_layer
from asgiref.sync import async_to_sync


def confirm_period(period_id, is_seal):
    """
    发送确认
    :param period_id 期数ID
    :param is_seal 是否封盘
    :return:
    """
    group = 'period_' + str(period_id)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "stock.message",
            "period_id": period_id,
            "is_seal": is_seal,
        },
    )
