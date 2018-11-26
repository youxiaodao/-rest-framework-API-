#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/11/22 10:59
# @Author  : DollA
# @Theme   : 课程相关序列化组件
from rest_framework import serializers

from api import models


class CouserViewSerializer(serializers.ModelSerializer):
    course_type_display = serializers.CharField(source='get_course_type_display')
    why_study = serializers.CharField(source='coursedetail.why_study')
    # name = serializers.CharField()

    class Meta:
        model = models.Course
        # fields = '__all__'
        fields = ['name', 'course_type_display', 'why_study']


class CouserDetailViewSerializer(serializers.ModelSerializer):
    teachers = serializers.SerializerMethodField()

    class Meta:
        model = models.CourseDetail
        # fields = '__all__'
        fields = ['teachers']

    def get_teachers(self,obj):
        queryset = obj.teachers.all()
        return [{'name':item.name} for item in queryset]

