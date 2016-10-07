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

import os

from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings
from django.template import loader, Context

from .models import Article, Comment
from .mail import send_mail
from .utils import strip_html, to_str
from .search import index_article as _index_article


@receiver(post_save, sender=Article, dispatch_uid='index_article')
def index_article(sender, instance, **_):
    _index_article(instance)


@receiver(post_save, sender=Comment, dispatch_uid='send_email')
def send_email(sender, instance, **_):
    comment = instance

    if settings.ENABLE_EMAIL and comment.visible:
        template = loader.get_template('blog/phantom/email.html')
        typo = 0 if comment.content_type.model == 'article' else 1
        ctx = Context({
            'type': typo,
            'comment': comment,
            'site': settings.SITE
        })
        html = template.render(ctx)
        plain_text = to_str(strip_html(html))

        if not comment.reply_to_comment:
            to_email = [settings.ADMINS[0][1], ]
            if type == 0:
                subject = '【残阳似血的博客】上的文章刚刚被%s评论了' % comment.username
            else:
                subject = '【残阳似血的博客】刚刚收到%s的留言' % comment.username
        else:
            to_email = [comment.reply_to_comment.email_address, ]
            if type == 0:
                subject = u'您在【残阳似血的博客】上的评论刚刚被%s回复了' % comment.username
            else:
                subject = u'您在【残阳似血的博客】上的留言刚刚被%s回复了' % comment.username
        from_email = settings.EMAIL_HOST_USER
        send_mail(subject, plain_text, from_email, to_email, html=html)