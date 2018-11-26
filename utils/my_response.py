#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/11/21 13:52
# @Author  : DollA
# @Theme   : 封装返回值的类
"""
解耦之后，不用每次都写一个字典
"""


class MyBaseResponse:
    def __init__(self):
        self.code = 1000
        self.msg = None
        self.error = None

    @property
    def dict(self):
        return self.__dict__
