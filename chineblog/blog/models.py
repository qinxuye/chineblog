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
from __future__ import unicode_literals

import re

import markdown
import bleach
from django.db import models
from django.db import transaction
from django.contrib.contenttypes import fields
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.admin import User
from django.core.urlresolvers import reverse
from django.conf import settings
from django_markdown.models import MarkdownField
from mptt.models import MPTTModel
from mptt.managers import TreeManager
from filebrowser.fields import FileBrowseField

from .managers import VisibleArticleManager, CommentsVisibleManager, \
    CommentToArticleManager, CommentToBlogUserManager
from .utils import tz_now, get_summary, to_text, to_binary, strip_html


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='分类名')
    slug = models.SlugField()
    order = models.IntegerField(null=True, blank=True, verbose_name='顺序')

    class Meta:
        verbose_name = "分类"
        verbose_name_plural = "分类"
        ordering = ['order', ]

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('blog_category', args=(self.slug, ))

    @transaction.atomic
    def save(self, *args, **kwargs):
        if self.order is None:
            agg = Category.objects.all().aggregate(
                max_order=models.Max('order'))
            if agg and agg.get('max_order', None) is not None:
                self.order = agg['max_order'] + 1
            else:
                self.order = 1

        super(Category, self).save(*args, **kwargs)


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='标签名')
    slug = models.SlugField()

    articles = models.ManyToManyField("Article", through="ArticleTag", verbose_name='文章')

    class Meta:
        verbose_name = "标签"
        verbose_name_plural = "标签"
        ordering = ['?']

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('blog_tag', args=(self.slug, ))


class Article(models.Model):
    STATUS_CHOICE = (
        (1, '编辑'),
        (2, '完成'),
        (3, '失效'),
    )

    title = models.CharField(max_length=100, verbose_name='标题')
    slug = models.SlugField(max_length=100)
    abstract_markdown = MarkdownField(verbose_name='摘要（markdown）', null=True, blank=True)
    abstract = models.TextField(verbose_name='摘要', null=True, editable=False)
    content_markdown = MarkdownField(verbose_name='内容（markdown）')
    content = models.TextField(verbose_name='内容', editable=False)
    status = models.IntegerField(choices=STATUS_CHOICE, default=1, verbose_name='状态')
    created = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    modified = models.DateTimeField(default=tz_now, verbose_name='修改时间')
    on_top = models.BooleanField(default=False, verbose_name='置顶')

    # 统计相关
    pvs = models.IntegerField(default=0, editable=False, verbose_name='pv数')
    uvs = models.IntegerField(default=0, editable=False, verbose_name='uv数')
    likes = models.IntegerField(default=0, editable=False, verbose_name='赞的个数')

    category = models.ForeignKey(Category, verbose_name='分类')
    author = models.ForeignKey('BlogUser', verbose_name='作者')
    tags = models.ManyToManyField(Tag, through="ArticleTag", verbose_name='标签')
    comments = fields.GenericRelation('Comment')

    # Managers
    objects = models.Manager()
    visible_objects = VisibleArticleManager()

    class Meta:
        verbose_name = "文章"
        verbose_name_plural = "文章"
        ordering = ['-on_top', '-created']

    def on_click(self, session):
        self.pvs += 1
        if session.get('reads', None) is None:
            self.uvs += 1
            session['reads'] = [self.pk, ]
        else:
            reads = set(session.get('reads', []))
            if self.pk not in reads:
                self.uvs += 1
                reads.add(self.pk)
                session['reads'] = list(reads)
        super(Article, self).save()

    def on_like(self, session):
        if session.get('likes', None) is None:
            self.likes += 1
            session['likes'] = [self.pk, ]
            return True
        else:
            likes = set(session.get('likes', []))
            if self.pk not in likes:
                self.likes += 1
                likes.add(self.pk)
                session['likes'] = list(likes)
                return True

        return False

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog_article', args=(self.slug, ))

    @property
    def summary(self):
        return get_summary(self.content)

    @property
    def visible_comments(self):
        return self.comments.filter(visible=True)

    def save(self, *args, **kwargs):
        if self.abstract_markdown:
            self.abstract = to_binary(markdown.markdown(to_text(self.abstract_markdown)))
        if self.content_markdown:
            self.content = to_binary(markdown.markdown(to_text(self.content_markdown),
                                                       extensions=['fenced_code']))

        super(Article, self).save(*args, **kwargs)


class ArticleTag(models.Model):
    article = models.ForeignKey(Article)
    tag = models.ForeignKey(Tag)

    class Meta:
        verbose_name = "文章标签"
        verbose_name_plural = "文章标签"

    def __unicode__(self):
        return unicode(self.tag)


class Comment(MPTTModel):
    username = models.CharField(max_length=50, verbose_name='用户名')
    email_address = models.EmailField(verbose_name='邮箱地址')
    site = models.URLField(blank=True, verbose_name='站点')
    avatar = models.URLField(blank=True, null=True, verbose_name='头像')
    content_markdown = MarkdownField(verbose_name='内容（markdown）')
    content = models.TextField(verbose_name='内容', editable=False)
    post_date = models.DateTimeField(editable=False, default=tz_now, verbose_name='评论时间')
    visible = models.BooleanField(default=True, verbose_name='是否可见')
    ip = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP地址')

    # mptt
    reply_to_comment = models.ForeignKey("self", blank=True, null=True, related_name="children")

    # contenttypes
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    comment_obj = fields.GenericForeignKey('content_type', 'object_id')

    # Managers
    objects = TreeManager()
    to_article_objects = CommentToArticleManager()
    to_blog_user_objects = CommentToBlogUserManager()
    visible_objects = CommentsVisibleManager()

    class Meta:
        ordering = ['-post_date']
        verbose_name = '评论'
        verbose_name_plural = '评论'

    class MPTTMeta:
        parent_attr = 'reply_to_comment'

    @property
    def is_author(self):
        return self.email_address == settings.ADMINS[0][1]

    def __getattr__(self, name):
        # avatar
        avatar_reg = re.compile("^avatar_([0-9]+)$")
        if avatar_reg.match(name):
            if self.avatar.startswith('http://www.gravatar.com/'):
                size = avatar_reg.match(name).group(0)
                return self.avatar.split('?')[0] + "?s=" + str(size) + "&d=404"
            else:
                return self.avatar

        return super(Comment, self).__getattr__(name)

    def __unicode__(self):
        return self.content

    def save(self, *args, **kwargs):
        if self.content_markdown:
            raw = strip_html(to_text(self.content_markdown), remove=False)
            content = markdown.markdown(raw, extensions=['fenced_code'])
            self.content = to_binary(bleach.linkify(content))

        super(Comment, self).save(*args, **kwargs)


class BlogUser(models.Model):
    small_avatar = FileBrowseField(max_length=40, verbose_name='头像（42×42）', null=True, blank=True)
    info_markdown = MarkdownField(verbose_name='用户信息（markdown）', null=True, blank=True)
    info = models.TextField(verbose_name='用户信息', editable=False, null=True)

    user = models.OneToOneField(User)

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'

    def __unicode__(self):
        return self.user.username

    @property
    def summary(self):
        return get_summary(self.info)

    def save(self, *args, **kwargs):
        if self.info_markdown:
            self.info = to_binary(markdown.markdown(to_text(self.info_markdown)))

        super(BlogUser, self).save(*args, **kwargs)


class Link(models.Model):
    name = models.CharField(max_length=50, verbose_name='链接名')
    site = models.URLField(verbose_name='链接地址')

    class Meta:
        verbose_name = '友情链接'
        verbose_name_plural = '友情链接'

    def __unicode__(self):
        return self.name




