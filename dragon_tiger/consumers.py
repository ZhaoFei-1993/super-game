# -*- coding: UTF-8 -*-
from channels.consumer import get_channel_layer
from asgiref.sync import async_to_sync


def dragon_tiger__send_score(table_id, boots, guest):
    """
    发送比分
    :param quiz_id 竞猜ID
    :param host     主队分数
    :param guest    客队分数
    :return:
    """
    group = 'dragon_tiger_' + str(table_id)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "command.message",
            "table_id": table_id,
            "boots": boots,
            "guest": guest,
        },
    )
