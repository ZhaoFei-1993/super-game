# -*- coding: UTF-8 -*-
from channels.consumer import get_channel_layer
from asgiref.sync import async_to_sync


def quiz_send_score(quiz_id):
    """
    发送比分
    :param quiz_id 竞猜ID
    :return:
    """
    group = 'quiz_' + str(quiz_id)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "command.message",
            "host": 1,
            "guest": 2,
        },
    )
