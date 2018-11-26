#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/11/21 13:44
# @Author  : DollA
# @Theme   : 课程视图
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSetMixin
from rest_framework.response import Response

from api import models
from utils.my_response import MyBaseResponse
from api.pagination.my_paginations import MyPageNumberPagination
from api.serializers.course_serializers import CouserViewSerializer,CouserDetailViewSerializer


class CourseView(ViewSetMixin, APIView):
    """
    课程相关视图
    """

    def list(self, request, *args, **kwargs):
        """
        全部课程接口
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        ret = MyBaseResponse()
        print(request.version)
        try:
            course_list = models.Course.objects.all()

            pager = MyPageNumberPagination()

            page_roles = pager.paginate_queryset(queryset=course_list, request=request, view=self)

            ser = CouserViewSerializer(instance=page_roles, many=True, )
            ret.data = ser.data
            return pager.get_paginated_response(ser.data)
        except Exception as e:
            print(e)
            ret.code = 1001
            ret.error = '获取课程失败'

        return Response(ret.dict)

    def retrieve(self,request,*args,**kwargs):

        ret = MyBaseResponse()

        try:

            id = kwargs.get('id')
            print(id)
            course_obj = models.CourseDetail.objects.filter(pk=id).first()
            ser = CouserDetailViewSerializer(instance=course_obj,many=False)

            return Response(ser.data)
        except Exception as e:
            print(e)
            ret.code = 1001
            ret.error = '获取课程失败'

        return Response(ret.dict)


