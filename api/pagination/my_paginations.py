#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/11/22 10:07
# @Author  : DollA
# @Theme   : 分页组件
from rest_framework.pagination import PageNumberPagination


class MyPageNumberPagination(PageNumberPagination):
    page_size = 2
    page_size_query_param = 'size'
    max_page_size = 5
    page_query_param = 'page'
