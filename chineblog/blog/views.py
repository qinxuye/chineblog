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

from django.shortcuts import render_to_response
from django.conf import settings
from django.contrib.auth.models import User
from django.core.context_processors import csrf
from django.core.paginator import Paginator, EmptyPage
from django.http import Http404

from .models import BlogUser, Category, Article, Link


admin = settings.ADMINS[0][0]


def _basic_response(request):
    try:
        author = BlogUser.objects.get(user__username=admin)
    except BlogUser.DoesNotExist:
        user = User.objects.get(username=admin)
        info = 'Define the user info in the admin interface'  # Define the admin info
        avatar = 'avatar.jpg'

        author = BlogUser.objects.create(
            small_avatar=avatar, info_markdown=info, user=user)

    commons = {
        'author': author,
        'categories': Category.objects.all(),
        'populars': Article.objects.order_by('-pvs')[:5],
        'links': Link.objects.all(),
        'debug': settings.DEBUG,
    }
    commons.update(csrf(request))
    return commons


def _paginator_response(request, page, p):
    # p is an instance of Paginator
    page = int(page)
    size = p.num_pages

    left_continual_max = settings.PAGE_ENTRY_EDGE_NUM + settings.PAGE_ENTRY_DISPLAY_NUM / 2 + 1
    left_edge_range = range(1, settings.PAGE_ENTRY_EDGE_NUM + 1)
    left_continual_range = range(1, page)
    left_range = range(page - settings.PAGE_ENTRY_DISPLAY_NUM / 2, page)

    right_continual_min = size - settings.PAGE_ENTRY_DISPLAY_NUM / 2 - 1 \
        if settings.PAGE_ENTRY_DISPLAY_NUM % 2 == 0 \
        else settings.PAGE_ENTRY_DISPLAY_NUM / 2
    right_continual_range = range(page + 1, size + 1)
    right_edge_range = range(size - settings.PAGE_ENTRY_EDGE_NUM + 1, size + 1)
    right_range = range(page + 1, page + settings.PAGE_ENTRY_EDGE_NUM + 1)

    d = locals()
    del d['size']
    return d


def _handle_session(request, save=False, **kwargs):
    session_data = request.session.get('comment_user', {})
    items = ('username', 'email_address', 'site', 'avatar')

    if not save:
        return session_data
    else:
        changed = False
        posts = request.POST

        for item in items:
            if session_data.get(item, '') != posts[item]:
                session_data[item] = posts[item]
                if not changed:
                    changed = True
        if kwargs:
            session_data.update(kwargs)
            if not changed:
                changed = True

        if changed:
            request.session['comment_user'] = session_data


def index(request, page=1):
    p = Paginator(Article.visible_objects.all(), settings.PAGE_SIZE)
    try:
        current_page = p.page(page)
    except EmptyPage:
        raise Http404

    data = locals()
    data.update(_basic_response(request))
    data.update(_paginator_response(request, page, p))

    blog_theme = settings.BLOG_THEME
    return render_to_response('blog/{0}/index.html'.format(blog_theme), data)
