# -*- coding: UTF-8 -*-
from base.app import ListAPIView
from django.conf import settings
# from .serializers import Gsg_SwitchSerializer
# from ...models import Gsg_Switch


class Html5ConfigView(ListAPIView):
    """
    return html5 config
    """
    authentication_classes = ()
    # serializer_class = Gsg_SwitchSerializer
    #
    # def get_queryset(self):
    #     return Gsg_Switch.objects.all()

    def list(self, request, *args, **kwargs):
        """
        return html5 config
        """
        return self.response({
            'code': 0,
            'is_captcha_enable': 1 if settings.IS_USER_CAPTCHA_ENABLE else 0,
            'is_club_profit_enable': 1 if settings.CLUB_REVENUE else 0,
            'revenue': 1 if settings.CLUB_REVENUE else 0
        })
