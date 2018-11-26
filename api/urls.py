#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/11/21 12:58
# @Author  : DollA
# @Theme   : api 的路由

# from django.urls import re_path
from django.conf.urls import url

from api.views import course
from api.views import account
from api.views import shopping_car
from api.views import order

urlpatterns = [
    url('login$', account.LoginView.as_view()),

    url('course/$', course.CourseView.as_view({'get': 'list'})),
    url('course/(?P<id>\d+)/$', course.CourseView.as_view({'get': 'retrieve'})),

    url('shopping_car$', shopping_car.ShoppingCar.as_view()),

    url('order$',)

]
