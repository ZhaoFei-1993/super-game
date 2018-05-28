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
            "quiz_id": quiz_id,
            "host": host,
            "guest": guest,
        },
    )


def quiz_send_football_time(quiz_id, status, quiz_time):
    """
    推送足球比赛时间
    :param quiz_id:
    :param status: 比赛状态： 0 => 进行中，1 => 中场休息，2 => 结束, 3 => 未开始
    :param quiz_time    比赛进行了多少时间（单位：秒）
    :return:
    """
    group = 'quiz_' + str(quiz_id)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "footballsynctime.message",
            "quiz_id": quiz_id,
            'status': status,
            "quiz_time": quiz_time,
        },
    )


def quiz_send_basketball_time(quiz_id, status):
    """
    推送篮球比赛时间
    :param quiz_id:
    :param status:    比赛状态: 0:未开始, 1: 第一节, 2: 第二节, 3: 第三节，4: 第四节, 50: 中场休息, -1: 结束
    :return:
    """
    group = 'quiz_' + str(quiz_id)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "basketballsynctime.message",
            "quiz_id": quiz_id,
            'status': status,
        },
    )

