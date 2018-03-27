# -*- coding: UTF-8 -*-
from base.backend import FormatListAPIView, CreateAPIView, RetrieveUpdateDestroyAPIView
from .serializers import CategorySerializer
from ..models import Category

from mptt.utils import get_cached_trees
from rest_framework import status
import json


class RecurseTreeNode(object):
    """
    递归获取分类树
    返回格式如：
    [
        {label: "时事", value: "时事", key: 3, children: [{label: "俄罗斯", value: "俄罗斯", key: 4}]}
    ]
    """

    def _node(self, node):
        bits = []
        context = {}
        for child in node.get_children():
            bits.append(self._node(child))
        context['label'] = node.name
        context['value'] = node.name
        context['key'] = node.id
        context['icon'] = node.icon
        if len(bits) > 0:
            context['children'] = bits
        return context

    def tree(self):
        roots = get_cached_trees(Category.objects.filter(is_delete=False))
        bits = [self._node(node) for node in roots]
        return bits


class CategoryListView(FormatListAPIView, CreateAPIView):
    """
    竞猜分类列表
    """
    serializer_class = CategorySerializer

    def list(self, request, *args, **kwargs):
        category_tree = RecurseTreeNode()
        return self.response(category_tree.tree())

    def post(self, request, *args, **kwargs):
        parent = None
        if 'parent' in request.data and request.data['parent'] != '':
            parent = Category.objects.get(name=request.data['parent'])

        category = Category()
        category.name = request.data['name']
        category.parent = parent
        category.admin = request.user
        category.icon = request.data['icon']
        category.save()

        content = {'status': status.HTTP_201_CREATED}
        return self.response(content)


class CategoryDetailView(RetrieveUpdateDestroyAPIView):
    """
    竞猜详情数据
    """
    serializer_class = CategorySerializer
    queryset = Category.objects.all()

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        # 获取上级分类
        if instance.parent_id is not None:
            parent = Category.objects.get(id=instance.parent_id)
            instance.parent_id = parent.name

        content = {
            'status': status.HTTP_200_OK,
            'data': {
                'name': instance.name,
                'parent_id': instance.parent_id,
                'is_delete': instance.is_delete,
                'icon': instance.icon,
            },
        }
        return self.response(content)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if 'is_delete' in request.data:
            instance.is_delete = 1
        if 'name' in request.data:
            instance.name = request.data['name']
        if 'icon' in request.data:
            instance.icon = request.data['icon']
        instance.save()
        content = {'status': status.HTTP_202_ACCEPTED}
        return self.response(content)
