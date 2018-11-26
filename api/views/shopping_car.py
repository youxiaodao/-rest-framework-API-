#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/11/23 11:31
# @Author  : DollA
# @Theme   : 购物车相关
import json
import redis

from rest_framework.views import APIView
from rest_framework.response import Response
from api.authentication.my_authentication import MyAuthentication
from django_redis import get_redis_connection
from django.core.exceptions import ObjectDoesNotExist

from api import models
from utils.my_response import MyBaseResponse
from utils.my_exceptions import PricePolicyInvalid
from django.conf import settings


class ShoppingCar(APIView):
    """
    购物车相关
        1、这个操作之前，需要登录认证
        2、配置redis
        """

    authentication_classes = [MyAuthentication, ]
    conn = get_redis_connection('default')

    def get(self, request, *args, **kwargs):
        """
        查看购物车
            根据用户ID拼接key，去redis查询信息
            注意:
                price_policy还需要json.load
            使用scan_iter，
            返回信息的格式:
                shopping_car_list = [
                    "title":self.conn.hget(key,'title').decode('utf-8'),
                    "img":self.conn.hget(key,'img').decode('utf-8'),
                    "policy":json.loads(self.conn.hget(key,'policy').decode('utf-8')),
                    "default_policy":self.conn.hget(key,'default_policy').decode('utf-8')
                      ]

        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        ret = MyBaseResponse()
        try:
            shopping_car_key = settings.SHOPPING_CAR_KEY % (request.auth.user_id, '*')

            shopping_car_list = []
            for key in self.conn.scan_iter(match=shopping_car_key, count=10):
                info = {
                    'name': self.conn.hget(key, 'name').decode('utf-8'),
                    "img": self.conn.hget(key, 'img').decode('utf-8'),
                    "price_policy": json.loads(self.conn.hget(key, 'price_policy').decode('utf-8')),
                    "default_policy": self.conn.hget(key, 'default_policy').decode('utf-8')
                }
                shopping_car_list.append(info)
            ret.data = shopping_car_list

        except Exception as e:
            print(e)
            ret.code = 1001
            ret.msg = '请求异常'

        return Response(ret.dict)

    def post(self, request, *args, **kwargs):
        """
        添加购物车
            1、接收客户端的参数{课程ID,价格策略ID}
            2、数据库查询到课程信息{课程名，课程图片}
            3、获取课程的所有价格策略,并提取为字典格式
            4、判断用户提交的价格策略是不是合法
                自定义异常
            5、将购物车保存在Redis中
                格式:shopping_car_用户ID_课程ID:{
                                            course_id:1,
                                            name:xxx,
                                            img:xxx.png,
                                            price_policy:{
                                                    11:{period:xxx,price:99},
                                                    15:{period:xxx,price:199},
                                                    16:{period:xxx,price:299},
                                                    },
                                            default_policy:0,
                                            }
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        ret = MyBaseResponse()
        try:
            course_id = int(request.data.get('course_id'))
            policy_id = int(request.data.get('policy_id'))
            course_obj = models.Course.objects.get(pk=course_id)  # 使用get，当课程不存在的时候，跑出异常
            policy_objs = course_obj.price_policy.all()

            # 将价格策略转化为字典
            price_policy_dict = {}
            for policy in policy_objs:
                price_policy_dict[policy.pk] = {
                    'period': policy.valid_period,
                    'period_display': policy.get_valid_period_display(),
                    'price': policy.price,
                }
            if policy_id not in price_policy_dict:
                raise PricePolicyInvalid('非法的价格策略请求')

            # 将购物信息添加到redis中
            shopping_car_key = settings.SHOPPING_CAR_KEY % (request.auth.user_id, course_id)
            car_dict = {
                'course_id': course_id,
                'name': course_obj.name,
                'img': course_obj.course_img,
                'price_policy': json.dumps(price_policy_dict),
                'default_policy': policy_id
            }
            self.conn.hmset(shopping_car_key, car_dict)
            ret.data = '添加成功'

        except PricePolicyInvalid as e:
            ret.code = 2001
            ret.error = e.msg

        except ObjectDoesNotExist as e:
            ret.code = 1001
            ret.error = '该课程不存在'

        except Exception as e:
            print(e)
            ret.code = 1002
            ret.error = '请求出现异常'

        return Response(ret.dict)

    def delete(self, request, *args, **kwargs):
        """
        删除购物车
            获取课程ID，拼接key
            前端传过来的是一个ID列表，加工成key，列表
            直接删除conn.delete

        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        ret = MyBaseResponse()
        try:
            course_id_list = request.data.get('course_ids')
            keys_list = [settings.SHOPPING_CAR_KEY % (request.auth.user_id, id) for id in course_id_list]
            self.conn.delete(*keys_list)
            ret.msg = '删除成功！'

        except Exception as e:
            ret.code = 1004
            ret.error = '操作失败'
        return Response(ret.dict)

    def patch(self, request, *args, **kwargs):
        """
        修改购物车
            修改的地方只有价格策略
            获取课程ID，价格策略ID，拼接key
            判断:
                redis是不是存在这个key，否则是非法请求
                该课程的价格策略中是否存在这一个，否则是非法请求
            查询到信息，更改default_policy
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        ret = MyBaseResponse()
        try:
            course_id = int(request.data.get('course_id'))
            policy_id = str(request.data.get('policy_id'))
            shoppping_car_key = settings.SHOPPING_CAR_KEY % (request.auth.user_id, course_id)

            if not self.conn.exists(shoppping_car_key):
                ret.code = 1004
                ret.error = "购物车中没有这个课程"
                return Response(ret.dict)
            # policy_dict = json.load(self.conn.hget(shoppping_car_key,'price_policy').decode('utf-8'))
            #  报错 'str' object has no attribute 'read'
            # 原因是错用了json.load
            policy_dict = json.loads(str(self.conn.hget(shoppping_car_key, 'price_policy'), encoding='utf-8'))

            if policy_id not in policy_dict:
                ret.code = 1003
                ret.error = "非法的价格策略"

            self.conn.hset(shoppping_car_key, 'default_policy', policy_id)

            ret.data = '修改成功'


        except Exception as e:
            print(e)
            ret.code = 1001
            ret.error = '请求失败'

        return Response(ret.dict)
