#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/11/23 11:57
# @Author  : DollA
# @Theme   : 对登陆用户的认证
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authentication import BaseAuthentication

from api import models


class MyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        """
        自定义认证必须写这个方法来进行用户认证
        :param request:
        :return:
        """
        token = request.query_params.get('token')
        token_obj = models.UserAuthToken.objects.filter(token=token).first()
        if not token_obj:
            return AuthenticationFailed({'code':1001,'error':'认证失败'})
        return (token_obj.user.username,token_obj)

