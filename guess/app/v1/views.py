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
        data = []
        for list in items:
            data.append({
                "id": list["pk"],
                "title": list["title"],
                "periods": list["periods"],
                "closing_time": list["closing_time"],
                "previous_result": list["previous_result"],
                "previous_result_colour": list["previous_result_colour"],
                "last_result": list["last_result"],
                "index": list["index"],
                "index_colour": list["index_colour"],
                "rise": list["rise"],
                "fall": list["fall"]
            })

        return self.response({'code': 0, 'data': data})