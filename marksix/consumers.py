# -*- coding: UTF-8 -*-
from channels.consumer import get_channel_layer
from asgiref.sync import async_to_sync


def mark_six_result_code(current_issue, next_issue):
    """
        结果号码推送
        :param current_issue 当前期数
        :param next_issue 下期期数
        :return:
    """
    group = 'mark_six_' + str(current_issue)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "result.message",
            "current_issue": str(current_issue),
            "current_issue_open": True,
            "next_issue": str(next_issue),
        },
    )
