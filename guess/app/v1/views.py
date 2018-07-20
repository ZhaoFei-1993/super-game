# -*- coding: UTF-8 -*-
from base.app import ListAPIView
from base.function import LoginRequired
from .serializers import PeriodsListSerialize


class StockList(ListAPIView):
    """
    股票列表
    """
    permission_classes = (LoginRequired,)
    serializer_class = PeriodsListSerialize

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        user = self.request.user.id
        data = []
        for list in items:
            data.append({
                "id": list["id"],
                "days": list["days"],
                "icon": list["icon"],
                "name": list["name"],
                "rewards": list["rewards"],
                "is_sign": list["is_sign"],
                "is_selected": list["is_selected"]
            })
        return self.response({'code': 0, 'data': data})