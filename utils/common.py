# -*- coding: UTF-8 -*-
"""
公共处理方法
"""
from django.conf import settings
import os


def get_user_message_save_path(message_id):
    """
    用户信息内容保存路径
    :param message_id:
    :return:
    """
    user_message_dir = settings.USER_MESSAGE_SAVE_PATH
    if not os.path.exists(user_message_dir):
        os.mkdir(user_message_dir)

    max_dir_level = 10000

    user_messages_id_dir = user_message_dir + str(message_id % max_dir_level) + '/'
    if not os.path.exists(user_messages_id_dir):
        os.mkdir(user_messages_id_dir)

    return user_messages_id_dir


def save_user_message_content(user_message_id, data):
    """
    存储用户消息内容
    :param user_message_id: 消息ID
    :param data: 消息内容：标题、标题（英文）、内容、内容（英文）
    :return:
    """
    user_messages_id_dir = get_user_message_save_path(user_message_id)
    with open(user_messages_id_dir + str(user_message_id), 'w') as f:
        message_content = [data['title'], data['title_en'], data['content'], data['content_en']]
        f.write(settings.USER_MESSAGE_SEPARATOR.join(message_content))


def get_user_message_content(user_message_id):
    """
    获取存储的用户消息内容
    :param user_message_id:
    :return:
    """
    user_message_dir = get_user_message_save_path(user_message_id)
    with open(user_message_dir + str(user_message_id)) as f:
        message_content = f.readlines()
    message_content = [x.strip() for x in message_content]
    message_content = message_content[0]
    title, title_en, content, content_en = message_content.split(settings.USER_MESSAGE_SEPARATOR)

    return {
        'title': title,
        'title_en': title_en,
        'content': content,
        'content_en': content_en,
    }
