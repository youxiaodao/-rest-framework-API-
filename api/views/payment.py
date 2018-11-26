#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/11/24 10:32
# @Author  : DollA
# @Theme   : 结算中心视图相关
import json
import datetime

from rest_framework.views import APIView
from django_redis import get_redis_connection
from django.conf import settings

from api import models
from rest_framework.response import Response
from api.authentication.my_authentication import MyAuthentication
from utils.my_response import MyBaseResponse


class PaymentView(APIView):
    authentication_classes = [MyAuthentication, ]
    conn = get_redis_connection('default')

    def post(self, request, *args, **kwargs):
        """
        将商品添加到结算中心
        1、清空当前用户中心的数据(商品信息和购物券信息)
            1.1、拼接key
                payment_用户ID_*
                payment_coupon_用户ID
            1.2、用conn.keys获取用户商品列表
            1.3、将优惠券的key放入列表中
            1.4、删除所有，self.conn.delete(*list)
        2、将新的结算信息加入redis
            2.1、结算中心结构
                商品信息:
                payment_1_2:{
                    'course_id':2,
                    'title': 'CRM客户关系管理系统实战开发-专题',
                    'img': 'CRM.jpg',
                    'policy_id': '4',
                    'coupon': {},
                    'default_coupon': 0,
                    'period': 210, 'period_display': '12个月', 'price': 122.0},
                },
                全站购物券信息:
                payment_global_coupon_1:{
                    'coupon': {
                        2: {'coupon_type': 1, 'coupon_display': '满减券', 'money_equivalent_value': 200, 'minimum_consume': 500}
                    },
                    'default_coupon': 0
                }

            2.2、构造payment_dict字典和global_coupon_dict两个字典
                payment_dict = {
                        ...
                        ...
                    }

                global_coupon_dict = {
                    "coupon":{},
                    "default_coupon":0
                }
            2.3、将课程信息和购物券信息加入结算中心
                2.3.1、获取要结算的课程ID列表
                2.3.2、循环这个列表，拼接成购物车的key，
                2.3.3、检测拼接的key是否在redis购物车信息中，即该请求结算的课程是否在购物车中
                2.3.4、从购物车取出信息，加入结算中心
                    图片、名称、价格策略(默认价格策略ID，该策略的详情)
                    注意:价格策略需要json.loads
                2.3.5、获取优惠券
                    获取当前时间,作为筛选条件，筛选出用户的所有优惠券
                    循环所有的优惠券
                        先处理没有绑定课程的优惠券
                            获取券ID、券类型，
                            根据券类型，获取优惠信息，封装在字典中
                        获取绑定的课程ID
                            获取券ID、类型
                            根据券类型，获取优惠信息，封装在字典中
                        以券ID为key，券信息为值-->保存在panment_dict中的绑定课程ID的coupon中

        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        ret = MyBaseResponse()
        try:
            current_user_keys_list = self.conn.keys(settings.PAYMENT_KEY % (request.auth.user_id, "*"))
            current_user_keys_list.append(settings.PAYMENT_COUPON_KEY % request.auth.user_id)
            self.conn.delete(*current_user_keys_list)

            payment_dict = {
            }
            """
            字典数据结构
            'course_id': {
                'course_id': None,
                'name': None,
                'img': None,
                'policy_id': None,
                'coupon': None,
                'default_coupon': None
            }
            """

            global_coupon_dict = {
                'coupon': {},
                'default_coupon': 0
            }
            course_id_list = request.data.get('course_ids')

            for course_id in course_id_list:
                shopping_car_key = settings.SHOPPING_CAR_KEY % (request.auth.user_id, course_id)

                if shopping_car_key not in self.conn.keys(settings.SHOPPING_CAR_KEY % (request.auth.user_id, "*")):
                    ret.code = 1003
                    ret.error = '请求得课程ID<%s>不在购物车中' % course_id

                price_policy = json.loads(self.conn.hget(shopping_car_key, 'price_policy').decode('utf-8'))
                default_policy = self.conn.hget(shopping_car_key, 'default_policy').decode('utf-8')
                current_policy_info = price_policy[default_policy]

                current_course_dict = {
                    'course_id': str(course_id),
                    'name': self.conn.hget(shopping_car_key, 'name').decode('utf-8'),
                    'img': self.conn.hget(shopping_car_key, 'img').decode('utf-8'),
                    'price_policy_id': default_policy,
                    'coupon': [],
                    'default_coupon': 0
                }

                current_course_dict.update(current_policy_info)
                payment_dict[str(course_id)] = current_course_dict

            current_time = datetime.date.today()

            coupon_list = models.CouponRecord.objects.filter(
                account=request.auth.user,
                status=0,
                coupon__valid_begin_date__lte=current_time,
                coupon__valid_begin_date__gte=current_time,
            )
            for coupon in coupon_list:
                coupon_id = coupon.id
                coupon_type = coupon.coupon.coupon_type

                coupon_info = {'coupon_id': coupon_id,
                               'coupon_type': coupon_type,
                               'coupon_type_display': coupon.coupon.get_coupon_type_display()}

                if coupon_type == 0:  # 立减
                    coupon_info['money_equivalent_value'] = coupon.coupon.money_equivalent_value
                elif coupon_type == 1:  # 满减
                    coupon_info['money_equivalent_value'] = coupon.coupon.money_equivalent_value
                    coupon_info['minimum_consume'] = coupon.coupon.minimum_consume
                else:  # 折扣
                    coupon_info['off_percent'] = coupon.coupon.off_percent

                if not coupon.coupon.object_id:
                    global_coupon_dict['coupon'][coupon_id] = coupon_info

                    continue

                coupon_course_id = str(coupon.coupon.object_id)
                if coupon_course_id not in payment_dict:
                    continue

                payment_dict[coupon_course_id]['coupon'][coupon_id] = coupon_info

            for cid, cinfo in payment_dict.items():
                payment_key = settings.PAYMENT_KEY % (request.auth.user_id, cid)
                cinfo['coupon'] = json.dumps(cinfo['coupon'])
                self.conn.hmget(payment_key, cinfo)

                global_coupon_key = settings.PAYMENT_COUPON_KEY % request.auth.user_id
                global_coupon_dict['coupon'] = json.dumps(global_coupon_dict['coupon'])
                self.conn.hmget(global_coupon_key, global_coupon_dict)

        except Exception as e:
            ret.code = 1001
            ret.error = '请求失败'

        return Response(ret.dict)

    def patch(self, request, *args, **kwargs):
        """
        堆结算中心的优惠券进行修改
        1、获取课程ID，优惠券ID
            如果是全站优惠券，就没有课程ID
        2、拼接key
        3、修改优惠券
            修改全站优惠券
                如果请求的是0，表示不使用
                根据key获取用户的所有全站优惠券，如果请求的优惠券不合法，返回错误
                有优惠券ID，且优惠券合法，将default_coupon修改为coupon_id

            修改绑定课程的优惠券
                如果请求的是0，表示不适用
                根据key获取所有的优惠券,如果请求的优惠券不合法，返回错误
                有优惠券ID，且优惠券合法，将default_coupon修改为coupon_id

        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        ret = MyBaseResponse()
        try:
            course_id = request.data.get('course_id')
            course_id = str(course_id) if course_id else course_id
            coupon_id = str(request.data.get('coupon_id'))

            payment_key = settings.PAYMENT_KEY % (request.auth.user_id, course_id)
            global_coupon_key = settings.PAYMENT_COUPON_KEY % request.auth.user_id

            if not course_id:
                if coupon_id == "0":
                    self.conn.hset(global_coupon_key, 'default_coupon', coupon_id)
                global_coupon_dict = json.loads(self.conn.hget(global_coupon_key, 'coupon').decode('utf-8'))

                if coupon_id not in global_coupon_dict:
                    ret.code = 1001
                    ret.error = '请求参数不合法'
                    return Response(ret.dict)
                self.conn.hset(global_coupon_key, 'default_coupon', coupon_id)
                ret.msg = "修改成功"

                return Response(ret.dict)
            if coupon_id == "0":
                self.conn.hget(payment_key, 'default_coupon', coupon_id)
                ret.msg = '修改成功'
                return Response(ret.dict)

            coupon_dict = json.loads(self.conn.hget(payment_key, 'coupon').decode('utf-8'))
            if coupon_id not in coupon_dict:
                ret.code = 1001
                ret.error = '请求参数不合法'
                return Response(ret.dict)
            self.conn.hset(payment_key, 'default_coupon', coupon_id)

        except Exception as e:
            ret.code = 1001
            ret.error = '请求异常'
        return Response(ret.dict)

    def get(self, request, *args, **kwargs):
        """
        查看结算中心
            1、拼接KEY
            2、获取绑定课程信息
                获取该用户的所有存在结算中心的key
                循环，拿出每一个key对应的字典
                如果对应的key是coupon，需要json.loads
                将值转化成字符串，添加到课程信息中
                并添加到所有课程字典中

            3、获取全站优惠券
                coupon对应的字典需要json.loads

            4、返回data给前端

        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        ret = MyBaseResponse()
        try:
            payment_key = settings.PAYMENT_KEY % (request.auth.user_id, "*")
            global_coupon_key = settings.PAYMENT_COUPON_KEY % request.auth.user_id

            course_list = []

            for key in self.conn.scan_iter(payment_key):
                course_info = {}
                data = self.conn.hgetll(key)
                for k, value in data.items():
                    k = k.decode('utf-8')
                    if k == 'coupon':
                        value = json.loads(value.decode('utf-8'))
                        course_info[k] = value
                    else:
                        course_info[k] = value.decode('utf-8')
                course_list.append(course_info)

            global_coupon_dict = {
                'coupon': json.loads(self.conn.hget(global_coupon_key, 'coupon').decode('utf-8')),
                'default_coupon': self.conn.hget(global_coupon_key, 'default_coupon').decode('utf-8')
            }

            ret.data = {
                'course_list': course_list,
                'global_coupon_dict': global_coupon_dict
            }

        except Exception as e:
            ret.code = 1001
            ret.error = "请求异常"

        return Response(ret.dict)
