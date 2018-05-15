# -*- coding: UTF-8 -*-
from channels.consumer import get_channel_layer
from asgiref.sync import async_to_sync


def quiz_send_score(quiz_id, host, guest):
    """
    发送比分
    :param quiz_id 竞猜ID
    :param host     主队分数
    :param guest    客队分数
    :return:
    """
    group = 'quiz_' + str(quiz_id)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "command.message",
            "host": host,
            "guest": guest,
        },
    )


def quiz_send_time(quiz_id, status, quiz_time):
    """
    推送比赛时间
    :param quiz_id:
    :param status      比赛状态： 0:进行中，1:中场休息，2:结束
    :param quiz_time    比赛进行了多少时间（单位：秒）
    :return:
    """
    group = 'quiz_' + str(quiz_id)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "synctime.message",
            'status': status,
            "quiz_time": quiz_time,
        },
    )
