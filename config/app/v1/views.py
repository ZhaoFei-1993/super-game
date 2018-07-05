# -*- coding: UTF-8 -*-
from base.app import ListAPIView
from django.conf import settings


class Html5ConfigView(ListAPIView):
    """
    return html5 config
    """
    authentication_classes = ()

    def list(self, request, *args, **kwargs):
        """
        return html5 config
        """
        return self.response({
            'code': 0,
            'is_captcha_enable': 1 if settings.IS_USER_CAPTCHA_ENABLE else 0,
            'is_club_profit_enable': 1 if settings.CLUB_REVENUE else 0,
        })
