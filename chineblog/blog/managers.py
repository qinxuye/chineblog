#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright (c) 2016 Qin Xuye <qin@qinxuye.me>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from django.db import models
from django.db.models import Q
from mptt.managers import TreeManager


class VisibleArticleManager(models.Manager):
    def get_query_set(self):
        return super(VisibleArticleManager, self).get_query_set().filter(status=2)


class CommentToArticleManager(TreeManager):
    def get_query_set(self):
        return super(CommentToArticleManager, self) \
            .get_query_set() \
            .filter(Q(visible=True) & Q(content_type__model="article"))


class CommentsVisibleManager(models.Manager):
    def get_query_set(self):
        return super(CommentsVisibleManager, self) \
            .get_query_set() \
            .filter(visible=True)


class CommentToBlogUserManager(TreeManager):
    def get_query_set(self):
        return super(CommentToBlogUserManager, self) \
            .get_query_set() \
            .filter(Q(visible=True) & Q(content_type__model="bloguser"))
