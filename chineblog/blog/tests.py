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

import tempfile
import shutil

from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from whoosh.index import open_dir
from whoosh.qparser import QueryParser

from .models import Category, Article, BlogUser, Comment
from .search import index_article
from .utils import to_text


class CategoryModelTestCase(TestCase):
    def test_create_category(self):
        cate1 = Category.objects.create(name='cate1', slug='cate1')
        cate2 = Category.objects.create(name='cate2', slug='cate2')

        self.assertEqual(cate1.order, 1)
        self.assertEqual(cate2.order, 2)


class ArticleModelTestCase(TestCase):
    def setUp(self):
        self.blog_user = BlogUser.objects.create(
            user=User.objects.create_user(username='abc', password='abc'),
        )
        self.cate1 = Category.objects.create(name='cate1', slug='cate1')

    def test_article_markdown_save(self):
        article = Article.objects.create(
            title='test1', slug='test1', abstract_markdown='<p>This is abstract</p>',
            content_markdown='#title\n* content1\n* content2',
            author=self.blog_user, category=self.cate1
        )

        expect_abstract = '<p>This is abstract</p>'
        expect_content = '<h1>title</h1>\n' \
                         '<ul>\n' \
                         '<li>content1</li>\n' \
                         '<li>content2</li>\n' \
                         '</ul>'
        self.assertEqual(article.abstract, expect_abstract)
        self.assertEqual(article.content, expect_content)

        article2 = Article.objects.create(
            title='test2', slug='test2',
            content_markdown='#title\n* content1\n* content2',
            author=self.blog_user, category=self.cate1
        )

        self.assertIsNone(article2.abstract)

    def test_article_click_and_like(self):
        article = Article.objects.create(
            title='test1', slug='test1',
            content_markdown='#title\n* content1\n* content2',
            author=self.blog_user, category=self.cate1
        )

        sess = self.client.session

        article.on_click(sess)
        self.assertEqual(article.pvs, 1)
        self.assertEqual(article.uvs, 1)

        article.on_click(sess)
        self.assertEqual(article.pvs, 2)
        self.assertEqual(article.uvs, 1)

        self.assertTrue(article.on_like(sess))
        self.assertEqual(article.likes, 1)

        self.assertFalse(article.on_like(sess))
        self.assertEqual(article.likes, 1)

    def test_article_index(self):
        index_dir = tempfile.mkdtemp()

        try:
            article = Article.objects.create(
                title='test1', slug='test1',
                content_markdown='#title\n* content1\n* 中文',
                author=self.blog_user, category=self.cate1
            )

            index_article(article, index_dir)

            idx = open_dir(index_dir)
            with idx.searcher() as searcher:
                qp = QueryParser('content', idx.schema)
                q = qp.parse(to_text('中文'))
                self.assertEqual(len(searcher.search(q)), 1)

                q = qp.parse(to_text('ul'))
                self.assertEqual(len(searcher.search(q)), 0)
        finally:
            shutil.rmtree(index_dir)


class CommentModelTestCase(TestCase):
    def setUp(self):
        blog_user = BlogUser.objects.create(
            user=User.objects.create_user(username='abc', password='abc'),
        )
        cate1 = Category.objects.create(name='cate1', slug='cate1')
        self.article = Article.objects.create(
            title='test1', slug='test1',
            content_markdown='#title\n* content1\n* 中文',
            author=blog_user, category=cate1
        )

    def test_comment_save(self):
        comment = Comment.objects.create(
            username='abc',
            email_address='abc@abc.com',
            content_markdown='<script>this</script>\n'
                             '中文\n'
                             '```python\n'
                             'import this\n'
                             '```\n'
                             'http://qinxuye.me',
            content_type=ContentType.objects.get(model='article'),
            object_id=self.article.pk
        )

        expected = '<p>&lt;script&gt;this&lt;/script&gt;\n' \
                   '中文</p>\n' \
                   '<pre><code class="python">import this\n' \
                   '</code></pre>\n\n' \
                   '<p><a href="http://qinxuye.me" rel="nofollow">http://qinxuye.me</a></p>'
        self.assertEqual(comment.content, expected)


class BlogUserModelTestCase(TestCase):
    def test_blog_user_save(self):
        blog_user = BlogUser.objects.create(
            user=User.objects.create_user(username='abc', password='abc'),
            info_markdown='# this title\nword'
        )

        expect = '<h1>this title</h1>\n' \
                 '<p>word</p>'
        self.assertEqual(blog_user.info, expect)
