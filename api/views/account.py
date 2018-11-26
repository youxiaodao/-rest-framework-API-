#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/11/23 12:20
# @Author  : DollA
# @Theme   : 登陆相关
import uuid  # 用来生成随机字符串

from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist

from api import models
from utils.my_response import MyBaseResponse

ret = MyBaseResponse()


class LoginView(APIView):

    def post(self, request, *args, **kwargs):
        try:
            user = request.POST.get('username')
            pwd = request.POST.get('password')
            user_obj = models.Account.objects.get(username=user, password=pwd)
            if not user_obj:
                ret.code = 1001
                ret.error = '用户名或者密码错误'
                return Response(ret.dict)
            uid = str(uuid.uuid4())
            models.UserAuthToken.objects.update_or_create(user=user_obj, defaults={'token': uid})
            ret.data = uid

        except ObjectDoesNotExist as e:  # 细粒度异常的捕捉
            ret.code = 1002
            ret.error = '登陆异常'

        except Exception as e:
            ret.code = 1001
            ret.error = '登陆异常'

        return Response(ret.dict)
