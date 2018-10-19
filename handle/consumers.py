from django.conf import settings
from django.core.mail import send_mail


def send_alert_email(exception, traceback, url):
    """
    消费报警邮件
    :param exception:   异常名称
    :param traceback:   异常追踪
    :param url:         出现异常的请求
    :return:
    """
    subject = 'GSG程序报警'
    message = 'exception = ' + str(exception) + "\n\n" + 'traceback = ' + str(traceback) + "\n" + 'url = ' + url + "\n"
    email_from = settings.EMAIL_HOST_USER
    recipient_list = settings.EMAIL_RECIPIENT_LIST

    send_mail(subject, message, email_from, recipient_list)
    print('alert email sent success')
    return True
