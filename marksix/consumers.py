# -*- coding: UTF-8 -*-
from channels.consumer import get_channel_layer
from asgiref.sync import async_to_sync


def mark_six_result_code(issue, result_code):
    """
        结果号码推送
        :param issue 期数
        :param result_code 结果号码
        :return:
    """
    group = 'mark_six_' + str(issue)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "result.message",
            "result_code": result_code,
        },
    )
