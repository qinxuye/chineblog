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

from django.contrib import admin
from django.contrib.contenttypes.admin import GenericStackedInline
from django_markdown.models import MarkdownField
from django_markdown.admin import AdminMarkdownWidget

from .models import ArticleTag, Category, Tag, Comment, \
    Article, BlogUser, Link


class ArticleTagInline(admin.TabularInline):
    model = ArticleTag


class CommentInline(GenericStackedInline):
    model = Comment
    max_num = 10


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    inlines = (ArticleTagInline,)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'on_top', 'status', 'pvs', 'uvs', 'created', 'modified')
    list_filter = ('status', 'created', 'modified')
    prepopulated_fields = {"slug": ("title", )}
    search_fields = ('title', 'content')
    formfield_overrides = {MarkdownField: {'widget': AdminMarkdownWidget}}
    fieldsets = [
        ('文章编辑', {'fields': ('title', 'slug', 'content_markdown',)}),
        ('日期', {'fields': ('created', 'modified')}),
        ('信息', {'fields': ('category', 'author', 'status', 'on_top')}),
    ]
    readonly_fields = ("created",)
    inlines = (ArticleTagInline, CommentInline)
    list_per_page = 10
    ordering = ['-created']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('username', 'email_address', 'site', 'content',
                    'avatar', 'ip', 'visible', 'post_date', 'comment_obj',)
    formfield_overrides = {MarkdownField: {'widget': AdminMarkdownWidget}}
    list_per_page = 10


@admin.register(BlogUser)
class BlogUserAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'small_avatar', 'info' )
    formfield_overrides = {MarkdownField: {'widget': AdminMarkdownWidget}}


@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = ('name', 'site')
